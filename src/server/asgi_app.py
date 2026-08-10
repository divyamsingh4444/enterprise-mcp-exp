"""
Enterprise MCP Server - ASGI Application
Phase 1: Transport & Network + Phase 2: OAuth & Sandboxing + Phase 3: OpenTelemetry
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse

from src.auth.auth_context import AuthContext, get_auth_context
from src.auth.middleware import CorrelationMiddleware, AuditLogger
from src.routers.oauth import router as oauth_router
from src.sandbox.runner import SandboxRunner
from src.tools.sandboxed import (
    run_command_sandboxed,
    read_file_sandboxed,
    write_file_sandboxed,
    list_directory_sandboxed,
)
from src.observability.metrics import MetricsCollector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize metrics (observability tracing disabled due to version compatibility)
metrics = MetricsCollector()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict = {}


class ToolCallResponse(BaseModel):
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Enterprise MCP Server starting up...")
    yield
    logger.info("🛑 Enterprise MCP Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Enterprise MCP Server",
    description="Production-grade Model Context Protocol with OAuth, Sandboxing, and Observability",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation middleware
app.add_middleware(CorrelationMiddleware)

# Initialize audit logger
audit_logger = AuditLogger()

# Initialize sandbox runner
sandbox_runner = SandboxRunner()


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


# Include OAuth router
app.include_router(oauth_router, tags=["authentication"])


# MCP Tool endpoints
@app.get("/api/v1/mcp/tools/list")
async def list_tools(auth: AuthContext = Depends(get_auth_context)):
    """List all available MCP tools"""
    metrics.increment("tool_list_called")

    tools = [
        {
            "name": "run_command",
            "description": "Execute shell commands in a sandboxed environment",
            "required_scope": "tools:shell:execute",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout_s": {"type": "number", "description": "Timeout in seconds (default: 20)"},
                },
                "required": ["command"],
            },
        },
        {
            "name": "read_file",
            "description": "Read file contents from sandbox",
            "required_scope": "tools:filesystem:read",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to a file in sandbox",
            "required_scope": "tools:filesystem:write",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                    "mode": {"type": "string", "enum": ["overwrite", "append"], "description": "Write mode"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "list_directory",
            "description": "List directory contents in sandbox",
            "required_scope": "tools:filesystem:list",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: '.')"},
                },
            },
        },
    ]

    logger.info(f"Tools listed by {auth.sub} from org {auth.org_id}")

    return {"tools": tools, "total": len(tools)}


@app.post("/api/v1/mcp/tools/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    """Execute an MCP tool"""
    import time

    start_time = time.time()
    tool_name = request.tool
    arguments = request.arguments

    # Tool to scope mapping
    tool_scopes = {
        "run_command": "tools:shell:execute",
        "read_file": "tools:filesystem:read",
        "write_file": "tools:filesystem:write",
        "list_directory": "tools:filesystem:list",
    }

    # Check if tool exists
    if tool_name not in tool_scopes:
        duration_ms = (time.time() - start_time) * 1000
        metrics.increment("tool_execution_failure")

        logger.error(f"Tool not found: {tool_name} by {auth.sub}")

        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # Check scope
    required_scope = tool_scopes[tool_name]
    if not auth.has_scope(required_scope):
        duration_ms = (time.time() - start_time) * 1000
        metrics.increment("scope_check_failure")
        metrics.increment("tool_execution_failure")

        logger.warning(f"Scope denied: {required_scope} for {auth.sub}")

        raise HTTPException(
            status_code=403,
            detail=f"Missing required scope: {required_scope}",
        )

    # Execute tool
    try:
        if tool_name == "run_command":
            result = await run_command_sandboxed(
                arguments.get("command", ""),
                arguments.get("timeout_s", 20.0),
                auth,
            )
        elif tool_name == "read_file":
            result = await read_file_sandboxed(
                arguments.get("path", ""),
                auth,
            )
        elif tool_name == "write_file":
            result = await write_file_sandboxed(
                arguments.get("path", ""),
                arguments.get("content", ""),
                arguments.get("mode", "overwrite"),
                auth,
            )
        elif tool_name == "list_directory":
            result = await list_directory_sandboxed(
                arguments.get("path", "."),
                auth,
            )

        duration_ms = (time.time() - start_time) * 1000
        metrics.increment("tool_execution_success")
        metrics.record_tool_execution_duration(duration_ms)

        logger.info(f"Tool executed successfully: {tool_name} by {auth.sub} in {duration_ms:.0f}ms")

        return ToolCallResponse(
            success=True,
            result=result,
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.increment("tool_execution_failure")

        logger.error(f"Tool execution failed: {tool_name} by {auth.sub}: {str(e)}")
        return ToolCallResponse(
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )


# Metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return metrics.export_prometheus()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.server.asgi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )

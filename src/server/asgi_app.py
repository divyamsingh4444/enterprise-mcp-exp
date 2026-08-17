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

from src.auth.auth_context import AuthContext, get_auth_context, require_authenticated
from src.auth.middleware import CorrelationMiddleware, AuditLogger
from src.routers.oauth import router as oauth_router, init_test_user
from src.sandbox.runner import SandboxRunner
from src.tools.sandboxed import (
    run_command_sandboxed,
    read_file_sandboxed,
    write_file_sandboxed,
    list_directory_sandboxed,
)
from src.observability.metrics import MetricsCollector
from src.observability.otel import tracer  # Initialize OpenTelemetry
from src.observability.trace_store import trace_store

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
    init_test_user()
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


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Enterprise MCP Server",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "auth": "/auth/login, /auth/signup, /auth/logout",
            "tools": "/api/v1/mcp/tools/list, /api/v1/mcp/tools/call",
            "metrics": "/metrics"
        }
    }


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


# API health check endpoint (alias for /health)
@app.get("/api/health", response_model=HealthResponse)
async def api_health_check():
    """API health check endpoint (alias)"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


# Traces endpoint
@app.get("/api/v1/mcp/traces")
async def get_traces(limit: int = 50, auth: AuthContext = Depends(require_authenticated)):
    """Get recent tool execution traces"""
    metrics.increment("traces_queried")
    traces = trace_store.get_recent(limit=limit)
    stats = trace_store.stats()
    return {"traces": traces, "stats": stats, "total": len(traces)}


# Include OAuth router
app.include_router(oauth_router, tags=["authentication"])


# MCP Tool endpoints
@app.get("/api/v1/mcp/tools/list")
async def list_tools(auth: AuthContext = Depends(require_authenticated)):
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

    logger.info(f"Tools listed by {auth.subject} from org {auth.org_id}")

    return {"tools": tools, "total": len(tools)}


@app.post("/api/v1/mcp/tools/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    auth: AuthContext = Depends(require_authenticated),
):
    """Execute an MCP tool"""
    import time
    start_time = time.time()

    try:
        tool_name = request.tool
        arguments = request.arguments

        tool_scopes = {
            "run_command": "tools:shell:execute",
            "read_file": "tools:filesystem:read",
            "write_file": "tools:filesystem:write",
            "list_directory": "tools:filesystem:list",
        }

        if tool_name not in tool_scopes:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        required_scope = tool_scopes[tool_name]
        if not auth.has_scope(required_scope):
            raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")

        if tool_name == "run_command":
            result = await run_command_sandboxed(arguments.get("command", ""), arguments.get("timeout_s", 20.0), auth)
        elif tool_name == "read_file":
            result = await read_file_sandboxed(arguments.get("path", ""), auth)
        elif tool_name == "write_file":
            result = await write_file_sandboxed(arguments.get("path", ""), arguments.get("content", ""), arguments.get("mode", "overwrite"), auth)
        elif tool_name == "list_directory":
            result = await list_directory_sandboxed(arguments.get("path", "."), auth)

        duration_ms = (time.time() - start_time) * 1000
        metrics.increment("tool_execution_success")
        logger.info(f"Tool executed: {tool_name} by {auth.subject}")
        return ToolCallResponse(success=True, result=result, duration_ms=duration_ms)

    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.increment("tool_execution_failure")
        logger.error(f"Tool execution error: {str(e)}")
        return ToolCallResponse(success=False, error=str(e), duration_ms=duration_ms)


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

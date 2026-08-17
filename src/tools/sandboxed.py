"""
Sandboxed tool implementations with scope enforcement.
All tools execute in isolated containers with resource limits.
Instrumented with OpenTelemetry for distributed tracing.
"""

import logging
import time
from typing import Dict, Any

from src.sandbox.runner import get_sandbox_runner
from src.auth.auth_context import AuthContext
from src.auth.middleware import AuditLogger
from src.observability.otel import tracer
from src.observability.trace_store import trace_store, TraceEvent
from opentelemetry import trace
from datetime import datetime

logger = logging.getLogger(__name__)

async def run_command_sandboxed(command: str, timeout_s: float = 20.0, auth: AuthContext = None) -> Dict[str, Any]:
    """Execute shell command in sandboxed container. Requires: tools:shell:execute scope"""
    with tracer.start_as_current_span("run_command") as span:
        span.set_attribute("tool.name", "run_command")
        span.set_attribute("tool.timeout_s", timeout_s)
        if auth:
            span.set_attribute("user.subject", auth.subject)
            span.set_attribute("org.id", auth.org_id)

        if not auth:
            span.set_attribute("result.status", "no_auth")
            return {"exit_code": 1, "stdout": "", "stderr": "No auth context", "duration_ms": 0, "sandboxed": True}

        start_time = time.time()
        runner = get_sandbox_runner()

        if not auth.has_scope("tools:shell:execute") and not auth.has_scope("tools:*"):
            span.set_attribute("result.status", "insufficient_scope")
            span.set_attribute("security.scope_required", "tools:shell:execute")
            AuditLogger.log_scope_check(auth.subject, "tools:shell:execute", False, auth.org_id)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="run_command",
                user=auth.subject,
                org_id=auth.org_id,
                status="insufficient_scope",
                duration_ms=0,
                error="Insufficient permissions"
            ))
            return {"exit_code": 1, "stdout": "", "stderr": "Insufficient permissions", "duration_ms": 0, "sandboxed": True}

        AuditLogger.log_scope_check(auth.subject, "tools:shell:execute", True, auth.org_id)
        try:
            result = await runner.run_command(command, timeout_s=timeout_s)
            span.set_attribute("result.exit_code", result.exit_code)
            span.set_attribute("result.duration_ms", result.duration_ms)
            span.set_attribute("result.status", "success")
            span.add_event("command_executed", {"command_length": len(command)})
            AuditLogger.log_tool_execution(auth.subject, "run_command", auth.org_id, result.duration_ms)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="run_command",
                user=auth.subject,
                org_id=auth.org_id,
                status="success",
                duration_ms=result.duration_ms,
                exit_code=result.exit_code
            ))
            return {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("result.status", "error")
            span.set_attribute("result.error", str(e))
            span.set_attribute("result.duration_ms", duration_ms)
            span.record_exception(e)
            AuditLogger.log_tool_execution(auth.subject, "run_command", auth.org_id, duration_ms)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="run_command",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=duration_ms,
                error=str(e)
            ))
            return {"exit_code": 1, "stdout": "", "stderr": str(e), "duration_ms": duration_ms, "sandboxed": True}

async def write_file_sandboxed(path: str, content: str, mode: str = "overwrite", auth: AuthContext = None) -> Dict[str, Any]:
    """Write file in sandboxed container. Requires: tools:filesystem:write scope"""
    with tracer.start_as_current_span("write_file") as span:
        span.set_attribute("tool.name", "write_file")
        span.set_attribute("file.path", path)
        span.set_attribute("file.mode", mode)
        span.set_attribute("file.size_bytes", len(content))
        if auth:
            span.set_attribute("user.subject", auth.subject)
            span.set_attribute("org.id", auth.org_id)

        if not auth:
            span.set_attribute("result.status", "no_auth")
            return {"success": False, "path": path, "error": "No auth context", "sandboxed": True}

        start_time = time.time()
        runner = get_sandbox_runner()

        if not auth.has_scope("tools:filesystem:write") and not auth.has_scope("tools:*"):
            span.set_attribute("result.status", "insufficient_scope")
            span.set_attribute("security.scope_required", "tools:filesystem:write")
            AuditLogger.log_scope_check(auth.subject, "tools:filesystem:write", False, auth.org_id)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="write_file",
                user=auth.subject,
                org_id=auth.org_id,
                status="insufficient_scope",
                duration_ms=0,
                error="Insufficient permissions"
            ))
            return {"success": False, "path": path, "error": "Insufficient permissions", "sandboxed": True}

        AuditLogger.log_scope_check(auth.subject, "tools:filesystem:write", True, auth.org_id)
        try:
            result = await runner.write_file(path, content, mode)
            if result.success:
                span.set_attribute("result.status", "success")
                span.set_attribute("result.duration_ms", result.duration_ms)
                AuditLogger.log_tool_execution(auth.subject, "write_file", auth.org_id, result.duration_ms)
                trace_store.add_trace(TraceEvent(
                    timestamp=datetime.utcnow().isoformat(),
                    tool_name="write_file",
                    user=auth.subject,
                    org_id=auth.org_id,
                    status="success",
                    duration_ms=result.duration_ms
                ))
                return {"success": True, "path": path, "mode": mode, "size_bytes": len(content), "duration_ms": result.duration_ms, "sandboxed": True}
            span.set_attribute("result.status", "failed")
            span.set_attribute("result.error", result.stderr)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="write_file",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=result.duration_ms,
                error=result.stderr
            ))
            return {"success": False, "path": path, "error": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("result.status", "error")
            span.set_attribute("result.error", str(e))
            span.record_exception(e)
            AuditLogger.log_tool_execution(auth.subject, "write_file", auth.org_id, duration_ms)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="write_file",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=duration_ms,
                error=str(e)
            ))
            return {"success": False, "path": path, "error": str(e), "duration_ms": duration_ms, "sandboxed": True}

async def read_file_sandboxed(path: str, auth: AuthContext = None) -> Dict[str, Any]:
    """Read file from sandboxed container. Requires: tools:filesystem:read scope"""
    with tracer.start_as_current_span("read_file") as span:
        span.set_attribute("tool.name", "read_file")
        span.set_attribute("file.path", path)
        if auth:
            span.set_attribute("user.subject", auth.subject)
            span.set_attribute("org.id", auth.org_id)

        if not auth:
            span.set_attribute("result.status", "no_auth")
            return {"success": False, "path": path, "error": "No auth context", "sandboxed": True}

        start_time = time.time()
        runner = get_sandbox_runner()

        if not auth.has_scope("tools:filesystem:read") and not auth.has_scope("tools:*"):
            span.set_attribute("result.status", "insufficient_scope")
            span.set_attribute("security.scope_required", "tools:filesystem:read")
            AuditLogger.log_scope_check(auth.subject, "tools:filesystem:read", False, auth.org_id)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="read_file",
                user=auth.subject,
                org_id=auth.org_id,
                status="insufficient_scope",
                duration_ms=0,
                error="Insufficient permissions"
            ))
            return {"success": False, "path": path, "error": "Insufficient permissions", "sandboxed": True}

        AuditLogger.log_scope_check(auth.subject, "tools:filesystem:read", True, auth.org_id)
        try:
            result = await runner.read_file(path)
            if result.success:
                span.set_attribute("result.status", "success")
                span.set_attribute("result.duration_ms", result.duration_ms)
                span.set_attribute("file.size_bytes", len(result.stdout))
                AuditLogger.log_tool_execution(auth.subject, "read_file", auth.org_id, result.duration_ms)
                trace_store.add_trace(TraceEvent(
                    timestamp=datetime.utcnow().isoformat(),
                    tool_name="read_file",
                    user=auth.subject,
                    org_id=auth.org_id,
                    status="success",
                    duration_ms=result.duration_ms
                ))
                return {"success": True, "path": path, "content": result.stdout, "size_bytes": len(result.stdout), "duration_ms": result.duration_ms, "sandboxed": True}
            span.set_attribute("result.status", "failed")
            span.set_attribute("result.error", result.stderr)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="read_file",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=result.duration_ms,
                error=result.stderr
            ))
            return {"success": False, "path": path, "error": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("result.status", "error")
            span.set_attribute("result.error", str(e))
            span.record_exception(e)
            AuditLogger.log_tool_execution(auth.subject, "read_file", auth.org_id, duration_ms)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="read_file",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=duration_ms,
                error=str(e)
            ))
            return {"success": False, "path": path, "error": str(e), "duration_ms": duration_ms, "sandboxed": True}

async def list_directory_sandboxed(path: str = ".", auth: AuthContext = None) -> Dict[str, Any]:
    """List directory contents in sandboxed container. Requires: tools:filesystem:list scope"""
    with tracer.start_as_current_span("list_directory") as span:
        span.set_attribute("tool.name", "list_directory")
        span.set_attribute("directory.path", path)
        if auth:
            span.set_attribute("user.subject", auth.subject)
            span.set_attribute("org.id", auth.org_id)

        if not auth:
            span.set_attribute("result.status", "no_auth")
            return {"success": False, "path": path, "error": "No auth context", "sandboxed": True}

        start_time = time.time()
        runner = get_sandbox_runner()

        if not auth.has_scope("tools:filesystem:list") and not auth.has_scope("tools:*"):
            span.set_attribute("result.status", "insufficient_scope")
            span.set_attribute("security.scope_required", "tools:filesystem:list")
            AuditLogger.log_scope_check(auth.subject, "tools:filesystem:list", False, auth.org_id)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="list_directory",
                user=auth.subject,
                org_id=auth.org_id,
                status="insufficient_scope",
                duration_ms=0,
                error="Insufficient permissions"
            ))
            return {"success": False, "path": path, "error": "Insufficient permissions", "sandboxed": True}

        AuditLogger.log_scope_check(auth.subject, "tools:filesystem:list", True, auth.org_id)
        try:
            result = await runner.list_directory(path)
            if result.success:
                entries = result.stdout.strip().split("\n") if result.stdout else []
                span.set_attribute("result.status", "success")
                span.set_attribute("result.duration_ms", result.duration_ms)
                span.set_attribute("directory.entry_count", len(entries))
                AuditLogger.log_tool_execution(auth.subject, "list_directory", auth.org_id, result.duration_ms)
                trace_store.add_trace(TraceEvent(
                    timestamp=datetime.utcnow().isoformat(),
                    tool_name="list_directory",
                    user=auth.subject,
                    org_id=auth.org_id,
                    status="success",
                    duration_ms=result.duration_ms
                ))
                return {"success": True, "path": path, "entries": entries, "count": len(entries), "duration_ms": result.duration_ms, "sandboxed": True}
            span.set_attribute("result.status", "failed")
            span.set_attribute("result.error", result.stderr)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="list_directory",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=result.duration_ms,
                error=result.stderr
            ))
            return {"success": False, "path": path, "error": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("result.status", "error")
            span.set_attribute("result.error", str(e))
            span.record_exception(e)
            AuditLogger.log_tool_execution(auth.subject, "list_directory", auth.org_id, duration_ms)
            trace_store.add_trace(TraceEvent(
                timestamp=datetime.utcnow().isoformat(),
                tool_name="list_directory",
                user=auth.subject,
                org_id=auth.org_id,
                status="error",
                duration_ms=duration_ms,
                error=str(e)
            ))
            return {"success": False, "path": path, "error": str(e), "duration_ms": duration_ms, "sandboxed": True}

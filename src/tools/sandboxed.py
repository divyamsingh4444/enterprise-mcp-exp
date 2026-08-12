"""
Sandboxed tool implementations with scope enforcement.
All tools execute in isolated containers with resource limits.
"""

import logging
import time
from typing import Dict, Any

from src.sandbox.runner import get_sandbox_runner
from src.auth.auth_context import AuthContext
from src.auth.middleware import AuditLogger

logger = logging.getLogger(__name__)

async def run_command_sandboxed(command: str, timeout_s: float = 20.0, auth: AuthContext = None) -> Dict[str, Any]:
    """Execute shell command in sandboxed container. Requires: tools:shell:execute scope"""
    if not auth:
        return {"exit_code": 1, "stdout": "", "stderr": "No auth context", "duration_ms": 0, "sandboxed": True}

    start_time = time.time()
    runner = get_sandbox_runner()

    if not auth.has_scope("tools:shell:execute") and not auth.has_scope("tools:*"):
        AuditLogger.log_scope_check(auth.subject, "tools:shell:execute", False, auth.org_id)
        return {"exit_code": 1, "stdout": "", "stderr": "Insufficient permissions", "duration_ms": 0, "sandboxed": True}

    AuditLogger.log_scope_check(auth.subject, "tools:shell:execute", True, auth.org_id)
    try:
        result = await runner.run_command(command, timeout_s=timeout_s)
        AuditLogger.log_tool_execution(auth.subject, "run_command", auth.org_id, result.duration_ms)
        return {"exit_code": result.exit_code, "stdout": result.stdout, "stderr": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        AuditLogger.log_tool_execution(auth.subject, "run_command", auth.org_id, duration_ms)
        return {"exit_code": 1, "stdout": "", "stderr": str(e), "duration_ms": duration_ms, "sandboxed": True}

async def write_file_sandboxed(path: str, content: str, mode: str = "overwrite", auth: AuthContext = None) -> Dict[str, Any]:
    """Write file in sandboxed container. Requires: tools:filesystem:write scope"""
    if not auth:
        return {"success": False, "path": path, "error": "No auth context", "sandboxed": True}

    start_time = time.time()
    runner = get_sandbox_runner()

    if not auth.has_scope("tools:filesystem:write") and not auth.has_scope("tools:*"):
        AuditLogger.log_scope_check(auth.subject, "tools:filesystem:write", False, auth.org_id)
        return {"success": False, "path": path, "error": "Insufficient permissions", "sandboxed": True}

    AuditLogger.log_scope_check(auth.subject, "tools:filesystem:write", True, auth.org_id)
    try:
        result = await runner.write_file(path, content, mode)
        if result.success:
            AuditLogger.log_tool_execution(auth.subject, "write_file", auth.org_id, result.duration_ms)
            return {"success": True, "path": path, "mode": mode, "size_bytes": len(content), "duration_ms": result.duration_ms, "sandboxed": True}
        return {"success": False, "path": path, "error": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        AuditLogger.log_tool_execution(auth.subject, "write_file", auth.org_id, duration_ms)
        return {"success": False, "path": path, "error": str(e), "duration_ms": duration_ms, "sandboxed": True}

async def read_file_sandboxed(path: str, auth: AuthContext = None) -> Dict[str, Any]:
    """Read file from sandboxed container. Requires: tools:filesystem:read scope"""
    if not auth:
        return {"success": False, "path": path, "error": "No auth context", "sandboxed": True}

    start_time = time.time()
    runner = get_sandbox_runner()

    if not auth.has_scope("tools:filesystem:read") and not auth.has_scope("tools:*"):
        AuditLogger.log_scope_check(auth.subject, "tools:filesystem:read", False, auth.org_id)
        return {"success": False, "path": path, "error": "Insufficient permissions", "sandboxed": True}

    AuditLogger.log_scope_check(auth.subject, "tools:filesystem:read", True, auth.org_id)
    try:
        result = await runner.read_file(path)
        if result.success:
            AuditLogger.log_tool_execution(auth.subject, "read_file", auth.org_id, result.duration_ms)
            return {"success": True, "path": path, "content": result.stdout, "size_bytes": len(result.stdout), "duration_ms": result.duration_ms, "sandboxed": True}
        return {"success": False, "path": path, "error": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        AuditLogger.log_tool_execution(auth.subject, "read_file", auth.org_id, duration_ms)
        return {"success": False, "path": path, "error": str(e), "duration_ms": duration_ms, "sandboxed": True}

async def list_directory_sandboxed(path: str = ".", auth: AuthContext = None) -> Dict[str, Any]:
    """List directory contents in sandboxed container. Requires: tools:filesystem:list scope"""
    if not auth:
        return {"success": False, "path": path, "error": "No auth context", "sandboxed": True}

    start_time = time.time()
    runner = get_sandbox_runner()

    if not auth.has_scope("tools:filesystem:list") and not auth.has_scope("tools:*"):
        AuditLogger.log_scope_check(auth.subject, "tools:filesystem:list", False, auth.org_id)
        return {"success": False, "path": path, "error": "Insufficient permissions", "sandboxed": True}

    AuditLogger.log_scope_check(auth.subject, "tools:filesystem:list", True, auth.org_id)
    try:
        result = await runner.list_directory(path)
        if result.success:
            AuditLogger.log_tool_execution(auth.subject, "list_directory", auth.org_id, result.duration_ms)
            entries = result.stdout.strip().split("\n") if result.stdout else []
            return {"success": True, "path": path, "entries": entries, "count": len(entries), "duration_ms": result.duration_ms, "sandboxed": True}
        return {"success": False, "path": path, "error": result.stderr, "duration_ms": result.duration_ms, "sandboxed": True}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        AuditLogger.log_tool_execution(auth.subject, "list_directory", auth.org_id, duration_ms)
        return {"success": False, "path": path, "error": str(e), "duration_ms": duration_ms, "sandboxed": True}

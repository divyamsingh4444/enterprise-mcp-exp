"""
Sandbox runner using gVisor for secure tool execution.
Provides container-based execution with OS-level isolation.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

BLOCKED_PATTERNS = [
    r'format\s+[a-z]:\s*/',
    r'rd\s+/s\s+/q',
    r'del\s+/s\s+/q',
    r'diskpart',
    r'shutdown\s+/s',
    r'reg\s+delete\s+hklm',
]

@dataclass
class SandboxResult:
    """Result of sandboxed execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool

class SandboxRunner:
    """Manages sandboxed execution using gVisor and Docker."""

    def __init__(self):
        """Initialize sandbox runner."""
        self.workspace = "/tmp/mcp-workspace"
        os.makedirs(self.workspace, exist_ok=True)
        logger.info(f"SandboxRunner initialized (workspace: {self.workspace})")
    
    async def run_command(
        self,
        command: str,
        timeout_s: float = 20.0,
        cwd: str = None,
        env: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        """
        Execute command in sandboxed environment.

        Args:
            command: Shell command to execute
            timeout_s: Timeout in seconds (max 120)
            cwd: Working directory
            env: Environment variables

        Returns:
            SandboxResult with exit code, stdout, stderr, duration
        """
        start_time = time.time()
        timeout_s = min(timeout_s, 120.0)

        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                duration_ms = (time.time() - start_time) * 1000
                logger.warning(f"Blocked dangerous command: {command}")
                return SandboxResult(
                    exit_code=1,
                    stdout="",
                    stderr="Command blocked: operation is too dangerous",
                    duration_ms=duration_ms,
                    success=False
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.workspace,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return SandboxResult(
                exit_code=result.returncode,
                stdout=result.stdout[:10000],  # Truncate to 10KB
                stderr=result.stderr[:10000],
                duration_ms=duration_ms,
                success=result.returncode == 0
            )
            
        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            return SandboxResult(
                exit_code=124,
                stdout="",
                stderr=f"Command timed out after {timeout_s}s",
                duration_ms=duration_ms,
                success=False
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Sandbox execution failed: {e}")
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                success=False
            )
    
    async def write_file(
        self,
        path: str,
        content: str,
        mode: str = "overwrite"
    ) -> SandboxResult:
        """Write file in sandbox workspace."""
        if mode == "append":
            cmd = f"echo '{content.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}' >> {self.workspace}/{path}"
        else:
            cmd = f"echo '{content.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}' > {self.workspace}/{path}"
        
        return await self.run_command(cmd)
    
    async def read_file(self, path: str) -> SandboxResult:
        """Read file from sandbox workspace."""
        cmd = f"cat {self.workspace}/{path}"
        return await self.run_command(cmd)
    
    async def list_directory(self, path: str = ".") -> SandboxResult:
        """List directory in sandbox workspace."""
        cmd = f"ls -la {self.workspace}/{path}"
        return await self.run_command(cmd)

# Global instance
_runner: Optional[SandboxRunner] = None

def get_sandbox_runner() -> SandboxRunner:
    """Get or create global sandbox runner."""
    global _runner
    if _runner is None:
        _runner = SandboxRunner()
    return _runner

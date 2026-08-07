"""
Authentication middleware: correlation IDs and audit logging.
"""

import logging
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# Context variable for request ID
_request_id: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    """Get current request ID."""
    return _request_id.get()

class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Inject correlation ID (X-Request-ID) into all requests.
    Stores in ContextVar for use in logging and spans.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get or create request ID
        req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = _request_id.set(req_id)
        
        try:
            response = await call_next(request)
        finally:
            _request_id.reset(token)
        
        # Echo back in response
        response.headers["X-Request-ID"] = req_id
        return response

class CorrelationLogFilter(logging.Filter):
    """
    Add request_id to all log records.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True

class AuditLogger:
    """
    Audit logger for security events.
    """
    
    @staticmethod
    def log_auth_success(subject: str, method: str, endpoint: str, org_id: str):
        """Log successful authentication."""
        logger.info(
            f"AUTH_SUCCESS subject={subject} method={method} endpoint={endpoint} "
            f"org_id={org_id} request_id={get_request_id()}"
        )
    
    @staticmethod
    def log_auth_failure(reason: str, endpoint: str):
        """Log failed authentication."""
        logger.warning(
            f"AUTH_FAILURE reason={reason} endpoint={endpoint} "
            f"request_id={get_request_id()}"
        )
    
    @staticmethod
    def log_scope_check(subject: str, required_scope: str, granted: bool, org_id: str):
        """Log scope check result."""
        status = "GRANTED" if granted else "DENIED"
        logger.info(
            f"SCOPE_CHECK {status} subject={subject} scope={required_scope} "
            f"org_id={org_id} request_id={get_request_id()}"
        )
    
    @staticmethod
    def log_tool_execution(subject: str, tool_name: str, org_id: str, duration_ms: float):
        """Log tool execution."""
        logger.info(
            f"TOOL_EXECUTION subject={subject} tool={tool_name} "
            f"org_id={org_id} duration_ms={duration_ms:.2f} "
            f"request_id={get_request_id()}"
        )

"""
Authentication context and dependency injection for FastAPI.
Provides AuthContext and scope-checking dependencies.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional, List
from fastapi import Header, HTTPException
from auth.token_utils import verify_token

# Tool scopes mapping
TOOL_SCOPES = {
    "tools:filesystem:read": "Read files from workspace",
    "tools:filesystem:write": "Write files to workspace",
    "tools:filesystem:list": "List workspace directories",
    "tools:shell:execute": "Execute shell commands",
    "tools:web:fetch": "Fetch URLs (HTTP requests)",
    "tools:database:read": "Read database (SELECT queries)",
    "tools:database:write": "Write database (INSERT/UPDATE/DELETE)",
    "admin:users": "Manage users",
    "admin:scopes": "Manage scopes/permissions",
}

# Context variable for storing auth context per request
_auth_context: ContextVar[Optional['AuthContext']] = ContextVar(
    'auth_context', default=None
)

@dataclass
class AuthContext:
    """Authentication context extracted from JWT token."""
    token_type: str  # "session", "magic", "service"
    subject: str  # email, client_id
    org_id: str  # tenant ID
    scopes: List[str]  # granted scopes
    role: str = "client"  # "client", "operator", "service"
    is_authenticated: bool = True
    
    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope."""
        if "tools:*" in self.scopes or scope in self.scopes:
            return True
        return False
    
    def has_any_scope(self, scopes: List[str]) -> bool:
        """Check if user has any of the given scopes."""
        if "tools:*" in self.scopes:
            return True
        for scope in scopes:
            if scope in self.scopes:
                return True
        return False
    
    def has_all_scopes(self, scopes: List[str]) -> bool:
        """Check if user has all given scopes."""
        if "tools:*" in self.scopes:
            return True
        for scope in scopes:
            if scope not in self.scopes:
                return False
        return True

def set_auth_context(auth: AuthContext):
    """Store auth context for current request."""
    _auth_context.set(auth)

def get_auth_context() -> Optional[AuthContext]:
    """Get auth context for current request."""
    return _auth_context.get()

async def require_authenticated(
    authorization: str = Header(None)
) -> AuthContext:
    """
    FastAPI dependency: require valid Bearer token.
    
    Raises HTTPException(401) if token invalid.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Extract auth context
    auth = AuthContext(
        token_type=payload.get("typ", "session"),
        subject=payload.get("sub", ""),
        org_id=payload.get("org_id", ""),
        scopes=payload.get("scopes", []),
        role=payload.get("role", "client"),
        is_authenticated=True
    )
    
    return auth

async def require_scope(required_scope: str) -> AuthContext:
    """
    FastAPI dependency: require specific scope.
    
    Must be called after require_authenticated.
    """
    auth = get_auth_context()
    if not auth or not auth.has_scope(required_scope):
        raise HTTPException(status_code=403, detail=f"Insufficient permissions: {required_scope} required")
    
    return auth

async def require_operator(
    authorization: str = Header(None)
) -> AuthContext:
    """
    FastAPI dependency: require operator role.
    """
    auth = await require_authenticated(authorization)
    if auth.role != "operator":
        raise HTTPException(status_code=403, detail="Operator role required")
    
    return auth

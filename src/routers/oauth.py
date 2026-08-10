"""
OAuth 2.1 router with 8 authentication endpoints.
Follows ThreatWatch client_auth.py pattern.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.auth.token_utils import (
    sign_token, verify_token, hash_pw, verify_pw,
    temp_password, generate_nonce,
    MAGIC_TTL, SESSION_TTL, SERVICE_TTL
)
from src.auth.auth_context import (
    require_authenticated, require_operator, AuthContext, TOOL_SCOPES
)
from src.auth.middleware import AuditLogger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["oauth"])

# In-memory user database for development
_users_db = {}  # email -> {password_hash, org_id, scopes, enabled, created_at}

# Request/Response models
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    org_id: str
    scopes: Optional[List[str]] = None

class MagicLinkRequest(BaseModel):
    email: str

class VerifyMagicLinkRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    token: str
    type: str
    expires_in_seconds: int
    org_id: str
    scopes: List[str]

# OAuth Endpoints

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Sign in with email + password."""
    email = body.email.strip().lower()
    password = body.password
    
    user = _users_db.get(email)
    if not user or not user.get("enabled") or not verify_pw(password, user["password_hash"]):
        AuditLogger.log_auth_failure("invalid_credentials", "/auth/login")
        raise HTTPException(401, "Invalid email or password")
    
    org_id = user["org_id"]
    scopes = user.get("scopes", list(TOOL_SCOPES.keys()))
    token = sign_token({
        "typ": "session",
        "sub": email,
        "org_id": org_id,
        "scopes": scopes,
        "role": "client"
    }, SESSION_TTL)
    
    AuditLogger.log_auth_success(email, "POST", "/auth/login", org_id)
    return TokenResponse(token=token, type="bearer", expires_in_seconds=SESSION_TTL, org_id=org_id, scopes=scopes)

@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupRequest):
    """Create new account."""
    email = body.email.strip().lower()
    org_id = body.org_id.strip()
    scopes = body.scopes or list(TOOL_SCOPES.keys())
    
    if not email or not org_id:
        raise HTTPException(400, "email and org_id required")
    
    if email in _users_db:
        raise HTTPException(400, "email already exists")
    
    _users_db[email] = {
        "password_hash": hash_pw(body.password),
        "org_id": org_id,
        "scopes": scopes,
        "enabled": True,
        "created_at": "2026-08-06T00:00:00Z",
        "last_login_at": None
    }
    
    token = sign_token({
        "typ": "session",
        "sub": email,
        "org_id": org_id,
        "scopes": scopes,
        "role": "client"
    }, SESSION_TTL)
    
    AuditLogger.log_auth_success(email, "POST", "/auth/signup", org_id)
    return TokenResponse(token=token, type="bearer", expires_in_seconds=SESSION_TTL, org_id=org_id, scopes=scopes)

@router.post("/magic-link")
async def create_magic_link(body: MagicLinkRequest):
    """Generate magic link for email-based login."""
    email = body.email.strip().lower()
    user = _users_db.get(email)
    if not user or not user.get("enabled"):
        AuditLogger.log_auth_failure("user_not_found", "/auth/magic-link")
        raise HTTPException(404, "User not found")
    
    nonce = generate_nonce()
    magic_token = sign_token({
        "typ": "magic",
        "sub": email,
        "org_id": user["org_id"],
        "nonce": nonce,
    }, MAGIC_TTL)
    
    logger.info(f"Magic link generated for {email}")
    return {
        "message": "Magic link generated",
        "magic_token": magic_token,
        "expires_in_seconds": MAGIC_TTL,
        "note": "In production, this token would be sent via email"
    }

@router.post("/verify", response_model=TokenResponse)
async def verify_magic_link(body: VerifyMagicLinkRequest):
    """Verify magic link and return session token."""
    payload = verify_token(body.token)
    if not payload or payload.get("typ") != "magic":
        AuditLogger.log_auth_failure("invalid_magic_token", "/auth/verify")
        raise HTTPException(401, "Invalid or expired link")
    
    email = payload.get("sub")
    user = _users_db.get(email)
    if not user or not user.get("enabled"):
        AuditLogger.log_auth_failure("user_not_active", "/auth/verify")
        raise HTTPException(401, "User not active")
    
    org_id = user["org_id"]
    scopes = user.get("scopes", list(TOOL_SCOPES.keys()))
    token = sign_token({
        "typ": "session",
        "sub": email,
        "org_id": org_id,
        "scopes": scopes,
        "role": "client"
    }, SESSION_TTL)
    
    AuditLogger.log_auth_success(email, "POST", "/auth/verify", org_id)
    return TokenResponse(token=token, type="bearer", expires_in_seconds=SESSION_TTL, org_id=org_id, scopes=scopes)

@router.get("/me")
async def get_current_user(auth: AuthContext = Depends(require_authenticated)):
    """Get current authenticated user info."""
    return {
        "email": auth.subject,
        "org_id": auth.org_id,
        "scopes": auth.scopes,
        "role": auth.role,
        "is_authenticated": True
    }

@router.post("/logout")
async def logout(auth: AuthContext = Depends(require_authenticated)):
    """Logout (stateless)."""
    AuditLogger.log_auth_success(auth.subject, "POST", "/auth/logout", auth.org_id)
    return {"ok": True, "message": "Logged out successfully"}

@router.get("/users")
async def list_users(auth: AuthContext = Depends(require_operator)):
    """Operator view of all users."""
    users_list = [
        {
            "email": email,
            "org_id": data["org_id"],
            "scopes": data.get("scopes", []),
            "enabled": data.get("enabled", False),
            "created_at": data.get("created_at")
        }
        for email, data in _users_db.items()
    ]
    return {"users": users_list, "total": len(users_list)}

@router.get("/audit-log")
async def get_audit_log(auth: AuthContext = Depends(require_operator)):
    """Operator view of audit logs."""
    return {
        "audit_log": [],
        "total": 0,
        "org_id": auth.org_id
    }

@router.get("/scopes")
async def list_available_scopes(auth: AuthContext = Depends(require_authenticated)):
    """List available tool scopes."""
    return {
        "scopes": TOOL_SCOPES,
        "total": len(TOOL_SCOPES),
        "org_id": auth.org_id
    }


def init_test_user():
    """Initialize test user for development."""
    email = "test@example.com"
    password = "TestPass123!"
    org_id = "org-test-001"

    if email not in _users_db:
        _users_db[email] = {
            "password_hash": hash_pw(password),
            "org_id": org_id,
            "scopes": list(TOOL_SCOPES.keys()),
            "enabled": True,
            "created_at": "2026-08-10T00:00:00Z"
        }
        logger.info(f"Test user initialized: {email} / org: {org_id}")

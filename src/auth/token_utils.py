"""
Token utilities for OAuth 2.1 implementation.
Provides JWT signing/verification and password hashing.
"""

import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any

# TTL constants (in seconds)
MAGIC_TTL = 3600        # 1 hour
SESSION_TTL = 604800    # 7 days
SERVICE_TTL = 2592000   # 30 days

# Get secret key from environment or use default
import os
SECRET_KEY = os.getenv("MCP_SECRET_KEY", "dev-secret-key-change-in-production")

class TokenError(Exception):
    """Token validation error."""
    pass

def base64url_encode(data: bytes) -> str:
    """Base64 URL-safe encoding without padding."""
    return __import__('base64').urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def base64url_decode(data: str) -> bytes:
    """Base64 URL-safe decoding."""
    padding = 4 - (len(data) % 4)
    data += '=' * padding
    return __import__('base64').urlsafe_b64decode(data)

def sign_token(payload: Dict[str, Any], ttl_seconds: int) -> str:
    """
    Sign a JWT token with HS256.
    
    Args:
        payload: Token claims dictionary
        ttl_seconds: Time to live in seconds
        
    Returns:
        Signed JWT token string
    """
    import jwt
    
    # Add issued-at and expiration
    payload['iat'] = int(time.time())
    payload['exp'] = payload['iat'] + ttl_seconds
    
    # Sign token
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    import jwt
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def hash_pw(password: str) -> str:
    """
    Hash password using PBKDF2 (matches ThreatWatch pattern).
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password with salt
    """
    salt = secrets.token_hex(16)
    iterations = 100000
    
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        bytes.fromhex(salt),
        iterations
    )
    
    return f"{salt}${iterations}${hash_obj.hex()}"

def verify_pw(password: str, hash_str: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hash_str: Hashed password string
        
    Returns:
        True if password matches
    """
    try:
        parts = hash_str.split('$')
        if len(parts) != 3:
            return False
        
        salt, iterations, stored_hash = parts
        iterations = int(iterations)
        
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            bytes.fromhex(salt),
            iterations
        )
        
        return hmac.compare_digest(hash_obj.hex(), stored_hash)
    except Exception:
        return False

def temp_password() -> str:
    """
    Generate a temporary password (secure random string).
    
    Returns:
        URL-safe random string
    """
    return secrets.token_urlsafe(12)

def generate_nonce() -> str:
    """
    Generate a secure nonce for magic links (single-use).
    
    Returns:
        Secure random nonce
    """
    return secrets.token_urlsafe(16)

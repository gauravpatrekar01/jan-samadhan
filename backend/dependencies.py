"""
Centralized dependency injection for role-based access control and auth.
"""

from fastapi import Depends, Header, HTTPException, status
from security import decode_token, verify_token_type, is_token_expired
from errors import AuthenticationError, AuthorizationError, TokenExpiredError
from typing import Optional, Literal
from jose import JWTError
import logging

logger = logging.getLogger(__name__)

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract and validate JWT token from Authorization header.
    Converts token errors to proper HTTPException responses.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_MISSING",
                    "message": "Authorization token is required"
                }
            }
        )

    token = authorization.split(" ", 1)[1]
    
    # Safe token parsing - check format before decoding
    if not token or len(token.strip()) == 0:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_EMPTY",
                    "message": "Token cannot be empty"
                }
            }
        )
    
    # Check JWT format (must have 3 segments separated by dots)
    if "." not in token or len(token.split(".")) != 3:
        logger.warning(f"Invalid token format: {len(token.split('.'))} segments")
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_INVALID_FORMAT",
                    "message": "Invalid token format"
                }
            }
        )
    
    # Debug logging (safe - only shows first 20 chars)
    logger.debug(f"Access token: {token[:20]}..." if len(token) > 20 else f"Access token: {token}")
    
    try:
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": "Invalid token"
                    }
                }
            )
        
        # Verify required fields in payload
        if "sub" not in payload:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": "Token missing required subject field"
                    }
                }
            )
        
        # Verify token type
        if not verify_token_type(payload, "access"):
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": {
                        "code": "TOKEN_INVALID_TYPE",
                        "message": "Invalid token type"
                    }
                }
            )
        
        # Check expiration
        if is_token_expired(payload):
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Token has expired"
                    }
                }
            )
            
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_INVALID",
                    "message": "Invalid token format or signature"
                }
            }
        )
    except HTTPException:
        # Re-raise HTTPException (already in correct format)
        raise
    except Exception as e:
        logger.error(f"Unexpected auth error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_VALIDATION_FAILED",
                    "message": "Token validation failed"
                }
            }
        )

async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        return payload
    except JWTError:
        return None


async def require_citizen(user: dict = Depends(get_current_user)) -> dict:
    """Require citizen role"""
    if user.get("role") != "citizen":
        raise AuthorizationError("Citizen access required")
    return user


async def require_officer(user: dict = Depends(get_current_user)) -> dict:
    """Require officer role"""
    if user.get("role") != "officer":
        raise AuthorizationError("Officer access required")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role"""
    if user.get("role") != "admin":
        raise AuthorizationError("Admin access required")
    return user


async def require_officer_or_admin(
    user: dict = Depends(get_current_user),
) -> dict:
    """Require officer or admin role"""
    if user.get("role") not in ("officer", "admin"):
        raise AuthorizationError("Officer or admin access required")
    return user


async def require_verified_citizen(
    user: dict = Depends(require_citizen),
) -> dict:
    """Require verified citizen"""
    from db import db

    collection = db.get_collection("users")
    db_user = collection.find_one({"email": user.get("sub")})
    if not db_user or not db_user.get("verified"):
        raise AuthorizationError(
            "Your account is not yet verified. Please wait for admin approval."
        )
    return user


def require_role(allowed_roles: list[str]):
    """Dynamic role requirement dependency."""
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise AuthorizationError(f"Access requires one of: {', '.join(allowed_roles)}")
        return user
    return role_checker

"""
Centralized dependency injection for role-based access control and auth.
"""

from fastapi import Depends, Header, HTTPException, status
from security import decode_token
from errors import AuthenticationError, AuthorizationError, TokenExpiredError
from typing import Optional, Literal
from jose import JWTError


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract and validate JWT token from Authorization header.
    Raises TokenExpiredError if token has expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        if not payload:
            raise TokenExpiredError()
        return payload
    except JWTError:
        raise TokenExpiredError()

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

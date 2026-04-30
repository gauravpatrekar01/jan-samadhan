"""
Standardized API error responses for JanSamadhan backend.
"""

from fastapi import HTTPException, status
from typing import Optional, Any


class APIError(HTTPException):
    """Base API error class"""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Any] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details,
                },
            },
        )


class AuthenticationError(APIError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_FAILED",
            message=message,
        )


class TokenExpiredError(Exception):
    """Simple exception for token expiration - converted to HTTPException in dependencies"""
    def __init__(self, message="TOKEN_EXPIRED"):
        self.message = message
        super().__init__(self.message)


class AuthorizationError(APIError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            message=message,
        )


class ValidationError(APIError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_FAILED",
            message=message,
            details=details,
        )


class NotFoundError(APIError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=f"{resource} not found",
        )


class ConflictError(APIError):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            message=message,
        )


class RateLimitError(APIError):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please try again later.",
        )

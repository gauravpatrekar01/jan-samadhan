from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from security import decode_token, verify_token_type, is_token_expired, create_access_token
from dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

class TokenExpiredError(Exception):
    """Custom exception for expired tokens"""
    pass

class TokenMiddleware:
    """Middleware to handle token expiration and provide consistent error responses"""
    
    @staticmethod
    def handle_token_error(request: Request, error_type: str = "TOKEN_EXPIRED"):
        """
        Handle token-related errors with consistent response format
        """
        error_messages = {
            "TOKEN_EXPIRED": "Token has expired. Please refresh your token.",
            "TOKEN_INVALID": "Invalid token. Please login again.",
            "TOKEN_MISSING": "Authorization token is required."
        }
        
        message = error_messages.get(error_type, "Authentication failed")
        
        logger.warning(f"Token error: {error_type} from {request.client.host if request.client else 'unknown'}")
        
        raise HTTPException(
            status_code=401,
            detail={
                "code": error_type,
                "message": message
            }
        )

def verify_token_with_expiry(token: str) -> dict:
    """
    Verify token and check for expiration with detailed error handling
    """
    if not token:
        raise TokenExpiredError("TOKEN_MISSING")
    
    try:
        payload = decode_token(token)
        if not payload:
            raise TokenExpiredError("TOKEN_INVALID")
        
        if not verify_token_type(payload, "access"):
            raise TokenExpiredError("TOKEN_INVALID")
        
        if is_token_expired(payload):
            raise TokenExpiredError("TOKEN_EXPIRED")
        
        return payload
        
    except Exception as e:
        if isinstance(e, TokenExpiredError):
            raise e
        logger.error(f"Token verification error: {str(e)}")
        raise TokenExpiredError("TOKEN_INVALID")

# Enhanced HTTPBearer with custom error handling
class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        try:
            credentials = await super().__call__(request)
            return credentials
        except Exception as e:
            # Convert any auth error to our custom format
            TokenMiddleware.handle_token_error(request, "TOKEN_MISSING")

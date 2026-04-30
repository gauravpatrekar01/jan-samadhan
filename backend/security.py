import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from config import settings
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    # bcrypt max input is 72 bytes — slice before encoding
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password[:72].encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password[:72].encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=30)  # Short expiry: 30 minutes
    )
    to_encode["exp"] = expire
    to_encode["type"] = "access"
    to_encode["iat"] = datetime.now(timezone.utc).timestamp()
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create a refresh token with longer expiration (30 days)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode["exp"] = expire
    to_encode["type"] = "refresh"
    to_encode["iat"] = datetime.now(timezone.utc).timestamp()
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected JWT error: {str(e)}")
        return None

def verify_token_type(payload: dict, expected_type: str) -> bool:
    """Verify that token is of the expected type (access or refresh)"""
    return payload.get("type") == expected_type

def is_token_expired(payload: dict) -> bool:
    """Check if token is expired"""
    if "exp" not in payload:
        return True
    exp = payload["exp"]
    current_time = datetime.now(timezone.utc).timestamp()
    return current_time > exp

def get_token_expiration_time(payload: dict) -> datetime | None:
    """Get token expiration time"""
    if "exp" not in payload:
        return None
    return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

def validate_refresh_token(token_str: str) -> dict | None:
    """Validate refresh token with detailed logging"""
    try:
        payload = decode_token(token_str)
        if not payload:
            logger.warning("Refresh token decode failed")
            return None
        
        if not verify_token_type(payload, "refresh"):
            logger.warning(f"Invalid token type: {payload.get('type')}")
            return None
        
        if is_token_expired(payload):
            logger.warning("Refresh token expired")
            return None
        
        logger.info(f"Refresh token valid for user: {payload.get('sub')}")
        return payload
        
    except Exception as e:
        logger.error(f"Refresh token validation error: {str(e)}")
        return None

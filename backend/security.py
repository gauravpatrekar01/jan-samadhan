import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from config import settings


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
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["type"] = "access"
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a refresh token with longer expiration (7 days)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode["exp"] = expire
    to_encode["type"] = "refresh"
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
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

from fastapi import APIRouter
from schemas.user import UserCreate, UserLogin
from db import db
from security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, verify_token_type
from government_registry import verify_citizen_record
from errors import AuthenticationError, ValidationError, ConflictError, TokenExpiredError
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", status_code=201)
def register(user: UserCreate):
    collection = db.get_collection("users")

    if collection.find_one({"email": user.email}):
        raise ConflictError("User already exists")

    if user.role != "citizen":
        raise ValidationError("Signup is only available for citizens")

    user_dict = user.model_dump()
    user_dict["role"] = "citizen"
    user_dict["password"] = hash_password(user.password)
    user_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
    user_dict["verified"] = verify_citizen_record(user.name, user.email, user.aadhar)

    collection.insert_one(user_dict)
    user_dict.pop("_id", None)
    user_dict.pop("password", None)

    return {"success": True, "data": user_dict}


@router.post("/login")
def login(user: UserLogin):
    collection = db.get_collection("users")
    db_user = collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise AuthenticationError("Invalid credentials")

    if db_user.get("role") == "admin":
        raise AuthenticationError("Admin login not available via standard login")

    access_token = create_access_token({"sub": db_user["email"], "role": db_user["role"]})
    refresh_token = create_refresh_token({"sub": db_user["email"], "role": db_user["role"]})

    db_user.pop("_id", None)
    db_user.pop("password", None)
    db_user["token"] = access_token
    db_user["refresh_token"] = refresh_token

    return {"success": True, "data": db_user}


@router.post("/admin-login")
def admin_login(user: UserLogin):
    collection = db.get_collection("users")
    db_user = collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise AuthenticationError("Invalid credentials")

    if db_user.get("role") != "admin":
        raise AuthenticationError("Admin role required")

    access_token = create_access_token({"sub": db_user["email"], "role": db_user["role"]})
    refresh_token = create_refresh_token({"sub": db_user["email"], "role": db_user["role"]})

    db_user.pop("_id", None)
    db_user.pop("password", None)
    db_user["token"] = access_token
    db_user["refresh_token"] = refresh_token

    return {"success": True, "data": db_user}


@router.post("/refresh")
def refresh_access_token(refresh_token: dict):
    """Exchange refresh token for new access token"""
    token_str = refresh_token.get("refresh_token")
    if not token_str:
        raise ValidationError("Refresh token is required")

    payload = decode_token(token_str)
    if not payload or not verify_token_type(payload, "refresh"):
        raise TokenExpiredError()

    # Create new access token using the refresh token's email/role
    access_token = create_access_token({"sub": payload["sub"], "role": payload["role"]})

    return {
        "success": True,
        "data": {
            "token": access_token,
            "refresh_token": token_str,
        },
    }

from fastapi import APIRouter
from schemas.user import UserCreate, UserLogin, NGORegistrationSchema
from db import db
from security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, verify_token_type
from limiter import limiter
from fastapi import Request
from government_registry import verify_citizen_record
from errors import AuthenticationError, ValidationError, ConflictError, TokenExpiredError
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate):
    collection = db.get_collection("users")

    if collection.find_one({"email": user.email}):
        raise ConflictError("User already exists")

    if user.role not in {"citizen", "ngo"}:
        raise ValidationError("Only citizens and NGOs can sign up directly")

    user_dict = user.model_dump()
    user_dict["role"] = user.role
    user_dict["password"] = hash_password(user.password)
    user_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
    
    if user.role == "citizen":
        user_dict["verified"] = verify_citizen_record(user.name, user.email, user.aadhar)
    else:
        # NGOs are pending admin approval
        user_dict["verified"] = False

    collection.insert_one(user_dict)
    user_dict.pop("_id", None)
    user_dict.pop("password", None)

    return {"success": True, "data": user_dict}


@router.post("/register-ngo", status_code=201)
@limiter.limit("3/minute")
def register_ngo(request: Request, ngo: NGORegistrationSchema):
    collection = db.get_collection("users")
    
    # Validation
    if collection.find_one({"email": ngo.email}):
        raise ConflictError("An account with this email already exists.")
        
    if collection.find_one({"registration_number": ngo.registration_number}):
        raise ConflictError("An organization with this registration number is already registered.")

    ngo_dict = ngo.model_dump()
    ngo_dict.update({
        "role": "ngo",
        "verified": False,
        "verification_level": 0,
        "is_active": True,
        "password": hash_password(ngo.password),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        # Metrics & Capacity Initialization
        "resolved_cases": 0,
        "avg_rating": 0,
        "active_cases_count": 0
    })
    
    collection.insert_one(ngo_dict)
    ngo_dict.pop("_id", None)
    ngo_dict.pop("password", None)
    
    return {"success": True, "data": ngo_dict}


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin):
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
@limiter.limit("5/minute")
def admin_login(request: Request, user: UserLogin):
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

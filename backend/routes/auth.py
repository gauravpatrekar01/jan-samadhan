from fastapi import APIRouter, Depends
from schemas.user import UserCreate, UserLogin, NGORegistrationSchema
from db import db
from security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, verify_token_type, validate_refresh_token
from limiter import limiter
from fastapi import Request, UploadFile, File, Form, HTTPException
import os, uuid, shutil, logging

logger = logging.getLogger(__name__)
from government_registry import verify_citizen_record
from errors import APIError, AuthenticationError, ValidationError, ConflictError, TokenExpiredError
from datetime import datetime, timezone
from services.s3_service import s3_service
from dependencies import get_current_user

router = APIRouter()

@router.get("/user")
def get_user_profile(user_payload: dict = Depends(get_current_user)):
    email = user_payload.get("sub")
    collection = db.get_collection("users")
    db_user = collection.find_one({"email": email})
    if not db_user:
        raise AuthenticationError("User not found")
    
    # Return flat structure for registration-map.js compat, but also include nested pattern for other usages
    db_user.pop("_id", None)
    db_user.pop("password", None)
    response_data = {"success": True, "data": db_user}
    response_data.update(db_user) # Add flat properties for registration-map.js
    return response_data

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
    user_dict["language"] = user_dict.get("language") or "en"
    
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
        "active_cases_count": 0,
        "rejection_reason": None,
        "verification_expiry": None,
        # Fraud Detection Signals
        "suspicious_activity": False,
        "request_count_today": 0,
        "last_request_reset": datetime.now(timezone.utc).isoformat()
    })

    
    collection.insert_one(ngo_dict)
    ngo_dict.pop("_id", None)
    ngo_dict.pop("password", None)
    
    return {"success": True, "data": ngo_dict}


@router.get("/ngo-upload-url")
def get_ngo_upload_url(file_name: str, file_type: str):
    """Generate a presigned URL or signal local fallback."""
    if not file_type.startswith(('image/', 'application/pdf')):
        raise ValidationError("Only PDF and Image files are allowed.")
        
    # Check if AWS is configured
    from config import settings
    if not settings.AWS_ACCESS_KEY or not settings.S3_BUCKET_NAME:
        # Signal frontend to use local upload via special response
        return {
            "success": True, 
            "data": {
                "use_local": True,
                "endpoint": "/api/auth/upload-local-doc"
            }
        }

    upload_data = s3_service.generate_presigned_url(file_name, file_type)
    if not upload_data:
        raise APIError(500, "UPLOAD_INIT_FAILED", "Failed to generate upload URL")
        
    return {"success": True, "data": upload_data}


@router.post("/upload-local-doc")
def upload_local_doc(file: UploadFile = File(...)):
    """Local fallback for document uploads when S3 is not available."""
    os.makedirs("static/uploads", exist_ok=True)
    safe_filename = os.path.basename(file.filename)
    fname = f"{uuid.uuid4()}-{safe_filename}"
    path = f"static/uploads/{fname}"
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Standard URL for frontend
    file_url = f"/static/uploads/{unique_name}"
    return {"success": True, "data": {"file_url": file_url}}


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin):
    collection = db.get_collection("users")
    db_user = collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise AuthenticationError("Invalid credentials")

    if db_user.get("role") == "admin":
        raise AuthenticationError("Admin login not available via standard login")

    access_token = create_access_token({"sub": db_user["email"], "role": db_user["role"], "lang": db_user.get("language", "en")})
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

    access_token = create_access_token({"sub": db_user["email"], "role": db_user["role"], "lang": db_user.get("language", "en")})
    refresh_token = create_refresh_token({"sub": db_user["email"], "role": db_user["role"]})

    db_user.pop("_id", None)
    db_user.pop("password", None)
    db_user["token"] = access_token
    db_user["refresh_token"] = refresh_token

    return {"success": True, "data": db_user}


@router.post("/refresh")
def refresh_access_token(refresh_token: dict):
    """
    Exchange refresh token for new access token
    Implements token rotation for enhanced security
    """
    token_str = refresh_token.get("refresh_token")
    
    # Debug logging
    print(f"Refresh token: {token_str[:20]}..." if token_str and len(token_str) > 20 else f"Refresh token: {token_str}")
    
    if not token_str or token_str == "undefined" or token_str == "":
        logger.warning("Refresh token missing or empty in request")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "REFRESH_TOKEN_MISSING",
                    "message": "Refresh token is required"
                }
            }
        )

    # Validate refresh token format (must have 3 segments for JWT)
    if len(token_str.split('.')) != 3:
        logger.warning(f"Invalid refresh token format: {len(token_str.split('.'))} segments")
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "REFRESH_TOKEN_INVALID",
                    "message": "Invalid refresh token format"
                }
            }
        )

    # Validate refresh token
    payload = validate_refresh_token(token_str)
    if not payload:
        logger.warning(f"Invalid refresh token attempt: {token_str[:20]}...")
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "REFRESH_TOKEN_INVALID",
                    "message": "Refresh token is invalid or expired"
                }
            }
        )

    try:
        user_email = payload["sub"]
        user_role = payload.get("role", "citizen")
        user_lang = payload.get("lang", "en")
        
        logger.info(f"Token refresh successful for user: {user_email}")
        
        # Create new access token
        new_access_token = create_access_token({
            "sub": user_email,
            "role": user_role,
            "lang": user_lang
        })
        
        # Create new refresh token (token rotation)
        new_refresh_token = create_refresh_token({
            "sub": user_email,
            "role": user_role,
            "lang": user_lang
        })
        
        return {
            "success": True,
            "data": {
                "token": new_access_token,
                "refresh_token": new_refresh_token,  # Rotated refresh token
                "expires_in": 1800,  # 30 minutes in seconds
                "token_type": "Bearer"
            }
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_REFRESH_ERROR",
                    "message": "Failed to refresh token"
                }
            }
        )

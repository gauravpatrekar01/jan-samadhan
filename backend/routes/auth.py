from fastapi import APIRouter, HTTPException
from schemas.user import UserCreate, UserLogin
from db import db
from security import hash_password, verify_password, create_access_token
from government_registry import verify_citizen_record
from datetime import datetime, timezone

router = APIRouter()


@router.post("/register", status_code=201)
def register(user: UserCreate):
    collection = db.get_collection("users")

    if collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    if user.role != "citizen":
        raise HTTPException(status_code=400, detail="Signup is only available for citizens")

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
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if db_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")

    token = create_access_token({"sub": db_user["email"], "role": db_user["role"]})

    db_user.pop("_id", None)
    db_user.pop("password", None)
    db_user["token"] = token

    return {"success": True, "data": db_user}


@router.post("/admin-login")
def admin_login(user: UserLogin):
    collection = db.get_collection("users")
    db_user = collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if db_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")

    token = create_access_token({"sub": db_user["email"], "role": db_user["role"]})

    db_user.pop("_id", None)
    db_user.pop("password", None)
    db_user["token"] = token

    return {"success": True, "data": db_user}

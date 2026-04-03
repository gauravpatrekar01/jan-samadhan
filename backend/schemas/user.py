from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = ""
    role: str = "citizen"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

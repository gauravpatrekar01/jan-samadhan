from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, Literal
import re


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    aadhar: Optional[str] = ""
    phone: Optional[str] = ""
    role: Literal["citizen", "officer", "admin"] = "citizen"

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v) or not re.search(r"[0-9]", v) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must include uppercase, lowercase, number, and special character")
        return v

    @model_validator(mode="after")
    def validate_aadhar(self):
        if self.role == "citizen":
            if not self.aadhar:
                raise ValueError("Aadhar number is required for citizens")
            if not re.fullmatch(r"\d{12}", self.aadhar):
                raise ValueError("Aadhar must be a 12-digit number")
        elif self.aadhar:
            if not re.fullmatch(r"\d{12}", self.aadhar):
                raise ValueError("Aadhar must be a 12-digit number")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, Literal, List
import re


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    aadhar: Optional[str] = ""
    phone: Optional[str] = ""
    district: Optional[str] = ""
    language: Optional[Literal["en", "mr", "hi"]] = "en"
    role: Literal["citizen", "officer", "admin", "ngo"] = "citizen"

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
        return v

    @model_validator(mode="after")
    def validate_user(self):
        if self.role == "citizen":
            if not self.aadhar:
                raise ValueError("Aadhar number is required for citizens")
            if not re.fullmatch(r"\d{12}", self.aadhar):
                raise ValueError("Aadhar must be a 12-digit number")
            if not re.search(r"[A-Z]", self.password) or not re.search(r"[a-z]", self.password) or not re.search(r"[0-9]", self.password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", self.password):
                raise ValueError("Citizen password must include uppercase, lowercase, number, and special character")
        elif self.aadhar:
            if not re.fullmatch(r"\d{12}", self.aadhar):
                raise ValueError("Aadhar must be a 12-digit number")

        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class NGORegistrationSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    registration_number: str
    organization_type: Literal["Trust", "Society", "Section 8"]
    categories: List[str]
    service_area: str
    contact_person: str
    phone: str
    address: str
    document_url: str  # URL of uploaded certificate

    @field_validator("registration_number")
    @classmethod
    def reg_num_min_len(cls, v: str) -> str:
        if len(v.strip()) < 5:
            raise ValueError("Registration number must be at least 5 characters")
        return v.strip()

    @field_validator("categories")
    @classmethod
    def categories_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one category must be selected")
        if len(v) > 3:
            raise ValueError("Max 3 categories allowed for quality focus")
        return v



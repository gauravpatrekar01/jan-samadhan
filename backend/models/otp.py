from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional
from config import settings

def default_expiry():
    return datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

class OTPRecord(BaseModel):
    phone: str
    otp_code: str
    purpose: str = Field(default="LOGIN")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=default_expiry)
    is_used: bool = Field(default=False)

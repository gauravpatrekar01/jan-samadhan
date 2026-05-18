from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotificationLog(BaseModel):
    recipient_phone: str
    message_content: str
    status: str = Field(..., description="'SENT' or 'FAILED'")
    error_message: Optional[str] = None
    related_complaint_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

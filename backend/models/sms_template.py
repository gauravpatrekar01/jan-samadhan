from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SMSTemplate(BaseModel):
    name: str = Field(..., description="Template name, e.g., 'Complaint Registered'")
    language: str = Field(default="en", description="Language code")
    content: str = Field(..., description="Template content with placeholders like {name}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Complaint Registered",
                "language": "en",
                "content": "Dear {name}, your complaint {complaint_id} is registered successfully."
            }
        }

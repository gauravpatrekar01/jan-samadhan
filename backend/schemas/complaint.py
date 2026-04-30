from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from datetime import datetime, timezone
from uuid import uuid4


VALID_CATEGORIES = {
    "Infrastructure", "Water Supply", "Electricity",
    "Sanitation", "Transport", "Law & Order", "Healthcare", "Other"
}


class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class MediaAttachment(BaseModel):
    url: str
    media_type: Literal["image", "video", "document"]
    file_name: str
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EscalationLog(BaseModel):
    previous_level: str
    new_level: str
    escalated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str


class TimelineEvent(BaseModel):
    stage: Literal["Submitted", "Under Review", "In Progress", "Resolved", "Closed", "Rejected"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by_user_id: Optional[str] = None
    remarks: str = ""


class ResolutionFeedback(BaseModel):
    rating: int = Field(ge=1, le=5)
    satisfaction: Literal["Satisfied", "Neutral", "Unsatisfied"]
    comments: Optional[str] = None
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., min_length=1)
    subcategory: Optional[str] = ""
    priority: Literal["low", "medium", "high", "emergency"] = "medium"
    location: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    media: Optional[List[MediaAttachment]] = []
    marathi_summary: Optional[str] = None
    summary_generated: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_min_length(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")
        return v.strip()


class NGORequestSchema(BaseModel):
    complaint_id: str
    admin_remarks: Optional[str] = ""


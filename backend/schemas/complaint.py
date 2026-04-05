from pydantic import BaseModel, field_validator
from typing import Optional, Literal


VALID_CATEGORIES = {
    "Infrastructure", "Water Supply", "Electricity",
    "Sanitation", "Transport", "Law & Order", "Healthcare", "Other"
}


class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: str
    subcategory: Optional[str] = ""
    priority: Literal["low", "medium", "high", "emergency"] = "medium"
    location: Optional[str] = ""
    region: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

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

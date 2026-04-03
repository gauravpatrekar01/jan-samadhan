from pydantic import BaseModel
from typing import Optional

class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: str
    subcategory: Optional[str] = ""
    priority: str = "medium"
    location: Optional[str] = ""
    region: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

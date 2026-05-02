from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NoticeAttachment(BaseModel):
    url: str
    public_id: str
    type: str
    filename: str

class NoticeBase(BaseModel):
    text: str
    pinned: bool = False
    visible_to: List[str] = ["citizen", "officer", "admin", "ngo"]

class NoticeCreate(NoticeBase):
    pass

class NoticeResponse(NoticeBase):
    id: str
    date: str
    created_by: str
    created_by_role: str
    attachments: List[NoticeAttachment] = []
    timestamp: str

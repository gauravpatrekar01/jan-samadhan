from pydantic import BaseModel

class ComplaintCreate(BaseModel):
    department: str
    title: str
    description: str
    priority: str = "normal"

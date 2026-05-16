from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, timezone

class Milestone(BaseModel):
    title: str
    status: Literal["Pending", "In Progress", "Completed"] = "Pending"
    expected_date: datetime
    completion_date: Optional[datetime] = None
    assigned_officer: Optional[str] = None
    remarks: Optional[str] = None
    attachments: Optional[List[str]] = []

class DeadlineHistory(BaseModel):
    previous_deadline: datetime
    new_deadline: datetime
    reason: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class ProjectProgressUpdate(BaseModel):
    project_id: str
    update_title: str
    description: str
    images: Optional[List[str]] = []
    videos: Optional[List[str]] = []
    progress_increment: int
    officer_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    title: str
    description: str
    category: str
    originating_complaint_id: str
    linked_complaints: List[str] = []
    department: str
    assigned_officer: str
    contractor_name: Optional[str] = None
    budget: float
    status: Literal[
        "Complaint Submitted", "Under Officer Review", "Project Conversion Requested", 
        "Awaiting Admin Approval", "Project Approved", "Budget Approval Pending", 
        "Budget Approved", "Tender Issued", "Contractor Assigned", "Site Survey Started", 
        "Work Started", "Under Construction", "Milestone In Progress", "Delayed", 
        "Deadline Extension Requested", "Deadline Extension Approved", "Escalated", 
        "Inspection Pending", "Quality Verification", "Rework Required", 
        "Reinspection Pending", "Completed"
    ] = "Project Approved"
    progress_percentage: int = 0
    geo_location: Optional[Dict[str, Any]] = None
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expected_completion: datetime
    current_deadline: datetime
    original_deadline: datetime
    total_extensions: int = 0
    delay_status: bool = False
    milestones: List[Milestone] = []
    deadline_history: List[DeadlineHistory] = []
    created_by_admin: str

class ProjectUpdate(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[int] = None
    update_remarks: Optional[str] = None
    contractor_name: Optional[str] = None
    budget: Optional[float] = None
    milestones: Optional[List[Milestone]] = None

class ExtensionRequest(BaseModel):
    project_id: str
    new_deadline: datetime
    reason: str
    reason_category: Literal[
        "Weather Conditions", "Budget Delay", "Contractor Delay", 
        "Material Shortage", "Technical Issue", "Legal Approval Pending", 
        "Safety Concerns", "Other"
    ]
    affected_milestone: Optional[str] = None
    supporting_files: Optional[List[str]] = []
    estimated_impact: Optional[str] = None

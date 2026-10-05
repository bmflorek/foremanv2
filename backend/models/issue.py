from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import new_id, now_iso

ISSUE_STATUSES = ["open", "resolved"]
ISSUE_SEVERITIES = ["low", "medium", "high"]


class IssueCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    severity: str = "medium"
    unit_id: Optional[str] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    unit_id: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None


class Issue(IssueCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    job_id: str
    unit_number: str = ""
    status: str = "open"
    resolution: str = ""
    created_by: str
    created_by_name: str
    resolved_by_name: str = ""
    resolved_at: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

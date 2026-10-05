from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import new_id, now_iso

JOB_STATUSES = ["quoted", "active", "on_hold", "complete"]
APPROVAL_TYPES = {"drawings": "Drawings", "color_sample": "Color Sample", "hardware": "Hardware"}


class Approval(BaseModel):
    approved: bool = False
    approved_by: str = ""
    approved_at: Optional[str] = None
    notes: str = ""


def default_approvals() -> dict:
    return {k: Approval().model_dump() for k in APPROVAL_TYPES}


class JobSpecs(BaseModel):
    paint_type: str = ""
    paint_color: str = ""
    hardware_brand: str = ""
    hardware_name: str = ""
    hinge_type: str = ""
    hinge_color: str = ""
    custom_hardware: str = ""
    threshold_color: str = ""
    glazing_bead_type: str = ""
    sdl_type: str = ""
    glass_type: str = ""
    additional_notes: str = ""


class JobCreate(BaseModel):
    job_number: str = Field(pattern=r"^\d{5}$", description="2-digit year + 3-digit sequence, e.g. 26207")
    name: str = Field(min_length=1)
    customer: str = ""
    address: str = ""
    sold_amount: float = 0
    status: str = "active"
    due_date: Optional[str] = None
    specs: JobSpecs = Field(default_factory=JobSpecs)
    notes: str = ""


class JobUpdate(BaseModel):
    job_number: Optional[str] = Field(default=None, pattern=r"^\d{5}$")
    name: Optional[str] = None
    customer: Optional[str] = None
    address: Optional[str] = None
    sold_amount: Optional[float] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    specs: Optional[JobSpecs] = None
    notes: Optional[str] = None


class Job(JobCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    approvals: Dict[str, Approval] = Field(default_factory=default_approvals)
    created_by: str
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

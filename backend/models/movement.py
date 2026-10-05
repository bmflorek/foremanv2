from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import new_id, now_iso


class MovementCreate(BaseModel):
    unit_id: str
    direction: Literal["out", "in"]
    vendor_id: Optional[str] = None
    process: str = ""
    notes: str = ""


class Movement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    unit_id: str
    unit_number: str
    job_id: str
    job_number: str
    direction: str
    vendor_id: Optional[str] = None
    vendor_name: str = ""
    process: str = ""
    notes: str = ""
    user_id: str
    user_name: str
    created_at: str = Field(default_factory=now_iso)

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from models.common import new_id, now_iso

UNIT_STATUSES = ["not_started", "in_fab", "out_for_process", "complete"]
PREFIX_TYPES = {"W": "window", "D": "door", "BF": "bifold", "SL": "slider"}
UNIT_NUMBER_RE = re.compile(r"^([A-Za-z]{1,3})(\d+)([A-Za-z]?)$")


def normalize_unit_number(value: str) -> str:
    m = UNIT_NUMBER_RE.match(value.strip())
    if not m:
        raise ValueError("Unit number must be like W1, D2, BF3, SL1 or W1a")
    prefix, num, suffix = m.groups()
    return f"{prefix.upper()}{int(num)}{suffix.lower()}"


def unit_type_from_number(unit_number: str) -> str:
    prefix = UNIT_NUMBER_RE.match(unit_number).group(1).upper()
    return PREFIX_TYPES.get(prefix, "custom")


class UnitCreate(BaseModel):
    unit_number: str
    unit_type: Optional[str] = None
    description: str = ""
    width: str = ""
    height: str = ""
    qty: int = 1
    location: str = ""
    status: str = "not_started"
    notes: str = ""

    @field_validator("unit_number")
    @classmethod
    def _normalize(cls, v):
        return normalize_unit_number(v)


class UnitUpdate(BaseModel):
    unit_number: Optional[str] = None
    unit_type: Optional[str] = None
    description: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    qty: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("unit_number")
    @classmethod
    def _normalize(cls, v):
        return normalize_unit_number(v) if v is not None else v


class Unit(UnitCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    job_id: str
    unit_type: str
    current_vendor_id: Optional[str] = None
    out_since: Optional[str] = None
    status_changed_at: str = Field(default_factory=now_iso)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

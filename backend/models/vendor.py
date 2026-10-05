from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import new_id, now_iso


class VendorCreate(BaseModel):
    name: str = Field(min_length=1)
    service: str = ""
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    service: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class Vendor(VendorCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

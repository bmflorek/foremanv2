from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import new_id, now_iso

PO_STATUSES = ["draft", "ordered", "received", "cancelled"]


class POLineItem(BaseModel):
    description: str = ""
    qty: float = 1
    unit_cost: float = 0


class PurchaseOrderCreate(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: str = ""
    date: Optional[str] = None
    line_items: List[POLineItem] = []
    status: str = "ordered"
    notes: str = ""


class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    date: Optional[str] = None
    line_items: Optional[List[POLineItem]] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrder(PurchaseOrderCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    job_id: str
    po_number: str
    total: float = 0
    created_by: str
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


def compute_total(line_items: List[POLineItem]) -> float:
    return round(sum(li.qty * li.unit_cost for li in line_items), 2)

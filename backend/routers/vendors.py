from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.auth import get_current_user
from models.common import now_iso
from models.vendor import Vendor, VendorCreate, VendorUpdate
from models.user import User

router = APIRouter(prefix="/vendors", tags=["vendors"])


async def vendor_stats() -> dict:
    stats: dict = {}
    open_out: dict = {}
    movements = db.movements.find({}, {"_id": 0, "unit_id": 1, "vendor_id": 1, "direction": 1, "created_at": 1}).sort("created_at", 1)
    async for m in movements:
        if m["direction"] == "out":
            open_out[m["unit_id"]] = m
        elif m["unit_id"] in open_out:
            out = open_out.pop(m["unit_id"])
            vid = out.get("vendor_id")
            if not vid:
                continue
            days = (datetime.fromisoformat(m["created_at"]) - datetime.fromisoformat(out["created_at"])).total_seconds() / 86400
            s = stats.setdefault(vid, {"trips": 0, "total_days": 0.0})
            s["trips"] += 1
            s["total_days"] += days
    result = {}
    for vid, s in stats.items():
        result[vid] = {"completed_trips": s["trips"], "avg_days_out": round(s["total_days"] / s["trips"], 1)}
    async for u in db.units.find({"current_vendor_id": {"$ne": None}}, {"_id": 0, "current_vendor_id": 1}):
        result.setdefault(u["current_vendor_id"], {"completed_trips": 0, "avg_days_out": None})
        result[u["current_vendor_id"]]["currently_out"] = result[u["current_vendor_id"]].get("currently_out", 0) + 1
    return result


@router.get("")
async def list_vendors(user: User = Depends(get_current_user)):
    vendors = await db.vendors.find({}, {"_id": 0}).sort("name", 1).to_list(5000)
    stats = await vendor_stats()
    for v in vendors:
        s = stats.get(v["id"], {})
        v["stats"] = {
            "completed_trips": s.get("completed_trips", 0),
            "avg_days_out": s.get("avg_days_out"),
            "currently_out": s.get("currently_out", 0),
        }
    return vendors


@router.post("", status_code=201)
async def create_vendor(request: VendorCreate, user: User = Depends(get_current_user)):
    vendor = Vendor(**request.model_dump())
    await db.vendors.insert_one(vendor.model_dump())
    return vendor


@router.put("/{vendor_id}")
async def update_vendor(vendor_id: str, request: VendorUpdate, user: User = Depends(get_current_user)):
    updates = request.model_dump(exclude_unset=True)
    updates["updated_at"] = now_iso()
    result = await db.vendors.update_one({"id": vendor_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return await db.vendors.find_one({"id": vendor_id}, {"_id": 0})


@router.delete("/{vendor_id}")
async def delete_vendor(vendor_id: str, user: User = Depends(get_current_user)):
    if await db.units.find_one({"current_vendor_id": vendor_id}):
        raise HTTPException(status_code=400, detail="Units are currently checked out to this vendor")
    result = await db.vendors.delete_one({"id": vendor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"message": "Vendor deleted"}

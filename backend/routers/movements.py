from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.auth import get_current_user
from models.common import now_iso
from models.movement import Movement, MovementCreate
from models.user import User

router = APIRouter(prefix="/movements", tags=["movements"])


@router.post("", status_code=201)
async def create_movement(request: MovementCreate, user: User = Depends(get_current_user)):
    unit = await db.units.find_one({"id": request.unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    job = await db.jobs.find_one({"id": unit["job_id"]}, {"_id": 0, "job_number": 1})
    now = now_iso()

    if request.direction == "out":
        if unit.get("current_vendor_id"):
            raise HTTPException(status_code=400, detail="Unit is already checked out")
        if not request.vendor_id:
            raise HTTPException(status_code=400, detail="Vendor is required to check out a unit")
        vendor = await db.vendors.find_one({"id": request.vendor_id}, {"_id": 0})
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        unit_updates = {"status": "out_for_process", "current_vendor_id": vendor["id"], "out_since": now}
    else:
        if not unit.get("current_vendor_id"):
            raise HTTPException(status_code=400, detail="Unit is not checked out")
        vendor = await db.vendors.find_one({"id": unit["current_vendor_id"]}, {"_id": 0})
        unit_updates = {"status": "in_fab", "current_vendor_id": None, "out_since": None}

    movement = Movement(
        unit_id=unit["id"],
        unit_number=unit["unit_number"],
        job_id=unit["job_id"],
        job_number=job["job_number"] if job else "",
        direction=request.direction,
        vendor_id=vendor["id"] if vendor else None,
        vendor_name=vendor["name"] if vendor else "",
        process=request.process or (vendor.get("service", "") if vendor else ""),
        notes=request.notes,
        user_id=user.id,
        user_name=user.name,
    )
    await db.movements.insert_one(movement.model_dump())
    await db.units.update_one(
        {"id": unit["id"]}, {"$set": {**unit_updates, "status_changed_at": now, "updated_at": now}}
    )
    return movement


@router.get("")
async def list_movements(
    job_id: str | None = None, unit_id: str | None = None, limit: int = 100,
    user: User = Depends(get_current_user),
):
    query = {}
    if job_id:
        query["job_id"] = job_id
    if unit_id:
        query["unit_id"] = unit_id
    return await db.movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(min(limit, 1000))


@router.get("/out")
async def units_currently_out(user: User = Depends(get_current_user)):
    units = await db.units.find({"current_vendor_id": {"$ne": None}}, {"_id": 0}).to_list(5000)
    job_ids = list({u["job_id"] for u in units})
    vendor_ids = list({u["current_vendor_id"] for u in units})
    jobs = {j["id"]: j async for j in db.jobs.find({"id": {"$in": job_ids}}, {"_id": 0, "id": 1, "job_number": 1, "name": 1})}
    vendors = {v["id"]: v async for v in db.vendors.find({"id": {"$in": vendor_ids}}, {"_id": 0, "id": 1, "name": 1, "service": 1})}
    now = datetime.now(timezone.utc)
    result = []
    for u in units:
        out_since = datetime.fromisoformat(u["out_since"]) if u.get("out_since") else now
        job = jobs.get(u["job_id"], {})
        vendor = vendors.get(u["current_vendor_id"], {})
        result.append({
            **u,
            "job_number": job.get("job_number", ""),
            "job_name": job.get("name", ""),
            "vendor_name": vendor.get("name", ""),
            "vendor_service": vendor.get("service", ""),
            "days_out": (now - out_since).days,
        })
    return sorted(result, key=lambda r: r.get("out_since") or "")

from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.auth import get_current_user
from models.common import now_iso
from models.unit import Unit, UnitCreate, UnitUpdate, UNIT_STATUSES, unit_type_from_number
from models.user import User
from routers.jobs import get_job_or_404

router = APIRouter(tags=["units"])


def unit_sort_key(u: dict):
    import re
    m = re.match(r"^([A-Z]+)(\d+)([a-z]?)$", u["unit_number"])
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (u["unit_number"], 0, "")


async def enrich_units(units: list[dict]) -> list[dict]:
    vendor_ids = {u["current_vendor_id"] for u in units if u.get("current_vendor_id")}
    vendors = {}
    if vendor_ids:
        async for v in db.vendors.find({"id": {"$in": list(vendor_ids)}}, {"_id": 0, "id": 1, "name": 1}):
            vendors[v["id"]] = v["name"]
    for u in units:
        u["current_vendor_name"] = vendors.get(u.get("current_vendor_id"), "")
    return sorted(units, key=unit_sort_key)


@router.get("/jobs/{job_id}/units")
async def list_units(job_id: str, user: User = Depends(get_current_user)):
    await get_job_or_404(job_id)
    units = await db.units.find({"job_id": job_id}, {"_id": 0}).to_list(5000)
    return await enrich_units(units)


@router.post("/jobs/{job_id}/units", status_code=201)
async def create_unit(job_id: str, request: UnitCreate, user: User = Depends(get_current_user)):
    await get_job_or_404(job_id)
    if request.status not in UNIT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if await db.units.find_one({"job_id": job_id, "unit_number": request.unit_number}):
        raise HTTPException(status_code=400, detail=f"Unit {request.unit_number} already exists on this job")
    data = request.model_dump()
    data["unit_type"] = data["unit_type"] or unit_type_from_number(data["unit_number"])
    unit = Unit(**data, job_id=job_id)
    await db.units.insert_one(unit.model_dump())
    return (await enrich_units([unit.model_dump()]))[0]


@router.get("/units/{unit_id}")
async def get_unit(unit_id: str, user: User = Depends(get_current_user)):
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return (await enrich_units([unit]))[0]


@router.patch("/units/{unit_id}")
async def update_unit(unit_id: str, request: UnitUpdate, user: User = Depends(get_current_user)):
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    updates = request.model_dump(exclude_unset=True)
    if "status" in updates:
        if updates["status"] not in UNIT_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        if unit.get("current_vendor_id") and updates["status"] != "out_for_process":
            raise HTTPException(status_code=400, detail="Unit is checked out to a vendor. Check it in first.")
        if updates["status"] != unit.get("status"):
            updates["status_changed_at"] = now_iso()
    if updates.get("unit_number") and updates["unit_number"] != unit["unit_number"]:
        if await db.units.find_one({"job_id": unit["job_id"], "unit_number": updates["unit_number"]}):
            raise HTTPException(status_code=400, detail=f"Unit {updates['unit_number']} already exists on this job")
        if not updates.get("unit_type"):
            updates["unit_type"] = unit_type_from_number(updates["unit_number"])
    updates["updated_at"] = now_iso()
    await db.units.update_one({"id": unit_id}, {"$set": updates})
    updated = await db.units.find_one({"id": unit_id}, {"_id": 0})
    return (await enrich_units([updated]))[0]


@router.delete("/units/{unit_id}")
async def delete_unit(unit_id: str, user: User = Depends(get_current_user)):
    result = await db.units.delete_one({"id": unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    await db.movements.delete_many({"unit_id": unit_id})
    return {"message": "Unit deleted"}

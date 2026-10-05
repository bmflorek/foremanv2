from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.auth import get_current_user
from models.common import now_iso
from models.job import Job, JobCreate, JobUpdate, JOB_STATUSES, Approval, APPROVAL_TYPES, default_approvals
from models.unit import UNIT_STATUSES
from models.user import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def enrich_job(job: dict) -> dict:
    units = await db.units.find({"job_id": job["id"]}, {"_id": 0, "status": 1}).to_list(5000)
    counts = {s: 0 for s in UNIT_STATUSES}
    for u in units:
        counts[u.get("status", "not_started")] = counts.get(u.get("status", "not_started"), 0) + 1
    counts["total"] = len(units)
    pos = await db.purchase_orders.find(
        {"job_id": job["id"], "status": {"$ne": "cancelled"}}, {"_id": 0, "total": 1}
    ).to_list(5000)
    po_total = round(sum(p.get("total", 0) for p in pos), 2)
    sold = float(job.get("sold_amount") or 0)
    remaining = round(sold - po_total, 2)
    approvals = {**default_approvals(), **(job.get("approvals") or {})}
    job["approvals"] = approvals
    job["approvals_done"] = sum(1 for a in approvals.values() if a.get("approved"))
    job["approvals_total"] = len(APPROVAL_TYPES)
    job["open_issues"] = await db.issues.count_documents({"job_id": job["id"], "status": "open"})
    job["unit_counts"] = counts
    job["budget"] = {
        "sold_amount": sold,
        "po_total": po_total,
        "remaining": remaining,
        "po_count": len(pos),
        "percent_used": round((po_total / sold) * 100, 1) if sold > 0 else 0,
        "over_budget": remaining < 0,
    }
    return job


async def get_job_or_404(job_id: str) -> dict:
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", status_code=201)
async def create_job(request: JobCreate, user: User = Depends(get_current_user)):
    if request.status not in JOB_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if await db.jobs.find_one({"job_number": request.job_number}):
        raise HTTPException(status_code=400, detail=f"Job {request.job_number} already exists")
    job = Job(**request.model_dump(), created_by=user.id)
    await db.jobs.insert_one(job.model_dump())
    return await enrich_job(job.model_dump())


@router.get("")
async def list_jobs(status: str | None = None, user: User = Depends(get_current_user)):
    query = {"status": status} if status else {}
    jobs = await db.jobs.find(query, {"_id": 0}).sort("job_number", -1).to_list(5000)
    return [await enrich_job(j) for j in jobs]


@router.get("/{job_id}")
async def get_job(job_id: str, user: User = Depends(get_current_user)):
    return await enrich_job(await get_job_or_404(job_id))


@router.put("/{job_id}")
async def update_job(job_id: str, request: JobUpdate, user: User = Depends(get_current_user)):
    job = await get_job_or_404(job_id)
    updates = request.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] not in JOB_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if updates.get("job_number") and updates["job_number"] != job["job_number"]:
        if await db.jobs.find_one({"job_number": updates["job_number"]}):
            raise HTTPException(status_code=400, detail=f"Job {updates['job_number']} already exists")
    updates["updated_at"] = now_iso()
    await db.jobs.update_one({"id": job_id}, {"$set": updates})
    return await enrich_job(await get_job_or_404(job_id))


@router.put("/{job_id}/approvals/{approval_type}")
async def set_approval(job_id: str, approval_type: str, request: Approval, user: User = Depends(get_current_user)):
    if approval_type not in APPROVAL_TYPES:
        raise HTTPException(status_code=400, detail="Invalid approval type")
    await get_job_or_404(job_id)
    data = request.model_dump()
    if data["approved"]:
        data["approved_at"] = data["approved_at"] or now_iso()[:10]
        data["approved_by"] = data["approved_by"] or user.name
    else:
        data["approved_at"] = None
    await db.jobs.update_one({"id": job_id}, {"$set": {f"approvals.{approval_type}": data, "updated_at": now_iso()}})
    return await enrich_job(await get_job_or_404(job_id))


@router.delete("/{job_id}")
async def delete_job(job_id: str, user: User = Depends(get_current_user)):
    await get_job_or_404(job_id)
    await db.jobs.delete_one({"id": job_id})
    await db.issues.delete_many({"job_id": job_id})
    await db.units.delete_many({"job_id": job_id})
    await db.movements.delete_many({"job_id": job_id})
    await db.purchase_orders.delete_many({"job_id": job_id})
    return {"message": "Job deleted"}

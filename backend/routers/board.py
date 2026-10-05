from fastapi import APIRouter, Depends
from core.db import db
from core.auth import get_current_user
from models.unit import UNIT_STATUSES
from models.user import User
from routers.units import unit_sort_key

router = APIRouter(prefix="/board", tags=["board"])

STATUS_LABELS = {
    "not_started": "Not Started",
    "in_fab": "In Fab",
    "out_for_process": "Out for Process",
    "complete": "Complete",
}


def urgency_key(u: dict) -> tuple:
    return (u.get("due_date") is None, u.get("due_date") or "", u["job_number"], unit_sort_key(u))


@router.get("")
async def shop_board(job_id: str | None = None, user: User = Depends(get_current_user)) -> dict:
    jobs: dict[str, dict] = {
        j["id"]: j async for j in db.jobs.find(
            {"status": {"$in": ["active", "on_hold"]}}, {"_id": 0, "id": 1, "job_number": 1, "name": 1, "customer": 1, "due_date": 1}
        )
    }
    job_ids = [job_id] if job_id and job_id in jobs else list(jobs.keys())
    units = await db.units.find({"job_id": {"$in": job_ids}}, {"_id": 0}).to_list(10000)
    vendors: dict[str, str] = {v["id"]: v["name"] async for v in db.vendors.find({}, {"_id": 0, "id": 1, "name": 1})}
    columns: dict[str, list[dict]] = {s: [] for s in UNIT_STATUSES}
    for u in units:
        job = jobs[u["job_id"]]
        columns.setdefault(u.get("status", "not_started"), []).append({
            **u,
            "job_number": job["job_number"],
            "job_name": job["name"],
            "customer": job.get("customer", ""),
            "due_date": job.get("due_date"),
            "current_vendor_name": vendors.get(u.get("current_vendor_id"), ""),
        })

    return {
        "columns": [
            {"status": s, "label": STATUS_LABELS[s], "units": sorted(columns[s], key=urgency_key)}
            for s in UNIT_STATUSES
        ],
        "total_units": len(units),
        "active_jobs": len(jobs),
        "jobs": sorted(
            [{"id": j["id"], "job_number": j["job_number"], "name": j["name"]} for j in jobs.values()],
            key=lambda j: j["job_number"], reverse=True,
        ),
    }

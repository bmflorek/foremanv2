from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.auth import get_current_user
from models.common import now_iso
from models.issue import Issue, IssueCreate, IssueUpdate, ISSUE_STATUSES, ISSUE_SEVERITIES
from models.user import User
from routers.jobs import get_job_or_404

router = APIRouter(tags=["issues"])


async def unit_number_for(unit_id: str | None) -> str:
    if not unit_id:
        return ""
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0, "unit_number": 1})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit["unit_number"]


@router.get("/jobs/{job_id}/issues")
async def list_issues(job_id: str, status: str | None = None, user: User = Depends(get_current_user)):
    await get_job_or_404(job_id)
    query = {"job_id": job_id}
    if status:
        query["status"] = status
    issues = await db.issues.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    return sorted(issues, key=lambda i: (i["status"] != "open", i["created_at"]), reverse=False)


@router.post("/jobs/{job_id}/issues", status_code=201)
async def create_issue(job_id: str, request: IssueCreate, user: User = Depends(get_current_user)):
    await get_job_or_404(job_id)
    if request.severity not in ISSUE_SEVERITIES:
        raise HTTPException(status_code=400, detail="Invalid severity")
    issue = Issue(
        **request.model_dump(), job_id=job_id,
        unit_number=await unit_number_for(request.unit_id),
        created_by=user.id, created_by_name=user.name,
    )
    await db.issues.insert_one(issue.model_dump())
    return issue


@router.patch("/issues/{issue_id}")
async def update_issue(issue_id: str, request: IssueUpdate, user: User = Depends(get_current_user)):
    issue = await db.issues.find_one({"id": issue_id}, {"_id": 0})
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    updates = request.model_dump(exclude_unset=True)
    if "severity" in updates and updates["severity"] not in ISSUE_SEVERITIES:
        raise HTTPException(status_code=400, detail="Invalid severity")
    if "unit_id" in updates:
        updates["unit_number"] = await unit_number_for(updates["unit_id"])
    if "status" in updates:
        if updates["status"] not in ISSUE_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        if updates["status"] == "resolved" and issue["status"] != "resolved":
            updates["resolved_at"] = now_iso()
            updates["resolved_by_name"] = user.name
        elif updates["status"] == "open":
            updates["resolved_at"] = None
            updates["resolved_by_name"] = ""
    updates["updated_at"] = now_iso()
    await db.issues.update_one({"id": issue_id}, {"$set": updates})
    return await db.issues.find_one({"id": issue_id}, {"_id": 0})


@router.delete("/issues/{issue_id}")
async def delete_issue(issue_id: str, user: User = Depends(get_current_user)):
    result = await db.issues.delete_one({"id": issue_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Issue not found")
    return {"message": "Issue deleted"}

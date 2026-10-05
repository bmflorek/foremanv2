import os
import re
import secrets
import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from core.db import db
from core.auth import get_current_user
from models.user import User
from services.digest import get_settings, save_settings, collect_digest, render_digest, send_digest

router = APIRouter(tags=["digest"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DigestSettingsUpdate(BaseModel):
    recipients: List[str] = Field(max_length=20)
    enabled: bool = True


@router.get("/settings/digest")
async def read_digest_settings(user: User = Depends(get_current_user)):
    settings = await get_settings()
    runs = await db.digest_runs.find({}, {"_id": 0}).sort("created_at", -1).to_list(10)
    return {**settings, "recent_runs": runs}


@router.put("/settings/digest")
async def update_digest_settings(request: DigestSettingsUpdate, user: User = Depends(get_current_user)):
    cleaned = []
    for r in request.recipients:
        r = r.strip().lower()
        if not EMAIL_RE.match(r):
            raise HTTPException(status_code=400, detail=f"Invalid email: {r}")
        if r not in cleaned:
            cleaned.append(r)
    return await save_settings(cleaned, request.enabled)


@router.get("/digest/preview")
async def preview_digest(user: User = Depends(get_current_user)):
    data = await collect_digest()
    subject, html = render_digest(data)
    return {**data, "subject": subject, "html": html}


@router.post("/digest/send-test")
async def send_test_digest(user: User = Depends(get_current_user)):
    settings = await get_settings()
    if not settings["recipients"]:
        raise HTTPException(status_code=400, detail="Add at least one recipient first")
    result = await send_digest(f"manual-{uuid.uuid4()}", trigger=f"manual:{user.email}")
    if not result["sent"]:
        raise HTTPException(status_code=502, detail="Digest could not be delivered to any recipient")
    return result


def _verify_cron_auth(authorization: Optional[str]) -> None:
    secret = os.environ.get("WEBHOOK_CRON_SECRET", "")
    token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    if not secret or not token or not secrets.compare_digest(token, secret):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _parse_envelope(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid body")
    return body


@router.post("/cron/digest", status_code=202)
async def cron_digest(request: Request, background_tasks: BackgroundTasks,
                      authorization: Optional[str] = Header(None), x_webhook_id: Optional[str] = Header(None)) -> dict:
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    _verify_cron_auth(authorization)
    body = await _parse_envelope(request)
    run_id = x_webhook_id or body.get("run_id") or str(uuid.uuid4())
    if await db.digest_runs.find_one({"run_id": run_id}):
        return {"status": "duplicate", "run_id": run_id}
    settings = await get_settings()
    if not settings.get("enabled", True) or not settings["recipients"]:
        return {"status": "skipped", "run_id": run_id}
    await db.digest_runs.insert_one({"run_id": run_id, "trigger": "cron", "status": "queued"})
    background_tasks.add_task(send_digest, run_id, "cron")
    return {"status": "queued", "run_id": run_id}

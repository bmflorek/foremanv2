import logging
import os
from datetime import datetime, timezone
from html import escape
from core.db import db
from core.email import send_email
from models.common import now_iso

logger = logging.getLogger(__name__)
SETTINGS_ID = "digest"
OUT_THRESHOLD_DAYS = 7


async def get_settings() -> dict:
    doc = await db.settings.find_one({"id": SETTINGS_ID}, {"_id": 0})
    return doc or {"id": SETTINGS_ID, "recipients": [], "enabled": True, "last_sent_at": None}


async def save_settings(recipients: list[str], enabled: bool) -> dict:
    await db.settings.update_one(
        {"id": SETTINGS_ID},
        {"$set": {"recipients": recipients, "enabled": enabled, "updated_at": now_iso()}},
        upsert=True,
    )
    return await get_settings()


async def collect_digest() -> dict:
    today = datetime.now(timezone.utc).date()
    jobs = await db.jobs.find(
        {"status": {"$in": ["active", "on_hold"]}, "due_date": {"$ne": None, "$lt": today.isoformat()}}, {"_id": 0}
    ).sort("due_date", 1).to_list(1000)
    overdue_jobs = []
    for j in jobs:
        open_units = await db.units.count_documents({"job_id": j["id"], "status": {"$ne": "complete"}})
        if open_units == 0:
            continue
        overdue_jobs.append({
            "job_number": j["job_number"], "name": j["name"], "customer": j.get("customer", ""),
            "due_date": j["due_date"], "days_overdue": (today - datetime.fromisoformat(j["due_date"]).date()).days,
            "open_units": open_units,
        })

    units = await db.units.find({"current_vendor_id": {"$ne": None}}, {"_id": 0}).to_list(5000)
    now = datetime.now(timezone.utc)
    job_map = {j["id"]: j async for j in db.jobs.find({}, {"_id": 0, "id": 1, "job_number": 1, "name": 1})}
    vendor_map = {v["id"]: v async for v in db.vendors.find({}, {"_id": 0, "id": 1, "name": 1})}
    stale_units = []
    for u in units:
        days_out = (now - datetime.fromisoformat(u["out_since"])).days if u.get("out_since") else 0
        if days_out < OUT_THRESHOLD_DAYS:
            continue
        job = job_map.get(u["job_id"], {})
        stale_units.append({
            "unit_number": u["unit_number"], "description": u.get("description", ""),
            "job_number": job.get("job_number", ""), "job_name": job.get("name", ""),
            "vendor_name": vendor_map.get(u["current_vendor_id"], {}).get("name", ""), "days_out": days_out,
        })
    stale_units.sort(key=lambda x: -x["days_out"])

    high_issues = await db.issues.count_documents({"status": "open", "severity": "high"})
    return {"date": today.isoformat(), "overdue_jobs": overdue_jobs, "stale_units": stale_units, "open_high_issues": high_issues}


TD = "padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:14px"
TH = "padding:8px 10px;text-align:left;font-size:12px;text-transform:uppercase;color:#6b7280;border-bottom:2px solid #e5e7eb"
OK = "color:#059669;margin:8px 0 24px"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th style='{TH}'>{escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td style='{TD}'>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table role='presentation' width='100%' cellspacing='0' style='border-collapse:collapse;margin:8px 0 24px'><tr>{head}</tr>{body}</table>"


def _overdue_section(jobs: list[dict]) -> str:
    if not jobs:
        return f"<p style='{OK}'>No overdue jobs. Nice.</p>"
    return _table(
        ["Job", "Name", "Due", "Overdue", "Open units"],
        [[f"<strong style='font-family:monospace'>{escape(j['job_number'])}</strong>", escape(j["name"]), escape(j["due_date"]),
          f"<span style='color:#dc2626;font-weight:bold'>{j['days_overdue']}d</span>", str(j["open_units"])] for j in jobs],
    )


def _stale_section(units: list[dict]) -> str:
    if not units:
        return f"<p style='{OK}'>No units out longer than {OUT_THRESHOLD_DAYS} days.</p>"
    return _table(
        ["Unit", "Job", "Vendor", "Days out"],
        [[f"<strong style='font-family:monospace'>{escape(u['unit_number'])}</strong> {escape(u['description'])}",
          f"{escape(u['job_number'])} · {escape(u['job_name'])}", escape(u["vendor_name"]),
          f"<span style='color:#d97706;font-weight:bold'>{u['days_out']}d</span>"] for u in units],
    )


def _issues_line(count: int) -> str:
    if not count:
        return "<p style='margin:0 0 16px;color:#059669'>No open high-severity issues.</p>"
    return f"<p style='margin:0 0 16px'><strong style='color:#dc2626'>{count}</strong> open high-severity issue{'s' if count != 1 else ''} across all jobs.</p>"


def _board_link() -> str:
    app_url = os.environ.get("APP_URL", "").rstrip("/")
    if not app_url.startswith("https://"):
        return ""
    return f"<p style='margin:0 0 24px'><a href='{escape(app_url)}/dashboard/board' style='color:#b45309;font-weight:bold'>Open the Shop Board</a></p>"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if n != 1 else ''}"


def render_digest(data: dict) -> tuple[str, str]:
    n_jobs, n_units = len(data["overdue_jobs"]), len(data["stale_units"])
    subject = f"ShopTrack morning digest — {_plural(n_jobs, 'overdue job')}, {_plural(n_units, 'unit')} out 7+ days"
    html = (
        "<table role='presentation' width='100%'><tr><td style='padding:24px;font-family:Arial,sans-serif;color:#111827'>"
        f"<p style='font-size:12px;text-transform:uppercase;letter-spacing:2px;color:#b45309;margin:0'>ShopTrack · {escape(data['date'])}</p>"
        "<h1 style='margin:4px 0 20px;font-size:24px'>Morning Digest</h1>"
        f"<h2 style='font-size:16px;margin:0'>Overdue jobs ({n_jobs})</h2>{_overdue_section(data['overdue_jobs'])}"
        f"<h2 style='font-size:16px;margin:0'>Units out {OUT_THRESHOLD_DAYS}+ days ({n_units})</h2>{_stale_section(data['stale_units'])}"
        f"{_issues_line(data['open_high_issues'])}{_board_link()}"
        "<p style='font-size:12px;color:#888;margin:0'>Sent by ShopTrack. Manage recipients from the Jobs page → Morning Digest.</p>"
        "</td></tr></table>"
    )
    return subject, html


async def send_digest(run_id: str, trigger: str) -> dict:
    settings = await get_settings()
    data = await collect_digest()
    subject, html = render_digest(data)
    sent, failed = [], []
    for to in settings["recipients"]:
        try:
            await send_email(to=to, subject=subject, html=html)
            sent.append(to)
        except Exception as e:
            logger.error(f"Digest to {to} failed: {e}")
            failed.append(to)
    result = {"run_id": run_id, "trigger": trigger, "sent": sent, "failed": failed, "subject": subject,
              "overdue_jobs": len(data["overdue_jobs"]), "stale_units": len(data["stale_units"]), "created_at": now_iso()}
    await db.digest_runs.update_one({"run_id": run_id}, {"$set": result}, upsert=True)
    if sent:
        await db.settings.update_one({"id": SETTINGS_ID}, {"$set": {"last_sent_at": result["created_at"]}}, upsert=True)
    return result

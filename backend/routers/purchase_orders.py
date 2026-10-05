from fastapi import APIRouter, Depends, HTTPException
from core.db import db
from core.auth import get_current_user
from models.common import now_iso
from models.purchase_order import (
    PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate, PO_STATUSES, compute_total,
)
from models.user import User
from routers.jobs import get_job_or_404, enrich_job

router = APIRouter(tags=["purchase-orders"])


async def resolve_vendor_name(data: dict):
    if data.get("vendor_id") and not data.get("vendor_name"):
        vendor = await db.vendors.find_one({"id": data["vendor_id"]}, {"_id": 0, "name": 1})
        data["vendor_name"] = vendor["name"] if vendor else ""


@router.get("/jobs/{job_id}/purchase-orders")
async def list_purchase_orders(job_id: str, user: User = Depends(get_current_user)):
    job = await enrich_job(await get_job_or_404(job_id))
    pos = await db.purchase_orders.find({"job_id": job_id}, {"_id": 0}).sort("po_number", 1).to_list(5000)
    return {"purchase_orders": pos, "budget": job["budget"]}


@router.post("/jobs/{job_id}/purchase-orders", status_code=201)
async def create_purchase_order(job_id: str, request: PurchaseOrderCreate, user: User = Depends(get_current_user)):
    job = await get_job_or_404(job_id)
    if request.status not in PO_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    seq = await db.purchase_orders.count_documents({"job_id": job_id}) + 1
    data = request.model_dump()
    await resolve_vendor_name(data)
    data["date"] = data["date"] or now_iso()[:10]
    po = PurchaseOrder(
        **data, job_id=job_id,
        po_number=f"{job['job_number']}-PO-{seq:02d}",
        total=compute_total(request.line_items),
        created_by=user.id,
    )
    await db.purchase_orders.insert_one(po.model_dump())
    budget = (await enrich_job(job))["budget"]
    return {**po.model_dump(), "budget": budget}


@router.put("/purchase-orders/{po_id}")
async def update_purchase_order(po_id: str, request: PurchaseOrderUpdate, user: User = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    updates = request.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] not in PO_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if request.line_items is not None:
        updates["total"] = compute_total(request.line_items)
    if "vendor_id" in updates:
        updates.setdefault("vendor_name", "")
        await resolve_vendor_name(updates)
    updates["updated_at"] = now_iso()
    await db.purchase_orders.update_one({"id": po_id}, {"$set": updates})
    updated = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    budget = (await enrich_job(await get_job_or_404(po["job_id"])))["budget"]
    return {**updated, "budget": budget}


@router.delete("/purchase-orders/{po_id}")
async def delete_purchase_order(po_id: str, user: User = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    await db.purchase_orders.delete_one({"id": po_id})
    budget = (await enrich_job(await get_job_or_404(po["job_id"])))["budget"]
    return {"message": "Purchase order deleted", "budget": budget}

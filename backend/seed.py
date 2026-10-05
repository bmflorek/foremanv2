"""Idempotent seed: demo user, vendors, one sample job with units. Run: python seed.py"""
import asyncio
import os
from core.db import db
from core.auth import hash_password
from models.user import User
from models.vendor import Vendor
from models.job import Job, JobSpecs
from models.unit import Unit, unit_type_from_number

DEMO_EMAIL: str = os.environ["SEED_DEMO_EMAIL"]
DEMO_PASSWORD: str = os.environ["SEED_DEMO_PASSWORD"]


async def main() -> None:
    user = await db.users.find_one({"email": DEMO_EMAIL})
    if not user:
        u = User(email=DEMO_EMAIL, name="Shop Manager",
                 picture="https://ui-avatars.com/api/?name=Shop+Manager&background=F59E0B&color=0F172A")
        doc = u.model_dump()
        doc["password"] = hash_password(DEMO_PASSWORD)
        await db.users.insert_one(doc)
        user = doc
    user_id = user["id"]

    vendors = [
        ("Precision Weld Co.", "Welding", "Mike Torres", "555-201-3344"),
        ("ColorCoat Finishing", "Painting / Powder Coat", "Dana Lee", "555-887-1200"),
        ("ClearView Glazing", "Glazing", "Sam Patel", "555-440-9910"),
        ("MetalBright Anodizing", "Anodizing", "Chris Young", "555-310-7788"),
    ]
    for name, service, contact, phone in vendors:
        if not await db.vendors.find_one({"name": name}):
            await db.vendors.insert_one(Vendor(name=name, service=service, contact_name=contact, phone=phone).model_dump())

    if not await db.jobs.find_one({"job_number": "26207"}):
        job = Job(
            job_number="26207", name="Hillcrest Residence", customer="J. Alvarez", address="412 Hillcrest Dr",
            sold_amount=48500, status="active", due_date="2026-08-15", created_by=user_id,
            specs=JobSpecs(paint_type="Kynar", paint_color="Bronze Anodized Match", hardware_brand="Emtek",
                           hardware_name="Helios Lever", hinge_type="Butt Hinge 4.5\"", hinge_color="Oil Rubbed Bronze",
                           custom_hardware="Custom flush bolts on BF units", threshold_color="Dark Bronze",
                           glazing_bead_type="Square", sdl_type="7/8\" Putty", glass_type="1\" IG Low-E 366 Tempered",
                           additional_notes="Client wants matching screen frames on all operable windows."),
        )
        await db.jobs.insert_one(job.model_dump())
        units = [
            ("W1", "Casement window", "36\"", "60\"", 1, "Living Room", "in_fab"),
            ("W1a", "Casement window - RH", "36\"", "60\"", 1, "Living Room", "in_fab"),
            ("W2", "Fixed picture window", "72\"", "60\"", 1, "Living Room", "not_started"),
            ("W3", "Awning window", "48\"", "24\"", 2, "Kitchen", "not_started"),
            ("D1", "Entry door w/ sidelites", "72\"", "96\"", 1, "Front Entry", "in_fab"),
            ("D2", "French door pair", "72\"", "96\"", 1, "Patio", "not_started"),
            ("BF1", "Bifold 4-panel", "144\"", "96\"", 1, "Great Room", "not_started"),
            ("SL1", "Slider 2-panel", "96\"", "96\"", 1, "Master Bedroom", "complete"),
        ]
        for num, desc, w, h, qty, loc, status in units:
            await db.units.insert_one(Unit(
                unit_number=num, unit_type=unit_type_from_number(num), description=desc, width=w, height=h,
                qty=qty, location=loc, status=status, job_id=job.id,
            ).model_dump())
    print("Seed complete:", DEMO_EMAIL)


if __name__ == "__main__":
    asyncio.run(main())

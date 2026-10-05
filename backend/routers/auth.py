import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header
from typing import Optional
from core.db import db
from core.auth import hash_password, verify_password, create_session, get_current_user
from core.email import send_email
from models.user import User, RegisterRequest, LoginRequest, PasswordResetRequest, PasswordResetVerify

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(request: RegisterRequest):
    email = request.email.strip().lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=email,
        name=request.name.strip(),
        picture=f"https://ui-avatars.com/api/?name={request.name.strip().replace(' ', '+')}&background=F59E0B&color=0F172A",
    )
    doc = user.model_dump()
    doc["password"] = hash_password(request.password)
    await db.users.insert_one(doc)
    token = await create_session(user.id)
    return {"user": user, "session_token": token}


@router.post("/login")
async def login(request: LoginRequest):
    user_doc = await db.users.find_one({"email": request.email.strip().lower()}, {"_id": 0})
    if not user_doc or not verify_password(request.password, user_doc.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = await create_session(user_doc["id"])
    user_doc.pop("password", None)
    return {"user": user_doc, "session_token": token}


@router.get("/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        await db.user_sessions.delete_one({"session_token": authorization[7:]})
    return {"message": "Logged out"}


@router.post("/request-password-reset")
async def request_password_reset(request: PasswordResetRequest, background_tasks: BackgroundTasks):
    email = request.email.strip().lower()
    if await db.users.find_one({"email": email}):
        otp = "".join(str(random.randint(0, 9)) for _ in range(6))
        now = datetime.now(timezone.utc)
        await db.password_reset_otps.delete_many({"email": email})
        await db.password_reset_otps.insert_one({
            "email": email, "otp": otp, "used": False,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=15)).isoformat(),
        })
        background_tasks.add_task(
            _send_reset_email, email, otp,
        )
    return {"message": "If the email exists, a reset code has been sent"}


async def _send_reset_email(email: str, otp: str):
    try:
        await send_email(
            to=email, subject="Your ShopTrack password reset code",
            html=(
                "<table role='presentation' width='100%'><tr><td style='padding:24px;font-family:Arial,sans-serif'>"
                "<h2 style='margin:0 0 12px'>Password reset</h2><p>Use this code in ShopTrack to set a new password:</p>"
                f"<p style='font-size:32px;letter-spacing:8px;font-weight:bold;margin:16px 0'>{otp}</p>"
                "<p>It expires in 15 minutes. If you didn't request this, you can ignore this email.</p>"
                "<p style='font-size:12px;color:#888'>Sent by ShopTrack.</p></td></tr></table>"
            ),
        )
    except Exception as e:
        import logging
        logging.error(f"Reset email failed: {e}")


@router.post("/verify-reset-otp")
async def verify_reset_otp(request: PasswordResetVerify):
    email = request.email.strip().lower()
    otp_doc = await db.password_reset_otps.find_one({"email": email, "otp": request.otp, "used": False})
    if not otp_doc or datetime.now(timezone.utc) > datetime.fromisoformat(otp_doc["expires_at"]):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"email": email}, {"$set": {"password": hash_password(request.new_password)}})
    await db.password_reset_otps.update_one({"_id": otp_doc["_id"]}, {"$set": {"used": True}})
    await db.user_sessions.delete_many({"user_id": user["id"]})
    return {"message": "Password reset successfully"}

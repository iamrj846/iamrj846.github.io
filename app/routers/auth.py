from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel, EmailStr

from app.services.auth_service import get_auth_service
from app.database import get_user_by_session, get_guest_search_count
from app.config import get_config

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class VerifyOtpRequest(BaseModel):
    email: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password: str

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.post("/register")
async def register(request: Request, payload: RegisterRequest):
    ip = get_client_ip(request)
    auth_svc = get_auth_service()
    res = auth_svc.register_user(payload.name, payload.email, payload.password, ip)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/verify-otp")
async def verify_otp(request: Request, response: Response, payload: VerifyOtpRequest):
    ip = get_client_ip(request)
    auth_svc = get_auth_service()
    res = auth_svc.verify_otp(payload.email, payload.otp, ip)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))

    # Set persistent session cookie (30 days)
    session_token = res["session_token"]
    response.set_cookie(
        key="cg_session",
        value=session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=False # set True in HTTPS production
    )
    return res

@router.post("/login")
async def login(request: Request, response: Response, payload: LoginRequest):
    ip = get_client_ip(request)
    auth_svc = get_auth_service()
    res = auth_svc.login_with_password(payload.email, payload.password, ip)
    if not res.get("success"):
        raise HTTPException(status_code=401, detail=res.get("message"))

    # Set persistent session cookie (30 days)
    session_token = res["session_token"]
    response.set_cookie(
        key="cg_session",
        value=session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return res

@router.post("/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("cg_session")
    if session_token:
        auth_svc = get_auth_service()
        auth_svc.logout(session_token)
    response.delete_cookie(key="cg_session")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_user(request: Request):
    ip = get_client_ip(request)
    session_token = request.cookies.get("cg_session") or request.cookies.get("cg_admin_session")
    config = get_config()
    limit = config.free_search_limit

    if session_token:
        user = get_user_by_session(session_token)
        if not user:
            from app.routers import admin as admin_mod
            if session_token == getattr(admin_mod.router, "_admin_token", None):
                from app.database import get_user_by_email
                user = get_user_by_email(f"{config.admin_username}@corporateguild.com")

        if user and user.get("is_verified", 0) == 1:
            from app.database import get_ist_now_str
            last_login = user.get("last_login") or get_ist_now_str()
            return {
                "is_authenticated": True,
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "username": user["name"],
                    "email": user["email"],
                    "is_admin": bool(user.get("is_admin", 0)),
                    "is_verified": True,
                    "is_otp_verified": True,
                    "verification_badge": "OTP Verified User",
                    "last_login": last_login,
                    "plan": "Unlimited Free Access",
                    "plan_status": "Active Member",
                    "total_searches": user.get("total_searches", 0),
                    "total_clicks": user.get("total_clicks", 0),
                    "total_visits": user.get("total_visits", 0)
                },
                "remaining_searches": 99999
            }

    # Guest user
    count = get_guest_search_count(ip)
    remaining = max(0, limit - count)
    return {
        "is_authenticated": False,
        "guest_ip": ip,
        "searches_used": count,
        "search_limit": limit,
        "remaining_searches": remaining,
        "upgrade_prompt": "Login or register to get unlimited free access"
    }

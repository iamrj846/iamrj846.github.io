from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel

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

class ResendOtpRequest(BaseModel):
    email: str

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def ensure_email_delivery_configured() -> None:
    """Do not report OTP success when the server cannot send mail."""
    config = get_config()
    if not config.smtp_user or not config.smtp_password:
        raise HTTPException(
            status_code=503,
            detail="Verification email service is temporarily unavailable. Please try again later."
        )

@router.post("/register")
async def register(request: Request, payload: RegisterRequest):
    ensure_email_delivery_configured()
    ip = get_client_ip(request)
    res = get_auth_service().register_user(payload.name, payload.email, payload.password, ip)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/resend-otp")
async def resend_otp(request: Request, payload: ResendOtpRequest):
    ensure_email_delivery_configured()
    ip = get_client_ip(request)
    res = get_auth_service().resend_otp(payload.email, ip)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/verify-otp")
@router.post("/verify_otp")
async def verify_otp(request: Request, response: Response, payload: VerifyOtpRequest):
    ip = get_client_ip(request)
    res = get_auth_service().verify_otp(payload.email, payload.otp, ip)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))

    # The session must be available to every frontend route, not only /api/auth.
    is_https = bool(request.headers.get("x-forwarded-proto", "").lower() == "https" or request.url.scheme == "https")
    response.set_cookie(
        key="cg_session",
        value=res["session_token"],
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=is_https,
        path="/"
    )
    return res

@router.post("/login")
async def login(request: Request, response: Response, payload: LoginRequest):
    ip = get_client_ip(request)
    res = get_auth_service().login_with_password(payload.email, payload.password, ip)
    if not res.get("success"):
        raise HTTPException(status_code=401, detail=res.get("message"))

    session_token = res["session_token"]
    is_https = bool(request.headers.get("x-forwarded-proto", "").lower() == "https" or request.url.scheme == "https")
    response.set_cookie(
        key="cg_session", value=session_token, max_age=30 * 86400,
        httponly=True, samesite="lax", secure=is_https, path="/"
    )
    if res.get("user", {}).get("is_admin"):
        from app.database import save_admin_session
        save_admin_session(session_token, payload.email)
        response.set_cookie(
            key="cg_admin_session", value=session_token, max_age=30 * 86400,
            httponly=True, samesite="lax", secure=is_https, path="/"
        )
    return res

@router.post("/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("cg_session")
    admin_token = request.cookies.get("cg_admin_session")
    auth_header = request.headers.get("Authorization", "")
    bearer_token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else None
    tokens = {t for t in (session_token, admin_token, bearer_token) if t}
    auth_svc = get_auth_service()
    from app.database import delete_admin_session
    for token in tokens:
        auth_svc.logout(token)
        delete_admin_session(token)
    response.delete_cookie(key="cg_session", path="/")
    response.delete_cookie(key="cg_admin_session", path="/")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_user(request: Request, response: Response):
    import secrets
    ip = get_client_ip(request)
    guest_id = request.cookies.get("cg_guest_id") or request.headers.get("x-guest-id")
    auth_hdr = request.headers.get("authorization", "")
    bearer_token = auth_hdr.split(" ", 1)[1].strip() if auth_hdr.startswith("Bearer ") else None
    session_token = (
        request.cookies.get("cg_session") or
        request.cookies.get("cg_admin_session") or
        request.headers.get("x-session-token") or
        bearer_token
    )
    if session_token:
        session_token = str(session_token).strip()
    if not guest_id:
        guest_id = f"cg_guest_{secrets.token_urlsafe(16)}"
    if not request.cookies.get("cg_guest_id"):
        response.set_cookie(key="cg_guest_id", value=guest_id, max_age=365 * 86400,
                            httponly=False, samesite="lax", secure=False, path="/")

    config = get_config()
    if session_token:
        user = get_user_by_session(session_token)
        if user and user.get("is_verified", 0) == 1:
            from app.database import get_ist_now_str
            return {
                "is_authenticated": True,
                "guest_id": guest_id,
                "user": {
                    "id": user["id"], "name": user["name"], "username": user["name"],
                    "email": user["email"], "is_admin": bool(user.get("is_admin", 0)),
                    "is_verified": True, "is_otp_verified": True,
                    "verification_badge": "Verified User",
                    "last_login": user.get("last_login") or get_ist_now_str(),
                    "plan": "Unlimited Free Access", "plan_status": "Active Member",
                    "total_searches": user.get("total_searches", 0),
                    "total_clicks": user.get("total_clicks", 0),
                    "total_visits": user.get("total_visits", 0)
                },
                "remaining_searches": 99999
            }

    count = get_guest_search_count(ip, guest_id)
    return {
        "is_authenticated": False, "guest_id": guest_id, "guest_ip": ip,
        "searches_used": count, "search_limit": config.free_search_limit,
        "remaining_searches": max(0, config.free_search_limit - count),
        "upgrade_prompt": "Login or register to get unlimited free access"
    }

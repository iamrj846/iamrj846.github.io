from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
import secrets

from app.config import get_config
from app.database import get_admin_metrics, get_all_users, get_user_by_session
from app.redis_client import get_redis_summary
from app.services.ingestion_service import get_ingestion_manager, get_sync_status

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class AdminLoginRequest(BaseModel):
    username: str
    password: str

def verify_admin_session(request: Request) -> Dict[str, Any]:
    session_token = request.cookies.get("cg_admin_session") or request.cookies.get("cg_session")
    if not session_token:
        raise HTTPException(status_code=401, detail="Admin authorization required.")
    user = get_user_by_session(session_token)
    config = get_config()
    if not user or not user.get("is_admin", 0):
        # Check special admin token
        if session_token != getattr(router, "_admin_token", None):
            raise HTTPException(status_code=403, detail="Access denied. Admin credentials required.")
    return user or {"name": config.admin_username, "is_admin": True}

@router.post("/login")
async def admin_login(payload: AdminLoginRequest, response: Response):
    config = get_config()
    if payload.username.strip() == config.admin_username and payload.password == config.admin_password_fallback:
        token = secrets.token_urlsafe(32)
        router._admin_token = token
        response.set_cookie(
            key="cg_admin_session",
            value=token,
            max_age=86400,
            httponly=True,
            samesite="lax",
            secure=False
        )
        return {"success": True, "message": "Admin authenticated successfully.", "token": token}
    raise HTTPException(status_code=401, detail="Invalid admin credentials.")

@router.get("/stats")
async def admin_stats(admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    db_metrics = get_admin_metrics()
    redis_summary = get_redis_summary()
    sync_status = get_sync_status()
    return {
        "success": True,
        "metrics": db_metrics,
        "redis": redis_summary,
        "sync": sync_status
    }

@router.get("/users")
async def admin_users(admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    users = get_all_users()
    return {"success": True, "users": users}

@router.post("/sync")
async def trigger_sync(admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    manager = get_ingestion_manager()
    # Trigger cycle in background
    import asyncio
    asyncio.create_task(manager.run_ingestion_cycle(full_sync=False))
    return {"success": True, "message": "ATS Ingestion cycle initiated successfully."}

@router.get("/sync-status")
async def check_sync_status(admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    return {"success": True, "status": get_sync_status()}

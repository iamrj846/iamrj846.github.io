from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
import secrets

from app.config import get_config
from app.database import (
    get_admin_metrics,
    get_all_users,
    get_user_by_session,
    save_admin_session,
    is_valid_admin_session,
    block_user,
    delete_user,
)
from app.redis_client import get_redis_summary
from app.services.ingestion_service import get_ingestion_manager, get_sync_status

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class AdminLoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class BlockUserRequest(BaseModel):
    block: bool = True

class AdminCreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    is_admin: Optional[bool] = False
    is_blocked: Optional[bool] = False

class ContactStatusRequest(BaseModel):
    status: str

def verify_admin_session(request: Request) -> Dict[str, Any]:
    # Collect candidate tokens in order of priority:
    # 1. Explicit Authorization header (Bearer <token>)
    # 2. Dedicated admin cookie (cg_admin_session)
    # 3. Regular session cookie (cg_session)
    candidates = []
    
    auth_hdr = request.headers.get("Authorization", "")
    if auth_hdr.startswith("Bearer "):
        bearer = auth_hdr.split(" ", 1)[1].strip()
        if bearer:
            candidates.append(bearer)
            
    admin_cookie = request.cookies.get("cg_admin_session")
    if admin_cookie and admin_cookie not in candidates:
        candidates.append(admin_cookie)
        
    user_cookie = request.cookies.get("cg_session")
    if user_cookie and user_cookie not in candidates:
        candidates.append(user_cookie)
        
    if not candidates:
        raise HTTPException(status_code=401, detail="Admin authorization required.")
    
    config = get_config()
    for token in candidates:
        if is_valid_admin_session(token):
            user = get_user_by_session(token)
            if user and user.get("is_admin", 0):
                return user
            return {"name": config.admin_username, "email": "jainraunak846@gmail.com", "is_admin": True}

        user = get_user_by_session(token)
        if user and user.get("is_admin", 0):
            return user

    raise HTTPException(status_code=403, detail="Access denied. Admin credentials required.")

@router.post("/login")
async def admin_login(payload: AdminLoginRequest, response: Response):
    config = get_config()
    ident = (payload.email or payload.username or "").strip().lower()
    valid_idents = [
        "jainraunak846@gmail.com",
        config.admin_username.lower(),
        f"{config.admin_username.lower()}@corporateguild.com"
    ]
    if ident in valid_idents and payload.password == config.admin_password_fallback:
        token = secrets.token_urlsafe(32)
        save_admin_session(token, ident)
        response.set_cookie(
            key="cg_admin_session",
            value=token,
            max_age=30 * 86400,
            httponly=True,
            samesite="lax",
            secure=False,
            path="/"
        )
        return {"success": True, "message": "Admin authenticated successfully.", "token": token}
    raise HTTPException(status_code=401, detail="Invalid admin email or password.")

@router.get("/contacts")
async def admin_contact_messages(admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    from app.database import get_contact_messages
    msgs = get_contact_messages(50)
    return {"success": True, "messages": msgs, "contacts": msgs}

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

@router.post("/users/{user_id}/block")
async def admin_block_user(user_id: int, payload: BlockUserRequest, admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    success = block_user(user_id, block=payload.block)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or cannot block admin.")
    action_str = "restricted/blocked" if payload.block else "unrestricted/active"
    return {"success": True, "message": f"User {user_id} {action_str} successfully."}

@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: int, admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or cannot delete admin.")
    return {"success": True, "message": f"User {user_id} deleted successfully."}

@router.post("/users")
async def admin_add_user(payload: AdminCreateUserRequest, admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    import bcrypt
    from app.database import get_user_by_email, admin_create_user
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address format.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")

    pw_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = admin_create_user(
        name=payload.name or email.split("@")[0],
        email=email,
        password_hash=pw_hash,
        is_admin=bool(payload.is_admin),
        is_blocked=bool(payload.is_blocked)
    )
    return {"success": True, "message": "User created successfully.", "user_id": user_id}

@router.post("/users/{user_id}/verify")
async def admin_verify_user(user_id: int, admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    from app.database import verify_user_manually
    success = verify_user_manually(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"success": True, "message": f"User {user_id} verified successfully."}

@router.post("/contacts/{contact_id}/status")
async def admin_update_contact_status(contact_id: int, payload: ContactStatusRequest, admin_user: Dict[str, Any] = Depends(verify_admin_session)):
    from app.database import update_contact_status
    st = payload.status.strip().lower()
    if st not in ("read", "unread"):
        raise HTTPException(status_code=400, detail="Status must be 'read' or 'unread'.")
    success = update_contact_status(contact_id, st)
    if not success:
        raise HTTPException(status_code=404, detail="Contact inquiry not found.")
    return {"success": True, "message": f"Contact inquiry #{contact_id} marked as {st}."}

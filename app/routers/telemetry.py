import logging
from typing import Optional
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.database import record_site_visit, record_site_click, record_site_search
from app.services.metrics_service import get_metrics_service

logger = logging.getLogger("telemetry")

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

class VisitPayload(BaseModel):
    session_id: Optional[str] = None
    path: Optional[str] = "/"
    referrer: Optional[str] = ""

class ClickPayload(BaseModel):
    session_id: Optional[str] = None
    element_type: Optional[str] = "button"
    element_label: Optional[str] = ""
    path: Optional[str] = "/"

class SearchPayload(BaseModel):
    session_id: Optional[str] = None
    query: Optional[str] = ""
    path: Optional[str] = "/"

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def extract_session(request: Request, payload_sid: Optional[str]) -> str:
    cookie_sid = request.cookies.get("cg_session") or request.cookies.get("cg_admin_session")
    if cookie_sid:
        return cookie_sid
    if payload_sid and payload_sid.strip():
        return payload_sid.strip()
    return "guest_session"

@router.post("/visit")
async def track_visit(request: Request, payload: VisitPayload):
    ip = get_client_ip(request)
    session_token = extract_session(request, payload.session_id)
    page_path = payload.path or "/"
    record_site_visit(session_token=session_token, ip_address=ip, page_path=page_path)
    
    ms = get_metrics_service()
    if page_path in ("/", "/index.html"): ms.inc_home()
    elif page_path == "/jobs.html": ms.inc_jobs_page()
    elif page_path == "/portfolio.html": ms.inc_portfolio()
    
    return {"success": True}

@router.post("/click")
async def track_click(request: Request, payload: ClickPayload):
    ip = get_client_ip(request)
    session_token = extract_session(request, payload.session_id)
    el_type = payload.element_type or "unknown"
    el_label = payload.element_label or ""
    page_path = payload.path or "/"
    record_site_click(session_token=session_token, ip_address=ip, target_element=el_type, target_label=el_label, page_path=page_path)
    
    ms = get_metrics_service()
    el_lower = el_label.lower()
    if "search" in el_lower or el_type == "search_button": ms.inc_search_btn()
    elif "filter" in el_lower or el_type == "filter": ms.inc_filter_btn()
    elif "apply" in el_lower or el_type == "apply": ms.inc_apply_btn()
    
    return {"success": True}

@router.post("/search")
async def track_search(request: Request, payload: SearchPayload):
    ip = get_client_ip(request)
    session_token = extract_session(request, payload.session_id)
    query = payload.query or ""
    page_path = payload.path or "/"
    record_site_search(session_token=session_token, ip_address=ip, query=query, page_path=page_path)
    return {"success": True}

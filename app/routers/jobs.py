from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Query, HTTPException, Response
from pydantic import BaseModel

from app.services.search_service import get_search_service, FIXED_ROLES
from app.services.auth_service import get_auth_service
from app.services.ats_service import get_ats_service
from app.database import record_site_search, record_site_click

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

class ClickRequest(BaseModel):
    company_name: str
    role_name: str
    apply_link: Optional[str] = None

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.get("/suggest")
async def get_suggestions(
    mode: str = Query(..., pattern="^(company|role)$"),
    q: str = Query("", alias="q"),
    limit: int = Query(100, ge=1, le=200)
):
    service = get_search_service()
    suggestions = service.get_suggestions(mode, q, limit=limit)
    return {"suggestions": suggestions}

@router.get("/search")
async def search_jobs(
    request: Request,
    search_type: str = Query("company", pattern="^(company|role|other_company|other_role|other|custom)$"),
    search_term: str = Query(""),
    custom_input: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    workplace_type: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    time_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    ip = get_client_ip(request)
    session_token = request.cookies.get("cg_session") or request.cookies.get("cg_admin_session")
    auth_service = get_auth_service()

    # Quota check: 5 free searches for guests
    quota = auth_service.check_search_allowed(ip, session_token)
    if not quota["allowed"]:
        return {
            "success": False,
            "requires_auth": True,
            "message": quota["message"],
            "remaining_searches": 0,
            "limit": quota.get("limit", 5)
        }

    search_svc = get_search_service()
    data = search_svc.search_jobs(
        search_type=search_type,
        search_term=search_term,
        custom_input=custom_input,
        location_filter=location,
        role_filter=role,
        employment_type=employment_type,
        workplace_type=workplace_type,
        experience_level=experience_level,
        time_filter=time_filter,
        page=page,
        page_size=page_size
    )

    # Record search telemetry in SQLite
    q_str = (custom_input or search_term or role or "").strip()
    record_site_search(session_token, ip, query=q_str, page_path="/")

    data["success"] = True
    data["requires_auth"] = False
    data["remaining_searches"] = quota.get("remaining", 99999)
    data["is_authenticated"] = quota.get("is_authenticated", False)

    return data

@router.post("/click")
async def track_click(request: Request, payload: ClickRequest):
    ip = get_client_ip(request)
    session_token = request.cookies.get("cg_session") or request.cookies.get("cg_admin_session")
    auth_service = get_auth_service()
    auth_service.record_job_click(ip, session_token, payload.model_dump())
    record_site_click(session_token, ip, target_element="job_apply_btn", target_label=f"{payload.company_name} - {payload.role_name}", page_path="/")
    return {"success": True}

@router.get("/metadata")
async def get_metadata():
    ats_svc = get_ats_service()
    return {
        "fixed_roles": [r["role"] for r in FIXED_ROLES],
        "top_companies": ats_svc.get_all_companies()[:50],
        "total_companies_count": len(ats_svc.get_all_companies()),
        "locations": [
            "All Locations", "Bengaluru", "Gurugram / Delhi NCR", "Pune", 
            "Mumbai", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Remote - India"
        ],
        "employment_types": [
            "All Types", "Full time", "Part time", "Internship", "Contract", "Freelance"
        ],
        "workplace_types": [
            "All Workplaces", "In office", "Hybrid", "Remote"
        ],
        "experience_levels": [
            "All Experience Levels", "Entry level", "Senior", "Manager", "Director", "Executive"
        ],
        "time_filters": [
            {"id": "all", "label": "Anytime"},
            {"id": "1h", "label": "Last 1 Hour"},
            {"id": "12h", "label": "Last 12 Hours"},
            {"id": "24h", "label": "Last 24 Hours"},
            {"id": "2d", "label": "Last 2 Days"},
            {"id": "7d", "label": "Last 7 Days"}
        ]
    }

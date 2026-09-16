from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Query, HTTPException, Response
from pydantic import BaseModel

from app.services.search_service import get_search_service, FIXED_ROLES
from app.services.auth_service import get_auth_service
from app.services.ats_service import get_ats_service
from app.database import record_site_search, record_site_click, record_job_apply_click, get_total_jobs_in_db

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
    
    # Inject "All Roles" / "All Companies"
    top_val = "All Roles" if mode == "role" else "All Companies"
    if not q or q.lower() in top_val.lower():
        suggestions.insert(0, {
            "type": mode,
            "value": "",
            "label": top_val,
            "subtitle": "View all available positions"
        })
        
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
    time_filter: Optional[str] = Query("24h"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    is_search_action: bool = Query(False)
):
    ip = get_client_ip(request)
    session_token = request.cookies.get("cg_session") or request.cookies.get("cg_admin_session")
    guest_id = request.cookies.get("cg_guest_id") or request.headers.get("x-guest-id")
    auth_service = get_auth_service()

    active_time_filter = (time_filter or "24h").strip()

    # Only decrement guest search quota if user explicitly clicked Search Jobs or Apply Filters
    has_active_query = bool((search_term and search_term.strip()) or (custom_input and custom_input.strip()))
    has_active_filter = bool(
        (location and location.strip().lower() not in ("all", "")) or
        (role and role.strip().lower() not in ("all", "")) or
        (employment_type and employment_type.strip().lower() not in ("all", "")) or
        (workplace_type and workplace_type.strip().lower() not in ("all", "")) or
        (experience_level and experience_level.strip().lower() not in ("all", "")) or
        (time_filter and time_filter.strip().lower() not in ("all", "anytime", "anytime (7 days)", "1h", ""))
    )
    should_increment = bool(is_search_action and (has_active_query or has_active_filter))

    # Quota check: 5 free searches for guests (tracked by persistent guest cookie + IP fallback)
    quota = auth_service.check_search_allowed(ip, session_token, guest_id, increment=should_increment)
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
        time_filter=active_time_filter,
        page=page,
        page_size=page_size
    )


    # Record search telemetry in SQLite
    q_str = (custom_input or search_term or role or "").strip()
    import time
    from app.services.metrics_service import get_metrics_service
    db_start = time.time()
    record_site_search(session_token, ip, query=q_str, page_path="/")
    get_metrics_service().record_db_latency((time.time() - db_start) * 1000)


    data["success"] = True
    data["requires_auth"] = False
    data["remaining_searches"] = quota.get("remaining", 99999)
    data["guest_searches_remaining"] = quota.get("remaining") if not quota.get("is_authenticated") else None
    data["is_authenticated"] = quota.get("is_authenticated", False)

    return data

@router.post("/click")
async def track_click(request: Request, payload: ClickRequest):
    ip = get_client_ip(request)
    session_token = request.cookies.get("cg_session") or request.cookies.get("cg_admin_session")
    auth_service = get_auth_service()
    auth_service.record_job_click(ip, session_token, payload.model_dump())
    record_job_apply_click(
        session_token=session_token,
        ip_address=ip,
        company_name=payload.company_name,
        role_name=payload.role_name,
        apply_link=payload.apply_link or "",
        page_path="/"
    )
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

@router.get("/stats")
async def get_jobs_stats():
    ats_svc = get_ats_service()
    total_companies = len(ats_svc.get_all_companies())
    db_count = 0
    try:
        db_count = get_total_jobs_in_db()
    except Exception:
        pass
    total_jobs = max(db_count, 12500)
    return {
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "formatted_jobs": f"{total_jobs:,}+",
        "formatted_companies": f"{total_companies:,}+"
    }


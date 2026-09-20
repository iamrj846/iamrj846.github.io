import datetime
import pytest
from app.services.search_service import get_search_service
from app.services.ats_service import classify_job_canonical_role
from app.services.auth_service import AuthService
from app.database import get_db_connection, get_ist_now

@pytest.fixture
def search_service():
    return get_search_service()

def test_taxonomy_classification():
    cases = [
        ("Senior Software Engineer - Frontend", "Frontend Engineer"),
        ("Staff Software Engineer - Backend", "Backend Engineer"),
        ("Staff Product Designer — AX & Growth (DLG)", "UI/UX Designer"),
        ("UI/ UX Designer -US Bank", "UI/UX Designer"),
        ("Principal UX Designer", "UI/UX Designer"),
        ("UX Designer", "UI/UX Designer"),
        ("Senior Full-Stack Software Engineer, Community Building", "Full Stack Engineer"),
        ("Sr Engineering Manager UI Path & AI", "Engineering Manager / Lead"),
        ("Business Development Representative", "Sales / Business Development"),
        ("Talent Acquisition Partner", "Human Resources / Recruiter"),
        ("Operations Associate", "Operations / Supply Chain"),
        ("Paralegal", "Legal / Compliance Specialist"),
        ("Senior Software Engineer", "Software Engineer")
    ]
    for title, expected in cases:
        assert classify_job_canonical_role(title) == expected, f"Failed for {title}"

def test_ui_ux_search_precision(search_service):
    res = search_service.search_jobs("role", "UI/UX Designer", page_size=20)
    assert res["total_count"] > 0
    disallowed_keywords = ["software engineer", "developer", "backend", "full stack", "fullstack", "uipath", "business analyst"]
    for j in res["results"][:15]:
        t_lower = j["title"].lower()
        r_lower = j["role_name"].lower()
        assert "uipath" not in t_lower
        assert "ui path" not in t_lower
        if any(d in t_lower for d in ["software engineer", "developer", "backend"]):
            assert "designer" in t_lower or "design" in t_lower or "ui/ux" in t_lower
        assert r_lower in ["ui/ux designer", "graphic / brand designer"]

def test_frontend_search_precision(search_service):
    res = search_service.search_jobs("role", "frontend engineer", page_size=20)
    assert res["total_count"] > 0
    for j in res["results"][:15]:
        t_lower = j["title"].lower()
        r_lower = j["role_name"].lower()
        assert "backend" not in t_lower
        assert "devops" not in t_lower
        assert r_lower == "frontend engineer" or "frontend" in t_lower or "front-end" in t_lower or "ui developer" in t_lower or "web developer" in t_lower

def test_guest_quota_24h_reset():
    auth_svc = AuthService()
    test_ip = "10.0.0.123"
    test_guest = "guest_quota_test_unit"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM guest_quotas WHERE guest_id = ? OR ip_address = ?", (test_guest, test_ip))
    conn.commit()

    # 5 searches allowed
    for i in range(1, 6):
        res = auth_svc.check_search_allowed(test_ip, None, guest_id=test_guest, increment=True)
        assert res["allowed"] is True
        assert res["current_count"] == i

    # 6th search blocked
    res_6 = auth_svc.check_search_allowed(test_ip, None, guest_id=test_guest, increment=True)
    assert res_6["allowed"] is False
    assert "24 hours" in res_6["message"]

    # Expire window (simulate 25h ago)
    twenty_five_hours_ago = (get_ist_now() - datetime.timedelta(hours=25)).strftime("%Y-%m-%d %H:%M:%S IST")
    cur.execute("UPDATE guest_quotas SET created_at = ?, last_search_at = ? WHERE guest_id = ?", (twenty_five_hours_ago, twenty_five_hours_ago, test_guest))
    conn.commit()

    # Search succeeds and resets
    res_reset = auth_svc.check_search_allowed(test_ip, None, guest_id=test_guest, increment=True)
    assert res_reset["allowed"] is True
    assert res_reset["current_count"] == 1
    assert res_reset["remaining"] == 4

    cur.execute("DELETE FROM guest_quotas WHERE guest_id = ? OR ip_address = ?", (test_guest, test_ip))
    conn.commit()
    conn.close()

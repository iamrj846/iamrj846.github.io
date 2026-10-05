import pytest
import datetime
import httpx
import pytz
from unittest.mock import patch, MagicMock

from app.services.remoteok_service import (
    fetch_remoteok_jobs,
    format_remoteok_salary,
    REMOTEOK_API_URL,
)
from app.services.ats_service import IST_TZ
from app.database import (
    get_db_connection,
    save_jobs_to_db,
    clean_invalid_jobs_from_db,
    clean_stale_jobs_from_db,
    search_jobs_direct_db,
)


def test_format_remoteok_salary():
    # Min and max present
    assert format_remoteok_salary(100000, 150000) == "$100,000 - $150,000 USD"
    assert format_remoteok_salary("80000", "120000") == "$80,000 - $120,000 USD"
    # Only min
    assert format_remoteok_salary(90000, 0) == "$90,000+ USD"
    assert format_remoteok_salary(90000, None) == "$90,000+ USD"
    # Only max
    assert format_remoteok_salary(0, 130000) == "Up to $130,000 USD"
    # None or 0
    assert format_remoteok_salary(0, 0) == "Competitive Market CTC"
    assert format_remoteok_salary(None, None) == "Competitive Market CTC"
    assert format_remoteok_salary("abc", "def") == "Competitive Market CTC"


import asyncio

def test_remoteok_filtering_and_parsing():
    now_ist = datetime.datetime.now(IST_TZ)
    recent_epoch = int((now_ist - datetime.timedelta(days=2)).timestamp())
    stale_epoch = int((now_ist - datetime.timedelta(days=20)).timestamp())

    mock_payload = [
        # Item 0: Legal disclaimer
        {"last_updated": 1791058832, "legal": "API terms"},
        # Item 1: Valid recent job
        {
            "id": 1001,
            "epoch": recent_epoch,
            "date": (now_ist - datetime.timedelta(days=2)).isoformat(),
            "company": "Test Acme Corp",
            "position": "Senior Backend Engineer",
            "tags": ["python", "fastapi", "postgres"],
            "location": "Worldwide",
            "salary_min": 120000,
            "salary_max": 180000,
            "url": "https://remoteok.com/remote-jobs/test-acme-backend-1001",
            "apply_url": "https://remoteok.com/remote-jobs/test-acme-backend-1001",
            "description": "Join our distributed team building high performance APIs.",
        },
        # Item 2: Stale job (> 14 days)
        {
            "id": 1002,
            "epoch": stale_epoch,
            "date": (now_ist - datetime.timedelta(days=20)).isoformat(),
            "company": "Stale Corp",
            "position": "Frontend Developer",
            "tags": ["react"],
            "location": "Remote",
            "salary_min": 80000,
            "salary_max": 100000,
            "url": "https://remoteok.com/remote-jobs/stale-corp-frontend-1002",
            "apply_url": "https://remoteok.com/remote-jobs/stale-corp-frontend-1002",
        },
        # Item 3: Invalid entry missing company or title
        {
            "id": 1003,
            "epoch": recent_epoch,
            "company": "",
            "position": "Ghost Job",
            "apply_url": "https://remoteok.com/remote-jobs/ghost",
        },
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload

    mock_client = MagicMock()
    mock_client.get = MagicMock(return_value=mock_response)

    # Async mock client get
    async def async_get(*args, **kwargs):
        return mock_response

    mock_client.get = async_get

    jobs = asyncio.run(fetch_remoteok_jobs(max_days=14, custom_client=mock_client))

    # Only 1 job should be returned (the recent valid one)
    assert len(jobs) == 1
    job = jobs[0]
    assert job["company_name"] == "Test Acme Corp"
    assert job["title"] == "Senior Backend Engineer"
    assert job["role_category"] == "Backend Engineer"
    assert job["workplace_type"] == "Remote"
    assert job["salary_range"] == "$120,000 - $180,000 USD"
    assert job["ats_platform"] == "RemoteOK"
    assert job["source"] == "RemoteOK"
    assert job["id"].startswith("job_")
    assert len(job["id"]) == 28  # 'job_' (4) + 24 sha256 chars
    assert job["time_derived"] == 1


def test_database_remoteok_upsert_and_retention():
    now_ist = datetime.datetime.now(IST_TZ)
    recent_p_time = (now_ist - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S IST")

    sample_job = {
        "apply_link": "https://remoteok.com/remote-jobs/test-sample-dev-9999",
        "apply_url": "https://remoteok.com/remote-jobs/test-sample-dev-9999",
        "company_name": "Test Global Tech",
        "title": "Staff Platform Architect",
        "role_category": "DevOps / Cloud Engineer",
        "location": "Remote",
        "workplace_type": "Remote",
        "salary_range": "$180,000 - $220,000 USD",
        "experience_level": "Senior",
        "employment_type": "Full time",
        "source": "RemoteOK",
        "ats_platform": "RemoteOK",
        "posted_timestamp_ist": recent_p_time,
        "posted_at": recent_p_time,
        "time_derived": 1,
        "tags": ["Cloud", "Kubernetes", "RemoteOK"],
        "skills": ["Terraform", "AWS"],
        "description": "Staff platform role.",
    }

    # 1. Save to DB
    count = save_jobs_to_db([sample_job])
    assert count == 1

    # 2. Verify clean_invalid_jobs_from_db does NOT delete this non-India remote role
    deleted = clean_invalid_jobs_from_db()
    
    # 3. Search via direct DB search
    search_res = search_jobs_direct_db(search_type="company", query_term="Test Global Tech")
    assert search_res["total_count"] >= 1
    found_job = next((j for j in search_res["results"] if j["company_name"] == "Test Global Tech"), None)
    assert found_job is not None
    assert found_job["title"] == "Staff Platform Architect"
    assert found_job["ats_platform"] == "RemoteOK"
    assert found_job["workplace_type"] == "Remote"
    assert found_job["location"] == "Remote"

    # Clean up test row
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs WHERE company = 'Test Global Tech'")
    conn.commit()
    conn.close()

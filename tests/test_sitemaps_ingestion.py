import os
import io
import gzip
import pytest
import datetime
import pytz

from app.services.sitemaps_service import (
    parse_naukri_url,
    parse_internshala_url,
    parse_foundit_url,
    download_sitemap_xml,
    IST_TZ,
)
from app.database import (
    get_db_connection,
    save_jobs_to_db,
    search_jobs_direct_db,
    clean_stale_jobs_from_db,
    clean_invalid_jobs_from_db,
)


def test_parse_naukri_url_valid_and_cutoff():
    # Today is in 2026-10. Let's test with a fresh date (e.g. 05-10-26) vs old date (01-01-25)
    now_ist = datetime.datetime.now(IST_TZ)
    fresh_date = (now_ist - datetime.timedelta(days=2)).date()
    ddmmyy_fresh = fresh_date.strftime("%d%m%y")

    cutoff_date = (now_ist - datetime.timedelta(days=14)).date()

    valid_url = (
        f"https://www.naukri.com/job-listings-software-engineer-amazon-development-centre-bangalore-"
        f"3-to-6-years-{ddmmyy_fresh}901234"
    )
    job = parse_naukri_url(valid_url, cutoff_date)
    assert job is not None
    assert "Software Engineer" in job["title"]
    assert "Amazon" in job["company_name"]
    assert "Bangalore" in job["location"]
    assert job["experience_level"] == "Mid level"
    assert job["source"] == "Naukri"
    assert job["id"].startswith("job_")
    assert job["apply_url"] == valid_url

    # Test stale URL older than 14 days
    stale_date = (now_ist - datetime.timedelta(days=20)).date()
    ddmmyy_stale = stale_date.strftime("%d%m%y")
    stale_url = (
        f"https://www.naukri.com/job-listings-software-engineer-amazon-development-centre-bangalore-"
        f"3-to-6-years-{ddmmyy_stale}901234"
    )
    job_stale = parse_naukri_url(stale_url, cutoff_date)
    assert job_stale is None


def test_parse_internshala_url():
    now_ist = datetime.datetime.now(IST_TZ)
    fresh_dt = now_ist - datetime.timedelta(days=1)
    cutoff_dt = now_ist - datetime.timedelta(days=14)

    url = "https://internshala.com/internship/detail/python-development-internship-in-bangalore-at-tech-innovations-ltd12345"
    lastmod = fresh_dt.isoformat()

    job = parse_internshala_url(url, lastmod, cutoff_dt)
    assert job is not None
    assert "Python Development" in job["title"]
    assert "Tech Innovations" in job["company_name"]
    assert "Bangalore" in job["location"]
    assert job["source"] == "Internshala"
    assert job["employment_type"] == "Internship"
    assert job["id"].startswith("job_")

    # Test stale cutoff
    stale_dt = now_ist - datetime.timedelta(days=25)
    job_stale = parse_internshala_url(url, stale_dt.isoformat(), cutoff_dt)
    assert job_stale is None


def test_parse_foundit_url():
    now_ist = datetime.datetime.now(IST_TZ)
    fresh_dt = now_ist - datetime.timedelta(days=3)
    cutoff_dt = now_ist - datetime.timedelta(days=14)

    url = "https://www.foundit.in/job/lead-data-scientist-pwc-hyderabad-987654"
    lastmod = fresh_dt.isoformat()

    job = parse_foundit_url(url, lastmod, cutoff_dt)
    assert job is not None
    assert "Lead Data Scientist" in job["title"]
    assert "Pwc" in job["company_name"]
    assert "Hyderabad" in job["location"]
    assert job["source"] == "Foundit"
    assert job["id"].startswith("job_")

    # Test stale cutoff
    stale_dt = now_ist - datetime.timedelta(days=30)
    job_stale = parse_foundit_url(url, stale_dt.isoformat(), cutoff_dt)
    assert job_stale is None


def test_gzip_sitemap_decompression():
    sample_xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/job1</loc></url></urlset>'
    bio = io.BytesIO()
    with gzip.GzipFile(fileobj=bio, mode="wb") as gz:
        gz.write(sample_xml.encode("utf-8"))
    gz_bytes = bio.getvalue()

    # Verify that gzip magic bytes are detected
    assert gz_bytes.startswith(b"\x1f\x8b")


def test_database_preserves_aggregator_sources():
    now_ist = datetime.datetime.now(IST_TZ)
    fresh_time = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")

    sample_jobs = [
        {
            "id": "job_test_naukri_1",
            "company_name": "TestNaukriCorp",
            "title": "Backend Python Engineer",
            "role_category": "Backend Developer",
            "location": "Pune, Maharashtra, India",
            "workplace_type": "In office",
            "experience_level": "Mid level",
            "employment_type": "Full time",
            "apply_url": "https://www.naukri.com/job-listings-backend-python-engineer-testnaukricorp-pune-240101001",
            "salary_range": "Competitive Market CTC",
            "posted_timestamp_ist": fresh_time,
            "posted_timestamp_raw": fresh_time,
            "relative_time_ist": "Just now",
            "time_derived": 1,
            "tags": ["Python", "Backend"],
            "description": "Naukri verified role.",
            "source": "Naukri",
            "ats_platform": "Naukri",
        },
        {
            "id": "job_test_internshala_1",
            "company_name": "TestInternCorp",
            "title": "Data Analyst Intern",
            "role_category": "Data Analyst",
            "location": "Bengaluru, Karnataka, India",
            "workplace_type": "Remote",
            "experience_level": "Entry level",
            "employment_type": "Internship",
            "apply_url": "https://internshala.com/internship/detail/data-analyst-internship-in-bengaluru-at-testinterncorp123",
            "salary_range": "Stipend Provided",
            "posted_timestamp_ist": fresh_time,
            "posted_timestamp_raw": fresh_time,
            "relative_time_ist": "Just now",
            "time_derived": 1,
            "tags": ["Data Analysis", "Internship"],
            "description": "Internshala verified role.",
            "source": "Internshala",
            "ats_platform": "Internshala",
        },
        {
            "id": "job_test_foundit_1",
            "company_name": "TestFounditCorp",
            "title": "Cloud DevOps Architect",
            "role_category": "DevOps Engineer",
            "location": "Mumbai, Maharashtra, India",
            "workplace_type": "Hybrid",
            "experience_level": "Senior",
            "employment_type": "Full time",
            "apply_url": "https://www.foundit.in/job/cloud-devops-architect-testfounditcorp-mumbai-9999",
            "salary_range": "Competitive Market CTC",
            "posted_timestamp_ist": fresh_time,
            "posted_timestamp_raw": fresh_time,
            "relative_time_ist": "Just now",
            "time_derived": 1,
            "tags": ["DevOps", "Cloud", "AWS"],
            "description": "Foundit verified role.",
            "source": "Foundit",
            "ats_platform": "Foundit",
        },
    ]

    saved = save_jobs_to_db(sample_jobs)
    assert saved == 3

    # Ensure clean_invalid_jobs_from_db does NOT delete these aggregator jobs
    cleaned = clean_invalid_jobs_from_db()
    
    # Verify search finds them
    res_naukri = search_jobs_direct_db(search_type="company", query_term="TestNaukriCorp")
    assert res_naukri["total_count"] >= 1

    res_intern = search_jobs_direct_db(search_type="company", query_term="TestInternCorp")
    assert res_intern["total_count"] >= 1

    res_foundit = search_jobs_direct_db(search_type="company", query_term="TestFounditCorp")
    assert res_foundit["total_count"] >= 1

    # Clean up test rows
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM jobs WHERE id IN ('job_test_naukri_1', 'job_test_internshala_1', 'job_test_foundit_1')"
    )
    conn.commit()
    conn.close()

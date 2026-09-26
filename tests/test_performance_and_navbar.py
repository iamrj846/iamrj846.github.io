import pytest
from pathlib import Path
from app.redis_client import get_redis_client, get_redis_summary, clean_stale_jobs_older_than_days
from app.services.ingestion_service import get_ingestion_manager

def test_redis_summary():
    summary = get_redis_summary()
    assert isinstance(summary, dict)
    assert "total_hashes" in summary
    assert "total_jobs" in summary
    assert "status" in summary
    assert summary["status"] == "online"

def test_seed_initial_jobs_warm_fast_path():
    ingestion_mgr = get_ingestion_manager()
    # Should run quickly and return a non-negative count
    res = ingestion_mgr.seed_initial_jobs()
    assert res >= 0

def test_clean_stale_jobs_non_blocking():
    # Calling non-blocking cleanup should not raise exceptions
    removed = clean_stale_jobs_older_than_days(max_days=60)
    assert removed >= 0

def test_mobile_navbar_css():
    index_html = Path("frontend/index.html").read_text(encoding="utf-8")
    assert ".nav-dropdown-header" in index_html
    assert "flex-direction: column" in index_html
    assert "padding: 12px 14px" in index_html
    assert ".nav-dropdown-all-btn" in index_html

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
    assert "Career Guides" in index_html
    assert 'href="/articles.html"' in index_html
    # Ensure dropdown is removed
    assert "navCareerGuidesDropdown" not in index_html

def test_career_guides_direct_link_across_pages():
    for page in ["frontend/index.html", "frontend/jobs.html", "frontend/portfolio.html", "frontend/articles.html"]:
        text = Path(page).read_text(encoding="utf-8")
        assert 'href="/articles.html"' in text
        assert "navCareerGuidesDropdown" not in text

def test_articles_seo_and_llm_optimization():
    articles_html = Path("frontend/articles.html").read_text(encoding="utf-8")
    assert "Career Guides" in articles_html
    assert "Industry Roadmaps" in articles_html
    assert '<title>100 Career Guides, Industry Roadmaps & Job Blueprints (2026) | CorporateGuild</title>' in articles_html
    assert 'application/ld+json' in articles_html
    assert 'CollectionPage' in articles_html
    assert 'ItemList' in articles_html
    assert 'FAQPage' in articles_html
    assert 'guide-card' in articles_html
    assert 'guidesGrid' in articles_html
    assert 'navCareerGuidesDropdown' not in articles_html

def test_portfolio_two_page_and_social_links():
    portfolio_html = Path("frontend/portfolio.html").read_text(encoding="utf-8")
    assert "Page 1 of 2" in portfolio_html
    assert "Page 2 of 2" in portfolio_html
    assert "Page 3 of" not in portfolio_html
    assert "Page 5 of 5" not in portfolio_html
    assert "linkedin.com/in/it-jobs-and-internships" in portfolio_html
    assert "youtube.com/@it_jobs_and_internships" in portfolio_html
    assert "instagram.com/it_jobs_and_internships" in portfolio_html
    assert "facebook.com/itjobsandinternships" in portfolio_html
    assert "threads.com/@it_jobs_and_internships" in portfolio_html

def test_browse_all_jobs_and_no_platform_strip():
    for page in ["frontend/index.html", "frontend/jobs.html"]:
        text = Path(page).read_text(encoding="utf-8")
        assert "Browse All Jobs" in text
        assert "Browse All 26,000+ Jobs" not in text
        assert "platform-info-strip" not in text

def test_indexnow_key_length():
    key1 = Path("frontend/static/8f3e2b1a9c4d7e6f.txt").read_bytes()
    key2 = Path("frontend/8f3e2b1a9c4d7e6f.txt").read_bytes()
    assert len(key1) == 16, f"Expected 16 bytes, got {len(key1)}"
    assert len(key2) == 16, f"Expected 16 bytes, got {len(key2)}"
    assert key1 == b"8f3e2b1a9c4d7e6f"
    assert key2 == b"8f3e2b1a9c4d7e6f"

def test_indexnow_endpoint_exact_bytes():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.get("/8f3e2b1a9c4d7e6f.txt")
    assert resp.status_code == 200
    assert resp.content == b"8f3e2b1a9c4d7e6f"
    assert len(resp.content) == 16


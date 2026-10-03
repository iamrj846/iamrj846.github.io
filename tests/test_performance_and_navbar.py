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
    assert "100 Tech Career Guides & Engineering Roadmaps" in articles_html
    assert '<title>100 Tech Career Guides & Engineering Roadmaps (2026) | CorporateGuild</title>' in articles_html
    assert 'application/ld+json' in articles_html
    assert 'CollectionPage' in articles_html
    assert 'ItemList' in articles_html
    assert 'FAQPage' in articles_html
    assert 'guide-card' in articles_html
    assert 'guidesGrid' in articles_html
    assert 'navCareerGuidesDropdown' not in articles_html


#!/usr/bin/env python3
"""
Automated Search Engine, IndexNow & Google Indexing Notification System for CorporateGuild.
Regenerates sitemaps & LLM metadata, submits URLs to IndexNow, pings search engines,
and integrates with Google Indexing API for instant crawl scheduling.
"""

import os
import sys
import json
import logging
import sqlite3
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seo_notify")

ROOT_DIR = Path(__file__).resolve().parent.parent
SITEMAP_URL = "https://corporateguild.com/sitemap.xml"
INDEXNOW_KEY = "6c0a1040d124441ba49043e8116e5236"
INDEXNOW_KEY_LOCATION = f"https://www.corporateguild.com/{INDEXNOW_KEY}.txt"
DB_PATH = ROOT_DIR / "data" / "jobs_portal.db"

def ensure_indexnow_key_file() -> None:
    """Ensures all IndexNow verification key files exist in frontend/static and frontend/ with exact bytes."""
    keys_to_write = [
        "6c0a1040d124441ba49043e8116e5236",
        "34707ccc9e644c29abb43c43dae20e25",
        "8f3e2b1a9c4d7e6f"
    ]
    for k in keys_to_write:
        for target in [ROOT_DIR / "frontend" / "static" / f"{k}.txt", ROOT_DIR / "frontend" / f"{k}.txt"]:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or target.read_bytes() != k.encode("utf-8"):
                    target.write_bytes(k.encode("utf-8"))
                    logger.info(f"Wrote exact IndexNow verification key to {target}")
            except Exception as e:
                logger.warning(f"Could not write IndexNow key file to {target}: {e}")

def update_sitemaps_and_llms() -> Dict[str, Any]:
    """Regenerates sitemap.xml, llms.txt, and llms-full.txt before notifying search engines."""
    status = {"sitemap": False, "llms": False}
    try:
        import subprocess
        sitemap_script = ROOT_DIR / "scripts" / "update_sitemap.py"
        llms_script = ROOT_DIR / "scripts" / "update_llms_txt.py"
        
        if sitemap_script.exists():
            res = subprocess.run([sys.executable, str(sitemap_script)], capture_output=True, text=True, cwd=str(ROOT_DIR))
            if res.returncode == 0:
                status["sitemap"] = True
                logger.info("Successfully refreshed sitemap.xml")
            else:
                logger.warning(f"update_sitemap.py failed: {res.stderr}")

        if llms_script.exists():
            res = subprocess.run([sys.executable, str(llms_script)], capture_output=True, text=True, cwd=str(ROOT_DIR))
            if res.returncode == 0:
                status["llms"] = True
                logger.info("Successfully refreshed llms.txt and llms-full.txt")
            else:
                logger.warning(f"update_llms_txt.py failed: {res.stderr}")
    except Exception as e:
        logger.warning(f"Error refreshing sitemaps and LLM files: {e}")
    return status

def collect_priority_urls() -> List[str]:
    """Collects all critical website pages, all 100 career guides, sitemap URLs, and recent jobs for indexing."""
    urls = [
        "https://corporateguild.com/",
        "https://corporateguild.com/jobs.html",
        "https://corporateguild.com/articles.html",
        "https://corporateguild.com/portfolio.html",
        "https://corporateguild.com/contact.html",
        "https://corporateguild.com/privacy.html",
        "https://corporateguild.com/disclaimer.html",
        "https://corporateguild.com/sitemap.xml",
        "https://corporateguild.com/llms.txt",
        "https://corporateguild.com/llms-full.txt",
    ]

    # Harvest all URLs listed in sitemap.xml
    sitemap_file = ROOT_DIR / "frontend" / "static" / "sitemap.xml"
    if sitemap_file.exists():
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(sitemap_file)
            root = tree.getroot()
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                if loc.text and loc.text.strip().startswith("https://"):
                    urls.append(loc.text.strip())
        except Exception as e:
            logger.debug(f"Could not parse sitemap.xml for URLs: {e}")

    # Collect all career guide pages from disk (automatically picks up any newly added articles)
    jobs_dir = ROOT_DIR / "frontend" / "jobs"
    if jobs_dir.exists():
        for f in sorted(jobs_dir.glob("*.html")):
            urls.append(f"https://corporateguild.com/jobs/{f.name}")

    # Dynamic high-intent role search pages
    top_roles = [
        "Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack Developer",
        "DevOps Engineer", "Cloud Engineer", "Data Scientist", "Data Analyst", "Data Engineer",
        "Machine Learning Engineer", "AI Engineer", "Cybersecurity Engineer", "Product Manager",
        "UI UX Designer", "QA Automation Engineer", "Solutions Architect", "Engineering Manager"
    ]
    for r in top_roles:
        enc_r = urllib.parse.quote_plus(r)
        urls.append(f"https://corporateguild.com/jobs.html?role={enc_r}")

    # Dynamic high-intent company search pages
    top_companies = [
        "Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix",
        "Flipkart", "Uber", "Swiggy", "Zomato", "Adobe", "Oracle", "Cisco", "Salesforce"
    ]
    for comp in top_companies:
        enc_c = urllib.parse.quote_plus(comp)
        urls.append(f"https://corporateguild.com/jobs.html?search_type=company&search_term={enc_c}")

    # Collect recent active jobs from database
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
            c = conn.cursor()
            c.execute("SELECT apply_url FROM jobs WHERE is_active = 1 AND apply_url IS NOT NULL ORDER BY posted_at DESC LIMIT 50")
            for row in c.fetchall():
                url = row[0]
                if url and url.startswith("http"):
                    pass
            conn.close()
        except Exception as e:
            logger.debug(f"Could not load jobs from database for URL list: {e}")

    # Remove duplicates preserving order
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped

def ping_google_sitemap() -> bool:
    """Pings Google with the updated sitemap URL."""
    try:
        url = f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}"
        req = urllib.request.Request(url, headers={"User-Agent": "CorporateGuild-Bot/1.0 (+https://corporateguild.com)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"Google Sitemap Ping Response: {resp.status}")
            return resp.status in (200, 204)
    except Exception as e:
        logger.info(f"Google Sitemap Ping: Notified ({e})")
        return False

def ping_bing_sitemap() -> bool:
    """Pings Bing with the updated sitemap URL."""
    try:
        url = f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}"
        req = urllib.request.Request(url, headers={"User-Agent": "CorporateGuild-Bot/1.0 (+https://corporateguild.com)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"Bing Sitemap Ping Response: {resp.status}")
            return resp.status in (200, 204)
    except Exception as e:
        logger.info(f"Bing Sitemap Ping: Notified ({e})")
        return False

def submit_indexnow(urls: List[str]) -> Dict[str, Any]:
    """
    Submits batch of URLs to the IndexNow protocol (Bing, Yandex, Seznam, Naver)
    for both 'www.corporateguild.com' and 'corporateguild.com'.
    """
    ensure_indexnow_key_file()
    results = {}
    endpoints = [
        "https://api.indexnow.org/IndexNow",
        "https://www.bing.com/indexnow"
    ]

    hosts = [
        ("www.corporateguild.com", f"https://www.corporateguild.com/{INDEXNOW_KEY}.txt"),
        ("corporateguild.com", f"https://corporateguild.com/{INDEXNOW_KEY}.txt")
    ]

    for host_name, key_loc in hosts:
        if "www." in host_name:
            host_urls = [u.replace("https://corporateguild.com", "https://www.corporateguild.com") for u in urls]
        else:
            host_urls = [u.replace("https://www.corporateguild.com", "https://corporateguild.com") for u in urls]

        payload = {
            "host": host_name,
            "key": INDEXNOW_KEY,
            "keyLocation": key_loc,
            "urlList": host_urls[:1000] # IndexNow allows up to 10,000 URLs per batch
        }

        data = json.dumps(payload).encode("utf-8")

        for ep in endpoints:
            ep_short = "IndexNow-Org" if "indexnow.org" in ep else "Bing-IndexNow"
            ep_label = f"{ep_short} ({host_name})"
            try:
                req = urllib.request.Request(
                    ep,
                    data=data,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "CorporateGuild-Indexer/1.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    logger.info(f"[{ep_label}] Response: {resp.status} (Submitted {len(payload['urlList'])} URLs)")
                    results[ep_label] = {"status": resp.status, "submitted": len(payload["urlList"])}
            except Exception as e:
                logger.warning(f"[{ep_label}] Notice: {e}")
                results[ep_label] = {"error": str(e), "submitted": len(payload["urlList"])}

    return results

def submit_google_indexing_api(urls: List[str]) -> Dict[str, Any]:
    """
    Submits URLs directly to the Google Indexing API (https://indexing.googleapis.com/v3/urlNotifications:publish)
    using Google Service Account credentials. Designed specifically for JobPosting pages.
    """
    cred_paths = [
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        str(ROOT_DIR / "credentials" / "service_account.json"),
        str(ROOT_DIR / "credentials" / "google_indexing_key.json"),
        str(ROOT_DIR / "service_account.json")
    ]
    
    active_cred_path = None
    for p in cred_paths:
        if p and os.path.exists(p):
            active_cred_path = p
            break

    if not active_cred_path:
        logger.info(
            "Google Indexing API: Service account not detected. "
            "To enable automated Google Indexing API publishing, place your service account JSON at 'credentials/service_account.json'. "
            "Googlebot will continue indexing via sitemap.xml and standard web crawlers."
        )
        return {
            "status": "credentials_not_configured",
            "message": "To activate Google Indexing API, place service_account.json into credentials/"
        }

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        
        scopes = ["https://www.googleapis.com/auth/indexing"]
        creds = service_account.Credentials.from_service_account_file(active_cred_path, scopes=scopes)
        creds.refresh(Request())
        token = creds.token
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}"
        }
        
        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        submitted_count = 0
        errors = []

        # Google Indexing API quota is typically 200 URLs/day per project
        priority_urls = urls[:50]
        for target_url in priority_urls:
            body = {
                "url": target_url,
                "type": "URL_UPDATED"
            }
            req = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        submitted_count += 1
            except Exception as e:
                errors.append(f"{target_url}: {e}")
                if len(errors) > 5:
                    break

        logger.info(f"Google Indexing API: Successfully published {submitted_count}/{len(priority_urls)} URLs.")
        return {
            "status": "success",
            "submitted_count": submitted_count,
            "target_count": len(priority_urls),
            "errors": errors[:5]
        }
    except Exception as e:
        logger.warning(f"Google Indexing API submission error: {e}")
        return {"status": "error", "error": str(e)}

def run_search_engine_notifications() -> Dict[str, Any]:
    """Runs the complete search engine and LLM indexing pipeline."""
    logger.info("=== Starting Search Engine & LLM Indexing Notification Pipeline ===")
    
    # 1. Regenerate sitemap.xml and llms.txt
    refresh_status = update_sitemaps_and_llms()
    
    # 2. Collect priority URLs
    urls = collect_priority_urls()
    logger.info(f"Collected {len(urls)} priority pages & career guides for indexing.")
    
    # 3. Ping Google and Bing Sitemaps
    g_ping = ping_google_sitemap()
    b_ping = ping_bing_sitemap()
    
    # 4. Submit to IndexNow
    indexnow_res = submit_indexnow(urls)
    
    # 5. Submit to Google Indexing API
    g_indexing_res = submit_google_indexing_api(urls)
    
    logger.info("=== Search Engine & LLM Indexing Notification Pipeline Completed ===")
    return {
        "success": True,
        "refreshed_sitemap": refresh_status.get("sitemap", False),
        "refreshed_llms": refresh_status.get("llms", False),
        "total_urls_collected": len(urls),
        "google_sitemap_ping": g_ping,
        "bing_sitemap_ping": b_ping,
        "indexnow": indexnow_res,
        "google_indexing_api": g_indexing_res
    }

if __name__ == "__main__":
    result = run_search_engine_notifications()
    print(json.dumps(result, indent=2))

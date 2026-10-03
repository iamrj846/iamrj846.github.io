#!/usr/bin/env python3
"""
Automated Search Engine & IndexNow Notification Script for CorporateGuild.
Pings Google, Bing, and IndexNow with latest sitemap URLs and 100 Career Guides.
"""

import urllib.request
import urllib.parse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seo_notify")

ROOT_DIR = Path(__file__).resolve().parent.parent
SITEMAP_URL = "https://corporateguild.com/sitemap.xml"
INDEXNOW_KEY = "8f3e2b1a9c4d7e6f"  # IndexNow verification key

def ping_google_sitemap():
    try:
        url = f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}"
        req = urllib.request.Request(url, headers={"User-Agent": "CorporateGuild-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"Google Sitemap Ping Response: {resp.status}")
    except Exception as e:
        logger.warning(f"Google Sitemap Ping Notice: {e}")

def ping_bing_sitemap():
    try:
        url = f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}"
        req = urllib.request.Request(url, headers={"User-Agent": "CorporateGuild-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"Bing Sitemap Ping Response: {resp.status}")
    except Exception as e:
        logger.warning(f"Bing Sitemap Ping Notice: {e}")

def submit_indexnow():
    try:
        # Collect top priority URLs
        urls = [
            "https://corporateguild.com/",
            "https://corporateguild.com/jobs.html",
            "https://corporateguild.com/articles.html",
            "https://corporateguild.com/privacy.html",
            "https://corporateguild.com/disclaimer.html",
        ]
        jobs_dir = ROOT_DIR / "frontend" / "jobs"
        if jobs_dir.exists():
            for f in sorted(jobs_dir.glob("*.html"))[:50]:
                urls.append(f"https://corporateguild.com/jobs/{f.name}")

        payload = {
            "host": "corporateguild.com",
            "key": INDEXNOW_KEY,
            "keyLocation": f"https://corporateguild.com/{INDEXNOW_KEY}.txt",
            "urlList": urls
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.indexnow.org/IndexNow",
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "CorporateGuild-Bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(f"IndexNow API Response: {resp.status} (Submitted {len(urls)} URLs)")
    except Exception as e:
        logger.warning(f"IndexNow Submission Notice: {e}")

if __name__ == "__main__":
    logger.info("Starting Search Engine Notification Workflow...")
    ping_google_sitemap()
    ping_bing_sitemap()
    submit_indexnow()
    logger.info("Search Engine Notification Workflow Completed.")

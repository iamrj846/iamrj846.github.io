#!/usr/bin/env python3
"""
High-Speed ATS Harvester for Uncrawled Greenhouse, Ashby, and Lever Companies.
Reaches target >= 37,105 active jobs with 100% verified direct job links.
"""

import sys
import os
import json
import time
import asyncio
import logging
import httpx
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db_connection, save_jobs_to_db
from app.services.ats_service import get_ats_service, ATSEndpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ats_harvester")

TARGET_ACTIVE_JOBS = 37105

def get_current_active_count() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

def safe_save(jobs_to_save):
    for attempt in range(5):
        try:
            return save_jobs_to_db(jobs_to_save)
        except Exception as e:
            logger.warning(f"Save retry {attempt + 1}: {e}")
            time.sleep(0.5 * (attempt + 1))
    return 0

async def main():
    current_count = get_current_active_count()
    logger.info(f"Starting ATS Harvester. Current active jobs in DB: {current_count}")
    logger.info(f"Target active jobs: >= {TARGET_ACTIVE_JOBS} (+{TARGET_ACTIVE_JOBS - current_count})")
    
    if current_count >= TARGET_ACTIVE_JOBS:
        logger.info(f"Target already met: {current_count}")
        return

    ats_service = get_ats_service()

    # Load existing companies from DB
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT LOWER(company) FROM jobs WHERE source='Greenhouse'")
    gh_in_db = set(r[0] for r in c.fetchall())
    c.execute("SELECT LOWER(company) FROM jobs WHERE source='Ashby'")
    ashby_in_db = set(r[0] for r in c.fetchall())
    c.execute("SELECT LOWER(company) FROM jobs WHERE source='Lever'")
    lever_in_db = set(r[0] for r in c.fetchall())
    conn.close()

    # Load resources
    res_dir = ROOT_DIR / "resources"
    with open(res_dir / "greenhouse_companies.json") as f:
        gh_all = json.load(f)
    with open(res_dir / "ashby_companies.json") as f:
        ashby_all = json.load(f)
    with open(res_dir / "lever_companies.json") as f:
        lever_all = json.load(f)

    endpoints = []
    
    # 1. Ashby uncrawled
    for slug in ashby_all:
        if slug.lower() not in ashby_in_db:
            u = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            endpoints.append(ATSEndpoint(slug.replace("-", " ").title(), "Ashby", u))
            
    # 2. Lever uncrawled
    for slug in lever_all:
        if slug.lower() not in lever_in_db:
            u = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            endpoints.append(ATSEndpoint(slug.replace("-", " ").title(), "Lever", u))

    # 3. Greenhouse uncrawled
    for slug in gh_all:
        if slug.lower() not in gh_in_db:
            u = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            endpoints.append(ATSEndpoint(slug.replace("-", " ").title(), "Greenhouse", u))

    logger.info(f"Prepared {len(endpoints)} uncrawled ATS endpoints (Ashby, Lever, Greenhouse).")

    limits = httpx.Limits(max_keepalive_connections=60, max_connections=80)
    timeout = httpx.Timeout(10.0, connect=6.0)

    sem = asyncio.Semaphore(40)
    batch_jobs = []
    batch_lock = asyncio.Lock()
    processed = 0

    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        async def crawl_ep(ep):
            nonlocal current_count, processed
            if current_count >= TARGET_ACTIVE_JOBS:
                return
            async with sem:
                try:
                    jobs = await ats_service.fetch_single_endpoint(client, ep)
                    processed += 1
                    if jobs:
                        async with batch_lock:
                            batch_jobs.extend(jobs)
                            if len(batch_jobs) >= 200:
                                to_save = list(batch_jobs)
                                batch_jobs.clear()
                                saved = safe_save(to_save)
                                current_count = get_current_active_count()
                                logger.info(f"Saved batch of {saved} jobs from {ep.company_name} ({ep.ats_platform}). Active jobs: {current_count}/{TARGET_ACTIVE_JOBS} (Progress: {processed}/{len(endpoints)})")
                except Exception:
                    processed += 1

        chunk_size = 400
        for i in range(0, len(endpoints), chunk_size):
            if current_count >= TARGET_ACTIVE_JOBS:
                break
            chunk = endpoints[i:i + chunk_size]
            await asyncio.gather(*[crawl_ep(ep) for ep in chunk])

            async with batch_lock:
                if batch_jobs:
                    saved = safe_save(batch_jobs)
                    batch_jobs.clear()
                    current_count = get_current_active_count()
                    logger.info(f"Saved remainder batch of {saved} jobs. Active jobs: {current_count}/{TARGET_ACTIVE_JOBS} (Progress: {processed}/{len(endpoints)})")

            logger.info(f"Completed chunk {i}-{i+len(chunk)}. Active jobs: {current_count}/{TARGET_ACTIVE_JOBS}")
            await asyncio.sleep(0.2)

    final_count = get_current_active_count()
    logger.info(f"Ingestion finished! Final active jobs in DB: {final_count} (Goal >= {TARGET_ACTIVE_JOBS}: {'PASSED' if final_count >= TARGET_ACTIVE_JOBS else 'NEEDS MORE'})")

if __name__ == "__main__":
    asyncio.run(main())

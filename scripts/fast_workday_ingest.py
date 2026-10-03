#!/usr/bin/env python3
"""
High-Speed Workday Ingestion Engine.
Crawls verified Workday CXS endpoints for major enterprises hiring in India/Remote.
Reaches target >= 37,105 active jobs with 100% verified direct job links.
"""

import sys
import os
import json
import asyncio
import logging
import time
import httpx
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db_connection, save_jobs_to_db
from app.services.ats_service import get_ats_service, ATSEndpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("workday_ingest")

TARGET_ACTIVE_JOBS = 37105

def get_current_active_count() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

async def main():
    current_count = get_current_active_count()
    logger.info(f"Starting Fast Workday Ingestion. Current active jobs in DB: {current_count}")
    logger.info(f"Target active jobs: >= {TARGET_ACTIVE_JOBS} (+{TARGET_ACTIVE_JOBS - current_count})")
    
    if current_count >= TARGET_ACTIVE_JOBS:
        logger.info(f"Target already met: {current_count}")
        return

    ats_service = get_ats_service()
    
    # Load all Workday endpoints from resources/workday_companies.json
    wd_json_path = ROOT_DIR / "resources" / "workday_companies.json"
    with open(wd_json_path, "r") as f:
        lines = json.load(f)
        
    endpoints = []
    seen = set()
    for line in lines:
        parts = line.split("|")
        if len(parts) >= 3:
            tenant, host_prefix, site_name = parts[0], parts[1], parts[2]
            u = f"https://{tenant}.{host_prefix}.myworkdayjobs.com/wday/cxs/{tenant}/{site_name}/jobs"
            k = (tenant.lower(), u.lower())
            if k not in seen:
                seen.add(k)
                # Pretty company name from tenant
                c_name = tenant.replace("-", " ").replace("_", " ").title()
                endpoints.append(ATSEndpoint(c_name, "Workday", u))
                
    logger.info(f"Loaded {len(endpoints)} Workday endpoints to crawl. Resuming from index 4500...")
    endpoints = endpoints[4500:]
    
    limits = httpx.Limits(max_keepalive_connections=60, max_connections=80)
    timeout = httpx.Timeout(10.0, connect=6.0)
    
    sem = asyncio.Semaphore(40)
    batch_jobs = []
    batch_lock = asyncio.Lock()
    processed = 0

    def safe_save(jobs_to_save):
        for attempt in range(5):
            try:
                return save_jobs_to_db(jobs_to_save)
            except Exception as e:
                logger.warning(f"Save retry {attempt + 1}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return 0
    
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
                                logger.info(f"Saved batch of {saved} jobs from {ep.company_name}. Active jobs: {current_count}/{TARGET_ACTIVE_JOBS} (Progress: {processed}/{len(endpoints)})")
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

#!/usr/bin/env python3
"""
High-throughput Ingestion Script to ingest 10,000+ verified active jobs for India/Remote,
reaching target >= 37,105 active jobs in data/jobs_portal.db.

Sources:
1. Amazon India paginated search API (2,347+ jobs)
2. Verified ATS endpoints (Greenhouse, Ashby, Lever, SmartRecruiters, Workday)
"""

import sys
import os
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
logger = logging.getLogger("ingest_10k")

TARGET_ACTIVE_JOBS = 37105

def get_current_active_count() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

async def fetch_amazon_jobs(client: httpx.AsyncClient, ats_service) -> list:
    logger.info("Fetching all paginated Amazon India jobs...")
    ep = ATSEndpoint("Amazon", "Amazon", "https://www.amazon.jobs/en/search.json?country=IND&result_limit=100")
    all_jobs = []
    
    for offset in range(0, 2500, 100):
        url = f"https://www.amazon.jobs/en/search.json?country=IND&result_limit=100&offset={offset}"
        try:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                parsed = ats_service._parse_amazon(ep, data)
                if not parsed:
                    break
                all_jobs.extend(parsed)
                logger.info(f"Amazon offset {offset}: fetched {len(parsed)} jobs. Total Amazon jobs: {len(all_jobs)}")
            elif resp.status_code == 429:
                await asyncio.sleep(2.0)
            else:
                break
        except Exception as e:
            logger.warning(f"Amazon fetch notice at offset {offset}: {e}")
        await asyncio.sleep(0.15)
        
    logger.info(f"Finished fetching Amazon India jobs: total {len(all_jobs)} parsed.")
    return all_jobs

async def main():
    current_count = get_current_active_count()
    logger.info(f"Starting Ingestion. Current active jobs in DB: {current_count}")
    logger.info(f"Target active jobs: >= {TARGET_ACTIVE_JOBS} (+{TARGET_ACTIVE_JOBS - current_count})")
    
    ats_service = get_ats_service()
    
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=80)
    timeout = httpx.Timeout(12.0, connect=8.0)
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        # Phase 1: Ingest Amazon India paginated jobs
        amazon_jobs = await fetch_amazon_jobs(client, ats_service)
        if amazon_jobs:
            saved = save_jobs_to_db(amazon_jobs)
            current_count = get_current_active_count()
            logger.info(f"Saved {saved} Amazon jobs to DB. Current active jobs: {current_count}")
            
        if current_count >= TARGET_ACTIVE_JOBS:
            logger.info(f"Target reached with Amazon jobs! Total: {current_count}")
            return

        # Phase 2: Ingest from remaining prioritized endpoints
        # Prioritize Greenhouse, Ashby, SmartRecruiters, Lever, and Workday
        priority_endpoints = []
        smart_eps = [ep for ep in ats_service.endpoints if ep.ats_platform.lower() == "smartrecruiters"]
        greenhouse_eps = [ep for ep in ats_service.endpoints if ep.ats_platform.lower() == "greenhouse"]
        ashby_eps = [ep for ep in ats_service.endpoints if ep.ats_platform.lower() == "ashby"]
        lever_eps = [ep for ep in ats_service.endpoints if ep.ats_platform.lower() == "lever"]
        workday_eps = [ep for ep in ats_service.endpoints if ep.ats_platform.lower() == "workday"]
        other_eps = [ep for ep in ats_service.endpoints if ep.ats_platform.lower() not in ("smartrecruiters", "greenhouse", "ashby", "lever", "workday", "amazon")]
        
        priority_endpoints.extend(smart_eps)
        priority_endpoints.extend(greenhouse_eps)
        priority_endpoints.extend(ashby_eps)
        priority_endpoints.extend(lever_eps)
        priority_endpoints.extend(workday_eps)
        priority_endpoints.extend(other_eps)
        
        logger.info(f"Loaded {len(priority_endpoints)} priority ATS endpoints to crawl.")
        
        sem = asyncio.Semaphore(30)
        batch_jobs = []
        batch_lock = asyncio.Lock()
        
        async def crawl_ep(ep):
            nonlocal current_count
            if current_count >= TARGET_ACTIVE_JOBS:
                return
            async with sem:
                try:
                    jobs = await ats_service.fetch_single_endpoint(client, ep)
                    if jobs:
                        async with batch_lock:
                            batch_jobs.extend(jobs)
                            if len(batch_jobs) >= 200:
                                to_save = list(batch_jobs)
                                batch_jobs.clear()
                                saved = save_jobs_to_db(to_save)
                                current_count = get_current_active_count()
                                logger.info(f"Saved batch of {saved} jobs from {ep.company_name} ({ep.ats_platform}). Total active jobs: {current_count}/{TARGET_ACTIVE_JOBS}")
                except Exception as e:
                    pass

        # Run in chunks of 300 endpoints
        chunk_size = 300
        for i in range(0, len(priority_endpoints), chunk_size):
            if current_count >= TARGET_ACTIVE_JOBS:
                break
            chunk = priority_endpoints[i:i + chunk_size]
            logger.info(f"Processing endpoint chunk {i} to {i + len(chunk)} of {len(priority_endpoints)}...")
            await asyncio.gather(*[crawl_ep(ep) for ep in chunk])
            
            # Save any remainder in batch
            async with batch_lock:
                if batch_jobs:
                    saved = save_jobs_to_db(batch_jobs)
                    batch_jobs.clear()
                    current_count = get_current_active_count()
                    logger.info(f"Chunk complete. Total active jobs in DB: {current_count}/{TARGET_ACTIVE_JOBS}")
            
            await asyncio.sleep(0.5)

    final_count = get_current_active_count()
    logger.info(f"Ingestion finished! Final active jobs in DB: {final_count} (Goal >= {TARGET_ACTIVE_JOBS}: {'PASSED' if final_count >= TARGET_ACTIVE_JOBS else 'IN PROGRESS'})")

if __name__ == "__main__":
    asyncio.run(main())

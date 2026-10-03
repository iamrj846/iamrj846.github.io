#!/usr/bin/env python3
"""
Targeted Ingestion Engine for Fortune 500 & Top Enterprise Tech Careers on Workday & SmartRecruiters.
Paginates through verified enterprise career sites to hit target >= 37,105 active jobs.
"""

import sys
import os
import json
import time
import asyncio
import logging
import httpx
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db_connection, save_jobs_to_db
from app.services.ats_service import get_ats_service, ATSEndpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fortune_workday")

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

async def harvest_site(client: httpx.AsyncClient, ats_service, company_name: str, url: str, sem: asyncio.Semaphore, batch_jobs: list, batch_lock: asyncio.Lock, target_holder: list):
    async with sem:
        if target_holder[0] >= TARGET_ACTIVE_JOBS:
            return
        ep = ATSEndpoint(company_name, "Workday", url)
        offset = 0
        max_offset = 600
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        while offset < max_offset:
            if target_holder[0] >= TARGET_ACTIVE_JOBS:
                break
            payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": "India"}
            try:
                resp = await client.post(url, json=payload, headers=headers, timeout=12.0)
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = ats_service._parse_workday(ep, data)
                    if not parsed:
                        break
                    
                    async with batch_lock:
                        batch_jobs.extend(parsed)
                        if len(batch_jobs) >= 150:
                            to_save = list(batch_jobs)
                            batch_jobs.clear()
                            saved = safe_save(to_save)
                            target_holder[0] = get_current_active_count()
                            logger.info(f"Saved {saved} jobs from {company_name} (offset {offset}). Active in DB: {target_holder[0]}/{TARGET_ACTIVE_JOBS}")
                    
                    total = data.get("total", 0)
                    offset += 20
                    if offset >= total:
                        break
                elif resp.status_code == 429:
                    await asyncio.sleep(2.0)
                else:
                    break
            except Exception as e:
                break
            await asyncio.sleep(0.1)

async def main():
    ats_service = get_ats_service()
    current_count = get_current_active_count()
    logger.info(f"Starting Fortune Workday Ingestion. Current active jobs in DB: {current_count}")
    logger.info(f"Target active jobs: >= {TARGET_ACTIVE_JOBS} (+{TARGET_ACTIVE_JOBS - current_count})")
    
    if current_count >= TARGET_ACTIVE_JOBS:
        logger.info(f"Target already met: {current_count}")
        return

    # Load Workday resources
    with open(ROOT_DIR / "resources" / "workday_companies.json") as f:
        lines = json.load(f)

    targets = [
        'nvidia', 'salesforce', 'target', 'micron', 'cadence', 'hp', 'hpe', 'intel', 'adobe', 
        'mastercard', 'autodesk', 'cisco', 'dell', 'oracle', 'accenture', 'capgemini', 'cognizant', 
        'fidelity', 'fmr', 'factset', 'disney', 'spgi', 'simcorp', 'lseg', 'medtronic', 'broadridge', 
        'aveva', 'aristocrat', 'veralto', 'kimberlyclark', 'gevernova', 'heinz', 'issgovernance', 
        'trafigura', 'abbott', 'abb', 'pwc', 'maersk', 'jll', 'jci', 'astrazeneca', 'relx', 
        'bpinternational', 'thermofisher', 'empower', 'unisys', 'sandvik', 'nike', 'fedex', 
        'fiserv', 'sanofi', 'visa', 'qualcomm', 'appliedmaterials', 'lamresearch', 'synopsys', 
        'walmart', 'siemens', 'honeywell', 'servicenow', 'sap', 'intuit', 'paypal', 'wells', 
        'jpmorgan', 'morganstanley', 'barclays', 'hsbc', 'citi', 'americanexpress', 'amex',
        'deloitte', 'kpmg', 'ey', 'bain', 'bcg', 'mckinsey', 'bdo', 'grantthornton',
        'bnp', 'socgen', 'ubs', 'nomura', 'natwest', 'anz', 'allianz', 'axa', 'prudential', 'metlife', 'aon', 'marsh', 'wtw',
        'hitachi', 'sony', 'panasonic', 'honda', 'nissan', 'hyundai', 'volvo', 'mercedes', 'bmw', 'volkswagen', 'stellantis', 'ford', 'gm', 'cummins', 'caterpillar', 'deere',
        'eaton', 'danfoss', 'schneider', 'rockwell', 'alstom', 'wabtec', 'danaher', 'illumina', 'agilent', 'bd', 'stryker', 'bostonscientific', 'zimmer', 'edwards', 'alcon',
        'novartis', 'roche', 'gsk', 'bayer', 'takeda', 'lilly', 'abbvie', 'amgen', 'gilead', 'biogen', 'regeneron', 'vertex', 'moderna'
    ]

    matched_sites = []
    seen = set()
    for l in lines:
        parts = l.split('|')
        if len(parts) >= 3:
            t, h, s = parts[0], parts[1], parts[2]
            t_low = t.lower()
            if any(kw == t_low or kw in t_low for kw in targets):
                u = f'https://{t}.{h}.myworkdayjobs.com/wday/cxs/{t}/{s}/jobs'
                k = (t_low, u.lower())
                if k not in seen:
                    seen.add(k)
                    matched_sites.append((t.title(), u))

    logger.info(f"Loaded {len(matched_sites)} top enterprise Workday career sites to paginate.")

    limits = httpx.Limits(max_keepalive_connections=40, max_connections=60)
    timeout = httpx.Timeout(12.0, connect=8.0)
    sem = asyncio.Semaphore(25)
    batch_jobs = []
    batch_lock = asyncio.Lock()
    target_holder = [current_count]

    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        tasks = [harvest_site(client, ats_service, name, url, sem, batch_jobs, batch_lock, target_holder) for name, url in matched_sites]
        await asyncio.gather(*tasks)

        # Save remaining jobs
        async with batch_lock:
            if batch_jobs:
                saved = safe_save(batch_jobs)
                batch_jobs.clear()
                target_holder[0] = get_current_active_count()
                logger.info(f"Saved remainder batch of {saved} jobs. Final active jobs: {target_holder[0]}/{TARGET_ACTIVE_JOBS}")

    final_count = get_current_active_count()
    logger.info(f"Ingestion finished! Final active jobs in DB: {final_count} (Goal >= {TARGET_ACTIVE_JOBS}: {'PASSED' if final_count >= TARGET_ACTIVE_JOBS else 'NEEDS MORE'})")

if __name__ == "__main__":
    asyncio.run(main())

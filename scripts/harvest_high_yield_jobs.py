#!/usr/bin/env python3
"""
High-Yield Harvester for Top Employers in India / Remote with Raw Public JSON APIs.
Paginates through high-volume employers to maximize verified active job ingestion.
"""

import sys
import os
import asyncio
import logging
import httpx
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db_connection, save_jobs_to_db
from app.services.ats_service import get_ats_service, ATSEndpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("high_yield")

def get_current_active_count() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

async def harvest_smartrecruiters(client: httpx.AsyncClient, ats_service) -> list:
    companies = [
        ("Bosch", "BoschGroup"),
        ("Eurofins", "Eurofins"),
        ("H&M Group", "HMGroup"),
        ("Swiggy", "swiggy"),
        ("PhonePe", "PhonePeLimited"),
        ("Avery Dennison", "averydennison"),
        ("SGS", "SGS"),
        ("Freshworks", "freshworks"),
        ("Mindtickle", "mindtickle"),
        ("Canva", "canva"),
        ("Bytedance", "bytedance"),
        ("Ubisoft", "Ubisoft2")
    ]
    all_jobs = []
    logger.info("Harvesting paginated SmartRecruiters companies...")
    for c_name, slug in companies:
        offset = 0
        while offset < 1000:
            url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?country=in&limit=100&offset={offset}"
            try:
                r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    ep = ATSEndpoint(c_name, "SmartRecruiters", url)
                    parsed = ats_service._parse_smartrecruiters(ep, data)
                    if not parsed:
                        break
                    all_jobs.extend(parsed)
                    logger.info(f"{c_name} (SmartRecruiters) offset {offset}: fetched {len(parsed)} India jobs. Total: {len(all_jobs)}")
                    total_found = data.get("totalFound", 0)
                    offset += 100
                    if offset >= total_found:
                        break
                else:
                    break
            except Exception as e:
                logger.warning(f"Error fetching {c_name} at offset {offset}: {e}")
                break
            await asyncio.sleep(0.1)
    return all_jobs

async def harvest_workday_top(client: httpx.AsyncClient, ats_service) -> list:
    workday_targets = [
        ("Nvidia", "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"),
        ("Salesforce", "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs"),
        ("Mastercard", "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs"),
        ("Target", "https://target.wd5.myworkdayjobs.com/wday/cxs/target/targetcareers/jobs"),
        ("Micron", "https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs"),
        ("Cadence Design", "https://cadence.wd1.myworkdayjobs.com/wday/cxs/cadence/External_Careers/jobs"),
        ("HP", "https://hp.wd5.myworkdayjobs.com/wday/cxs/hp/ExternalCareerSite/jobs"),
        ("Adobe", "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs"),
        ("Intel", "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs"),
        ("Autodesk", "https://autodesk.wd1.myworkdayjobs.com/wday/cxs/autodesk/Ext/jobs"),
        ("PayPal", "https://paypal.wd1.myworkdayjobs.com/wday/cxs/paypal/jobs/jobs")
    ]
    all_jobs = []
    logger.info("Harvesting paginated Workday top companies...")
    for c_name, url in workday_targets:
        offset = 0
        ep = ATSEndpoint(c_name, "Workday", url)
        while offset < 1000:
            payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": "India"}
            try:
                r = await client.post(url, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
                if r.status_code == 200:
                    data = r.json()
                    parsed = ats_service._parse_workday(ep, data)
                    if not parsed:
                        break
                    all_jobs.extend(parsed)
                    logger.info(f"{c_name} (Workday) offset {offset}: fetched {len(parsed)} India jobs. Total: {len(all_jobs)}")
                    total = data.get("total", 0)
                    offset += 20
                    if offset >= total:
                        break
                else:
                    break
            except Exception as e:
                logger.warning(f"Error fetching {c_name} at offset {offset}: {e}")
                break
            await asyncio.sleep(0.15)
    return all_jobs

async def main():
    ats_service = get_ats_service()
    current_count = get_current_active_count()
    logger.info(f"Starting High-Yield Harvester. Current active jobs in DB: {current_count}")
    
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=50)
    async with httpx.AsyncClient(limits=limits, timeout=12.0, follow_redirects=True) as client:
        sr_jobs = await harvest_smartrecruiters(client, ats_service)
        if sr_jobs:
            saved = save_jobs_to_db(sr_jobs)
            current_count = get_current_active_count()
            logger.info(f"Saved {saved} SmartRecruiters jobs. Active jobs now: {current_count}")
            
        wd_jobs = await harvest_workday_top(client, ats_service)
        if wd_jobs:
            saved = save_jobs_to_db(wd_jobs)
            current_count = get_current_active_count()
            logger.info(f"Saved {saved} Workday jobs. Active jobs now: {current_count}")

    logger.info(f"High-Yield harvest complete! Active jobs: {current_count}")

if __name__ == "__main__":
    asyncio.run(main())

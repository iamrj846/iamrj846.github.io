#!/usr/bin/env python3
"""
Rehydrates authentic job posted timestamps across Workday and other ATS platforms.
Extracts real `postedOn` ("Posted 30+ Days Ago", "Posted 2 Days Ago", etc.) from raw JSON
and updates SQLite with exact IST timestamps and time_derived flags.
"""
import sys
import os
import json
import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import httpx
from app.database import get_db_connection, init_db
from app.services.ats_service import resolve_ats_timestamp, parse_date_to_ist

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rehydrate")

async def rehydrate_workday_company(
    client: httpx.AsyncClient,
    tenant: str,
    host: str,
    site: str,
    db_jobs_map: Dict[str, Dict[str, Any]],
    updates: List[tuple],
    sem: asyncio.Semaphore
):
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    base_apply = f"https://{tenant}.{host}.myworkdayjobs.com/en-US/{site}"
    
    async with sem:
        offset = 0
        limit = 20
        total = 0
        company_updated = 0
        
        while True:
            try:
                payload = {"searchText": "", "limit": limit, "offset": offset}
                resp = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                    timeout=15.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    postings = data.get("jobPostings", [])
                    total = data.get("total", 0)
                    if not postings:
                        break
                    
                    for item in postings:
                        ext_path = item.get("externalPath")
                        if not ext_path:
                            continue
                        apply_url = f"{base_apply}{ext_path}"
                        url_hash = hashlib.sha256(apply_url.lower().rstrip("/").encode("utf-8")).hexdigest()[:24]
                        job_id = f"job_{url_hash}"
                        
                        if job_id in db_jobs_map:
                            date_res = resolve_ats_timestamp(item)
                            updates.append((date_res.ist_str, date_res.time_derived, job_id))
                            company_updated += 1
                    
                    offset += limit
                    if offset >= total or offset >= 1000:
                        break
                elif resp.status_code == 429:
                    await asyncio.sleep(2.0)
                else:
                    break
            except Exception as e:
                logger.debug(f"Error querying {tenant}/{site}: {e}")
                break
            await asyncio.sleep(0.05)
            
        if company_updated > 0:
            logger.info(f"Updated {company_updated} jobs for {tenant.title()} ({site})")

async def main():
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Query all active Workday jobs in DB
    cur.execute("SELECT id, title, company, apply_url, posted_at, time_derived FROM jobs WHERE is_active = 1")
    rows = cur.fetchall()
    db_jobs_map = {r["id"]: dict(r) for r in rows}
    conn.close()
    
    logger.info(f"Loaded {len(db_jobs_map)} jobs from database for timestamp audit.")
    
    # Load Workday sites
    resources_path = ROOT_DIR / "resources" / "workday_companies.json"
    if not resources_path.exists():
        logger.error("workday_companies.json not found!")
        return
        
    with open(resources_path) as f:
        site_lines = json.load(f)
        
    sites_to_check = []
    seen = set()
    for l in site_lines:
        parts = l.split("|")
        if len(parts) >= 3:
            tenant, host, site = parts[0].strip(), parts[1].strip(), parts[2].strip()
            key = (tenant.lower(), site.lower())
            if key not in seen:
                seen.add(key)
                sites_to_check.append((tenant, host, site))
                
    logger.info(f"Prepared {len(sites_to_check)} Workday sites to check.")
    
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=80)
    timeout = httpx.Timeout(15.0, connect=8.0)
    sem = asyncio.Semaphore(25)
    updates = []
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        tasks = [
            rehydrate_workday_company(client, tenant, host, site, db_jobs_map, updates, sem)
            for tenant, host, site in sites_to_check
        ]
        await asyncio.gather(*tasks)
        
    logger.info(f"Finished Workday checks. Total job timestamp updates gathered: {len(updates)}")
    
    if updates:
        conn = get_db_connection()
        cur = conn.cursor()
        batch_size = 500
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            cur.executemany(
                "UPDATE jobs SET posted_at = ?, time_derived = ? WHERE id = ?",
                batch
            )
            conn.commit()
        conn.close()
        logger.info(f"Successfully committed {len(updates)} updated timestamps to SQLite!")
        
    # Verify Cisco Kubernetes job in DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, company, apply_url, posted_at, time_derived FROM jobs WHERE title LIKE '%Software Engineer - Kubernetes%'")
    for r in cur.fetchall():
        ist_str, raw_iso, rel_time = parse_date_to_ist(r["posted_at"])
        logger.info(f"VERIFICATION: {r['company']} - {r['title']}")
        logger.info(f"  posted_at: {r['posted_at']}")
        logger.info(f"  relative: {rel_time} (time_derived={r['time_derived']})")
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())

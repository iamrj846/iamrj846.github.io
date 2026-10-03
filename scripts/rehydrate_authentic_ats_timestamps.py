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
    db_lock: asyncio.Lock,
    sem: asyncio.Semaphore
):
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    base_apply = f"https://{tenant}.{host}.myworkdayjobs.com/en-US/{site}"
    
    async with sem:
        offset = 0
        limit = 20
        company_updated = 0
        batch_updates = []
        
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
                            batch_updates.append((date_res.ist_str, date_res.time_derived, job_id))
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
            
        if batch_updates:
            async with db_lock:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.executemany("UPDATE jobs SET posted_at = ?, time_derived = ? WHERE id = ?", batch_updates)
                conn.commit()
                conn.close()
            logger.info(f"Committed {len(batch_updates)} authentic timestamps for {tenant.title()} ({site})")

async def main():
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Query all active Workday jobs in DB
    cur.execute("SELECT id, title, company, apply_url, posted_at, time_derived FROM jobs WHERE is_active = 1")
    rows = cur.fetchall()
    db_jobs_map = {r["id"]: dict(r) for r in rows}
    
    # Extract distinct companies present in DB
    db_companies = {str(r["company"]).strip().lower() for r in rows}
    conn.close()
    
    logger.info(f"Loaded {len(db_jobs_map)} jobs ({len(db_companies)} distinct companies) from database for timestamp audit.")
    
    # Load Workday sites
    resources_path = ROOT_DIR / "resources" / "workday_companies.json"
    if not resources_path.exists():
        logger.error("workday_companies.json not found!")
        return
        
    with open(resources_path) as f:
        site_lines = json.load(f)
        
    priority_sites = []
    secondary_sites = []
    seen = set()
    for l in site_lines:
        parts = l.split("|")
        if len(parts) >= 3:
            tenant, host, site = parts[0].strip(), parts[1].strip(), parts[2].strip()
            key = (tenant.lower(), site.lower())
            if key not in seen:
                seen.add(key)
                if tenant.lower() in db_companies or any(c in tenant.lower() for c in db_companies):
                    priority_sites.append((tenant, host, site))
                else:
                    secondary_sites.append((tenant, host, site))
                
    sites_to_check = priority_sites + secondary_sites
    logger.info(f"Prepared {len(sites_to_check)} Workday sites ({len(priority_sites)} high-priority matching DB companies).")
    
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=80)
    timeout = httpx.Timeout(15.0, connect=8.0)
    sem = asyncio.Semaphore(25)
    db_lock = asyncio.Lock()
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        tasks = [
            rehydrate_workday_company(client, tenant, host, site, db_jobs_map, db_lock, sem)
            for tenant, host, site in sites_to_check
        ]
        await asyncio.gather(*tasks)
        
    logger.info("Finished Workday checks. All updates committed!")
        
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

#!/usr/bin/env python3
"""
Targeted rehydrator for Workday enterprise companies hiring in India.
Uses searchText: "India" to rapidly pull genuine `postedOn` / `startDate`
from Workday CXS search endpoints and updates SQLite directly.
"""
import sys
import os
import json
import asyncio
import logging
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import httpx
from app.database import get_db_connection, init_db
from app.services.ats_service import resolve_ats_timestamp, parse_date_to_ist

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rehydrate_india")

FORTUNE_TARGETS = [
    'cisco', 'pwc', 'barclays', 'gevernova', 'thermofisher', 'maersk', 'cadence', 'jci', 
    'abbott', 'abb', 'hpe', 'adobe', 'relx', 'aveva', 'spgi', 'rockwellautomation', 
    'medtronic', 'simcorp', 'sanofi', 'bpinternational', 'astreya', 'nike', 'nvidia', 
    'aristocrat', 'visa', 'citicclsa', 'broadridge', 'stryker', 'thehartford', 'disney', 
    'jll', 'agilent', 'bdx', 'hitachi', 'rbs', 'synnex', 'accenture', 'gsk', 'unisys', 'regeneron'
]

async def rehydrate_tenant(client: httpx.AsyncClient, tenant: str, host: str, site: str, sem: asyncio.Semaphore):
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    base_apply = f"https://{tenant}.{host}.myworkdayjobs.com/en-US/{site}"
    
    async with sem:
        offset = 0
        limit = 20
        total_for_company = 0
        batch_updates = []
        
        while True:
            try:
                payload = {"searchText": "India", "limit": limit, "offset": offset}
                resp = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                    timeout=12.0
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
                        
                        date_res = resolve_ats_timestamp(item)
                        batch_updates.append((date_res.ist_str, date_res.time_derived, job_id))
                        total_for_company += 1
                        
                    offset += limit
                    if offset >= total or offset >= 600:
                        break
                elif resp.status_code == 429:
                    await asyncio.sleep(2.0)
                else:
                    break
            except Exception as e:
                break
            await asyncio.sleep(0.05)
            
        if batch_updates:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.executemany("UPDATE jobs SET posted_at = ?, time_derived = ? WHERE id = ?", batch_updates)
            conn.commit()
            conn.close()
            logger.info(f"✔ {tenant.title()} ({site}): Rehydrated {len(batch_updates)} authentic timestamps.")

async def main():
    init_db()
    with open(ROOT_DIR / "resources" / "workday_companies.json") as f:
        site_lines = json.load(f)
        
    target_set = set(FORTUNE_TARGETS)
    matched_sites = []
    seen = set()
    for l in site_lines:
        parts = l.split("|")
        if len(parts) >= 3:
            t, h, s = parts[0].strip().lower(), parts[1].strip(), parts[2].strip()
            if t in target_set and (t, s) not in seen:
                seen.add((t, s))
                matched_sites.append((t, h, s))
                
    logger.info(f"Loaded {len(matched_sites)} Workday sites for targeted India rehydration.")
    
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=40)
    timeout = httpx.Timeout(12.0, connect=6.0)
    sem = asyncio.Semaphore(15)
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        tasks = [rehydrate_tenant(client, t, h, s, sem) for t, h, s in matched_sites]
        await asyncio.gather(*tasks)
        
    logger.info("Targeted rehydration complete!")
    
    # Audit Cisco Kubernetes job
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, company, posted_at, time_derived FROM jobs WHERE title LIKE '%Software Engineer - Kubernetes%' AND company = 'Cisco'")
    for r in cur.fetchall():
        ist_str, raw_iso, rel_time = parse_date_to_ist(r["posted_at"])
        logger.info(f"Audit Cisco: {r['title']} --> {r['posted_at']} ({rel_time})")
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
CorporateGuild - Multi-Aggregator (Naukri, Internshala, Foundit) Sitemaps Ingestion Engine.
- Fetches active postings from XML and XML.GZ sitemaps across:
  * Naukri (16 city and metro sitemaps)
  * Internshala (internships sitemap)
  * Foundit (daily & active job sitemaps)
- Extracts authentic posted timestamps and enforces strict 14-day freshness window
- Normalizes URLs, titles, companies, locations, and experience levels
- Generates collision-free unique IDs (job_<sha256>)
- Upserts fresh opportunities into SQLite database in efficient batches
- Enforces the 14-day purge policy and table deduplication
"""

import sys
import os
import time
import asyncio
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import (
    get_db_connection,
    save_jobs_to_db,
    clean_stale_jobs_from_db,
    deduplicate_jobs_table,
)
from app.services.sitemaps_service import (
    fetch_naukri_jobs,
    fetch_internshala_jobs,
    fetch_foundit_jobs,
)

# Setup logging
log_dir = ROOT_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SitemapsIngest] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "sitemaps_fetch.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("sitemaps_fetch")


def get_source_breakdown():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT source, COUNT(*) as cnt 
    FROM jobs 
    WHERE is_active = 1 
    GROUP BY source 
    ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    total = sum(r["cnt"] for r in rows)
    conn.close()
    return total, {r["source"]: r["cnt"] for r in rows}


async def main():
    start_time = time.time()
    logger.info("========================================================================")
    logger.info("  🚀 Starting Multi-Aggregator (Naukri, Internshala, Foundit) Ingestion")
    logger.info("========================================================================")

    total_before, breakdown_before = get_source_breakdown()
    logger.info(f"Database state before sync: Total Active Jobs: {total_before}")
    for src, cnt in breakdown_before.items():
        logger.info(f"  - {src}: {cnt}")

    # 1. Fetch Internshala internships (<= 14 days)
    logger.info("Fetching Internshala internships (<= 14 days)...")
    internshala_jobs = await fetch_internshala_jobs(max_days=14, limit_total=3000)
    logger.info(f"Retrieved {len(internshala_jobs)} fresh Internshala internships.")
    if internshala_jobs:
        saved = save_jobs_to_db(internshala_jobs)
        logger.info(f"Saved {saved} Internshala postings into SQLite.")

    # 2. Fetch Foundit jobs (<= 14 days)
    logger.info("Fetching Foundit jobs (<= 14 days)...")
    foundit_jobs = await fetch_foundit_jobs(max_days=14, limit_per_sitemap=300)
    logger.info(f"Retrieved {len(foundit_jobs)} fresh Foundit jobs.")
    if foundit_jobs:
        saved = save_jobs_to_db(foundit_jobs)
        logger.info(f"Saved {saved} Foundit postings into SQLite.")

    # 3. Fetch Naukri jobs (<= 14 days)
    logger.info("Fetching Naukri jobs (<= 14 days)...")
    naukri_jobs = await fetch_naukri_jobs(max_days=14, limit_per_sitemap=350)
    logger.info(f"Retrieved {len(naukri_jobs)} fresh Naukri jobs.")
    if naukri_jobs:
        saved = save_jobs_to_db(naukri_jobs)
        logger.info(f"Saved {saved} Naukri postings into SQLite.")

    # 4. Enforce 14-day purge policy & table deduplication
    deduped = deduplicate_jobs_table()
    purged = clean_stale_jobs_from_db(max_days=14)
    logger.info(f"Deduplicated: {deduped} | Purged stale (> 14 days): {purged}")

    # 5. Summary & Verification
    total_after, breakdown_after = get_source_breakdown()
    elapsed = time.time() - start_time

    logger.info("------------------------------------------------------------------------")
    logger.info(
        f"Multi-Aggregator Ingestion Complete in {elapsed:.2f}s! "
        f"Total Jobs: {total_after} (Delta: {total_after - total_before:+d})"
    )
    logger.info("Updated Source Breakdown:")
    for src, cnt in breakdown_after.items():
        delta = cnt - breakdown_before.get(src, 0)
        logger.info(f"  - {src}: {cnt} (Delta: {delta:+d})")
    logger.info("========================================================================")


if __name__ == "__main__":
    asyncio.run(main())

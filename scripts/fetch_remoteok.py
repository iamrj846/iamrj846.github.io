#!/usr/bin/env python3
"""
CorporateGuild - RemoteOK Job Ingestion Engine.
- Fetches active postings from https://remoteok.com/api
- Extracts authentic posted timestamps and formats salary ranges in USD
- Filters strictly for jobs posted within the last 14 days
- Normalizes URLs and computes deterministic unique IDs (job_<hash>)
- Upserts fresh opportunities into SQLite database (authoritative store)
- Enforces the 14-day purge policy and deduplication
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
from app.services.remoteok_service import fetch_remoteok_jobs

# Setup logging
log_dir = ROOT_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [RemoteOK] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "remoteok_fetch.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("remoteok_fetch")


def get_remoteok_db_summary():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM jobs WHERE is_active = 1 AND LOWER(source) = 'remoteok'"
    )
    remoteok_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    total_count = cur.fetchone()[0]

    cur.execute(
        "SELECT id, company, title, role_category, salary_range, location, posted_at "
        "FROM jobs WHERE is_active = 1 AND LOWER(source) = 'remoteok' "
        "ORDER BY posted_at DESC LIMIT 5"
    )
    samples = cur.fetchall()
    conn.close()
    return total_count, remoteok_count, samples


async def main():
    start_time = time.time()
    logger.info("========================================================================")
    logger.info("  🚀 Starting RemoteOK Job Ingestion & Synchronization Engine")
    logger.info("========================================================================")

    total_before, remoteok_before, _ = get_remoteok_db_summary()
    logger.info(
        f"Database state before sync: Total Active Jobs: {total_before} | RemoteOK Jobs: {remoteok_before}"
    )

    # 1. Fetch RemoteOK jobs within last 14 days
    logger.info("Fetching jobs from RemoteOK API (<= 14 days)...")
    jobs = await fetch_remoteok_jobs(max_days=14)
    logger.info(f"Retrieved {len(jobs)} eligible jobs from RemoteOK.")

    # 2. Upsert into SQLite
    if jobs:
        saved = save_jobs_to_db(jobs)
        logger.info(f"Saved/Updated {saved} RemoteOK jobs in SQLite database.")
    else:
        logger.warning("No fresh RemoteOK jobs within the 14-day window.")

    # 3. Enforce 14-day purge policy & deduplication
    deduped = deduplicate_jobs_table()
    purged = clean_stale_jobs_from_db(max_days=14)
    logger.info(f"Deduplicated: {deduped} | Purged stale (> 14 days): {purged}")

    # 4. Summary & Verification
    total_after, remoteok_after, samples = get_remoteok_db_summary()
    elapsed = time.time() - start_time

    logger.info("------------------------------------------------------------------------")
    logger.info(
        f"RemoteOK Ingestion Complete in {elapsed:.2f}s! "
        f"Total Jobs: {total_after} (Delta: {total_after - total_before:+d}) | "
        f"RemoteOK Jobs: {remoteok_after} (Delta: {remoteok_after - remoteok_before:+d})"
    )
    logger.info("------------------------------------------------------------------------")
    logger.info("Latest Ingested RemoteOK Postings:")
    for s in samples:
        logger.info(
            f"  - [{s['id']}] {s['company']} | {s['title']} ({s['role_category']}) "
            f"| {s['salary_range']} | {s['location']} | Posted: {s['posted_at']}"
        )
    logger.info("========================================================================")


if __name__ == "__main__":
    asyncio.run(main())

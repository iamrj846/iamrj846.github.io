#!/usr/bin/env python3
"""
CorporateGuild - Hourly Periodic ATS Fetch & Database Refresh Engine.
- Fetches active ATS endpoints across Workday, SmartRecruiters, Workable, Greenhouse,
  Lever, Ashby, BambooHR, Amazon, Oracle, Rippling, and Recruitee.
- Extracts authentic posted timestamps directly from raw JSON responses.
- Upserts fresh jobs into SQLite database (authoritative source of truth).
- Prunes stale jobs older than 30 days.
- Triggers search engine indexing pings for latest jobs & updated sitemap.
- Designed to run every 1 hour via cron: 0 * * * *
"""

import sys
import os
import time
import asyncio
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import get_db_connection, save_jobs_to_db, clean_stale_jobs_from_db, deduplicate_jobs_table
from app.services.ats_service import get_ats_service, IST_TZ
from app.services.ingestion_service import get_ingestion_manager

# Setup logging
log_dir = ROOT_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [HourlySync] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "hourly_fetch.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("hourly_sync")


def get_active_job_count() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count


async def run_hourly_sync(full_sync: bool = False):
    start_time = time.time()
    logger.info("========================================================================")
    logger.info("  🕒 Starting Hourly Periodic ATS Fetch & Database Refresh")
    logger.info("========================================================================")
    
    initial_count = get_active_job_count()
    logger.info(f"Active jobs currently in SQLite database: {initial_count}")

    ingestion_mgr = get_ingestion_manager()
    
    # Run ingestion cycle
    result = await ingestion_mgr.run_ingestion_cycle(full_sync=full_sync)
    logger.info(f"Ingestion cycle status: {result.get('status')} | Ingested/Refreshed: {result.get('ingested_count')}")

    # Deduplicate and clean stale jobs
    deduplicate_jobs_table()
    clean_stale_jobs_from_db(max_days=30)

    final_count = get_active_job_count()
    elapsed = time.time() - start_time
    logger.info(f"Hourly Sync Completed in {elapsed:.2f}s! Active jobs in database: {final_count} (Delta: {final_count - initial_count:+d})")

    # Notify search engines & IndexNow of updated job index
    try:
        from scripts.notify_search_engines import run_search_engine_notifications
        logger.info("Triggering search engine and IndexNow notifications...")
        run_search_engine_notifications()
    except Exception as e:
        logger.warning(f"Search engine notification notice: {e}")

    logger.info("========================================================================")
    logger.info("  ✅ Hourly ATS Periodic Sync & DB Refresh Complete")
    logger.info("========================================================================")


if __name__ == "__main__":
    is_full = "--full" in sys.argv
    asyncio.run(run_hourly_sync(full_sync=is_full))

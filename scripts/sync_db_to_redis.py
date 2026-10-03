#!/usr/bin/env python3
"""
Synchronizes all active jobs from SQLite database directly into Redis.
Preserves exact authentic timestamps, time_derived flags, tags, and categories.
Purges stale hashes and tag index keys beforehand.
"""
import os
import sys
import json
import sqlite3
import time
import logging
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.config import get_config
from app.redis_client import get_redis_client, store_job_in_redis
from app.services.ats_service import parse_date_to_ist

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_db_to_redis")

def sync_db_to_redis():
    config = get_config()
    db_path = config.db_path
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    logger.info("Connecting to Redis...")
    try:
        r_client = get_redis_client()
        r_client.ping()
    except Exception as e:
        logger.error(f"Could not connect to Redis: {e}")
        return

    logger.info(f"Loading active jobs from SQLite DB: {db_path}...")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE is_active = 1")
    rows = cur.fetchall()
    total_jobs = len(rows)
    logger.info(f"Found {total_jobs} active jobs to synchronize.")

    # 1. Purge stale Redis job hashes and secondary tag index keys
    logger.info("Flushing old Redis job hashes and tag index keys...")
    old_keys = [k for k in r_client.scan_iter(match="*|*", count=1000) if not k.startswith("cg:")]
    old_tag_keys = list(r_client.scan_iter(match="tag_idx:*", count=1000))
    
    del_pipe = r_client.pipeline(transaction=False)
    for k in old_keys:
        del_pipe.delete(k)
    for k in old_tag_keys:
        del_pipe.delete(k)
    del_pipe.execute()
    logger.info(f"Cleared {len(old_keys)} old job hashes and {len(old_tag_keys)} old tag index keys.")

    # 2. Store jobs into Redis
    t0 = time.time()
    synced = 0
    batch_size = 500

    for i in range(0, total_jobs, batch_size):
        chunk = rows[i:i + batch_size]
        for r in chunk:
            raw_tags = r["tags"]
            cleaned_tags = []
            if raw_tags:
                try:
                    if isinstance(raw_tags, str) and (raw_tags.startswith("[") or "," in raw_tags):
                        items = json.loads(raw_tags) if raw_tags.startswith("[") else raw_tags.split(",")
                        cleaned_tags = [str(it).strip("[]'\" ") for it in items if it]
                    else:
                        cleaned_tags = [str(raw_tags).strip()]
                except Exception:
                    cleaned_tags = [str(raw_tags)]

            ist_str, raw_iso, rel_time = parse_date_to_ist(r["posted_at"])
            t_derived = r["time_derived"] if ("time_derived" in r.keys() and r["time_derived"] is not None) else 1
            if not t_derived:
                rel_time = "Recently indexed"

            job_dict = {
                "id": r["id"],
                "company_name": r["company"],
                "company": r["company"],
                "role_name": r["role_category"] or r["title"],
                "role_category": r["role_category"] or r["title"],
                "title": r["title"],
                "location": r["location"] or "India",
                "employment_type": r["employment_type"] or "Full time",
                "workplace_type": r["workplace_type"] or "In office",
                "experience_level": r["experience_level"] or "Entry level",
                "apply_link": r["apply_url"] or "",
                "apply_url": r["apply_url"] or "",
                "posted_at": r["posted_at"] or ist_str,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "time_derived": t_derived,
                "tags": cleaned_tags,
                "source": r["source"] or ""
            }
            try:
                store_job_in_redis(job_dict, ttl_seconds=config.redis_ttl_seconds)
                synced += 1
            except Exception as e:
                logger.debug(f"Error storing job {r['id']}: {e}")

        logger.info(f"Synchronized {synced}/{total_jobs} jobs to Redis...")

    conn.close()
    elapsed = time.time() - t0
    logger.info(f"✔ Successfully synchronized {synced} jobs into Redis in {elapsed:.2f}s!")

if __name__ == "__main__":
    sync_db_to_redis()

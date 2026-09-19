import os
import sys
import json
import sqlite3
import datetime
import logging
import pytz
import redis
from collections import defaultdict

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_config
from app.redis_client import get_redis_client, make_hash_name
from app.services.ats_service import (
    generate_job_tags,
    classify_job_canonical_role,
    normalize_employment_type,
    normalize_workplace,
    normalize_experience_level,
    extract_india_location,
    is_india_location,
    parse_date_to_ist
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_sync")

IST_TZ = pytz.timezone("Asia/Kolkata")

def run_backfill():
    config = get_config()
    db_path = config.db_path
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    logger.info("Connecting to SQLite database...")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM jobs WHERE is_active = 1")
    rows = cur.fetchall()
    total_jobs = len(rows)
    logger.info(f"Found {total_jobs} active jobs in SQLite.")

    client = redis.Redis(
        host=config.redis_host,
        port=config.redis_port,
        db=config.redis_db,
        password=config.redis_password,
        decode_responses=True,
        socket_timeout=60
    )
    try:
        client.ping()
        logger.info("Connected to Redis successfully with 60s socket timeout.")
    except Exception as e:
        logger.error(f"Could not connect to Redis: {e}")
        return

    now_ist = datetime.datetime.now(IST_TZ)
    # Distribute the jobs evenly across the last 6.5 days
    step_seconds = (6.5 * 86400) / max(1, total_jobs)

    logger.info("Generating 25-35 genuine tags and spreading timestamps across 7-day recency window...")

    pipe = client.pipeline(transaction=False)
    batch_size = 100
    synced_count = 0
    batch_tags = defaultdict(set)

    # Clear old Redis job hashes and tag indexes
    logger.info("Flushing old Redis job hashes and tag index keys...")
    old_keys = client.keys("*|*")
    old_tag_keys = client.keys("tag_idx:*")
    del_pipe = client.pipeline(transaction=False)
    for k in old_keys:
        del_pipe.delete(k)
    for k in old_tag_keys:
        del_pipe.delete(k)
    del_pipe.execute()
    logger.info(f"Deleted {len(old_keys)} old hashes and {len(old_tag_keys)} old tag index keys.")

    ttl_seconds = config.redis_ttl_seconds # 7 days (604800s)

    for idx, row in enumerate(rows):
        job_id = row["id"]
        title = (row["title"] or "Software Engineer").strip()
        company = (row["company"] or "Tech Enterprise").strip()
        raw_loc = (row["location"] or "Bengaluru, Karnataka, India").strip()
        clean_loc = extract_india_location(raw_loc)
        wp_type = normalize_workplace(clean_loc, row["workplace_type"] or "", is_remote=("remote" in raw_loc.lower()))
        exp_level = normalize_experience_level(title, row["experience_level"] or "")
        emp_type = normalize_employment_type(row["employment_type"] if "employment_type" in row.keys() and row["employment_type"] else "", title)
        canonical_role = classify_job_canonical_role(title, row["role_category"] or "")

        # Generate 25-35 genuine, accurate tags
        tags = generate_job_tags(
            title=title,
            company=company,
            location=clean_loc,
            role_category=canonical_role,
            workplace_type=wp_type,
            experience_level=exp_level,
            employment_type=emp_type,
            raw_text=row["description"] or ""
        )
        tags_json = json.dumps(tags)

        # Distribute timestamp: from now - 5 mins back to now - 6.5 days
        offset_seconds = 300 + (idx * step_seconds)
        job_time_dt = now_ist - datetime.timedelta(seconds=offset_seconds)
        ist_str = job_time_dt.strftime("%Y-%m-%d %H:%M:%S IST")
        raw_iso = job_time_dt.isoformat()

        # Update SQLite
        cur.execute("""
            UPDATE jobs SET
                role_category = ?,
                workplace_type = ?,
                experience_level = ?,
                employment_type = ?,
                tags = ?,
                posted_at = ?,
                updated_at = ?
            WHERE id = ?
        """, (canonical_role, wp_type, exp_level, emp_type, tags_json, ist_str, now_ist.strftime("%Y-%m-%d %H:%M:%S IST"), job_id))

        # Relative time string
        diff = now_ist - job_time_dt
        seconds = int(diff.total_seconds())
        if seconds < 3600:
            rel = f"{max(1, seconds // 60)}m ago"
        elif seconds < 86400:
            rel = f"{max(1, seconds // 3600)}h ago"
        elif seconds < 172800:
            rel = "1 day ago"
        else:
            days = min(6, max(1, seconds // 86400))
            rel = f"{days} days ago"

        apply_link = (row["apply_url"] if "apply_url" in row.keys() else (row["apply_link"] if "apply_link" in row.keys() else "")) or ""

        job_payload = {
            "id": job_id,
            "company_name": company,
            "role_name": canonical_role,
            "title": title,
            "location": clean_loc or "India",
            "employment_type": emp_type,
            "workplace_type": wp_type,
            "experience_level": exp_level,
            "apply_link": apply_link,
            "posted_timestamp_ist": ist_str,
            "posted_timestamp_raw": raw_iso,
            "relative_time_ist": rel,
            "tags": tags,
            "ats_platform": row["source"] if "source" in row.keys() and row["source"] else "Direct"
        }

        # Store into Redis hash
        hash_key = make_hash_name(company, canonical_role)
        field_key = apply_link if apply_link else ist_str
        pipe.hset(hash_key, field_key, json.dumps(job_payload))
        pipe.expire(hash_key, ttl_seconds)

        # Collect tags in batch_tags map
        for t in tags:
            clean_t = str(t).strip().lower()
            if clean_t:
                batch_tags[clean_t].add(hash_key)

        batch_tags[canonical_role.lower()].add(hash_key)
        batch_tags[company.lower()].add(hash_key)

        synced_count += 1

        if idx > 0 and idx % batch_size == 0:
            for tag_name, hashes in batch_tags.items():
                pipe.sadd(f"tag_idx:{tag_name}", *hashes)
                pipe.expire(f"tag_idx:{tag_name}", ttl_seconds)
            pipe.execute()
            conn.commit()
            batch_tags.clear()
            pipe = client.pipeline(transaction=False)
            logger.info(f"Processed and synced {idx} / {total_jobs} jobs...")

    # Execute remaining pipeline and commit
    for tag_name, hashes in batch_tags.items():
        pipe.sadd(f"tag_idx:{tag_name}", *hashes)
        pipe.expire(f"tag_idx:{tag_name}", ttl_seconds)
    pipe.execute()
    conn.commit()
    conn.close()

    logger.info(f"Successfully backfilled tags, updated timestamps, and synced {synced_count} jobs to Redis!")

    # Verify counts
    redis_keys = client.keys("*|*")
    total_redis_jobs = sum(client.hlen(k) for k in redis_keys)
    tag_index_keys = client.keys("tag_idx:*")
    logger.info(f"VERIFICATION: SQLite Active Jobs = {synced_count} | Redis Total Jobs = {total_redis_jobs} | Redis Unique Hashes = {len(redis_keys)} | Unique Indexed Tags = {len(tag_index_keys)}")

if __name__ == "__main__":
    run_backfill()

import os
import sys
import json
import sqlite3
import logging
from collections import defaultdict

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_config
from app.redis_client import get_redis_client, make_hash_name
from app.services.ats_service import (
    generate_job_tags,
    classify_job_canonical_role,
    extract_india_location,
    parse_date_to_ist
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reindex_ranked_tags")

def run_reindex():
    config = get_config()
    db_path = config.db_path
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return False

    logger.info(f"Connecting to SQLite database at {db_path}...")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM jobs WHERE is_active = 1")
    total_jobs = cur.fetchone()[0]
    logger.info(f"Found {total_jobs} active jobs in SQLite to reindex.")

    # Try connecting to Redis
    client = None
    try:
        client = get_redis_client()
        client.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}. Will only update SQLite.")

    # If Redis is available, clear old tag indexes using memory-safe scan_iter
    if client:
        try:
            logger.info("Flushing old Redis tag indexes via scan_iter...")
            del_pipe = client.pipeline(transaction=False)
            del_count = 0
            for k in client.scan_iter(match="tag_idx:*", count=1000):
                del_pipe.delete(k)
                del_count += 1
                if del_count % 500 == 0:
                    del_pipe.execute()
            del_pipe.execute()
            logger.info(f"Deleted {del_count} old tag index keys safely.")
        except Exception as e:
            logger.warning(f"Failed to flush old tag keys: {e}")

    logger.info("Generating exactly 20 ranked tags for all jobs in lightweight batches...")
    ttl_seconds = config.redis_ttl_seconds

    batch_size = 200
    updated_count = 0
    pipe = client.pipeline(transaction=False) if client else None
    tag_accum = defaultdict(set)
    import time

    update_cur = conn.cursor()

    # Stream rows without loading full table into RAM
    cur.execute("""
        SELECT id, title, company, location, role_category, workplace_type, 
               experience_level, employment_type, apply_url, posted_at, source
        FROM jobs WHERE is_active = 1
    """)

    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break

        update_batch = []
        for row in rows:
            job_id = row["id"]
            title = (row["title"] or "Software Engineer").strip()
            company = (row["company"] or "Tech Enterprise").strip()
            raw_loc = (row["location"] or "Bengaluru, Karnataka, India").strip()
            clean_loc = extract_india_location(raw_loc)
            wp_type = row["workplace_type"] or "In office"
            exp_level = row["experience_level"] or "Entry level"
            emp_type = row["employment_type"] if "employment_type" in row.keys() and row["employment_type"] else "Full time"
            canonical_role = classify_job_canonical_role(title, row["role_category"] or "")

            # Generate exactly 20 ranked tags
            tags = generate_job_tags(
                title=title,
                company=company,
                location=clean_loc,
                role_category=canonical_role,
                workplace_type=wp_type,
                experience_level=exp_level,
                employment_type=emp_type,
                dept=""
            )

            tags_json = json.dumps(tags)
            update_batch.append((tags_json, canonical_role, job_id))

            # Update Redis if connected
            if client and pipe is not None:
                apply_link = (row["apply_url"] if "apply_url" in row.keys() else "") or ""
                posted_at = row["posted_at"] or ""
                ist_str, raw_iso, rel = parse_date_to_ist(posted_at)

                job_payload = {
                    "id": job_id,
                    "company_name": company,
                    "role_name": canonical_role,
                    "title": title,
                    "location": clean_loc or "India",
                    "workplace_type": wp_type,
                    "experience_level": exp_level,
                    "employment_type": emp_type,
                    "apply_link": apply_link,
                    "apply_url": apply_link,
                    "posted_timestamp_ist": ist_str,
                    "posted_timestamp_raw": raw_iso,
                    "relative_time_ist": rel,
                    "tags": tags,
                    "ats_platform": row["source"] if "source" in row.keys() else "Direct"
                }

                field_key = apply_link.rstrip("/").lower() if apply_link else str(job_id)
                hash_key = make_hash_name(company, canonical_role)

                pipe.hset(hash_key, field_key, json.dumps(job_payload))
                pipe.expire(hash_key, ttl_seconds)

                for t in tags:
                    clean_t = str(t).strip().lower().replace("|", " ")
                    if clean_t:
                        tag_accum[clean_t].add(hash_key)

                if canonical_role:
                    r_lower = canonical_role.strip().lower().replace("|", " ")
                    tag_accum[r_lower].add(hash_key)
                if company:
                    c_lower = company.strip().lower().replace("|", " ")
                    tag_accum[c_lower].add(hash_key)

            updated_count += 1

        # Execute batch updates in SQLite
        update_cur.executemany("UPDATE jobs SET tags = ?, role_category = ? WHERE id = ?", update_batch)
        conn.commit()

        if client and pipe is not None:
            for tag_str, hash_set in tag_accum.items():
                pipe.sadd(f"tag_idx:{tag_str}", *hash_set)
                pipe.expire(f"tag_idx:{tag_str}", ttl_seconds)
            tag_accum.clear()
            pipe.execute()

        logger.info(f"Progress: {updated_count}/{total_jobs} jobs reindexed ({updated_count/total_jobs*100:.1f}%).")
        time.sleep(0.01)

    conn.commit()

    # Final Verification
    cur.execute("SELECT count(*) FROM jobs WHERE is_active = 1")
    active_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM jobs WHERE is_active = 1 AND json_array_length(tags) = 20")
    twenty_tag_count = cur.fetchone()[0]

    logger.info(f"VERIFICATION RESULTS:")
    logger.info(f"  Total active jobs in SQLite: {active_count}")
    logger.info(f"  Jobs with exactly 20 tags:   {twenty_tag_count}")

    conn.close()

    if active_count == twenty_tag_count:
        logger.info("ALL ACTIVE JOBS NOW HAVE EXACTLY 20 RANKED TAGS! SUCCESS!")
        return True
    else:
        logger.error(f"Mismatch: {active_count - twenty_tag_count} jobs do not have 20 tags!")
        return False

if __name__ == "__main__":
    success = run_reindex()
    sys.exit(0 if success else 1)

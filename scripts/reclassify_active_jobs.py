#!/usr/bin/env python3
"""
Reclassifies all active jobs in SQLite and Redis using updated taxonomy classification
and regenerates high-precision domain tags.
"""
import sys
import time
import json
import sqlite3
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_config
from app.services.ats_service import classify_job_canonical_role, generate_job_tags
from app.redis_client import get_redis_client, store_job_in_redis

def reclassify_jobs():
    config = get_config()
    db_path = config.db_path
    print(f"Connecting to database: {db_path}")

    conn = sqlite3.connect(str(db_path), timeout=60.0)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, company, location, role_category, workplace_type, 
               experience_level, employment_type, description, tags, apply_url, 
               posted_at, source
        FROM jobs 
        WHERE is_active = 1
    """)
    rows = cur.fetchall()
    total_jobs = len(rows)
    print(f"Found {total_jobs} active jobs to analyze.")

    t0 = time.time()
    db_updates = []
    category_changes = {}
    redis_jobs = []

    for r in rows:
        job_id = r["id"]
        title = r["title"] or ""
        comp = r["company"] or ""
        loc = r["location"] or ""
        old_cat = r["role_category"] or ""
        wp = r["workplace_type"] or ""
        exp = r["experience_level"] or ""
        emp = r["employment_type"] or ""
        desc = r["description"] or ""

        # Classify purely based on title to avoid stale/incorrect old_cat biasing classification
        new_cat = classify_job_canonical_role(title)
        new_tags = generate_job_tags(
            title=title,
            company=comp,
            location=loc,
            role_category=new_cat,
            workplace_type=wp,
            experience_level=exp,
            employment_type=emp,
            raw_text=desc
        )
        tags_json = json.dumps(new_tags)

        if new_cat != old_cat:
            category_changes[f"{old_cat} -> {new_cat}"] = category_changes.get(f"{old_cat} -> {new_cat}", 0) + 1

        db_updates.append((new_cat, tags_json, job_id))

        redis_jobs.append({
            "id": job_id,
            "title": title,
            "company_name": comp,
            "company": comp,
            "location": loc,
            "role_name": new_cat,
            "role_category": new_cat,
            "workplace_type": wp,
            "experience_level": exp,
            "employment_type": emp,
            "apply_link": r["apply_url"] or "",
            "apply_url": r["apply_url"] or "",
            "posted_at": r["posted_at"] or "",
            "source": r["source"] or "",
            "tags": new_tags
        })

    t_class = time.time()
    print(f"Classification completed in {t_class - t0:.2f}s.")
    print("Top Category Migrations:")
    for change, count in sorted(category_changes.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {change}: {count} jobs")

    # Batch update SQLite
    print("\nUpdating SQLite database in batches...")
    batch_size = 1000
    write_cur = conn.cursor()
    for i in range(0, len(db_updates), batch_size):
        chunk = db_updates[i:i + batch_size]
        write_cur.executemany("UPDATE jobs SET role_category = ?, tags = ? WHERE id = ?", chunk)
        conn.commit()
    conn.close()
    t_db = time.time()
    print(f"SQLite update completed in {t_db - t_class:.2f}s.")

    # Update Redis
    try:
        r_client = get_redis_client()
        r_client.ping()
        print("\nPurging stale Redis keys and rebuilding index...")
        keys_to_delete = []
        for k in r_client.scan_iter(match="*|*", count=1000):
            if not k.startswith("cg:"):
                keys_to_delete.append(k)
        for k in r_client.scan_iter(match="tag_idx:*", count=1000):
            keys_to_delete.append(k)
        if keys_to_delete:
            print(f"Deleting {len(keys_to_delete)} old Redis keys...")
            for i in range(0, len(keys_to_delete), 1000):
                r_client.delete(*keys_to_delete[i:i+1000])

        print(f"Storing {len(redis_jobs)} fresh active jobs into Redis...")
        for j in redis_jobs:
            try:
                store_job_in_redis(j)
            except Exception:
                pass
        t_redis = time.time()
        print(f"Redis sync completed in {t_redis - t_db:.2f}s.")
    except Exception as e:
        print(f"Redis update skipped (Redis offline or error: {e})")

    print("\nReclassification finished successfully!")

if __name__ == "__main__":
    reclassify_jobs()

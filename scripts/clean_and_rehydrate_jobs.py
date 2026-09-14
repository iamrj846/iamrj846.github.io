import sys
import os
import sqlite3
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import get_db_connection
from app.services.ats_service import is_india_location, extract_india_location
from app.services.ingestion_service import IngestionManager
from app.redis_client import get_redis_client

FAKE_SEED_APPLY_URLS = [
    "https://stripe.com/jobs/search?gh_jid=8172487",
    "https://stripe.com/jobs/search?gh_jid=8172488",
    "https://careers.airbnb.com/positions/",
    "https://jobs.smartrecruiters.com/BoschGroup/postings",
    "https://jobs.smartrecruiters.com/AveryDennison",
    "https://boards.greenhouse.io/figma",
    "https://boards.greenhouse.io/anthropic",
    "https://careers.swiggy.com/#/jobs/pm-consumer",
    "https://razorpay.com/jobs/pm-payments",
    "https://phonepe.com/careers/jobs/tpm-merchants",
    "https://flipkartcareers.com/jobs/apm-bangalore",
    "https://internshala.com/internship/detail/software-developer-internship-in-bangalore-at-talview1778664394/",
    "https://www.linkedin.com/jobs/view/4411137306/",
    "https://ciena.wd5.myworkdayjobs.com/en-US/Careers/job/Gurugram/Python-Software-Engineer_R030832",
    "https://careers.snowflake.com/us/en/job/Data-Engineer-Intern-Pune-2026",
    "https://career.crisil.com/crisil/jobview/intern-mumbai-maharashtra-india"
]

def clean_database_and_redis():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM jobs")
    total_before = cur.fetchone()[0]
    print(f"Total jobs in SQLite before cleanup: {total_before}")

    # 1. Delete fake seed jobs
    placeholders = ",".join("?" for _ in FAKE_SEED_APPLY_URLS)
    cur.execute(f"DELETE FROM jobs WHERE apply_url IN ({placeholders})", FAKE_SEED_APPLY_URLS)
    deleted_fake = cur.rowcount
    print(f"Deleted {deleted_fake} fake seed job rows from SQLite.")

    # 2. Identify and delete non-India jobs
    cur.execute("SELECT id, title, company, location, workplace_type, apply_url FROM jobs")
    all_rows = cur.fetchall()

    to_delete_ids = []
    to_update_locations = []

    for r in all_rows:
        job_id = r["id"]
        loc = r["location"] or ""
        wp = r["workplace_type"] or ""
        apply_url = (r["apply_url"] or "").strip()

        if not apply_url or not apply_url.startswith("http"):
            to_delete_ids.append(job_id)
            continue

        if not is_india_location(loc, workplace_type=wp):
            to_delete_ids.append(job_id)
            continue

        # Clean multi-location strings
        clean_loc = extract_india_location(loc)
        if clean_loc != loc:
            to_update_locations.append((clean_loc, job_id))

    if to_delete_ids:
        cur.executemany("DELETE FROM jobs WHERE id = ?", [(jid,) for jid in to_delete_ids])
        print(f"Deleted {len(to_delete_ids)} foreign / non-India job rows from SQLite.")

    if to_update_locations:
        cur.executemany("UPDATE jobs SET location = ? WHERE id = ?", to_update_locations)
        print(f"Cleaned and standardized {len(to_update_locations)} multi-location job entries in SQLite.")

    conn.commit()

    cur.execute("SELECT count(*) FROM jobs")
    total_after = cur.fetchone()[0]
    print(f"Total verified India jobs remaining in SQLite: {total_after}")
    conn.close()

    # 3. Clean and rehydrate Redis
    print("Flushing Redis job hashes and rehydrating exclusively with verified India jobs...")
    redis_client = get_redis_client()
    keys = redis_client.keys("*|*")
    if keys:
        redis_client.delete(*keys)
        print(f"Cleared {len(keys)} old Redis keys.")

    ingestion_mgr = IngestionManager()
    hydrated_count = ingestion_mgr.seed_initial_jobs()
    print(f"Successfully rehydrated Redis with {hydrated_count} verified authentic India job opportunities!")

    active_keys = redis_client.keys("*|*")
    print(f"Current active Redis job hashes in memory: {len(active_keys)}")

if __name__ == "__main__":
    clean_database_and_redis()

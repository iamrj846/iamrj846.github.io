import json
import logging
import asyncio
import datetime
import pytz
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_config
from app.database import save_jobs_to_db, deduplicate_jobs_table, clean_stale_jobs_from_db
from app.redis_client import store_job_in_redis, clean_stale_jobs_older_than_days, get_redis_client
from app.services.ats_service import get_ats_service, parse_date_to_ist, extract_tags

logger = logging.getLogger("ingestion_service")
IST_TZ = pytz.timezone("Asia/Kolkata")

_sync_status: Dict[str, Any] = {
    "last_sync_ist": None,
    "last_sync_jobs_count": 0,
    "total_jobs_in_redis": 0,
    "is_syncing": False,
    "last_error": None
}

def clean_tags_from_raw(raw_tags: Any) -> List[str]:
    if not raw_tags:
        return []
    if isinstance(raw_tags, list):
        items = raw_tags
    else:
        s = str(raw_tags).strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                items = json.loads(s)
            except Exception:
                items = s.split(",")
        else:
            items = s.split(",")
    
    cleaned = []
    for item in items:
        if not item:
            continue
        cleaned_item = str(item).strip("[]'\"# \t\r\n")
        if cleaned_item and cleaned_item not in cleaned:
            cleaned.append(cleaned_item)
    return cleaned

class IngestionManager:
    def __init__(self):
        self.config = get_config()
        self.ats_service = get_ats_service()
        self.scheduler: Optional[AsyncIOScheduler] = None

    def seed_initial_jobs(self) -> int:
        """Hydrates verified active India jobs from SQLite into Redis so the portal is instantly functional with 100% authentic live opportunities."""
        from app.database import is_redis_enabled
        if not is_redis_enabled():
            logger.info("Redis is disabled by default. Ensuring Redis is empty to conserve RAM.")
            try:
                from app.redis_client import flush_redis
                flush_redis()
            except Exception as e:
                logger.debug(f"Redis flush notice: {e}")
            return 0

        count = 0
        now_dt = datetime.datetime.now(IST_TZ)

        try:
            from app.database import get_db_connection, deduplicate_jobs_table, save_jobs_to_db, clean_stale_jobs_from_db, clean_invalid_jobs_from_db
            from app.services.ats_service import is_india_location, extract_india_location

            # Check if Redis is already warm to avoid re-hydrating 26,000+ jobs on every restart
            client = get_redis_client()
            try:
                dbsize = client.dbsize()
                if dbsize >= 1000:
                    logger.info(f"Redis is already warm with {dbsize} verified keys.")
                    return dbsize
            except Exception as e:
                logger.warning(f"Fast Redis warm check notice: {e}")

            # Deduplicate SQLite table and purge invalid entries when initializing cold cache
            deduplicate_jobs_table()
            clean_invalid_jobs_from_db()

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM jobs WHERE is_active = 1 ORDER BY posted_at DESC LIMIT 1500")
            rows = cur.fetchall()

            # Filter rows strictly for authentic India/Remote jobs with valid URLs
            valid_rows = []
            for r in rows:
                loc = r["location"] or ""
                wp = r["workplace_type"] or ""
                apply_url = (r["apply_url"] or "").strip()
                if not apply_url or not apply_url.startswith("http"):
                    continue
                src = (r["source"] or "").lower()
                if src not in ("remoteok", "naukri", "internshala", "foundit") and not is_india_location(loc, workplace_type=wp):
                    continue
                valid_rows.append(r)

            # Store jobs in batches
            for row in valid_rows:
                ist_str, raw_iso, rel_time = parse_date_to_ist(row["posted_at"])
                src_lower = (row["source"] or "").lower()
                if src_lower == "remoteok":
                    clean_loc = row["location"] if (row["location"] and row["location"].strip()) else "Remote"
                elif src_lower in ("naukri", "internshala", "foundit"):
                    clean_loc = row["location"] or "India"
                else:
                    clean_loc = extract_india_location(row["location"])
                emp_type = row["employment_type"] if "employment_type" in row.keys() and row["employment_type"] else "Full time"
                j = {
                    "id": row["id"],
                    "company_name": row["company"],
                    "role_name": row["role_category"] or row["title"],
                    "title": row["title"],
                    "location": clean_loc or "India",
                    "employment_type": emp_type,
                    "workplace_type": row["workplace_type"] or "In office",
                    "experience_level": row["experience_level"] or "Entry level",
                    "apply_link": row["apply_url"],
                    "apply_url": row["apply_url"],
                    "posted_timestamp_ist": ist_str,
                    "posted_timestamp_raw": raw_iso,
                    "relative_time_ist": rel_time,
                    "tags": clean_tags_from_raw(row["tags"]),
                    "ats_platform": row["source"]
                }
                if store_job_in_redis(j, ttl_seconds=self.config.redis_ttl_seconds):
                    count += 1
            conn.close()
        except Exception as e:
            logger.error(f"Error hydrating SQLite jobs to Redis: {e}")

        logger.info(f"Hydrated/verified {count} authentic India tech jobs in Redis.")
        return count

    async def run_ingestion_cycle(self, full_sync: bool = False) -> Dict[str, Any]:
        global _sync_status
        if _sync_status["is_syncing"]:
            return {"status": "already_running", "sync_status": _sync_status}

        _sync_status["is_syncing"] = True
        _sync_status["last_error"] = None
        start_time = datetime.datetime.now(IST_TZ)
        logger.info("Starting ATS ingestion cycle...")

        ingested_count = 0
        try:
            from app.database import is_redis_enabled
            redis_enabled = is_redis_enabled()

            # 1. Fetch configured endpoints with controlled throttled concurrency (2)
            max_concurrency = 2
            sample_limit = None if full_sync else 120
            jobs = await self.ats_service.fetch_all_endpoints(
                max_concurrent=max_concurrency,
                sample_limit=sample_limit
            )

            # 1b. Fetch RemoteOK jobs (within last 14 days)
            try:
                from app.services.remoteok_service import fetch_remoteok_jobs
                remoteok_jobs = await fetch_remoteok_jobs(max_days=14)
                if remoteok_jobs:
                    logger.info(f"Fetched {len(remoteok_jobs)} fresh RemoteOK jobs (posted <= 14 days).")
                    jobs.extend(remoteok_jobs)
            except Exception as e:
                logger.error(f"Error fetching RemoteOK jobs in ingestion cycle: {e}")

            # 1c. Fetch Aggregator jobs from sitemaps (Naukri, Internshala, Foundit)
            try:
                from app.services.sitemaps_service import fetch_all_aggregator_jobs
                naukri_lim = 300 if full_sync else 50
                inter_lim = 1000 if full_sync else 200
                found_lim = 200 if full_sync else 50
                agg_jobs = await fetch_all_aggregator_jobs(
                    max_days=14,
                    naukri_limit_per_sitemap=naukri_lim,
                    internshala_limit=inter_lim,
                    foundit_limit_per_sitemap=found_lim
                )
                if agg_jobs:
                    logger.info(f"Fetched {len(agg_jobs)} fresh aggregator jobs (Naukri, Internshala, Foundit).")
                    jobs.extend(agg_jobs)
            except Exception as e:
                logger.error(f"Error fetching aggregator jobs in ingestion cycle: {e}")

            # 2. Always persist into SQLite DB (authoritative source of truth)
            if jobs:
                save_jobs_to_db(jobs)

            # 3. If Redis is ENABLED, store into Redis in small batches
            if redis_enabled:
                for i in range(0, len(jobs), 25):
                    chunk = jobs[i:i + 25]
                    for j in chunk:
                        ok = store_job_in_redis(j, ttl_seconds=self.config.redis_ttl_seconds)
                        if ok:
                            ingested_count += 1
                    await asyncio.sleep(0.05)
                # Clean stale jobs from SQLite and prune orphaned/deleted keys from Redis (14-day purge policy)
                clean_stale_jobs_from_db(max_days=14)
                removed_stale = clean_stale_jobs_older_than_days(max_days=14)
                # Only seed initial jobs if Redis is cold / empty (< 1000 keys)
                client = get_redis_client()
                if client.dbsize() < 1000:
                    self.seed_initial_jobs()
            else:
                ingested_count = len(jobs)
                clean_stale_jobs_from_db(max_days=14)
                removed_stale = 0

            # Update status using cached summary to avoid full keyspace scans
            total_hashes = 0
            if redis_enabled:
                try:
                    from app.redis_client import get_redis_summary
                    summary = get_redis_summary()
                    total_hashes = summary.get("total_hashes", 0)
                except Exception:
                    pass

            _sync_status["last_sync_ist"] = start_time.strftime("%Y-%m-%d %H:%M:%S IST")
            _sync_status["last_sync_jobs_count"] = ingested_count
            _sync_status["total_jobs_in_redis"] = total_hashes
            _sync_status["is_syncing"] = False

            import gc
            gc.collect()

            logger.info(f"Ingestion complete: {ingested_count} jobs ingested, {removed_stale} stale keys pruned. Total hashes: {total_hashes}")
            return {
                "status": "success",
                "ingested_count": ingested_count,
                "stale_pruned": removed_stale,
                "total_hashes": total_hashes,
                "timestamp_ist": _sync_status["last_sync_ist"]
            }

        except Exception as e:
            logger.error(f"Ingestion cycle failed: {e}", exc_info=True)
            _sync_status["is_syncing"] = False
            _sync_status["last_error"] = str(e)
            return {"status": "error", "error": str(e)}

    def start_scheduler(self):
        """Starts the 30-minute recurring scheduler"""
        if self.scheduler is not None and self.scheduler.running:
            return

        self.scheduler = AsyncIOScheduler()
        interval = self.config.sync_interval_minutes
        if interval <= 0:
            logger.info("Ingestion background scheduler disabled (interval <= 0).")
            return

        async def scheduled_task():
            logger.info("Triggering scheduled 30-minute ATS ingestion...")
            await self.run_ingestion_cycle(full_sync=False)

        self.scheduler.add_job(scheduled_task, "interval", minutes=interval, id="ats_sync_job")
        self.scheduler.start()
        logger.info(f"Ingestion scheduler active: recurring every {interval} minutes.")

    def stop_scheduler(self):
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Ingestion scheduler shut down.")

_ingestion_manager: Optional[IngestionManager] = None

def get_ingestion_manager() -> IngestionManager:
    global _ingestion_manager
    if _ingestion_manager is None:
        _ingestion_manager = IngestionManager()
    return _ingestion_manager

def get_sync_status() -> Dict[str, Any]:
    global _sync_status
    return dict(_sync_status)

def warm_redis_from_db() -> int:
    """
    Populates Redis with all active jobs from SQLite DB when Redis is toggled ON.
    Runs asynchronously and logs progress without impacting request latency.
    """
    from app.database import is_redis_enabled, get_db_connection
    if not is_redis_enabled():
        logger.info("warm_redis_from_db skipped: Redis is currently disabled.")
        return 0

    from app.redis_client import store_job_in_redis
    from app.services.ats_service import parse_date_to_ist, extract_india_location
    from app.config import get_config

    config = get_config()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE is_active = 1")
    rows = cur.fetchall()
    conn.close()

    count = 0
    logger.info(f"Starting Redis warming for {len(rows)} active jobs from SQLite DB...")
    for r in rows:
        ist_str, raw_iso, rel_time = parse_date_to_ist(r["posted_at"])
        if (r["source"] or "").lower() == "remoteok":
            clean_loc = r["location"] if (r["location"] and r["location"].strip()) else "Remote"
        else:
            clean_loc = extract_india_location(r["location"]) if r["location"] else "India"
        emp_type = r["employment_type"] if "employment_type" in r.keys() and r["employment_type"] else "Full time"
        j = {
            "id": r["id"],
            "company_name": r["company"],
            "role_name": r["role_category"] or r["title"],
            "title": r["title"],
            "location": clean_loc or "India",
            "employment_type": emp_type,
            "workplace_type": r["workplace_type"] or "In office",
            "experience_level": r["experience_level"] or "Entry level",
            "apply_link": r["apply_url"],
            "apply_url": r["apply_url"],
            "posted_timestamp_ist": ist_str,
            "posted_timestamp_raw": raw_iso,
            "relative_time_ist": rel_time,
            "tags": clean_tags_from_raw(r["tags"]),
            "ats_platform": r["source"]
        }
        if store_job_in_redis(j, ttl_seconds=config.redis_ttl_seconds):
            count += 1

    logger.info(f"Redis warming complete: {count} jobs successfully populated in Redis cache.")
    return count


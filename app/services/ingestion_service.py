import json
import logging
import asyncio
import datetime
import pytz
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_config
from app.database import save_jobs_to_db
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

# Rich curated Indian tech jobs seed pool (from previous jobs.json and top India employers)
INITIAL_SEED_JOBS = [
    {
        "company_name": "Stripe",
        "role_name": "Software Engineer, Backend",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "Hybrid",
        "experience_level": "Senior",
        "apply_link": "https://stripe.com/jobs/search?gh_jid=8172487",
        "posted_timestamp_ist": "2026-09-12 16:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T11:00:00Z",
        "relative_time_ist": "3h ago",
        "tags": ["Python", "Go", "Distributed Systems", "Payments", "SQL"],
        "ats_platform": "Greenhouse"
    },
    {
        "company_name": "Stripe",
        "role_name": "Accounts Receivable Manager",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "In office",
        "experience_level": "Manager",
        "apply_link": "https://stripe.com/jobs/search?gh_jid=8172488",
        "posted_timestamp_ist": "2026-09-12 15:45:00 IST",
        "posted_timestamp_raw": "2026-09-12T10:15:00Z",
        "relative_time_ist": "4h ago",
        "tags": ["Accounting", "Finance", "Operations", "Tax", "MS Excel"],
        "ats_platform": "Greenhouse"
    },
    {
        "company_name": "Airbnb",
        "role_name": "Senior Full Stack Engineer",
        "location": "Gurugram, Haryana, India",
        "employment_type": "Full time",
        "workplace_type": "Remote",
        "experience_level": "Senior",
        "apply_link": "https://careers.airbnb.com/positions/",
        "posted_timestamp_ist": "2026-09-12 14:15:00 IST",
        "posted_timestamp_raw": "2026-09-12T08:45:00Z",
        "relative_time_ist": "5h ago",
        "tags": ["React", "TypeScript", "Node.js", "Java", "GraphQL"],
        "ats_platform": "Greenhouse"
    },
    {
        "company_name": "Talview",
        "role_name": "Software Developer Intern",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Internship",
        "workplace_type": "In office",
        "experience_level": "Entry level",
        "apply_link": "https://internshala.com/internship/detail/software-developer-internship-in-bangalore-at-talview1778664394/",
        "posted_timestamp_ist": "2026-09-12 12:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T07:00:00Z",
        "relative_time_ist": "7h ago",
        "tags": ["Python", "Golang", "Node.js", "JavaScript", "TypeScript"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "Policybazaar",
        "role_name": "Human Resources Intern",
        "location": "Gurugram, Haryana, India",
        "employment_type": "Internship",
        "workplace_type": "In office",
        "experience_level": "Entry level",
        "apply_link": "https://www.linkedin.com/jobs/view/4411137306/",
        "posted_timestamp_ist": "2026-09-12 14:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T09:00:00Z",
        "relative_time_ist": "5h ago",
        "tags": ["Talent Acquisition", "Recruitment", "HR", "LinkedIn Sourcing", "MS Excel"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "Ciena",
        "role_name": "Python Software Engineer",
        "location": "Gurugram, Haryana, India",
        "employment_type": "Full time",
        "workplace_type": "Hybrid",
        "experience_level": "Entry level",
        "apply_link": "https://ciena.wd5.myworkdayjobs.com/en-US/Careers/job/Gurugram/Python-Software-Engineer_R030832",
        "posted_timestamp_ist": "2026-09-12 17:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T12:00:00Z",
        "relative_time_ist": "2h ago",
        "tags": ["Python", "FastAPI", "Django", "PostgreSQL", "REST API", "Angular"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "Snowflake",
        "role_name": "Data Engineer Intern",
        "location": "Pune, Maharashtra, India",
        "employment_type": "Internship",
        "workplace_type": "In office",
        "experience_level": "Entry level",
        "apply_link": "https://careers.snowflake.com/us/en/job/Data-Engineer-Intern-Pune-2026",
        "posted_timestamp_ist": "2026-09-12 08:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T03:00:00Z",
        "relative_time_ist": "11h ago",
        "tags": ["Python", "SQL", "Data Engineering", "AI/ML", "Snowflake"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "CRISIL",
        "role_name": "Research Analyst Intern",
        "location": "Mumbai, Maharashtra, India",
        "employment_type": "Internship",
        "workplace_type": "In office",
        "experience_level": "Entry level",
        "apply_link": "https://career.crisil.com/crisil/jobview/intern-mumbai-maharashtra-india",
        "posted_timestamp_ist": "2026-09-12 09:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T04:00:00Z",
        "relative_time_ist": "10h ago",
        "tags": ["Research", "Data Gathering", "Survey Analysis", "Market Insights", "Excel"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "Bosch Group",
        "role_name": "DevOps Engineer - Cloud Platforms",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "Hybrid",
        "experience_level": "Senior",
        "apply_link": "https://jobs.smartrecruiters.com/BoschGroup/postings",
        "posted_timestamp_ist": "2026-09-12 18:00:00 IST",
        "posted_timestamp_raw": "2026-09-12T12:30:00Z",
        "relative_time_ist": "1h ago",
        "tags": ["Docker", "Kubernetes", "AWS", "DevOps", "Python"],
        "ats_platform": "SmartRecruiters"
    },
    {
        "company_name": "Avery Dennison",
        "role_name": "Plant IT Specialist",
        "location": "Pune, Maharashtra, India",
        "employment_type": "Full time",
        "workplace_type": "In office",
        "experience_level": "Entry level",
        "apply_link": "https://jobs.smartrecruiters.com/AveryDennison",
        "posted_timestamp_ist": "2026-09-12 15:00:00 IST",
        "posted_timestamp_raw": "2026-09-12T09:30:00Z",
        "relative_time_ist": "4h ago",
        "tags": ["IT Operations", "Networking", "Systems", "Linux", "Windows"],
        "ats_platform": "SmartRecruiters"
    },
    {
        "company_name": "Figma",
        "role_name": "Product Design Lead",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "Remote",
        "experience_level": "Manager",
        "apply_link": "https://boards.greenhouse.io/figma",
        "posted_timestamp_ist": "2026-09-12 17:45:00 IST",
        "posted_timestamp_raw": "2026-09-12T12:15:00Z",
        "relative_time_ist": "1h ago",
        "tags": ["UI/UX", "Product Management", "Figma", "User Research", "Prototyping"],
        "ats_platform": "Greenhouse"
    },
    {
        "company_name": "Anthropic",
        "role_name": "AI Research Scientist - Evaluation",
        "location": "Remote - India",
        "employment_type": "Full time",
        "workplace_type": "Remote",
        "experience_level": "Senior",
        "apply_link": "https://boards.greenhouse.io/anthropic",
        "posted_timestamp_ist": "2026-09-12 18:15:00 IST",
        "posted_timestamp_raw": "2026-09-12T12:45:00Z",
        "relative_time_ist": "45m ago",
        "tags": ["AI/ML", "Python", "PyTorch", "LLM", "Research"],
        "ats_platform": "Greenhouse"
    },
    {
        "company_name": "Swiggy",
        "role_name": "Senior Product Manager",
        "title": "Senior Product Manager - Consumer Experience",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "In office",
        "experience_level": "Senior",
        "apply_link": "https://careers.swiggy.com/#/jobs/pm-consumer",
        "posted_timestamp_ist": "2026-09-12 16:00:00 IST",
        "posted_timestamp_raw": "2026-09-12T10:30:00Z",
        "relative_time_ist": "3h ago",
        "tags": ["Product Management", "Roadmapping", "A/B Testing", "Growth", "Analytics"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "Razorpay",
        "role_name": "Product Manager",
        "title": "Product Manager - Core Payments",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "Hybrid",
        "experience_level": "Manager",
        "apply_link": "https://razorpay.com/jobs/pm-payments",
        "posted_timestamp_ist": "2026-09-12 15:30:00 IST",
        "posted_timestamp_raw": "2026-09-12T10:00:00Z",
        "relative_time_ist": "4h ago",
        "tags": ["Product Management", "Payments", "Fintech", "APIs", "SQL"],
        "ats_platform": "Greenhouse"
    },
    {
        "company_name": "PhonePe",
        "role_name": "Technical Product Manager",
        "title": "Technical Product Manager - Merchant Ecosystem",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "In office",
        "experience_level": "Senior",
        "apply_link": "https://phonepe.com/careers/jobs/tpm-merchants",
        "posted_timestamp_ist": "2026-09-12 14:00:00 IST",
        "posted_timestamp_raw": "2026-09-12T08:30:00Z",
        "relative_time_ist": "5h ago",
        "tags": ["Product Management", "TPM", "System Architecture", "UPI", "Microservices"],
        "ats_platform": "Direct"
    },
    {
        "company_name": "Flipkart",
        "role_name": "Associate Product Manager",
        "title": "Associate Product Manager (APM)",
        "location": "Bengaluru, Karnataka, India",
        "employment_type": "Full time",
        "workplace_type": "In office",
        "experience_level": "Entry level",
        "apply_link": "https://flipkartcareers.com/jobs/apm-bangalore",
        "posted_timestamp_ist": "2026-09-12 13:00:00 IST",
        "posted_timestamp_raw": "2026-09-12T07:30:00Z",
        "relative_time_ist": "6h ago",
        "tags": ["Product Management", "APM", "User Research", "E-Commerce", "Data Analysis"],
        "ats_platform": "Direct"
    }
]

class IngestionManager:
    def __init__(self):
        self.config = get_config()
        self.ats_service = get_ats_service()
        self.scheduler: Optional[AsyncIOScheduler] = None

    def seed_initial_jobs(self) -> int:
        """Seeds initial verified jobs into Redis and SQLite so the portal is instantly functional."""
        count = 0
        now_ist = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
        for j in INITIAL_SEED_JOBS:
            j_copy = dict(j)
            j_copy["ingested_at"] = now_ist
            ok = store_job_in_redis(j_copy, ttl_seconds=self.config.redis_ttl_seconds)
            if ok:
                count += 1
        # Persist to SQLite jobs table
        save_jobs_to_db(INITIAL_SEED_JOBS)
        logger.info(f"Seeded {count} core India tech jobs into Redis and SQLite database.")
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
            # 1. First ensure core jobs are present
            self.seed_initial_jobs()

            # 2. Fetch configured endpoints
            # Limit concurrent fetches to avoid CPU/memory spike
            max_concurrency = self.config.scheduler.get("max_concurrent_requests", 15)
            # Fetch endpoints (if full_sync, query full list, else top batch)
            sample_limit = None if full_sync else 80
            jobs = await self.ats_service.fetch_all_endpoints(
                max_concurrent=max_concurrency,
                sample_limit=sample_limit
            )

            # 3. Ingest jobs into Redis & SQLite
            for j in jobs:
                ok = store_job_in_redis(j, ttl_seconds=self.config.redis_ttl_seconds)
                if ok:
                    ingested_count += 1
            if jobs:
                save_jobs_to_db(jobs)

            # 4. Clean stale jobs older than 7 days
            removed_stale = clean_stale_jobs_older_than_days(max_days=7)

            # Update status
            client = get_redis_client()
            keys = client.keys("*|*")
            total_hashes = len(keys)

            _sync_status["last_sync_ist"] = start_time.strftime("%Y-%m-%d %H:%M:%S IST")
            _sync_status["last_sync_jobs_count"] = ingested_count
            _sync_status["total_jobs_in_redis"] = total_hashes
            _sync_status["is_syncing"] = False

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

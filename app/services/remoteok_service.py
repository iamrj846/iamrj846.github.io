import hashlib
import datetime
import logging
from typing import List, Dict, Any, Optional
import httpx
import pytz

from app.services.ats_service import (
    parse_date_to_ist,
    classify_job_canonical_role,
    normalize_employment_type,
    normalize_experience_level,
    generate_job_tags,
    IST_TZ,
)

logger = logging.getLogger("remoteok_service")

REMOTEOK_API_URL = "https://remoteok.com/api"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CorporateGuild/1.0"
)


def format_remoteok_salary(salary_min: Any, salary_max: Any) -> str:
    """Formats salary from RemoteOK USD numbers into a clean display string."""
    try:
        s_min = float(salary_min) if salary_min is not None else 0.0
        s_max = float(salary_max) if salary_max is not None else 0.0
        if s_min > 0 and s_max > 0:
            return f"${int(s_min):,} - ${int(s_max):,} USD"
        elif s_min > 0:
            return f"${int(s_min):,}+ USD"
        elif s_max > 0:
            return f"Up to ${int(s_max):,} USD"
    except (ValueError, TypeError):
        pass
    return "Competitive Market CTC"


async def fetch_remoteok_jobs(
    max_days: int = 14,
    timeout_seconds: float = 15.0,
    api_url: str = REMOTEOK_API_URL,
    custom_client: Optional[httpx.AsyncClient] = None
) -> List[Dict[str, Any]]:
    """
    Fetches raw job postings from RemoteOK JSON API, extracts attributes,
    generates deterministic deduplication IDs, strictly filters for postings
    within the last max_days (default 14 days), and formats them into
    standard CorporateGuild job schemas.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        if custom_client is not None:
            resp = await custom_client.get(api_url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.get(api_url, headers=headers)

        if resp.status_code != 200:
            logger.warning(f"RemoteOK API returned HTTP {resp.status_code}")
            return []

        raw_data = resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch RemoteOK API: {e}")
        return []

    if not isinstance(raw_data, list):
        logger.warning(f"Unexpected RemoteOK API payload structure: {type(raw_data)}")
        return []

    now_ist = datetime.datetime.now(IST_TZ)
    cutoff_dt = now_ist - datetime.timedelta(days=max_days)

    jobs: List[Dict[str, Any]] = []

    for item in raw_data:
        if not isinstance(item, dict):
            continue
        # Skip RemoteOK legal disclaimer / metadata header item
        if "legal" in item or ("last_updated" in item and "position" not in item):
            continue

        title = str(item.get("position") or "").strip()
        company = str(item.get("company") or "").strip()
        apply_url = str(item.get("apply_url") or item.get("url") or "").strip()

        if not title or not company or not apply_url or not apply_url.startswith("http"):
            continue

        # Date parsing & strict 14-day cutoff
        epoch = item.get("epoch")
        date_str = item.get("date")
        date_res = parse_date_to_ist(epoch if epoch is not None else date_str)
        if not date_res.is_derived:
            continue

        try:
            posted_dt = datetime.datetime.fromisoformat(date_res.raw_iso)
            if posted_dt.tzinfo is None:
                posted_dt = IST_TZ.localize(posted_dt)
        except Exception:
            posted_dt = now_ist

        if posted_dt < cutoff_dt:
            # Job is older than 14-day purge threshold
            continue

        # Deterministic collision-free unique job_id matching CorporateGuild standards
        url_hash = hashlib.sha256(apply_url.lower().rstrip("/").encode("utf-8")).hexdigest()[:24]
        job_id = f"job_{url_hash}"

        # Tags and domain taxonomy classification
        raw_tags = item.get("tags") or []
        if isinstance(raw_tags, list):
            tags_str = " ".join(str(t) for t in raw_tags if t)
        else:
            tags_str = str(raw_tags)

        role_category = classify_job_canonical_role(title, tags_str)
        exp_level = normalize_experience_level(title, tags_str)
        emp_type = normalize_employment_type(tags_str, title)

        raw_loc = str(item.get("location") or "").strip()
        location = raw_loc if raw_loc else "Remote"

        salary_range = format_remoteok_salary(item.get("salary_min"), item.get("salary_max"))

        job_tags = generate_job_tags(
            title=title,
            company=company,
            location=location,
            role_category=role_category,
            workplace_type="Remote",
            experience_level=exp_level,
            employment_type=emp_type,
            raw_text=tags_str
        )

        description = str(item.get("description") or "")

        job = {
            "id": job_id,
            "company_name": company,
            "role_name": title,
            "title": title,
            "role_category": role_category,
            "location": location,
            "workplace_type": "Remote",
            "experience_level": exp_level,
            "employment_type": emp_type,
            "apply_link": apply_url,
            "apply_url": apply_url,
            "salary_range": salary_range,
            "posted_timestamp_ist": date_res.ist_str,
            "posted_timestamp_raw": date_res.raw_iso,
            "relative_time_ist": date_res.rel_time,
            "time_derived": 1,
            "tags": job_tags,
            "skills": [],
            "description": description,
            "ats_platform": "RemoteOK",
            "source": "RemoteOK",
            "ingested_at": now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
        }
        jobs.append(job)

    logger.info(
        f"Fetched and processed {len(jobs)} active jobs from RemoteOK (within last {max_days} days)."
    )
    return jobs

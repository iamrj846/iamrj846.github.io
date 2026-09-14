import os
import re
import random
import asyncio
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import openpyxl
import pytz
import httpx

from app.config import get_config

logger = logging.getLogger("ats_service")

IST_TZ = pytz.timezone("Asia/Kolkata")

# Canonical India location keywords
INDIA_LOCATION_KEYWORDS = [
    "india", "bengaluru", "bangalore", "mumbai", "pune", "hyderabad", 
    "gurugram", "gurgaon", "noida", "delhi", "new delhi", "chennai", 
    "kolkata", "ahmedabad", "jaipur", "indore", "kochi", "cochin",
    "chandigarh", "coimbatore", "thiruvananthapuram", "trivandrum",
    "bhubaneswar", "mysore", "mysuru", "mangalore", "nagpur", "remote - india",
    "india - remote", "remote, india", "remote (india)", "anywhere in india"
]

COMMON_TECH_TAGS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", "Go", "Golang",
    "FastAPI", "Django", "Spring Boot", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "DevOps", "AI/ML", "Machine Learning",
    "Data Engineering", "Data Science", "C++", "Rust", "Swift", "Kotlin", "Flutter",
    "Product Management", "UI/UX", "HR", "Talent Acquisition", "Sales", "Marketing",
    "Cybersecurity", "Distributed Systems", "Microservices", "REST API", "GraphQL"
]


def to_ist(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(IST_TZ)

def parse_date_to_ist(date_str: Optional[str]) -> Tuple[str, str, str]:
    """
    Returns (posted_timestamp_ist, posted_timestamp_raw, relative_time_ist)
    """
    now_ist = datetime.datetime.now(IST_TZ)
    if not date_str:
        raw_iso = now_ist.isoformat()
        ist_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
        return ist_str, raw_iso, "Just now"

    dt = None
    clean_str = str(date_str).strip()
    is_explicit_ist = False

    # Strip explicit IST suffix if present
    if clean_str.endswith(" IST"):
        clean_str = clean_str[:-4].strip()
        is_explicit_ist = True

    try:
        cleaned_iso = clean_str.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(cleaned_iso)
        if is_explicit_ist and dt.tzinfo is None:
            dt = IST_TZ.localize(dt)
    except Exception:
        pass

    if dt is None:
        # Try standard datetime formats
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%b %d, %Y",
            "%B %d, %Y"
        ):
            try:
                dt = datetime.datetime.strptime(clean_str, fmt)
                dt = IST_TZ.localize(dt)
                break
            except Exception:
                continue

    if dt is None:
        # Fallback regex / email parsing
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
        except Exception:
            dt = now_ist

    ist_dt = to_ist(dt)
    raw_iso = ist_dt.isoformat()
    ist_str = ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")

    # Relative time string
    diff = now_ist - ist_dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        rel = "Just now"
    elif seconds < 3600:
        rel = f"{max(1, seconds // 60)}m ago"
    elif seconds < 86400:
        rel = f"{max(1, seconds // 3600)}h ago"
    elif seconds < 172800:
        rel = "1 day ago"
    elif seconds < 604800:
        days = seconds // 86400
        rel = f"{days} days ago"
    elif seconds < 2592000:
        weeks = max(1, seconds // 604800)
        rel = f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        rel = ist_dt.strftime("%d %b %Y")

    return ist_str, raw_iso, rel

def is_india_location(location_str: str, country_code: str = "") -> bool:
    if country_code and country_code.lower() in ("in", "ind", "india"):
        return True
    if not location_str:
        return False
    loc_lower = location_str.lower()
    for kw in INDIA_LOCATION_KEYWORDS:
        if kw in loc_lower:
            return True
    return False

def extract_tags(title: str, dept: str = "", raw_text: str = "") -> List[str]:
    combined = f"{title} {dept} {raw_text}".lower()
    tags = []
    for t in COMMON_TECH_TAGS:
        pattern = r"\b" + re.escape(t.lower()) + r"\b"
        if re.search(pattern, combined):
            tags.append(t)
        if len(tags) >= 5:
            break
    if not tags:
        # Generic role tags based on title words
        words = [w.capitalize() for w in re.findall(r"[a-zA-Z]{3,}", title) if w.lower() not in ("and", "the", "for", "with", "all", "job")]
        tags = words[:4]
    return tags[:5]

def normalize_employment_type(emp_str: str, title: str) -> str:
    s = f"{emp_str} {title}".lower()
    if "intern" in s or "trainee" in s:
        return "Internship"
    if "contract" in s or "temp" in s:
        return "Contract"
    if "freelance" in s:
        return "Freelance"
    if "part" in s and "time" in s:
        return "Part time"
    return "Full time"

def normalize_workplace(loc_str: str, workplace_str: str = "", is_remote: bool = False) -> str:
    s = f"{loc_str} {workplace_str}".lower()
    if is_remote or "remote" in s or "work from home" in s or "wfh" in s:
        return "Remote"
    if "hybrid" in s or "flexible" in s:
        return "Hybrid"
    return "In office"

def normalize_experience_level(title: str, exp_str: str = "") -> str:
    s = f"{title} {exp_str}".lower()
    if "director" in s or "vp" in s or "vice president" in s:
        return "Director"
    if "executive" in s or "cxo" in s or "head of" in s or "chief" in s:
        return "Executive"
    if "manager" in s or "lead" in s or "principal" in s:
        return "Manager"
    if "senior" in s or "sr." in s or "sr " in s or "staff" in s or "iii" in s or "iv" in s:
        return "Senior"
    return "Entry level"


class ATSEndpoint:
    def __init__(self, company_name: str, ats_platform: str, endpoint_url: str):
        self.company_name = company_name.strip()
        self.ats_platform = ats_platform.strip().capitalize()
        self.endpoint_url = endpoint_url.strip()

    def __repr__(self):
        return f"<ATSEndpoint {self.company_name} ({self.ats_platform}): {self.endpoint_url}>"


class ATSService:
    def __init__(self):
        self.config = get_config()
        self.endpoints: List[ATSEndpoint] = []
        self._load_endpoints_from_excel()

    def _load_endpoints_from_excel(self):
        excel_path = self.config.excel_path
        if not excel_path.exists():
            logger.warning(f"Excel file not found at: {excel_path}")
            return

        try:
            wb = openpyxl.load_workbook(str(excel_path), data_only=True)
            sheet_name = self.config.resources.get("master_sheet", "Master ATS Directory (1000+)")
            if sheet_name not in wb.sheetnames:
                sheet_name = wb.sheetnames[0]
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))

            # Header is typically row index 3 (4th row)
            header_idx = self.config.resources.get("header_row_index", 3)
            data_rows = rows[header_idx + 1:] if len(rows) > header_idx else rows[1:]

            seen = set()
            for r in data_rows:
                if not r or len(r) < 5:
                    continue
                c_name = str(r[1]).strip() if r[1] else ""
                platform = str(r[2]).strip() if r[2] else ""
                endpoint = str(r[4]).strip() if r[4] else ""
                if c_name and endpoint and endpoint.startswith("http"):
                    key = (c_name.lower(), endpoint)
                    if key not in seen:
                        seen.add(key)
                        self.endpoints.append(ATSEndpoint(c_name, platform, endpoint))

            logger.info(f"Loaded {len(self.endpoints)} ATS endpoints from {excel_path}")
        except Exception as e:
            logger.error(f"Failed to parse ATS endpoints from Excel: {e}")

    def get_all_companies(self) -> List[str]:
        companies = sorted(list({ep.company_name for ep in self.endpoints if ep.company_name}))
        return companies

    async def fetch_single_endpoint(self, client: httpx.AsyncClient, ep: ATSEndpoint) -> List[Dict[str, Any]]:
        """
        Fetches an ATS JSON endpoint with retries, timeouts, and rate limits.
        Parses and returns valid India-specific job dictionaries.
        """
        headers = {
            "User-Agent": "CorporateGuildJobSearch/1.0 (+https://corporateguild.com)",
            "Accept": "application/json"
        }
        retries = self.config.scheduler.get("max_retries", 3)
        backoff = self.config.scheduler.get("backoff_factor", 1.5)

        for attempt in range(retries):
            try:
                resp = await client.get(ep.endpoint_url, headers=headers, timeout=self.config.scheduler.get("request_timeout_seconds", 10))
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_ats_data(ep, data)
                elif resp.status_code == 429:
                    await asyncio.sleep(backoff * (attempt + 1) + random.uniform(0.1, 0.5))
                else:
                    break
            except Exception as e:
                if attempt == retries - 1:
                    logger.debug(f"Failed fetching {ep.company_name} ({ep.endpoint_url}): {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
        return []

    def _parse_ats_data(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        platform = ep.ats_platform.lower()
        if "greenhouse" in platform:
            return self._parse_greenhouse(ep, data)
        elif "ashby" in platform:
            return self._parse_ashby(ep, data)
        elif "smartrecruiters" in platform:
            return self._parse_smartrecruiters(ep, data)
        else:
            # Try generic detection
            if "jobs" in data and isinstance(data["jobs"], list):
                return self._parse_greenhouse(ep, data)
            elif "content" in data and isinstance(data["content"], list):
                return self._parse_smartrecruiters(ep, data)
        return []

    def _parse_greenhouse(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobs", [])
        for j in jobs:
            loc_obj = j.get("location") or {}
            loc_name = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
            title = j.get("title", "").strip()
            
            # India location verification
            if not is_india_location(loc_name) and not is_india_location(title):
                continue

            apply_link = j.get("absolute_url") or f"https://boards.greenhouse.io/{ep.company_name.lower()}/jobs/{j.get('id')}"
            updated_at = j.get("updated_at") or j.get("first_published")
            ist_str, raw_iso, rel_time = parse_date_to_ist(updated_at)
            
            dept_names = [d.get("name", "") for d in j.get("departments", []) if isinstance(d, dict)]
            dept_str = " ".join(dept_names)
            tags = extract_tags(title, dept_str)
            emp_type = normalize_employment_type(j.get("employment_type", ""), title)
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower()))
            exp_level = normalize_experience_level(title)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": loc_name or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Greenhouse",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    def _parse_ashby(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobs", [])
        for j in jobs:
            title = j.get("title", "").strip()
            loc_name = j.get("location", "")
            is_remote = bool(j.get("isRemote", False))
            workplace_type_raw = j.get("workplaceType", "")
            
            # Check secondary locations for India
            sec_locs = [str(sl.get("location", "")) for sl in j.get("secondaryLocations", []) if isinstance(sl, dict)]
            combined_loc = f"{loc_name} {' '.join(sec_locs)}"
            if not is_india_location(combined_loc) and not is_india_location(title):
                continue

            apply_link = j.get("applyUrl") or j.get("jobUrl") or f"https://jobs.ashbyhq.com/{ep.company_name.lower()}/{j.get('id')}"
            published_at = j.get("publishedAt")
            ist_str, raw_iso, rel_time = parse_date_to_ist(published_at)

            dept = j.get("department", "")
            tags = extract_tags(title, dept)
            emp_type = normalize_employment_type(j.get("employmentType", ""), title)
            workplace = normalize_workplace(loc_name, workplace_type_raw, is_remote)
            exp_level = normalize_experience_level(title)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": loc_name or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Ashby",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    def _parse_smartrecruiters(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        items = data.get("content", [])
        for j in items:
            title = j.get("name", "").strip()
            loc_obj = j.get("location") or {}
            city = loc_obj.get("city", "")
            region = loc_obj.get("region", "")
            country = loc_obj.get("country", "")
            loc_str = f"{city}, {region}, {country}".strip(", ")

            if not is_india_location(loc_str, country) and not is_india_location(title):
                continue

            comp_name = j.get("company", {}).get("name") or ep.company_name
            apply_link = j.get("postingUrl") or j.get("ref") or f"https://jobs.smartrecruiters.com/{ep.company_name}/{j.get('id')}"
            released_at = j.get("releasedDate")
            ist_str, raw_iso, rel_time = parse_date_to_ist(released_at)

            type_obj = j.get("typeOfEmployment") or {}
            type_label = type_obj.get("label", "") if isinstance(type_obj, dict) else str(type_obj)
            exp_obj = j.get("experienceLevel") or {}
            exp_label = exp_obj.get("label", "") if isinstance(exp_obj, dict) else str(exp_obj)

            tags = extract_tags(title, j.get("function", {}).get("label", ""))
            emp_type = normalize_employment_type(type_label, title)
            workplace = normalize_workplace(loc_str)
            exp_level = normalize_experience_level(title, exp_label)

            results.append({
                "company_name": comp_name,
                "role_name": title,
                "location": loc_str or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "SmartRecruiters",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    async def fetch_all_endpoints(self, max_concurrent: int = 15, sample_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetches all configured endpoints asynchronously with rate limiting.
        """
        all_jobs: List[Dict[str, Any]] = []
        endpoints_to_query = self.endpoints[:sample_limit] if sample_limit else self.endpoints
        semaphore = asyncio.Semaphore(max_concurrent)

        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            async def worker(ep: ATSEndpoint):
                async with semaphore:
                    try:
                        jobs = await self.fetch_single_endpoint(client, ep)
                        return jobs
                    except Exception as e:
                        logger.debug(f"Error fetching {ep.company_name}: {e}")
                        return []

            tasks = [worker(ep) for ep in endpoints_to_query]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    all_jobs.extend(res)

        logger.info(f"Fetched {len(all_jobs)} India-specific jobs across {len(endpoints_to_query)} ATS endpoints.")
        return all_jobs

_ats_service: Optional[ATSService] = None

def get_ats_service() -> ATSService:
    global _ats_service
    if _ats_service is None:
        _ats_service = ATSService()
    return _ats_service

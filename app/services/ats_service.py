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

# Canonical Indian cities, metros, IT hubs, and states (used for strict word-boundary matching)
INDIA_CITIES_AND_STATES = [
    # Top IT Hubs & Metros
    "bengaluru", "bangalore", "mumbai", "bombay", "pune", "hyderabad", "secunderabad",
    "gurugram", "gurgaon", "noida", "greater noida", "delhi", "new delhi", "chennai", "madras",
    "kolkata", "calcutta", "ahmedabad", "jaipur", "indore", "kochi", "cochin", "ernakulam",
    "chandigarh", "mohali", "panchkula", "coimbatore", "thiruvananthapuram", "trivandrum",
    "bhubaneswar", "mysore", "mysuru", "mangalore", "mangaluru", "nagpur", "surat",
    "vadodara", "baroda", "visakhapatnam", "vizag", "bhopal", "lucknow", "patna",
    "ludhiana", "agra", "nashik", "rajkot", "varanasi", "amritsar", "navi mumbai", "thane",
    "ghaziabad", "faridabad", "guwahati", "dehradun", "hubli", "dharwad", "tiruchirappalli",
    "trichy", "madurai", "vijayawada", "guntur", "warangal", "jamshedpur", "ranchi", "cuttack",
    # States & Union Territories
    "karnataka", "maharashtra", "telangana", "tamil nadu", "tamilnadu", "haryana",
    "uttar pradesh", "west bengal", "gujarat", "rajasthan", "kerala", "andhra pradesh",
    "punjab", "odisha", "orissa", "madhya pradesh", "bihar", "assam", "goa", "uttarakhand",
    "himachal pradesh", "jharkhand", "chhattisgarh"
]

FOREIGN_RESTRICTED_REMOTES = [
    r"\bus\s*only\b", r"\bus\s*remote\b", r"\bremote\s*-\s*us\b", r"\bremote\s*\(us\)\b",
    r"\bremote\s*,\s*us\b", r"\bremote\s*-\s*usa\b", r"\bremote\s*,\s*usa\b",
    r"\bamericas\b", r"\bnorth\s*america\b", r"\bemea\b", r"\blatam\b",
    r"\beurope\b", r"\buk\s*only\b", r"\bcanada\s*only\b", r"\baus\s*only\b"
]

FOREIGN_TERRITORIES = [
    "united states", "usa", "u.s.", "u.s.a.", "united kingdom", "great britain",
    "england", "scotland", "wales", "ireland", "dublin", "canada", "australia",
    "germany", "france", "spain", "italy", "netherlands", "switzerland", "sweden",
    "poland", "japan", "china", "singapore", "israel", "uae", "dubai", "hong kong",
    "new zealand", "austria", "belgium", "denmark", "norway", "finland",
    "london", "paris", "berlin", "montreal", "toronto", "vancouver", "warsaw",
    "sydney", "melbourne", "tokyo", "zurich", "geneva", "amsterdam", "madrid",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming", "indianapolis"
]

INDIA_LOCATION_KEYWORDS = [
    "india", "remote - india", "india - remote", "remote, india", "remote (india)", "anywhere in india"
] + INDIA_CITIES_AND_STATES

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

    # Handle numeric epoch timestamp (ms or s)
    if isinstance(date_str, (int, float)) or (clean_str.isdigit() and len(clean_str) >= 9):
        try:
            val = float(clean_str)
            if val > 1e11: # Epoch in milliseconds
                val = val / 1000.0
            dt = datetime.datetime.fromtimestamp(val, tz=datetime.timezone.utc)
        except Exception:
            dt = None

    # Strip explicit IST suffix if present
    if dt is None and clean_str.endswith(" IST"):
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

GENERIC_REMOTE_KEYWORDS = [
    "remote", "anywhere", "worldwide", "global", "work from home", "wfh", "remote - global",
    "remote - worldwide", "work from anywhere", "anywhere in the world"
]

def is_india_location(location_str: str, country_code: str = "", workplace_type: str = "") -> bool:
    """
    Strictly verifies if a position is located in India or is an eligible unconstrained Remote role.
    Prevents false positives from US locations like Indiana/Indianapolis, and rejects foreign-only locations like Dublin/London/Atlanta.
    """
    if country_code and country_code.strip().lower() in ("in", "ind", "india"):
        return True

    loc_clean = (location_str or "").strip().lower()
    wp_clean = (workplace_type or "").strip().lower()

    if not loc_clean:
        if wp_clean == "remote":
            return True
        return False

    # 1. Eliminate false positives from US locations containing 'indian' (e.g. Indiana, Indianapolis)
    loc_without_us_indian = re.sub(
        r"\b(indiana|indianapolis|indian\s+river|indian\s+wells|indian\s+trail|indianola)\b",
        "",
        loc_clean
    )

    # 2. Check for explicit India country reference
    has_india_word = bool(re.search(r"\b(india|indian)\b", loc_without_us_indian))

    # 3. Check for recognized Indian cities, metros, and states
    has_indian_city = False
    for city in INDIA_CITIES_AND_STATES:
        if re.search(r"\b" + re.escape(city) + r"\b", loc_clean):
            has_indian_city = True
            break

    # If explicit Indian city or country is present, it is valid!
    if has_india_word or has_indian_city:
        return True

    # 4. If no Indian city/country is present:
    # A job can ONLY qualify if the location string itself is purely generic Remote (e.g. 'Remote', 'Worldwide')
    # If the location specifies a physical location (e.g. 'Atlanta', 'Boston', 'Dublin', 'Chicago'), it is NOT India!
    has_foreign_restricted = any(bool(re.search(pat, loc_clean)) for pat in FOREIGN_RESTRICTED_REMOTES)
    if has_foreign_restricted:
        return False

    has_foreign = any(re.search(r"\b" + re.escape(fc) + r"\b", loc_clean) for fc in FOREIGN_TERRITORIES)
    has_us_code = bool(re.search(r",\s*(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)\b", loc_clean))
    if has_foreign or has_us_code:
        return False

    # Check if the string is purely generic remote terms (e.g. 'Remote', 'Remote / Work From Home')
    stripped = loc_clean
    for kw in GENERIC_REMOTE_KEYWORDS:
        stripped = re.sub(r"\b" + re.escape(kw) + r"\b", "", stripped)
    stripped = re.sub(r"[\s,\-–—/|()]+", "", stripped)

    if not stripped and (wp_clean == "remote" or any(kw in loc_clean for kw in GENERIC_REMOTE_KEYWORDS)):
        return True

    return False

def extract_india_location(location_str: str) -> str:
    """
    Extracts the clean Indian location from a multi-location string.
    Example: 'Bengaluru, Karnataka, India; Berlin, Germany; Dublin, Ireland' -> 'Bengaluru, Karnataka, India'
             'London, New York, Singapore, Boston, Bangalore' -> 'Bangalore, India'
    """
    if not location_str:
        return "India"
    s = location_str.strip()

    # Semicolon, pipe, or newline delimited multi-locations
    delims = [";", "|", "\n"]
    for d in delims:
        if d in s:
            parts = [p.strip() for p in s.split(d) if p.strip()]
            for part in parts:
                p_lower = part.lower()
                clean_p = re.sub(r"\b(indiana|indianapolis|indian\s+river|indian\s+wells|indian\s+trail|indianola)\b", "", p_lower)
                if re.search(r"\b(india|indian)\b", clean_p) or any(re.search(r"\b" + re.escape(c) + r"\b", p_lower) for c in INDIA_CITIES_AND_STATES):
                    return part

    # Comma-delimited list of worldwide cities (e.g. 'Montreal, Bangalore, Warsaw' or 'London & Bangalore')
    norm_s = s.replace(" & ", ", ").replace(" and ", ", ")
    if "," in norm_s:
        parts = [p.strip() for p in norm_s.split(",") if p.strip()]
        if len(parts) >= 2:
            has_foreign_part = any(any(re.search(r"\b" + re.escape(fc) + r"\b", p.lower()) for fc in FOREIGN_TERRITORIES) for p in parts)
            if has_foreign_part:
                for part in parts:
                    p_lower = part.lower()
                    clean_p = re.sub(r"\b(indiana|indianapolis|indian\s+river|indian\s+wells|indian\s+trail|indianola)\b", "", p_lower)
                    if re.search(r"\b(india|indian)\b", clean_p) or any(re.search(r"\b" + re.escape(c) + r"\b", p_lower) for c in INDIA_CITIES_AND_STATES):
                        if "india" in p_lower:
                            return part
                        return f"{part}, India"

    return s

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

    def _parse_ats_data(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        platform = ep.ats_platform.lower()
        if "greenhouse" in platform:
            return self._parse_greenhouse(ep, data)
        elif "ashby" in platform:
            return self._parse_ashby(ep, data)
        elif "smartrecruiters" in platform:
            return self._parse_smartrecruiters(ep, data)
        elif "lever" in platform:
            return self._parse_lever(ep, data)
        elif "bamboohr" in platform:
            return self._parse_bamboohr(ep, data)
        else:
            # Try generic detection
            if isinstance(data, list):
                return self._parse_lever(ep, data)
            elif isinstance(data, dict):
                if "jobs" in data and isinstance(data["jobs"], list):
                    return self._parse_greenhouse(ep, data)
                elif "content" in data and isinstance(data["content"], list):
                    return self._parse_smartrecruiters(ep, data)
                elif "result" in data and isinstance(data["result"], list):
                    return self._parse_bamboohr(ep, data)
        return []

    def _parse_greenhouse(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobs", [])
        for j in jobs:
            loc_obj = j.get("location") or {}
            loc_name = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
            title = j.get("title", "").strip()
            
            # India location verification
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)

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
                "location": clean_loc or "India",
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
            combined_loc = f"{loc_name}; {'; '.join(sec_locs)}".strip("; ")
            if not is_india_location(combined_loc, workplace_type=workplace_type_raw):
                if not combined_loc.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(combined_loc)

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
                "location": clean_loc or "India",
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

            if not is_india_location(loc_str, country_code=country):
                if not loc_str.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

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
                "location": clean_loc or "India",
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

    def _parse_lever(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        jobs = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
        if not isinstance(jobs, list):
            return []

        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = j.get("text", "").strip()
            cats = j.get("categories") or {}
            loc_str = cats.get("location", "")
            workplace_type_raw = cats.get("workplaceType", "")
            
            # India location verification
            if not is_india_location(loc_str, workplace_type=workplace_type_raw):
                if not loc_str.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = j.get("hostedUrl") or j.get("applyUrl") or f"https://jobs.lever.co/{ep.company_name.lower()}/{j.get('id')}"
            created_at = j.get("createdAt")
            ist_str, raw_iso, rel_time = parse_date_to_ist(created_at)

            dept = cats.get("department", "") or cats.get("team", "")
            tags = extract_tags(title, dept)
            emp_type = normalize_employment_type(cats.get("commitment", ""), title)
            workplace = normalize_workplace(loc_str, workplace_type_raw, is_remote=("remote" in loc_str.lower()))
            exp_level = normalize_experience_level(title)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Lever",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    def _parse_bamboohr(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if not isinstance(data, dict):
            return []
        items = data.get("result", [])
        if not isinstance(items, list):
            return []

        for j in items:
            if not isinstance(j, dict):
                continue
            title = j.get("jobOpeningName", "").strip()
            loc_obj = j.get("location") or {}
            city = loc_obj.get("city", "") if isinstance(loc_obj, dict) else ""
            state = loc_obj.get("state", "") if isinstance(loc_obj, dict) else ""
            loc_str = f"{city}, {state}".strip(", ")
            is_rem = bool(j.get("isRemote"))
            
            # India location verification
            if not is_india_location(loc_str, workplace_type="Remote" if is_rem else ""):
                if not loc_str.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            job_id = str(j.get("id", "")).strip()
            # Derive apply link: https://{company}.bamboohr.com/careers/{job_id}
            base_careers = ep.endpoint_url.replace("/careers/list", f"/careers/{job_id}")
            apply_link = base_careers if job_id else ep.endpoint_url
            
            now_ist = datetime.datetime.now(IST_TZ)
            ist_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            raw_iso = now_ist.isoformat()
            rel_time = "Recently"

            dept = j.get("departmentLabel", "")
            tags = extract_tags(title, dept)
            emp_type = normalize_employment_type(j.get("employmentStatusLabel", ""), title)
            workplace = normalize_workplace(loc_str, is_remote=bool(j.get("isRemote")))
            exp_level = normalize_experience_level(title)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "BambooHR",
                "ingested_at": now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
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

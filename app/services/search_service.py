import re
import json
import logging
import datetime
import pytz
from typing import Dict, Any, List, Optional, Set, Tuple

from app.config import get_config
from app.redis_client import get_redis_client, parse_hash_name
from app.services.ats_service import get_ats_service, parse_date_to_ist

logger = logging.getLogger("search_service")
IST_TZ = pytz.timezone("Asia/Kolkata")

# Fixed roles catalog with semantic synonyms
FIXED_ROLES = [
    {
        "role": "Software Engineer",
        "synonyms": ["software developer", "sde", "swe", "programmer", "software development engineer"]
    },
    {
        "role": "Backend Engineer",
        "synonyms": ["backend developer", "api developer", "python developer", "java developer", "golang developer", "node.js developer"]
    },
    {
        "role": "Frontend Engineer",
        "synonyms": ["frontend developer", "ui developer", "react developer", "web developer", "angular developer"]
    },
    {
        "role": "Full Stack Engineer",
        "synonyms": ["full stack developer", "web application developer", "mern developer"]
    },
    {
        "role": "Data Engineer",
        "synonyms": ["big data engineer", "etl developer", "data platform engineer", "snowflake developer"]
    },
    {
        "role": "AI / Machine Learning Engineer",
        "synonyms": ["ai engineer", "machine learning engineer", "ml engineer", "data scientist", "deep learning", "nlp engineer"]
    },
    {
        "role": "DevOps / SRE",
        "synonyms": ["site reliability engineer", "cloud engineer", "infrastructure engineer", "platform engineer", "sre", "kubernetes engineer"]
    },
    {
        "role": "Product Manager",
        "synonyms": ["product manager", "product management", "associate product manager", "technical product manager", "group product manager", "product lead", "product owner", "head of product", "vp product", "apm", "tpm", "principal product manager"]
    },
    {
        "role": "QA / SDET",
        "synonyms": ["quality assurance", "sdet", "test engineer", "automation engineer", "qa engineer"]
    },
    {
        "role": "UI/UX Designer",
        "synonyms": ["product designer", "user experience designer", "visual designer", "interaction designer"]
    },
    {
        "role": "Human Resources / Recruiter",
        "synonyms": ["talent acquisition", "hr generalist", "hr intern", "people operations", "recruiter", "talent partner"]
    },
    {
        "role": "Sales / Business Development",
        "synonyms": ["account executive", "bdr", "sdr", "business development associate", "enterprise sales"]
    },
    {
        "role": "Marketing Specialist",
        "synonyms": ["growth marketer", "content strategist", "seo specialist", "digital marketer"]
    },
    {
        "role": "Finance / Operations",
        "synonyms": ["financial analyst", "accountant", "operations manager", "accounts receivable"]
    },
    {
        "role": "Cybersecurity Engineer",
        "synonyms": ["security analyst", "infosec", "penetration tester", "security engineer"]
    }
]

def role_matches(synonyms: List[str], text: Optional[str]) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    for syn in synonyms:
        s = syn.strip().lower()
        if not s:
            continue
        pattern = rf"\b{re.escape(s)}\b"
        if re.search(pattern, text_lower):
            return True
    return False

class SearchService:
    def __init__(self):
        self.config = get_config()
        self.ats_service = get_ats_service()

    def get_suggestions(self, mode: str, query: str, limit: int = 25) -> List[Dict[str, str]]:
        """
        Provides autocomplete suggestions based on verified company names or industry roles.
        Returns prominent valid options when query is empty, and filters semantically as user types.
        """
        q = (query or "").strip().lower()
        results = []

        if mode == "company":
            all_comps = self.ats_service.get_all_companies()
            client = get_redis_client()
            try:
                keys = client.keys("*|*")
                for k in keys:
                    c, _ = parse_hash_name(k)
                    if c and c not in all_comps:
                        all_comps.append(c)
            except Exception:
                pass

            prominent = [
                "Stripe", "Google", "Microsoft", "Amazon", "Swiggy", "Zomato",
                "Razorpay", "Flipkart", "Atlassian", "Uber", "Cisco", "PhonePe",
                "CRED", "InMobi", "Meesho", "Coinbase", "Airbnb", "Snowflake",
                "Databricks", "Oracle", "Intuit", "ServiceNow"
            ]
            all_comps = sorted(list(set(all_comps + prominent)))
            if not q:
                matched = list(prominent)
                for ac in all_comps:
                    if ac not in matched and len(matched) < max(limit, 120):
                        matched.append(ac)
            else:
                matched = [c for c in all_comps if q in c.lower()]

            for c in matched[:max(limit, 120)]:
                results.append({"type": "company", "value": c, "label": c})

        elif mode == "role":
            matched = []
            for item in FIXED_ROLES:
                r_name = item["role"]
                syns = item["synonyms"]
                if not q:
                    matched.append((r_name, ", ".join(syns[:2])))
                elif q in r_name.lower() or any(q in s.lower() for s in syns):
                    matched.append((r_name, ", ".join(syns[:2])))

            # Return all matched roles (ensures all 15 valid roles are visible on click)
            for r, sub in matched:
                results.append({"type": "role", "value": r, "label": r, "subtitle": sub})

        return results

    def get_role_synonyms(self, role_name: str) -> List[str]:
        target = role_name.strip().lower()
        for item in FIXED_ROLES:
            if item["role"].lower() == target or target in [s.lower() for s in item["synonyms"]]:
                return [item["role"].lower()] + [s.lower() for s in item["synonyms"]]
        return [target]

    def search_jobs(
        self,
        search_type: str, # "company", "role", "other_company", "other_role"
        search_term: str,
        custom_input: Optional[str] = None,
        location_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        employment_type: Optional[str] = None,
        workplace_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        time_filter: Optional[str] = None, # "1h", "12h", "24h", "2d", "7d"
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Executes search strictly based on Redis hashes {company_name}|{role_name}.
        Applies filter options, descending timestamp sort, and page 10 pagination.
        """
        client = get_redis_client()
        query_term = (custom_input if custom_input else search_term or "").strip()
        query_lower = query_term.lower()

        # Step 1: Scan Redis hashes matching company or role
        matching_hashes = set()
        all_keys = client.keys("*|*")

        if not query_term:
            matching_hashes = set(all_keys)
        elif search_type == "company":
            for k in all_keys:
                c, r = parse_hash_name(k)
                if query_lower in c.lower() or c.lower() == query_lower:
                    matching_hashes.add(k)

        elif search_type == "role":
            synonyms = self.get_role_synonyms(query_term)
            all_syns = list(set(synonyms + [query_lower]))
            for k in all_keys:
                c, r = parse_hash_name(k)
                if role_matches(all_syns, r):
                    matching_hashes.add(k)

        elif search_type in ("other_company", "other_role", "other", "custom"):
            tokens = [t for t in re.split(r"\s+", query_lower) if len(t) > 1]
            synonyms = self.get_role_synonyms(query_term)
            for k in all_keys:
                c, r = parse_hash_name(k)
                combined = f"{c} {r}".lower()
                if not tokens or any(t in combined for t in tokens) or role_matches(synonyms, combined):
                    matching_hashes.add(k)
        else:
            matching_hashes = set(all_keys)

        # Step 2: Fetch all jobs from matching Redis hashes
        raw_jobs = []
        for h_key in matching_hashes:
            hdata = client.hgetall(h_key)
            for ts_key, val_str in hdata.items():
                try:
                    jdata = json.loads(val_str)
                    raw_jobs.append(jdata)
                except Exception:
                    pass

        # Step 3: Apply Filters
        filtered_jobs = []
        now_ist = datetime.datetime.now(IST_TZ)

        for job in raw_jobs:
            # If search_type was role and query was provided, strictly verify that this individual job satisfies role semantics
            if search_type == "role" and query_term:
                r_name = job.get("role_name", "")
                title = job.get("title", "")
                synonyms = self.get_role_synonyms(query_term)
                all_syns = list(set(synonyms + [query_lower]))
                if not (role_matches(all_syns, r_name) or role_matches(all_syns, title)):
                    continue

            # Location filter
            if location_filter and location_filter.lower() != "all":
                loc = job.get("location", "").lower()
                if location_filter.lower() not in loc:
                    continue

            # Role filter
            if role_filter and role_filter.lower() != "all":
                r_name = job.get("role_name", "")
                title = job.get("title", "")
                r_syns = self.get_role_synonyms(role_filter)
                if not (role_matches(r_syns, r_name) or role_matches(r_syns, title)):
                    continue

            # Employment type filter
            if employment_type and employment_type.lower() != "all":
                emp = job.get("employment_type", "").lower()
                if employment_type.lower() not in emp:
                    continue

            # Workplace filter
            if workplace_type and workplace_type.lower() != "all":
                wp = job.get("workplace_type", "").lower()
                if workplace_type.lower() not in wp:
                    continue

            # Experience level filter
            if experience_level and experience_level.lower() != "all":
                exp = job.get("experience_level", "").lower()
                if experience_level.lower() not in exp:
                    continue

            # Time filter ("1h", "12h", "24h", "2d", "7d")
            if time_filter and time_filter.lower() != "all":
                hours_map = {"1h": 1, "12h": 12, "24h": 24, "2d": 48, "7d": 168}
                max_hours = hours_map.get(time_filter.lower(), 168)
                posted_iso = job.get("posted_timestamp_raw")
                if posted_iso:
                    try:
                        dt = datetime.datetime.fromisoformat(posted_iso.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = pytz.utc.localize(dt)
                        ist_dt = dt.astimezone(IST_TZ)
                        diff_hours = (now_ist - ist_dt).total_seconds() / 3600.0
                        if diff_hours > max_hours:
                            continue
                    except Exception:
                        pass

            # Calculate live relative time in IST
            _, _, rel = parse_date_to_ist(job.get("posted_timestamp_raw") or job.get("posted_timestamp_ist"))
            job["relative_time_ist"] = rel

            filtered_jobs.append(job)

        # Step 4: Sort by Decreasing Timestamp Order (newest first in IST)
        def sort_key(j: Dict[str, Any]) -> str:
            return j.get("posted_timestamp_raw") or j.get("posted_timestamp_ist") or ""

        filtered_jobs.sort(key=sort_key, reverse=True)

        # Step 5: Paginate (Page size 10)
        total_count = len(filtered_jobs)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = filtered_jobs[start_idx:end_idx]

        return {
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "search_type": search_type,
            "search_term": query_term,
            "applied_filters": {
                "location": location_filter,
                "role": role_filter,
                "employment_type": employment_type,
                "workplace_type": workplace_type,
                "experience_level": experience_level,
                "time_filter": time_filter
            },
            "results": paginated_results
        }

_search_service: Optional[SearchService] = None

def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

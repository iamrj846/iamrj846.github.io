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
        "synonyms": ["software developer", "sde", "swe", "programmer", "software development engineer", "graduate engineer trainee", "member of technical staff"]
    },
    {
        "role": "Backend Engineer",
        "synonyms": ["backend developer", "api developer", "python developer", "java developer", "golang developer", "node.js developer", "c++ developer", "spring boot developer"]
    },
    {
        "role": "Frontend Engineer",
        "synonyms": ["frontend developer", "ui developer", "react developer", "web developer", "angular developer", "vue developer", "next.js developer", "javascript developer"]
    },
    {
        "role": "Full Stack Engineer",
        "synonyms": ["full stack developer", "web application developer", "mern developer", "mean developer", "fullstack"]
    },
    {
        "role": "Mobile Engineer",
        "synonyms": ["android developer", "ios developer", "flutter developer", "react native developer", "mobile app developer", "swift developer", "kotlin developer"]
    },
    {
        "role": "AI / Machine Learning Engineer",
        "synonyms": ["ai engineer", "machine learning engineer", "ml engineer", "deep learning", "nlp engineer", "computer vision", "llm engineer", "genai developer"]
    },
    {
        "role": "Data Scientist",
        "synonyms": ["data scientist", "applied scientist", "ai scientist", "quantitative analyst", "statistical modeler", "research scientist"]
    },
    {
        "role": "Data Engineer",
        "synonyms": ["big data engineer", "etl developer", "data platform engineer", "snowflake developer", "spark developer", "data pipeline developer"]
    },
    {
        "role": "Data Analyst / BI",
        "synonyms": ["data analyst", "business intelligence analyst", "tableau developer", "power bi developer", "bi analyst", "sql analyst", "product analyst"]
    },
    {
        "role": "DevOps / Cloud Engineer",
        "synonyms": ["devops engineer", "cloud engineer", "cloud architect", "infrastructure engineer", "platform engineer", "aws engineer", "azure engineer", "gcp engineer", "terraform"]
    },
    {
        "role": "Site Reliability Engineer (SRE)",
        "synonyms": ["site reliability engineer", "sre", "systems engineer", "production engineer", "reliability engineer", "kubernetes engineer"]
    },
    {
        "role": "Cybersecurity Engineer",
        "synonyms": ["security analyst", "infosec", "penetration tester", "security engineer", "appsec", "cloud security", "soc analyst", "cyber security specialist"]
    },
    {
        "role": "QA / SDET",
        "synonyms": ["quality assurance", "sdet", "test engineer", "automation engineer", "qa engineer", "software tester", "qa lead", "manual tester"]
    },
    {
        "role": "Product Manager",
        "synonyms": ["product manager", "product management", "associate product manager", "technical product manager", "group product manager", "product lead", "product owner", "head of product", "vp product", "apm", "tpm", "principal product manager"]
    },
    {
        "role": "Engineering Manager / Lead",
        "synonyms": ["engineering manager", "tech lead", "lead engineer", "director of engineering", "vp engineering", "software engineering manager", "architect"]
    },
    {
        "role": "Solutions Architect",
        "synonyms": ["solutions architect", "enterprise architect", "technical architect", "systems architect", "pre-sales architect"]
    },
    {
        "role": "Technical Program Manager",
        "synonyms": ["technical program manager", "tpm", "program manager", "project manager", "scrum master", "agile coach", "delivery manager"]
    },
    {
        "role": "UI/UX Designer",
        "synonyms": ["product designer", "user experience designer", "visual designer", "interaction designer", "ux researcher", "ui designer", "figma designer"]
    },
    {
        "role": "Graphic / Brand Designer",
        "synonyms": ["graphic designer", "brand designer", "motion designer", "creative designer", "multimedia artist", "illustrator"]
    },
    {
        "role": "Human Resources / Recruiter",
        "synonyms": ["talent acquisition", "hr generalist", "hr intern", "people operations", "recruiter", "talent partner", "technical recruiter", "hrbp", "human resources manager"]
    },
    {
        "role": "Sales / Business Development",
        "synonyms": ["account executive", "bdr", "sdr", "business development associate", "enterprise sales", "sales manager", "inside sales", "business development manager"]
    },
    {
        "role": "Customer Success / Account Manager",
        "synonyms": ["customer success manager", "csm", "account manager", "client success", "relationship manager", "customer onboarding specialist"]
    },
    {
        "role": "Marketing / Growth Specialist",
        "synonyms": ["growth marketer", "content strategist", "digital marketer", "performance marketer", "brand manager", "campaign manager", "social media manager"]
    },
    {
        "role": "Content Writer / Copywriter",
        "synonyms": ["content writer", "copywriter", "technical writer", "content creator", "documentation specialist", "editorial lead"]
    },
    {
        "role": "SEO / SEM Specialist",
        "synonyms": ["seo specialist", "search engine optimization", "sem specialist", "ppc specialist", "performance marketing", "organic search manager"]
    },
    {
        "role": "Finance / Accounting",
        "synonyms": ["financial analyst", "accountant", "chartered accountant", "accounts receivable", "accounts payable", "finance manager", "controller", "auditor"]
    },
    {
        "role": "Operations / Supply Chain",
        "synonyms": ["operations manager", "operations associate", "supply chain analyst", "logistics manager", "procurement specialist", "inventory manager"]
    },
    {
        "role": "Legal / Compliance Specialist",
        "synonyms": ["legal counsel", "compliance officer", "corporate counsel", "regulatory affairs", "risk analyst", "contract manager"]
    },
    {
        "role": "Technical Support / IT",
        "synonyms": ["it support", "technical support engineer", "application support", "helpdesk specialist", "desktop support", "customer support engineer"]
    },
    {
        "role": "Hardware / Embedded Engineer",
        "synonyms": ["embedded engineer", "firmware developer", "iot engineer", "vlsi engineer", "hardware engineer", "electronics engineer", "robotics engineer"]
    },
    {
        "role": "Business Analyst / Strategy",
        "synonyms": ["business analyst", "strategy analyst", "management consultant", "operations analyst", "business operations", "bizops", "strategy associate", "commercial analyst"]
    },
    {
        "role": "Chief of Staff / Founder's Office",
        "synonyms": ["founder's office", "chief of staff", "executive assistant", "business manager", "general management associate", "special projects lead"]
    }
]

def sanitize_tags(raw_tags: Any) -> List[str]:
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

    clean_list = []
    for item in items:
        if not item:
            continue
        cleaned = str(item).strip("[]'\"# \t\r\n")
        for sub in re.split(r'["\',]+', cleaned):
            c_sub = sub.strip("[]'\"# \t\r\n")
            if c_sub and c_sub not in clean_list:
                clean_list.append(c_sub)
    return clean_list

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
        time_filter: Optional[str] = "1h", # "1h", "12h", "24h", "2d", "7d", "all"
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
        active_time_filter = (time_filter or "1h").strip()

        # Step 1: Scan Redis hashes matching company or role
        matching_hashes = set()
        all_keys = client.keys("*|*")
        if not all_keys:
            from app.services.ingestion_service import get_ingestion_manager
            get_ingestion_manager().seed_initial_jobs()
            all_keys = client.keys("*|*")

        if not query_term:
            matching_hashes = set(all_keys)
        elif search_type == "company":
            for k in all_keys:
                c, r = parse_hash_name(k)
                if query_lower in c.lower() or c.lower() == query_lower:
                    matching_hashes.add(k)

            # If no cached jobs in Redis, check if company is in our master ATS directory and fetch live
            if not matching_hashes:
                matching_eps = [
                    ep for ep in self.ats_service.endpoints
                    if query_lower == ep.company_name.lower() or query_lower in ep.company_name.lower()
                ]
                if matching_eps:
                    target_ep = matching_eps[0]
                    try:
                        import httpx
                        with httpx.Client(timeout=6.0, follow_redirects=True) as sync_client:
                            headers = {
                                "User-Agent": "CorporateGuildJobSearch/1.0 (+https://corporateguild.com)",
                                "Accept": "application/json"
                            }
                            resp = sync_client.get(target_ep.endpoint_url, headers=headers)
                            if resp.status_code == 200:
                                live_jobs = self.ats_service._parse_ats_data(target_ep, resp.json())
                                if live_jobs:
                                    from app.database import save_jobs_to_db
                                    from app.redis_client import store_job_in_redis
                                    save_jobs_to_db(live_jobs)
                                    for lj in live_jobs:
                                        store_job_in_redis(lj)
                                    all_keys = client.keys("*|*")
                                    for k in all_keys:
                                        c, r = parse_hash_name(k)
                                        if query_lower in c.lower() or c.lower() == query_lower:
                                            matching_hashes.add(k)
                    except Exception as e:
                        logger.debug(f"On-demand fetch failed for {target_ep.company_name}: {e}")

            # Smart fallback: only if query is generic and neither Redis nor ATS had this company
            if not matching_hashes and len(query_term) > 3:
                synonyms = self.get_role_synonyms(query_term)
                all_syns = list(set(synonyms + [query_lower]))
                for k in all_keys:
                    c, r = parse_hash_name(k)
                    if role_matches(all_syns, r) or any(s in r.lower() for s in all_syns):
                        matching_hashes.add(k)

        elif search_type == "role":
            synonyms = self.get_role_synonyms(query_term)
            all_syns = list(set(synonyms + [query_lower]))
            for k in all_keys:
                c, r = parse_hash_name(k)
                if role_matches(all_syns, r) or any(s in r.lower() for s in all_syns):
                    matching_hashes.add(k)
            # Smart fallback: if no role matched, check if query matches company name
            if not matching_hashes:
                for k in all_keys:
                    c, r = parse_hash_name(k)
                    if query_lower in c.lower() or c.lower() == query_lower:
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
                    jdata["tags"] = sanitize_tags(jdata.get("tags"))
                    raw_jobs.append(jdata)
                except Exception:
                    pass

        # Step 3: Apply Filters
        filtered_jobs = []
        now_ist = datetime.datetime.now(IST_TZ)

        for job in raw_jobs:
            r_name = job.get("role_name", "")
            title = job.get("title", "")
            c_name = job.get("company_name", "")

            # If search_type was role and query was provided, verify individual job satisfies role or fallback company
            if search_type == "role" and query_term:
                synonyms = self.get_role_synonyms(query_term)
                all_syns = list(set(synonyms + [query_lower]))
                matches_role = role_matches(all_syns, r_name) or role_matches(all_syns, title) or any(s in r_name.lower() or s in title.lower() for s in all_syns)
                if not matches_role and query_lower not in c_name.lower():
                    continue

            # Location filter
            if location_filter and location_filter.lower() != "all":
                loc = job.get("location", "").lower()
                wp = job.get("workplace_type", "").lower()
                lf = location_filter.lower()
                if lf == "remote":
                    if "remote" not in loc and "remote" not in wp:
                        continue
                elif lf not in loc:
                    continue

            # Role filter
            if role_filter and role_filter.lower() != "all":
                r_syns = self.get_role_synonyms(role_filter)
                rf_lower = role_filter.lower()
                all_rf_syns = list(set(r_syns + [rf_lower]))
                if not (role_matches(all_rf_syns, r_name) or role_matches(all_rf_syns, title) or any(s in r_name.lower() or s in title.lower() for s in all_rf_syns)):
                    continue

            # Employment type filter
            if employment_type and employment_type.lower() != "all":
                emp = job.get("employment_type", "").lower()
                target_emp = employment_type.lower()
                title_lower = title.lower()
                if "intern" in target_emp:
                    if "intern" not in emp and "intern" not in title_lower:
                        continue
                elif target_emp not in emp:
                    continue

            # Workplace filter
            if workplace_type and workplace_type.lower() != "all":
                wp = job.get("workplace_type", "").lower()
                loc = job.get("location", "").lower()
                target_wp = workplace_type.lower()
                if target_wp == "remote":
                    if "remote" not in wp and "remote" not in loc:
                        continue
                elif target_wp not in wp:
                    continue

            # Experience level filter
            if experience_level and experience_level.lower() != "all":
                exp = job.get("experience_level", "").lower()
                title_lower = title.lower()
                target_exp = experience_level.lower()
                if "entry" in target_exp:
                    if "entry" not in exp and "intern" not in title_lower and "fresher" not in title_lower:
                        continue
                elif "senior" in target_exp:
                    if "senior" not in exp and "sr" not in title_lower and "lead" not in title_lower:
                        continue
                elif target_exp not in exp:
                    continue

            # Time filter ("1h", "12h", "24h", "2d", "7d", "all")
            if active_time_filter and active_time_filter.lower() not in ("all", "anytime", "anytime (7 days)"):
                hours_map = {"1h": 1, "12h": 12, "24h": 24, "2d": 48, "7d": 168}
                max_hours = hours_map.get(active_time_filter.lower(), 1)
                posted_iso = job.get("posted_timestamp_raw") or job.get("posted_timestamp_ist") or job.get("posted_at")
                if posted_iso:
                    try:
                        clean_ts = str(posted_iso).replace(" IST", "").replace("Z", "+00:00").strip()
                        if "T" in clean_ts:
                            dt = datetime.datetime.fromisoformat(clean_ts)
                        else:
                            dt = datetime.datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                        if dt.tzinfo is None:
                            dt = pytz.timezone("Asia/Kolkata").localize(dt)
                        ist_dt = dt.astimezone(IST_TZ)
                        diff_hours = (now_ist - ist_dt).total_seconds() / 3600.0
                        if diff_hours > max_hours:
                            continue
                    except Exception:
                        pass

            # Calculate live relative time in IST
            _, _, rel = parse_date_to_ist(job.get("posted_timestamp_raw") or job.get("posted_timestamp_ist") or job.get("posted_at"))
            job["relative_time_ist"] = rel
            job["tags"] = sanitize_tags(job.get("tags"))

            filtered_jobs.append(job)

        # Step 4: Sort by Decreasing Timestamp Order (newest first in IST)
        def sort_key(j: Dict[str, Any]) -> float:
            raw_epoch = j.get("posted_epoch")
            if raw_epoch is not None:
                try:
                    return float(raw_epoch)
                except Exception:
                    pass
            ts = j.get("posted_timestamp_raw") or j.get("posted_timestamp_ist") or j.get("posted_at")
            if not ts:
                return 0.0
            try:
                clean_ts = str(ts).replace(" IST", "").replace("Z", "+00:00").strip()
                if "T" in clean_ts:
                    dt = datetime.datetime.fromisoformat(clean_ts)
                else:
                    dt = datetime.datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                if dt.tzinfo is None:
                    dt = pytz.timezone("Asia/Kolkata").localize(dt)
                return dt.astimezone(IST_TZ).timestamp()
            except Exception:
                return 0.0

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
                "time_filter": active_time_filter
            },
            "results": paginated_results
        }

_search_service: Optional[SearchService] = None

def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

import re
import json
import logging
import datetime
import pytz
from typing import Dict, Any, List, Optional, Set, Tuple

from app.config import get_config
from app.redis_client import get_redis_client, parse_hash_name
from app.services.ats_service import get_ats_service, parse_date_to_ist, is_india_location, extract_india_location

logger = logging.getLogger("search_service")
IST_TZ = pytz.timezone("Asia/Kolkata")

# Fixed roles catalog with comprehensive semantic synonyms, industry acronyms, and related job titles
FIXED_ROLES = [
    {
        "role": "Software Engineer",
        "synonyms": [
            "sde", "swe", "software developer", "software development engineer", 
            "programmer", "developer", "sde 1", "sde 2", "sde 3", "sde-1", "sde-2", 
            "graduate engineer trainee", "member of technical staff", "mts", 
            "software engineer 1", "software engineer 2"
        ]
    },
    {
        "role": "Backend Engineer",
        "synonyms": [
            "backend", "backend developer", "api developer", "server engineer", 
            "microservices", "python developer", "java developer", "golang developer", 
            "node.js developer", "node developer", "c++ developer", "spring boot developer", 
            "django developer", "fastapi developer", "backend software engineer"
        ]
    },
    {
        "role": "Frontend Engineer",
        "synonyms": [
            "frontend", "frontend developer", "ui developer", "react developer", 
            "web developer", "angular developer", "vue developer", "next.js developer", 
            "javascript developer", "typescript developer", "html", "css", "frontend engineer"
        ]
    },
    {
        "role": "Full Stack Engineer",
        "synonyms": [
            "full stack", "fullstack", "full stack developer", "web application developer", 
            "mern developer", "mean developer", "fullstack developer", "full stack engineer"
        ]
    },
    {
        "role": "Mobile Engineer",
        "synonyms": [
            "mobile", "mobile engineer", "mobile developer", "apps", "apps engineer", 
            "apps developer", "app developer", "android", "android developer", "android engineer", 
            "ios", "ios developer", "ios engineer", "flutter", "flutter developer", 
            "react native", "react native developer", "swift developer", "swift", 
            "kotlin developer", "kotlin", "mobile app developer"
        ]
    },
    {
        "role": "AI / Machine Learning Engineer",
        "synonyms": [
            "ai", "ml", "ai engineer", "machine learning engineer", "machine learning", 
            "ml engineer", "deep learning", "nlp engineer", "nlp", "computer vision", 
            "llm engineer", "llm", "genai developer", "genai", "generative ai", 
            "artificial intelligence", "data scientist - ai"
        ]
    },
    {
        "role": "Data Scientist",
        "synonyms": [
            "data science", "data scientist", "applied scientist", "ai scientist", 
            "quantitative analyst", "statistical modeler", "research scientist", "statistician"
        ]
    },
    {
        "role": "Data Engineer",
        "synonyms": [
            "data engineer", "big data engineer", "big data", "etl developer", "etl", 
            "data platform engineer", "snowflake developer", "spark developer", 
            "data pipeline developer", "data infrastructure"
        ]
    },
    {
        "role": "Data Analyst / BI",
        "synonyms": [
            "data analyst", "business intelligence", "business intelligence analyst", 
            "bi", "bi analyst", "tableau developer", "power bi developer", "power bi", 
            "sql analyst", "product analyst", "analytics consultant", "reporting analyst"
        ]
    },
    {
        "role": "DevOps / Cloud Engineer",
        "synonyms": [
            "devops", "devops engineer", "cloud engineer", "cloud", "cloud architect", 
            "infrastructure engineer", "infrastructure", "platform engineer", "aws engineer", 
            "aws", "azure engineer", "azure", "gcp engineer", "gcp", "terraform", 
            "ci/cd", "build and release engineer"
        ]
    },
    {
        "role": "Site Reliability Engineer (SRE)",
        "synonyms": [
            "sre", "site reliability engineer", "site reliability", "systems engineer", 
            "production engineer", "reliability engineer", "kubernetes engineer", "kubernetes"
        ]
    },
    {
        "role": "Cybersecurity Engineer",
        "synonyms": [
            "security analyst", "infosec", "penetration tester", "security engineer", 
            "appsec", "cloud security", "soc analyst", "cyber security specialist", 
            "cybersecurity", "information security", "vulnerability analyst"
        ]
    },
    {
        "role": "QA / SDET",
        "synonyms": [
            "qa", "sdet", "quality assurance", "test engineer", "automation engineer", 
            "automation tester", "qa engineer", "software tester", "qa lead", "manual tester", 
            "software developer in test", "quality engineer", "testing"
        ]
    },
    {
        "role": "Product Manager",
        "synonyms": [
            "pm", "product manager", "product management", "associate product manager", 
            "apm", "technical product manager", "tpm", "group product manager", 
            "product lead", "product owner", "head of product", "vp product", 
            "principal product manager"
        ]
    },
    {
        "role": "Engineering Manager / Lead",
        "synonyms": [
            "engineering manager", "tech lead", "lead engineer", "director of engineering", 
            "vp engineering", "software engineering manager", "architect", "engineering lead", 
            "principal engineer", "staff engineer"
        ]
    },
    {
        "role": "Solutions Architect",
        "synonyms": [
            "solutions architect", "enterprise architect", "technical architect", 
            "systems architect", "pre-sales architect", "solution architect", "customer architect"
        ]
    },
    {
        "role": "Technical Program Manager",
        "synonyms": [
            "technical program manager", "tpm", "program manager", "project manager", 
            "scrum master", "agile coach", "delivery manager"
        ]
    },
    {
        "role": "UI/UX Designer",
        "synonyms": [
            "ui", "ux", "ui/ux", "ui ux", "product designer", "user experience designer", 
            "visual designer", "interaction designer", "ux researcher", "ui designer", 
            "figma designer", "design lead"
        ]
    },
    {
        "role": "Graphic / Brand Designer",
        "synonyms": [
            "graphic designer", "brand designer", "motion designer", "creative designer", 
            "multimedia artist", "illustrator", "visual designer"
        ]
    },
    {
        "role": "Human Resources / Recruiter",
        "synonyms": [
            "hr", "human resource", "human resources", "talent acquisition", "recruiter", 
            "recruitment", "people operations", "people partner", "talent partner", 
            "technical recruiter", "hrbp", "human resources business partner", 
            "hr generalist", "hr intern", "human resources manager", "hr manager", 
            "hr coordinator", "hr executive", "people team"
        ]
    },
    {
        "role": "Sales / Business Development",
        "synonyms": [
            "sales", "business development", "bdr", "sdr", "account executive", 
            "business development associate", "bda", "enterprise sales", "sales manager", 
            "inside sales", "business development manager", "sales development representative"
        ]
    },
    {
        "role": "Customer Success / Account Manager",
        "synonyms": [
            "customer success", "customer success manager", "csm", "account manager", 
            "client success", "relationship manager", "customer onboarding specialist", 
            "customer experience", "client partner"
        ]
    },
    {
        "role": "Marketing / Growth Specialist",
        "synonyms": [
            "marketing", "digital marketing", "digital marketer", "social media", 
            "social media executive", "social media manager", "social media specialist", 
            "growth marketer", "growth marketing", "content strategist", "performance marketer", 
            "performance marketing", "brand manager", "campaign manager", "marketing manager", 
            "marketing executive", "growth lead"
        ]
    },
    {
        "role": "Content Writer / Copywriter",
        "synonyms": [
            "content writer", "copywriter", "technical writer", "content creator", 
            "documentation specialist", "editorial lead", "content specialist"
        ]
    },
    {
        "role": "SEO / SEM Specialist",
        "synonyms": [
            "seo", "sem", "seo specialist", "search engine optimization", "sem specialist", 
            "ppc specialist", "ppc", "performance marketing", "organic search manager", 
            "search marketing"
        ]
    },
    {
        "role": "Finance / Accounting",
        "synonyms": [
            "finance", "accounting", "financial analyst", "accountant", "chartered accountant", 
            "ca", "accounts receivable", "accounts payable", "finance manager", 
            "controller", "auditor", "fp&a"
        ]
    },
    {
        "role": "Operations / Supply Chain",
        "synonyms": [
            "operations", "operations manager", "operations associate", "supply chain", 
            "supply chain analyst", "logistics manager", "logistics", "procurement specialist", 
            "procurement", "inventory manager", "business operations"
        ]
    },
    {
        "role": "Legal / Compliance Specialist",
        "synonyms": [
            "legal", "legal counsel", "compliance", "compliance officer", "corporate counsel", 
            "regulatory affairs", "risk analyst", "contract manager"
        ]
    },
    {
        "role": "Technical Support / IT",
        "synonyms": [
            "it support", "technical support engineer", "technical support", "application support", 
            "helpdesk specialist", "desktop support", "customer support engineer", "it administrator"
        ]
    },
    {
        "role": "Hardware / Embedded Engineer",
        "synonyms": [
            "embedded engineer", "firmware developer", "iot engineer", "vlsi engineer", 
            "hardware engineer", "electronics engineer", "robotics engineer"
        ]
    },
    {
        "role": "Business Analyst / Strategy",
        "synonyms": [
            "business analyst", "strategy analyst", "management consultant", "operations analyst", 
            "business operations", "bizops", "strategy associate", "commercial analyst"
        ]
    },
    {
        "role": "Chief of Staff / Founder's Office",
        "synonyms": [
            "founder's office", "chief of staff", "executive assistant", "business manager", 
            "general management associate", "special projects lead"
        ]
    }
]

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

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
        if " " in s and s in text_lower:
            return True
    return False

def calculate_semantic_relevance(query: str, title: str, role_cat: str = "", tags: List[str] = None, synonyms: List[str] = None) -> float:
    """
    Computes a semantic relevance score from 0.0 to 100.0.
    Considers exact phrase, word boundary regex, taxonomy synonyms, and RapidFuzz token matching.
    """
    if not query:
        return 1.0
    q = query.strip().lower()
    combined_target = f"{title} {role_cat} {' '.join(tags or [])}".strip().lower()

    if q == title.strip().lower():
        return 100.0
    if re.search(rf"\b{re.escape(q)}\b", title.lower()):
        return 95.0
    if q in title.lower():
        return 90.0

    # Synonym check
    if synonyms:
        for syn in synonyms:
            s_clean = syn.strip().lower()
            if not s_clean:
                continue
            if re.search(rf"\b{re.escape(s_clean)}\b", title.lower()):
                return 88.0
            if " " in s_clean and s_clean in title.lower():
                return 85.0
            if re.search(rf"\b{re.escape(s_clean)}\b", combined_target):
                return 75.0

    # Rapidfuzz token set and partial ratio matching
    if HAS_RAPIDFUZZ:
        token_score = fuzz.token_set_ratio(q, title.lower())
        if token_score >= 70:
            return float(token_score * 0.8)
        partial_score = fuzz.partial_ratio(q, title.lower())
        if partial_score >= 80:
            return float(partial_score * 0.75)
        combined_token = fuzz.token_set_ratio(q, combined_target)
        if combined_token >= 75:
            return float(combined_token * 0.65)

    return 0.0

class SearchService:
    def __init__(self):
        self.config = get_config()
        self.ats_service = get_ats_service()

    def _get_active_companies_and_roles(self) -> tuple:
        """
        Returns (active_companies_set, active_roles_set) of lowercase names
        from Redis keys + DB rows posted in the last 7 days.
        Uses a 30-second in-process cache to avoid repeated full Redis scans.
        """
        import time as _time
        import datetime
        cache = getattr(self, "_active_cache", None)
        if cache and (_time.time() - cache["ts"]) < 30:
            return cache["companies"], cache["roles"]

        active_companies: set = set()
        active_roles: set = set()

        # --- Redis (primary / fastest source) ---
        try:
            client = get_redis_client()
            try:
                get_metrics_service().inc_redis()
            except:
                pass
            keys = client.keys("*|*")
            tz = pytz.timezone("Asia/Kolkata")
            now_ist = datetime.datetime.now(tz)
            
            for k in keys:
                k_str = k.decode("utf-8") if isinstance(k, bytes) else k
                c, r = parse_hash_name(k_str)
                if not c and not r: continue
                
                # Check if this hash has ANY job posted in the last 7 days (168 hours)
                hdata = client.hgetall(k)
                if not hdata: continue
                
                has_active = False
                for field, val_str in hdata.items():
                    try:
                        import json
                        job_data = json.loads(val_str)
                        posted_iso = job_data.get("posted_timestamp_ist") or job_data.get("posted_timestamp_raw") or job_data.get("posted_at")
                        if posted_iso:
                            clean_ts = str(posted_iso).replace(" IST", "").replace("Z", "+00:00").strip()
                            if "T" in clean_ts:
                                dt = datetime.datetime.fromisoformat(clean_ts)
                            else:
                                dt = datetime.datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                            if dt.tzinfo is None:
                                dt = pytz.timezone("Asia/Kolkata").localize(dt)
                            ist_dt = dt.astimezone(tz)
                            if (now_ist - ist_dt).total_seconds() / 3600.0 <= 168:
                                has_active = True
                                break
                    except Exception:
                        pass
                
                if has_active:
                    if c:
                        active_companies.add(c.lower())
                    if r:
                        active_roles.add(r.lower())
        except Exception as e:
            logger.debug(f"Redis active-suggestions query error: {e}")

        # --- DB fallback: last 7 days ---
        try:
            from app.database import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT company FROM jobs WHERE is_active=1 AND datetime(substr(posted_at, 1, 19)) >= datetime('now', '+5 hours', '+30 minutes', '-7 days')"
            )
            for (co,) in cur.fetchall():
                if co:
                    active_companies.add(co.lower())
            cur.execute(
                "SELECT DISTINCT role_category FROM jobs WHERE is_active=1 AND posted_at >= ?",
                (seven_days_ago,)
            )
            for (rc,) in cur.fetchall():
                if rc:
                    active_roles.add(rc.lower())
            conn.close()
        except Exception as e:
            logger.debug(f"DB active-suggestions query skipped: {e}")

        self._active_cache = {"ts": _time.time(), "companies": active_companies, "roles": active_roles}
        return active_companies, active_roles

    def get_suggestions(self, mode: str, query: str, limit: int = 25) -> List[Dict[str, str]]:
        """
        Provides autocomplete suggestions based on verified company names or industry roles.
        Only includes entries that have at least one active job posted in the last 7 days
        (checked against Redis + DB) to minimise zero-result searches.
        Falls back to full list if the data store is empty (cold start / warm-up).
        """
        q = (query or "").strip().lower()
        results = []

        active_companies, active_roles = self._get_active_companies_and_roles()

        if mode == "company":
            all_comps = self.ats_service.get_all_companies()
            client = get_redis_client()
            try:
                try:
                    get_metrics_service().inc_redis()
                except:
                    pass
                keys = client.keys("*|*")
                for k in keys:
                    k_str = k.decode("utf-8") if isinstance(k, bytes) else k
                    c, _ = parse_hash_name(k_str)
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

            # Filter to companies that have live jobs; fall back to full list on cold start
            if active_companies:
                valid_comps = [c for c in all_comps if c.lower() in active_companies]
            else:
                valid_comps = all_comps

            if not q:
                matched = [c for c in prominent if c.lower() in active_companies] if active_companies else list(prominent)
                for ac in valid_comps:
                    if ac not in matched and len(matched) < max(limit, 120):
                        matched.append(ac)
            else:
                matched = [c for c in valid_comps if q in c.lower()]

            for c in matched[:max(limit, 120)]:
                results.append({"type": "company", "value": c, "label": c})

        elif mode == "role":
            matched = []
            for item in FIXED_ROLES:
                r_name = item["role"]
                syns = item["synonyms"]

                # Filter roles to those with active jobs; skip filter on cold start
                if active_roles:
                    all_syns_lower = [r_name.lower()] + [s.lower() for s in syns]
                    has_active = any(
                        role_matches(all_syns_lower, ar) for ar in active_roles
                    )
                    if not has_active:
                        continue

                if not q:
                    matched.append((r_name, ", ".join(syns[:2])))
                elif q in r_name.lower() or any(q in s.lower() for s in syns):
                    matched.append((r_name, ", ".join(syns[:2])))

            for r, sub in matched:
                results.append({"type": "role", "value": r, "label": r, "subtitle": sub})

        return results

    def get_role_synonyms(self, role_name: str) -> List[str]:
        target = role_name.strip().lower()
        if not target:
            return []
        syns_found = set()
        for item in FIXED_ROLES:
            r_lower = item["role"].lower()
            all_s = [r_lower] + [s.lower() for s in item["synonyms"]]
            if target == r_lower or target in all_s:
                syns_found.update(all_s)
                continue
                
            for s in all_s:
                if len(s) < 2:
                    continue
                # Use word boundaries to avoid 'sde' matching 'sdet'
                pattern = rf"\b{re.escape(s)}\b"
                if re.search(pattern, target) or re.search(rf"\b{re.escape(target)}\b", s):
                    syns_found.update(all_s)
                    break

        if syns_found:
            return list(syns_found)
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
        time_filter: Optional[str] = "24h", # "1h", "12h", "24h", "2d", "7d", "all"
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
        active_time_filter = (time_filter or "24h").strip()

        # Step 1: Scan Redis hashes matching company or role

        import time
        from app.services.metrics_service import get_metrics_service
        metrics_svc = get_metrics_service()

        redis_start = time.time()
        matching_hashes = set()
        try:
            get_metrics_service().inc_redis()
        except:
            pass
        all_keys = client.keys("*|*")
        metrics_svc.record_redis_latency((time.time() - redis_start) * 1000)

        if not all_keys:
            from app.services.ingestion_service import get_ingestion_manager
            get_ingestion_manager().seed_initial_jobs()
            try:
                get_metrics_service().inc_redis()
            except:
                pass
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
                                    try:
                                        get_metrics_service().inc_redis()
                                    except:
                                        pass
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
                    if role_matches(all_syns, r):
                        matching_hashes.add(k)

        elif search_type == "role":
            synonyms = self.get_role_synonyms(query_term)
            all_syns = list(set(synonyms + [query_lower]))
            for k in all_keys:
                c, r = parse_hash_name(k)
                if role_matches(all_syns, r):
                    matching_hashes.add(k)
                elif HAS_RAPIDFUZZ and fuzz.token_sort_ratio(query_lower, r.lower()) >= 85:
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
            all_syns = list(set(synonyms + [query_lower]))
            for k in all_keys:
                c, r = parse_hash_name(k)
                combined = f"{c} {r}".lower()
                if role_matches(all_syns, combined) or (tokens and all(t in combined for t in tokens)):
                    matching_hashes.add(k)
                elif HAS_RAPIDFUZZ and (fuzz.token_sort_ratio(query_lower, r.lower()) >= 85 or fuzz.token_sort_ratio(query_lower, combined) >= 85):
                    matching_hashes.add(k)
        else:
            matching_hashes = set(all_keys)

        # Step 2: Fetch all jobs from matching Redis hashes
        raw_jobs = []
        for h_key in matching_hashes:
            try:
                get_metrics_service().inc_redis()
            except:
                pass
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
            loc = job.get("location", "")
            wp = job.get("workplace_type", "")
            apply_link = (job.get("apply_link") or "").strip()

            # Defense-in-depth: Strict India & Remote validation
            if not apply_link or not apply_link.startswith("http"):
                continue
            if not is_india_location(loc, workplace_type=wp):
                continue

            # Ensure location string is clean
            clean_loc = extract_india_location(loc)
            if clean_loc:
                job["location"] = clean_loc

            r_name = job.get("role_name", "")
            title = job.get("title", "")
            c_name = job.get("company_name", "")

            # If search_type was role and query was provided, verify individual job satisfies role or fallback company
            if search_type == "role" and query_term:
                synonyms = self.get_role_synonyms(query_term)
                all_syns = list(set(synonyms + [query_lower]))
                matches_role = role_matches(all_syns, r_name) or role_matches(all_syns, title) or any(s in r_name.lower() or s in title.lower() for s in all_syns)
                if not matches_role:
                    rel_score = calculate_semantic_relevance(query_term, title, r_name, job.get("tags"), all_syns)
                    if rel_score >= 60.0:
                        matches_role = True
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

        # Step 4: Strict Deduplication by normalized apply_link and (company, title, location)
        seen_urls = set()
        seen_tuples = set()
        deduped_jobs = []
        for job in filtered_jobs:
            link = (job.get("apply_link") or "").strip().rstrip("/").lower()
            comp = (job.get("company_name") or "").strip().lower()
            t_name = (job.get("role_name") or job.get("title") or "").strip().lower()
            l_name = (job.get("location") or "").strip().lower()

            if link and link in seen_urls:
                continue
            tup_key = (comp, t_name, l_name)
            if tup_key in seen_tuples:
                continue

            if link:
                seen_urls.add(link)
            seen_tuples.add(tup_key)
            deduped_jobs.append(job)

        filtered_jobs = deduped_jobs

        # Step 5: Sort by Decreasing Timestamp Order (newest first in IST) with Semantic Relevance
        def sort_key(j: Dict[str, Any]) -> float:
            rel_boost = 0.0
            if query_term:
                syns = self.get_role_synonyms(query_term)
                score = calculate_semantic_relevance(query_term, j.get("title", ""), j.get("role_name", ""), j.get("tags"), syns)
                if score >= 75.0:
                    rel_boost = score * 100000.0

            raw_epoch = j.get("posted_epoch")
            if raw_epoch is not None:
                try:
                    return float(raw_epoch) + rel_boost
                except Exception:
                    pass
            ts = j.get("posted_timestamp_raw") or j.get("posted_timestamp_ist") or j.get("posted_at")
            if not ts:
                return rel_boost
            try:
                clean_ts = str(ts).replace(" IST", "").replace("Z", "+00:00").strip()
                if "T" in clean_ts:
                    dt = datetime.datetime.fromisoformat(clean_ts)
                else:
                    dt = datetime.datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                if dt.tzinfo is None:
                    dt = pytz.timezone("Asia/Kolkata").localize(dt)
                return dt.astimezone(IST_TZ).timestamp() + rel_boost
            except Exception:
                return rel_boost

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

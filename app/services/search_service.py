import re
import json
import logging
import datetime
import pytz
from typing import Dict, Any, List, Optional, Set, Tuple

from app.config import get_config
from app.redis_client import get_redis_client, parse_hash_name, get_hashes_by_tag
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
    },
    {
        "role": "Intern / Trainee",
        "synonyms": [
            "intern", "internship", "trainee", "graduate trainee", "summer intern", 
            "engineering intern", "software intern", "sde intern", "product intern", 
            "research intern", "apprentice", "apprenticeship"
        ]
    },
    {
        "role": "Blockchain / Web3 Engineer",
        "synonyms": [
            "blockchain engineer", "web3 engineer", "smart contract developer", "solidity developer", 
            "rust blockchain", "ethereum developer", "web3 developer", "blockchain developer", 
            "crypto engineer", "defi engineer", "blockchain"
        ]
    },
    {
        "role": "MLOps Engineer",
        "synonyms": [
            "mlops engineer", "mlops", "machine learning operations", "ml platform engineer", 
            "ai platform engineer", "model deployment engineer", "ml infrastructure engineer"
        ]
    },
    {
        "role": "NLP / LLM Engineer",
        "synonyms": [
            "nlp engineer", "llm engineer", "natural language processing", "prompt engineer", 
            "ai prompt engineer", "large language model", "llm developer", "nlp scientist", 
            "genai engineer", "conversational ai"
        ]
    },
    {
        "role": "Computer Vision Engineer",
        "synonyms": [
            "computer vision engineer", "computer vision", "cv engineer", "image processing engineer", 
            "perception engineer", "deep learning vision", "vision ai engineer"
        ]
    },
    {
        "role": "Platform / Infrastructure Engineer",
        "synonyms": [
            "platform engineer", "infrastructure engineer", "cloud platform engineer", 
            "core platform developer", "systems infrastructure", "developer platform", "developer tooling"
        ]
    },
    {
        "role": "Embedded Software Engineer",
        "synonyms": [
            "embedded software engineer", "embedded software", "embedded systems developer", 
            "embedded c++", "embedded c", "iot software engineer", "embedded linux engineer"
        ]
    },
    {
        "role": "Firmware Engineer",
        "synonyms": [
            "firmware engineer", "firmware developer", "microcontroller developer", 
            "bsp engineer", "board support package", "rtos engineer", "device driver developer", "firmware"
        ]
    },
    {
        "role": "Hardware Engineer",
        "synonyms": [
            "hardware engineer", "hardware design engineer", "electronics engineer", 
            "pcb design engineer", "fpga engineer", "vlsi design engineer", "asic engineer", "hardware"
        ]
    },
    {
        "role": "Database Administrator (DBA)",
        "synonyms": [
            "database administrator", "dba", "sql dba", "oracle dba", "postgres dba", 
            "mongodb dba", "database engineer", "data architect dba", "db admin"
        ]
    },
    {
        "role": "Network Engineer",
        "synonyms": [
            "network engineer", "network administrator", "ccna", "ccnp", "cisco network engineer", 
            "network security engineer", "telecom engineer", "infrastructure network", "network specialist"
        ]
    },
    {
        "role": "Business Analyst",
        "synonyms": [
            "business analyst", "technical business analyst", "functional analyst", 
            "it business analyst", "senior business analyst", "lead business analyst", "business analysis"
        ]
    },
    {
        "role": "Scrum Master / Agile Coach",
        "synonyms": [
            "scrum master", "agile coach", "certified scrum master", "csm", 
            "agile project manager", "kanban coach", "agile facilitator", "scrum lead"
        ]
    },
    {
        "role": "Growth Marketing Specialist",
        "synonyms": [
            "growth marketing specialist", "growth marketer", "growth hacker", "acquisition marketer", 
            "lifecycle marketer", "growth marketing manager", "demand generation", "growth lead marketing"
        ]
    },
    {
        "role": "Technical Writer",
        "synonyms": [
            "technical writer", "tech writer", "api documenter", "documentation engineer", 
            "technical documentation", "content developer tech", "sdk documenter"
        ]
    },
    {
        "role": "IT Support Specialist",
        "synonyms": [
            "it support specialist", "it support engineer", "it technician", "desktop support engineer", 
            "help desk technician", "service desk analyst", "workstation support", "it desk engineer"
        ]
    },
    {
        "role": "Salesforce Developer",
        "synonyms": [
            "salesforce developer", "salesforce", "salesforce administrator", "salesforce engineer", 
            "apex developer", "salesforce architect", "lightning developer", "sfdc developer"
        ]
    },
    {
        "role": "Game Developer",
        "synonyms": [
            "game developer", "unity developer", "unreal engine developer", "game programmer", 
            "game designer", "gameplay engineer", "3d game developer", "unreal developer", "unity 3d"
        ]
    },
    {
        "role": "Release / Build Engineer",
        "synonyms": [
            "release engineer", "build engineer", "release manager", "ci cd engineer", 
            "devops release", "deployment engineer", "configuration manager", "build and release"
        ]
    },
    {
        "role": "Information Security Analyst",
        "synonyms": [
            "information security analyst", "infosec analyst", "security analyst", "soc analyst", 
            "cyber defense analyst", "threat intelligence analyst", "incident response analyst", "secops analyst"
        ]
    },
    {
        "role": "Fintech / Algorithmic Trading Engineer",
        "synonyms": [
            "fintech engineer", "algorithmic trading engineer", "quant developer", "quantitative developer", 
            "trading systems engineer", "low latency engineer", "hft developer", "financial software engineer",
            "fintech", "trading", "quant", "algorithmic trading", "hft"
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

def company_matches(query: str, company_name: Optional[str]) -> bool:
    if not query or not company_name:
        return False
    q = query.strip().lower()
    c = company_name.strip().lower()
    if q == c:
        return True
    pattern = rf"\b{re.escape(q)}\b"
    return bool(re.search(pattern, c))

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

    # Multi-word phrase: ensure each word appears with word boundaries
    q_words = [w for w in re.split(r"\s+", q) if len(w) > 1]
    if len(q_words) > 1 and all(re.search(rf"\b{re.escape(w)}\b", title.lower()) for w in q_words):
        return 90.0

    # Synonym check with word boundaries
    if synonyms:
        for syn in synonyms:
            s_clean = syn.strip().lower()
            if not s_clean:
                continue
            if re.search(rf"\b{re.escape(s_clean)}\b", title.lower()):
                return 88.0
            syn_words = [w for w in re.split(r"\s+", s_clean) if len(w) > 1]
            if len(syn_words) > 1 and all(re.search(rf"\b{re.escape(w)}\b", title.lower()) for w in syn_words):
                return 85.0
            if re.search(rf"\b{re.escape(s_clean)}\b", combined_target):
                return 75.0

    # Direct tag match check (gives high boost for matching skills/keywords)
    if tags:
        for t in tags:
            t_lower = t.strip().lower()
            if q == t_lower:
                return 82.0
            if re.search(rf"\b{re.escape(q)}\b", t_lower):
                return 80.0

    # Rapidfuzz token set matching with word boundary verification
    if HAS_RAPIDFUZZ:
        token_score = fuzz.token_set_ratio(q, title.lower())
        if token_score >= 80:
            # Verify that at least one query token matches as a distinct word in title
            q_tokens = [t for t in re.split(r"\s+", q) if len(t) > 2]
            if not q_tokens or any(re.search(rf"\b{re.escape(t)}\b", title.lower()) for t in q_tokens):
                return float(token_score * 0.8)
        combined_token = fuzz.token_set_ratio(q, combined_target)
        if combined_token >= 85:
            q_tokens = [t for t in re.split(r"\s+", q) if len(t) > 2]
            if not q_tokens or any(re.search(rf"\b{re.escape(t)}\b", combined_target) for t in q_tokens):
                return float(combined_token * 0.65)

    return 0.0

class SearchService:
    def __init__(self):
        self.config = get_config()
        self.ats_service = get_ats_service()

    def _get_active_companies_and_roles(self) -> tuple:
        """
        Returns (active_companies_set, active_roles_set) of lowercase names
        from database rows and active keys with an in-process 1-hour cache
        to eliminate blocking Redis scans.
        """
        import time as _time
        cache = getattr(self, "_active_cache", None)
        if cache and (_time.time() - cache["ts"]) < 3600:
            return cache["companies"], cache["roles"]

        active_companies: set = set()
        active_roles: set = set()

        # Fast indexed SQLite fetch (30ms)
        try:
            from app.database import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT company FROM jobs WHERE is_active = 1 AND company IS NOT NULL AND company != ''"
            )
            for (co,) in cur.fetchall():
                if co:
                    active_companies.add(co.strip().lower())
            cur.execute(
                "SELECT DISTINCT role_category FROM jobs WHERE is_active = 1 AND role_category IS NOT NULL AND role_category != ''"
            )
            for (rc,) in cur.fetchall():
                if rc:
                    active_roles.add(rc.strip().lower())
            conn.close()
        except Exception as e:
            logger.debug(f"DB active-suggestions query error: {e}")

        # Fallback: extract company & role directly from Redis key names without calling hgetall
        if not active_companies or not active_roles:
            try:
                client = get_redis_client()
                for k in client.scan_iter(match="*|*", count=1000):
                    if k.startswith("tag_idx:") or k.startswith("cg:"):
                        continue
                    k_str = k.decode("utf-8") if isinstance(k, bytes) else k
                    c, r = parse_hash_name(k_str)
                    if c:
                        active_companies.add(c.strip().lower())
                    if r:
                        active_roles.add(r.strip().lower())
            except Exception as e:
                logger.debug(f"Redis active-suggestions query error: {e}")

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

        from app.database import is_redis_kill_switch_active, get_db_suggestions
        if is_redis_kill_switch_active():
            return get_db_suggestions(mode, query, limit=limit)

        active_companies, active_roles = self._get_active_companies_and_roles()

        if mode == "company":
            all_comps = self.ats_service.get_all_companies()
            client = get_redis_client()
            try:
                try:
                    get_metrics_service().inc_redis()
                except:
                    pass
                keys = [k for k in client.scan_iter(match="*|*", count=1000) if not k.startswith("tag_idx:") and not k.startswith("cg:")]
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

        # 1. Exact match with a role category or its exact synonym
        for item in FIXED_ROLES:
            r_lower = item["role"].lower()
            all_s = [r_lower] + [s.lower() for s in item["synonyms"]]
            if target == r_lower or target in all_s:
                return all_s

        # 2. Phrase matching: check if any multi-word or distinct synonym appears in target
        syns_found = set()
        for item in FIXED_ROLES:
            r_lower = item["role"].lower()
            all_s = [r_lower] + [s.lower() for s in item["synonyms"]]
            for s in all_s:
                if len(s) < 2:
                    continue
                pattern = rf"\b{re.escape(s)}\b"
                if re.search(pattern, target):
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
        time_filter: Optional[str] = "all", # "1h", "12h", "24h", "2d", "7d", "all"
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Executes search strictly based on Redis hashes {company_name}|{role_name} and tag secondary index.
        Applies filter options, descending timestamp sort, and page 10 pagination.
        """
        query_term = (custom_input if custom_input else search_term or "").strip()
        if (
            query_term.lower() in ("all roles", "all companies", "all", "all positions", "all jobs", "any", "all category", "all categories") or
            bool(re.match(r"^all\s*(roles?|companies|jobs?|positions?)?$", query_term.lower()))
        ):
            query_term = ""
        query_lower = query_term.lower()
        active_time_filter = (time_filter or "all").strip()

        # If searching without specific query and role_filter is all/unspecified,
        # ensure legacy 7d filter is upgraded to 'all' so Redis and DB full directory counts match 1:1
        is_all_role_filter = not role_filter or role_filter.strip().lower() in ("all", "all roles", "all role", "all categories", "all category", "")
        if not query_term and is_all_role_filter and active_time_filter in ("7d", "7 days", "anytime (7 days)"):
            active_time_filter = "all"

        import time
        from app.services.metrics_service import get_metrics_service
        from app.database import is_redis_kill_switch_active, search_jobs_direct_db, get_db_candidates_for_search
        metrics_svc = get_metrics_service()
        raw_jobs = []

        use_direct_db = is_redis_kill_switch_active()

        if use_direct_db or not query_term:
            db_start = time.time()
            syns = self.get_role_synonyms(role_filter or query_term) if (role_filter or search_type == "role") else []
            data = search_jobs_direct_db(
                search_type=search_type,
                query_term=query_term,
                role_synonyms=syns,
                location_filter=location_filter,
                role_filter=role_filter,
                employment_type=employment_type,
                workplace_type=workplace_type,
                experience_level=experience_level,
                time_filter=active_time_filter,
                page=page,
                page_size=page_size
            )
            metrics_svc.record_db_latency((time.time() - db_start) * 1000)
            return data

        try:
            client = get_redis_client()
            redis_start = time.time()
            matching_hashes = set()
            try:
                metrics_svc.inc_redis()
            except:
                pass

            now_ts = time.time()
            cached_keys = getattr(self, "_cached_all_keys", None)
            cached_ts = getattr(self, "_cached_keys_ts", 0)
            if not cached_keys or (now_ts - cached_ts > 30):
                all_keys = [k for k in client.scan_iter(match="*|*", count=1000) if not k.startswith("tag_idx:") and not k.startswith("cg:")]
                self._cached_all_keys = all_keys
                self._cached_keys_ts = now_ts
            else:
                all_keys = cached_keys

            metrics_svc.record_redis_latency((time.time() - redis_start) * 1000)

            if not all_keys:
                from app.services.ingestion_service import get_ingestion_manager
                get_ingestion_manager().seed_initial_jobs()
                try:
                    metrics_svc.inc_redis()
                except:
                    pass
                all_keys = [k for k in client.scan_iter(match="*|*", count=1000) if not k.startswith("tag_idx:") and not k.startswith("cg:")]
                self._cached_all_keys = all_keys
                self._cached_keys_ts = time.time()

            if search_type == "company":
                matching_hashes.update(get_hashes_by_tag(query_lower))
                for k in all_keys:
                    c, r = parse_hash_name(k)
                    if company_matches(query_lower, c):
                        matching_hashes.add(k)

                # If no cached jobs in Redis, check if company is in our master ATS directory and fetch live
                if not matching_hashes:
                    matching_eps = [
                        ep for ep in self.ats_service.endpoints
                        if company_matches(query_lower, ep.company_name)
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
                                            metrics_svc.inc_redis()
                                        except:
                                            pass
                                        all_keys = [k for k in client.scan_iter(match="*|*", count=1000) if not k.startswith("tag_idx:") and not k.startswith("cg:")]
                                        self._cached_all_keys = all_keys
                                        self._cached_keys_ts = time.time()
                                        for k in all_keys:
                                            c, r = parse_hash_name(k)
                                            if company_matches(query_lower, c):
                                                matching_hashes.add(k)
                        except Exception as e:
                            logger.debug(f"On-demand fetch failed for {target_ep.company_name}: {e}")

                # Smart fallback: only if query is generic and neither Redis nor ATS had this company
                if not matching_hashes and len(query_term) > 3:
                    synonyms = self.get_role_synonyms(query_term)
                    all_syns = list(set(synonyms + [query_lower]))
                    for s in all_syns:
                        matching_hashes.update(get_hashes_by_tag(s))
                    for k in all_keys:
                        c, r = parse_hash_name(k)
                        if role_matches(all_syns, r):
                            matching_hashes.add(k)

            elif search_type == "role":
                synonyms = self.get_role_synonyms(query_term)
                all_syns = list(set(synonyms + [query_lower]))

                # 1. Fast secondary tag index lookup for query and all synonyms
                for s in all_syns:
                    matching_hashes.update(get_hashes_by_tag(s))

                # 2. Extract significant tokens from query
                tokens = [t for t in query_lower.split() if t not in ("jobs", "job", "careers", "career", "hiring", "openings", "positions", "in", "at", "for") and len(t) > 2]
                for t in tokens:
                    matching_hashes.update(get_hashes_by_tag(t))

                # 3. Hash name matching with word boundary verification
                for k in all_keys:
                    c, r = parse_hash_name(k)
                    combined = f"{c} {r}".lower()
                    if role_matches(all_syns, combined) or (tokens and all(role_matches([t], combined) for t in tokens)):
                        matching_hashes.add(k)
                    elif HAS_RAPIDFUZZ and (fuzz.token_sort_ratio(query_lower, r.lower()) >= 65 or fuzz.token_sort_ratio(query_lower, combined) >= 85):
                        if any(role_matches([t], combined) for t in tokens):
                            matching_hashes.add(k)
            else:
                matching_hashes = set(all_keys)

            # Fetch all jobs from matching Redis hashes in high-speed batch pipeline
            valid_keys = [k for k in matching_hashes if not k.startswith("tag_idx:") and not k.startswith("cg:")]
            if len(valid_keys) > 500:
                # If too many matching hashes, use indexed DB search to prevent Redis pipeline stalls
                db_start = time.time()
                syns = self.get_role_synonyms(role_filter or query_term) if (role_filter or search_type == "role") else []
                data = search_jobs_direct_db(
                    search_type=search_type,
                    query_term=query_term,
                    role_synonyms=syns,
                    location_filter=location_filter,
                    role_filter=role_filter,
                    employment_type=employment_type,
                    workplace_type=workplace_type,
                    experience_level=experience_level,
                    time_filter=active_time_filter,
                    page=page,
                    page_size=page_size
                )
                metrics_svc.record_db_latency((time.time() - db_start) * 1000)
                return data

            if valid_keys:
                try:
                    metrics_svc.inc_redis()
                except:
                    pass
                pipe = client.pipeline(transaction=False)
                for h_key in valid_keys:
                    pipe.hgetall(h_key)
                try:
                    batch_results = pipe.execute()
                    for hdata in batch_results:
                        if not hdata or not isinstance(hdata, dict):
                            continue
                        for ts_key, val_str in hdata.items():
                            try:
                                jdata = json.loads(val_str)
                                jdata["tags"] = sanitize_tags(jdata.get("tags"))
                                raw_jobs.append(jdata)
                            except Exception:
                                pass
                except Exception as e:
                    logger.warning(f"Error in Redis batch pipeline for matching hashes: {e}")
        except Exception as redis_err:
            logger.warning(f"Redis search encountered error: {redis_err}. Seamlessly falling back to direct SQLite DB query.")
            db_start = time.time()
            syns = self.get_role_synonyms(role_filter or query_term) if (role_filter or search_type == "role") else []
            data = search_jobs_direct_db(
                search_type=search_type,
                query_term=query_term,
                role_synonyms=syns,
                location_filter=location_filter,
                role_filter=role_filter,
                employment_type=employment_type,
                workplace_type=workplace_type,
                experience_level=experience_level,
                time_filter=active_time_filter,
                page=page,
                page_size=page_size
            )
            metrics_svc.record_db_latency((time.time() - db_start) * 1000)
            return data

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

            # If query was provided, verify individual job satisfies query semantics or company match
            if query_term:
                c_matches = company_matches(query_term, c_name)
                job_tags = job.get("tags") or []
                synonyms = self.get_role_synonyms(query_term)
                all_syns = list(set(synonyms + [query_lower]))

                if search_type == "company":
                    if not c_matches:
                        rel_score = calculate_semantic_relevance(query_term, title, r_name, job_tags, all_syns)
                        if rel_score < 40.0:
                            continue
                else:
                    # search_type in ("role", "other_role", "other_company", "other", "custom")
                    matches_role = role_matches(all_syns, r_name) or role_matches(all_syns, title)
                    if not matches_role:
                        if any(query_lower == str(t).strip().lower() or re.search(rf"\b{re.escape(query_lower)}\b", str(t).lower()) for t in job_tags):
                            matches_role = True
                        else:
                            rel_score = calculate_semantic_relevance(query_term, title, r_name, job_tags, all_syns)
                            if rel_score >= 40.0:
                                matches_role = True
                    if not matches_role and not c_matches:
                        continue

            # Location filter
            if location_filter and location_filter.strip().lower() not in ("all", "all locations", "all location", ""):
                loc = job.get("location", "").lower()
                wp = job.get("workplace_type", "").lower()
                lf = location_filter.strip().lower()
                if lf in ("india", "pan india", "anywhere in india"):
                    pass
                elif lf == "remote":
                    if "remote" not in loc and "remote" not in wp:
                        continue
                elif lf not in loc:
                    continue

            # Role filter
            if role_filter and role_filter.strip().lower() not in ("all", "all roles", "all role", "all categories", "all category", ""):
                r_syns = self.get_role_synonyms(role_filter)
                rf_lower = role_filter.lower()
                all_rf_syns = list(set(r_syns + [rf_lower]))
                if not (role_matches(all_rf_syns, r_name) or role_matches(all_rf_syns, title)):
                    continue

            # Employment type filter
            if employment_type and employment_type.lower() != "all":
                emp = job.get("employment_type", "").lower()
                target_emp = employment_type.lower()
                title_lower = title.lower()
                if "intern" in target_emp:
                    is_intern = (
                        bool(re.search(r"\bintern(ship)?s?\b", emp)) or
                        bool(re.search(r"\bintern(ship)?s?\b", title_lower)) or
                        bool(re.search(r"\btrainee\b", title_lower)) or
                        bool(re.search(r"\bapprentice(ship)?\b", title_lower))
                    )
                    if not is_intern:
                        continue
                elif target_emp not in emp:
                    continue

            # Workplace filter (Strict: Remote jobs must strictly be Remote, never in-office)
            if workplace_type and workplace_type.lower() != "all":
                wp = job.get("workplace_type", "").strip().lower()
                loc = job.get("location", "").strip().lower()
                target_wp = workplace_type.strip().lower()
                if target_wp == "remote":
                    is_remote = (wp == "remote") or ("remote" in loc)
                    if not is_remote:
                        continue
                elif target_wp in ("in office", "in-office", "office"):
                    if wp not in ("in office", "office") and "remote" in wp:
                        continue
                elif target_wp == "hybrid":
                    if "hybrid" not in wp:
                        continue

            # Experience level filter
            if experience_level and experience_level.lower() != "all":
                exp = job.get("experience_level", "").lower()
                title_lower = title.lower()
                target_exp = experience_level.lower()
                if "entry" in target_exp:
                    is_entry = (
                        "entry" in exp or
                        bool(re.search(r"\bintern(ship)?s?\b", title_lower)) or
                        bool(re.search(r"\b(fresher|trainee|junior|jr\.?)\b", title_lower))
                    )
                    if not is_entry:
                        continue
                elif "senior" in target_exp:
                    is_senior = (
                        "senior" in exp or
                        bool(re.search(r"\b(sr\.?|lead|principal|staff|architect|director)\b", title_lower))
                    )
                    if not is_senior:
                        continue
                elif target_exp not in exp:
                    continue

            # Time filter ("1h", "12h", "24h", "2d", "7d", "all")
            if active_time_filter and active_time_filter.lower() not in ("all", "anytime", "anytime (7 days)", "all time", "none", ""):
                hours_map = {
                    "1h": 1, "1 hour": 1,
                    "12h": 12, "12 hours": 12,
                    "24h": 24, "24 hours": 24, "1d": 24, "1 day": 24,
                    "2d": 48, "2 days": 48, "48h": 48,
                    "7d": 168, "7 days": 168, "1w": 168, "1 week": 168,
                    "30d": 720, "30 days": 720, "1m": 720, "1 month": 720
                }
                max_hours = hours_map.get(active_time_filter.lower(), 168)
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

        # Step 4: Strict Deduplication by normalized apply_link (fallback to company+title+location if no URL)
        seen_urls = set()
        seen_tuples = set()
        deduped_jobs = []
        for job in filtered_jobs:
            link = (job.get("apply_link") or job.get("apply_url") or "").strip().rstrip("/").lower()
            comp = (job.get("company_name") or "").strip().lower()
            t_name = (job.get("role_name") or job.get("title") or "").strip().lower()
            l_name = (job.get("location") or "").strip().lower()

            if link:
                if link in seen_urls:
                    continue
                seen_urls.add(link)
            else:
                tup_key = (comp, t_name, l_name)
                if tup_key in seen_tuples:
                    continue
                seen_tuples.add(tup_key)

            deduped_jobs.append(job)

        filtered_jobs = deduped_jobs

        # Step 5: Sort by Decreasing Timestamp Order (newest first in IST) with Semantic Relevance
        def sort_key(j: Dict[str, Any]) -> float:
            rel_boost = 0.0
            if query_term:
                syns = self.get_role_synonyms(query_term)
                score = calculate_semantic_relevance(query_term, j.get("title", ""), j.get("role_name", ""), j.get("tags"), syns)
                # Any score applies a boost, effectively making relevance the primary sort key
                # A score difference of 1.0 = 1,000,000 seconds = ~11.5 days of boost
                rel_boost = score * 1000000.0

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

        # Conceal tags from the serialized job objects to strictly prevent exposing keywords to the frontend / client devtools
        clean_results = []
        for j in paginated_results:
            job_copy = dict(j)
            job_copy["tags"] = []  # Strictly conceal internal search tags
            clean_results.append(job_copy)

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
            "results": clean_results
        }

_search_service: Optional[SearchService] = None

def get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

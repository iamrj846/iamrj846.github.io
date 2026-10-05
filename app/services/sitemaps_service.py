import re
import io
import gzip
import datetime
import hashlib
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
import pytz

from app.services.ats_service import (
    classify_job_canonical_role,
    normalize_employment_type,
    normalize_experience_level,
    generate_job_tags,
    parse_date_to_ist,
    IST_TZ,
)

logger = logging.getLogger("sitemaps_service")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CorporateGuild/1.0"
)

# Canonical list of sitemaps provided by user
NAUKRI_SITEMAP_URLS = [
    "https://www.naukri.com/sitemap/jobDescPagesPune.xml",
    "https://www.naukri.com/sitemap/jobDescPagesAhmedabad.xml",
    "https://www.naukri.com/sitemap/jobDescPagesKolkata.xml",
    "https://www.naukri.com/sitemap/jobDescPagesMumbai-1.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesMumbai-2.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesNoida.xml",
    "https://www.naukri.com/sitemap/jobDescPagesDelhi.xml",
    "https://www.naukri.com/sitemap/jobDescPagesBangalore.xml",
    "https://www.naukri.com/sitemap/jobDescPagesChennai.xml",
    "https://www.naukri.com/sitemap/jobDescPagesHyderabad.xml",
    "https://www.naukri.com/sitemap/jobDescPagesOtherCities-1.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesOtherCities-2.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesOtherCities-3.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesOtherCities-4.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesOtherCities-5.xml.gz",
    "https://www.naukri.com/sitemap/jobDescPagesOtherCities-6.xml.gz",
]

INTERNSHALA_SITEMAP_URLS = [
    "https://internshala.com/sitemap-internships.xml"
]

FOUNDIT_SITEMAP_URLS = [
    "https://www.foundit.in/xmlsitemap/todays-jobs-sitemap.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap0.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap1.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap2.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap3.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap4.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap5.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap6.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap7.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap8.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap9.xml.gz",
    "https://www.foundit.in/xmlsitemap/active-jobs-sitemap10.xml.gz",
]

KNOWN_INDIAN_CITIES = {
    "pune", "bangalore", "bengaluru", "mumbai", "delhi", "noida", "gurugram", "gurgaon",
    "hyderabad", "chennai", "kolkata", "ahmedabad", "kochi", "cochin", "chandigarh",
    "mohali", "panchkula", "nagpur", "indore", "jaipur", "surat", "vadodara", "baroda",
    "visakhapatnam", "vizag", "bhopal", "lucknow", "patna", "ludhiana", "agra", "nashik",
    "rajkot", "varanasi", "navi-mumbai", "thane", "ghaziabad", "faridabad", "dehradun",
    "remote", "yerwada", "yerawada", "hinjewadi", "bhosari", "whitefield", "secunderabad",
    "telangana", "karnataka", "maharashtra", "india", "rural"
}

COMMON_TITLE_NOUNS = {
    "engineer", "developer", "manager", "lead", "architect", "specialist",
    "analyst", "consultant", "designer", "executive", "associate", "officer",
    "intern", "internship", "technician", "director", "specialists", "coordinator",
    "supervisor", "scientist", "scientists", "tester", "programmer", "expert",
    "administrator", "representative", "professional", "accountant", "head", "practitioner"
}


def split_title_and_company(rem: List[str]) -> (str, str):
    if not rem:
        return "Opportunity", "Enterprise"
    split_idx = -1
    for i in range(len(rem) - 1, 0, -1):
        if rem[i - 1].lower() in COMMON_TITLE_NOUNS:
            split_idx = i
            break
    if split_idx > 0:
        title = " ".join(rem[:split_idx]).replace("amp", "&").title()
        company = " ".join(rem[split_idx:]).title()
        return title, company
    if len(rem) >= 3:
        return " ".join(rem[:-2]).title(), " ".join(rem[-2:]).title()
    elif len(rem) >= 2:
        return rem[0].title(), " ".join(rem[1:]).title()
    return " ".join(rem).title(), "Enterprise"



async def download_sitemap_xml(
    url: str,
    client: Optional[httpx.AsyncClient] = None,
    timeout_seconds: float = 30.0
) -> Optional[str]:
    """Downloads XML content from URL, decompressing gz if compressed."""
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        if client is not None:
            resp = await client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as local_client:
                resp = await local_client.get(url, headers=headers)

        if resp.status_code != 200:
            logger.warning(f"Sitemap {url} returned HTTP {resp.status_code}")
            return None

        content_bytes = resp.content
        if not content_bytes:
            return None

        # Check if gzip compressed (by .gz extension or magic bytes 1f 8b)
        if url.endswith(".gz") or content_bytes.startswith(b"\x1f\x8b"):
            with gzip.GzipFile(fileobj=io.BytesIO(content_bytes)) as gz:
                decompressed = gz.read()
            return decompressed.decode("utf-8", errors="replace")
        else:
            return content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Error downloading sitemap {url}: {e}")
        return None


def parse_naukri_url(url: str, cutoff_date: datetime.date) -> Optional[Dict[str, Any]]:
    """Extracts job attributes and verifies the 14-day cutoff from Naukri URL."""
    clean = re.sub(r"^https?://[^/]+/job-listings-", "", url)
    # Match experience range and DDMMYY date in the trailing numeric ID
    m = re.search(r"-(?:(\d+)-to-(\d+)-years|(\d+)-years)-(\d{2})(\d{2})(\d{2})\d{4,8}$", clean)
    if not m:
        return None

    dd, mm, yy = int(m.group(4)), int(m.group(5)), int(m.group(6))
    try:
        posted_date = datetime.date(2000 + yy, mm, dd)
    except Exception:
        return None

    if posted_date < cutoff_date:
        return None

    exp_min = int(m.group(1) or m.group(3) or 0)
    exp_max = int(m.group(2) or exp_min)
    exp_lvl = "Entry level" if exp_min <= 2 else ("Senior" if exp_min >= 5 else "Mid level")

    middle = clean[:m.start()]
    tokens = middle.split("-")

    loc_tokens = []
    idx = len(tokens) - 1
    while idx >= 0:
        t = tokens[idx].lower()
        if t in KNOWN_INDIAN_CITIES:
            loc_tokens.insert(0, tokens[idx])
            idx -= 1
        else:
            break

    loc_str = " ".join(loc_tokens).title() if loc_tokens else "India"
    rem = tokens[:idx + 1]
    if not rem:
        return None

    title, company = split_title_and_company(rem)

    # Workplace & employment normalization
    wp = "Remote" if "remote" in url.lower() or "work-from-home" in url.lower() else "In office"
    emp_type = "Full time"

    # Deterministic job id
    url_hash = hashlib.sha256(url.lower().rstrip("/").encode("utf-8")).hexdigest()[:24]
    job_id = f"job_{url_hash}"

    p_time_str = f"{posted_date.strftime('%Y-%m-%d')} 09:00:00 IST"
    role_category = classify_job_canonical_role(title)
    tags = generate_job_tags(
        title=title,
        company=company,
        location=loc_str,
        role_category=role_category,
        workplace_type=wp,
        experience_level=exp_lvl,
        employment_type=emp_type,
        raw_text=f"Naukri {title} {company}"
    )

    return {
        "id": job_id,
        "company_name": company,
        "role_name": title,
        "title": title,
        "role_category": role_category,
        "location": loc_str,
        "workplace_type": wp,
        "experience_level": exp_lvl,
        "employment_type": emp_type,
        "apply_link": url,
        "apply_url": url,
        "salary_range": "Competitive Market CTC",
        "posted_timestamp_ist": p_time_str,
        "posted_timestamp_raw": f"{posted_date.isoformat()}T09:00:00+05:30",
        "relative_time_ist": parse_date_to_ist(p_time_str).rel_time,
        "time_derived": 1,
        "tags": tags,
        "skills": [],
        "description": f"Verified position at {company}. Apply directly on official Naukri job posting portal.",
        "ats_platform": "Naukri",
        "source": "Naukri",
        "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
    }


def parse_internshala_url(url: str, lastmod_str: str, cutoff_dt: datetime.datetime) -> Optional[Dict[str, Any]]:
    """Extracts internship attributes and verifies the 14-day cutoff from Internshala URL."""
    if not lastmod_str:
        return None

    try:
        dt = datetime.datetime.fromisoformat(lastmod_str)
        if dt.tzinfo is None:
            dt = IST_TZ.localize(dt)
    except Exception:
        return None

    if dt < cutoff_dt:
        return None

    clean = re.sub(r"^https?://[^/]+/internship/detail/", "", url)

    # Extract company from -at-{company}{id}
    m = re.search(r"-at-([a-zA-Z0-9\-_]+)$", clean)
    if m:
        comp_raw = m.group(1)
        comp_clean = re.sub(r"\d+$", "", comp_raw).replace("-", " ").strip().title()
        left = clean[:m.start()]
    else:
        comp_clean = "Enterprise"
        left = clean

    # Extract location from -in-{location}
    m_loc = re.search(r"-in-([a-zA-Z0-9\-_]+)$", left)
    if m_loc:
        loc_clean = m_loc.group(1).replace("-", " ").strip().title()
        role_raw = left[:m_loc.start()]
    else:
        loc_clean = "Remote" if "work-from-home" in left else "India"
        role_raw = left

    role_clean = re.sub(r"^(?:work-from-home-)?(?:part-time-)?", "", role_raw).replace("-", " ").strip().title()
    if not role_clean.lower().endswith("internship") and not role_clean.lower().endswith("intern"):
        role_clean += " Intern"

    wp = "Remote" if "work-from-home" in url.lower() else "In office"
    emp_type = "Internship"
    exp_lvl = "Entry level"

    url_hash = hashlib.sha256(url.lower().rstrip("/").encode("utf-8")).hexdigest()[:24]
    job_id = f"job_{url_hash}"

    date_res = parse_date_to_ist(dt.strftime("%Y-%m-%d %H:%M:%S IST"))
    role_category = classify_job_canonical_role(role_clean)
    tags = generate_job_tags(
        title=role_clean,
        company=comp_clean,
        location=loc_clean,
        role_category=role_category,
        workplace_type=wp,
        experience_level=exp_lvl,
        employment_type=emp_type,
        raw_text=f"Internshala Internship {role_clean} {comp_clean}"
    )

    return {
        "id": job_id,
        "company_name": comp_clean,
        "role_name": role_clean,
        "title": role_clean,
        "role_category": role_category,
        "location": loc_clean,
        "workplace_type": wp,
        "experience_level": exp_lvl,
        "employment_type": emp_type,
        "apply_link": url,
        "apply_url": url,
        "salary_range": "Competitive Market Stipend",
        "posted_timestamp_ist": date_res.ist_str,
        "posted_timestamp_raw": date_res.raw_iso,
        "relative_time_ist": date_res.rel_time,
        "time_derived": 1,
        "tags": tags,
        "skills": [],
        "description": f"Verified internship opportunity at {comp_clean}. Apply directly on official Internshala portal.",
        "ats_platform": "Internshala",
        "source": "Internshala",
        "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
    }


def parse_foundit_url(url: str, lastmod_str: str, cutoff_dt: datetime.datetime) -> Optional[Dict[str, Any]]:
    """Extracts job attributes and verifies the 14-day cutoff from Foundit URL."""
    if not lastmod_str:
        return None

    try:
        dt = datetime.datetime.fromisoformat(lastmod_str)
        if dt.tzinfo is None:
            dt = IST_TZ.localize(dt)
    except Exception:
        return None

    if dt < cutoff_dt:
        return None

    clean = re.sub(r"^https?://[^/]+/job/", "", url)
    m = re.search(r"-(\d+)$", clean)
    body = clean[:m.start()] if m else clean
    tokens = body.split("-")

    loc_tokens = []
    idx = len(tokens) - 1
    while idx >= 0:
        t = tokens[idx].lower()
        if t in KNOWN_INDIAN_CITIES:
            loc_tokens.insert(0, tokens[idx])
            idx -= 1
        else:
            break

    loc_str = " ".join(loc_tokens).title() if loc_tokens else "India"
    rem = tokens[:idx + 1]

    title, company = split_title_and_company(rem)

    wp = "Remote" if "remote" in url.lower() or "work-from-home" in url.lower() else "In office"
    emp_type = "Full time"
    exp_lvl = normalize_experience_level(title)

    url_hash = hashlib.sha256(url.lower().rstrip("/").encode("utf-8")).hexdigest()[:24]
    job_id = f"job_{url_hash}"

    date_res = parse_date_to_ist(dt.strftime("%Y-%m-%d %H:%M:%S IST"))
    role_category = classify_job_canonical_role(title)
    tags = generate_job_tags(
        title=title,
        company=company,
        location=loc_str,
        role_category=role_category,
        workplace_type=wp,
        experience_level=exp_lvl,
        employment_type=emp_type,
        raw_text=f"Foundit {title} {company}"
    )

    return {
        "id": job_id,
        "company_name": company,
        "role_name": title,
        "title": title,
        "role_category": role_category,
        "location": loc_str,
        "workplace_type": wp,
        "experience_level": exp_lvl,
        "employment_type": emp_type,
        "apply_link": url,
        "apply_url": url,
        "salary_range": "Competitive Market CTC",
        "posted_timestamp_ist": date_res.ist_str,
        "posted_timestamp_raw": date_res.raw_iso,
        "relative_time_ist": date_res.rel_time,
        "time_derived": 1,
        "tags": tags,
        "skills": [],
        "description": f"Verified opportunity at {company}. Apply directly on official Foundit portal.",
        "ats_platform": "Foundit",
        "source": "Foundit",
        "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
    }


async def fetch_naukri_jobs(
    max_days: int = 14,
    limit_per_sitemap: int = 750,
    sitemap_urls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Fetches jobs from Naukri sitemaps within the last max_days."""
    now_ist = datetime.datetime.now(IST_TZ)
    cutoff_date = (now_ist - datetime.timedelta(days=max_days)).date()

    urls_to_crawl = sitemap_urls or NAUKRI_SITEMAP_URLS
    all_jobs: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for sitemap_url in urls_to_crawl:
            try:
                xml_text = await download_sitemap_xml(sitemap_url, client=client)
                if not xml_text:
                    continue

                root = ET.fromstring(xml_text)
                count = 0
                for u in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc = u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if not loc:
                        continue
                    job = parse_naukri_url(loc, cutoff_date)
                    if job:
                        all_jobs.append(job)
                        count += 1
                        if limit_per_sitemap and count >= limit_per_sitemap:
                            break
                logger.info(f"Naukri: Ingested {count} jobs from {sitemap_url}")
            except Exception as e:
                logger.warning(f"Error processing Naukri sitemap {sitemap_url}: {e}")

    logger.info(f"Naukri total jobs collected: {len(all_jobs)}")
    return all_jobs


async def fetch_internshala_jobs(
    max_days: int = 14,
    limit_total: int = 3000,
    sitemap_urls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Fetches internships from Internshala sitemaps within the last max_days."""
    now_ist = datetime.datetime.now(IST_TZ)
    cutoff_dt = now_ist - datetime.timedelta(days=max_days)

    urls_to_crawl = sitemap_urls or INTERNSHALA_SITEMAP_URLS
    all_jobs: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for sitemap_url in urls_to_crawl:
            try:
                xml_text = await download_sitemap_xml(sitemap_url, client=client)
                if not xml_text:
                    continue

                root = ET.fromstring(xml_text)
                count = 0
                # Process URLs in reverse to prioritize latest entries
                for u in reversed(root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")):
                    loc = u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    lm = u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
                    if not loc:
                        continue
                    job = parse_internshala_url(loc, lm, cutoff_dt)
                    if job:
                        all_jobs.append(job)
                        count += 1
                        if limit_total and len(all_jobs) >= limit_total:
                            break
                logger.info(f"Internshala: Ingested {count} internships from {sitemap_url}")
            except Exception as e:
                logger.warning(f"Error processing Internshala sitemap {sitemap_url}: {e}")

    logger.info(f"Internshala total jobs collected: {len(all_jobs)}")
    return all_jobs


async def fetch_foundit_jobs(
    max_days: int = 14,
    limit_per_sitemap: int = 600,
    sitemap_urls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Fetches jobs from Foundit sitemaps within the last max_days."""
    now_ist = datetime.datetime.now(IST_TZ)
    cutoff_dt = now_ist - datetime.timedelta(days=max_days)

    urls_to_crawl = sitemap_urls or FOUNDIT_SITEMAP_URLS
    all_jobs: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for sitemap_url in urls_to_crawl:
            try:
                xml_text = await download_sitemap_xml(sitemap_url, client=client)
                if not xml_text:
                    continue

                root = ET.fromstring(xml_text)
                count = 0
                for u in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc = u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    lm = u.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
                    if not loc:
                        continue
                    job = parse_foundit_url(loc, lm, cutoff_dt)
                    if job:
                        all_jobs.append(job)
                        count += 1
                        if limit_per_sitemap and count >= limit_per_sitemap:
                            break
                logger.info(f"Foundit: Ingested {count} jobs from {sitemap_url}")
            except Exception as e:
                logger.warning(f"Error processing Foundit sitemap {sitemap_url}: {e}")

    logger.info(f"Foundit total jobs collected: {len(all_jobs)}")
    return all_jobs


async def fetch_all_aggregator_jobs(
    max_days: int = 14,
    naukri_limit_per_sitemap: int = 500,
    internshala_limit: int = 2000,
    foundit_limit_per_sitemap: int = 400
) -> List[Dict[str, Any]]:
    """Fetches jobs from all 3 aggregators: Naukri, Internshala, and Foundit."""
    logger.info("Starting multi-aggregator ingestion across Naukri, Internshala, and Foundit...")
    jobs: List[Dict[str, Any]] = []

    # 1. Naukri
    n_jobs = await fetch_naukri_jobs(max_days=max_days, limit_per_sitemap=naukri_limit_per_sitemap)
    jobs.extend(n_jobs)

    # 2. Internshala
    i_jobs = await fetch_internshala_jobs(max_days=max_days, limit_total=internshala_limit)
    jobs.extend(i_jobs)

    # 3. Foundit
    f_jobs = await fetch_foundit_jobs(max_days=max_days, limit_per_sitemap=foundit_limit_per_sitemap)
    jobs.extend(f_jobs)

    logger.info(
        f"Completed multi-aggregator fetch: Total {len(jobs)} jobs (Naukri: {len(n_jobs)}, "
        f"Internshala: {len(i_jobs)}, Foundit: {len(f_jobs)})"
    )
    return jobs

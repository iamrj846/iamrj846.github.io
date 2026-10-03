# CorporateGuild Resources & ATS Directory Documentation

This directory contains the authoritative configuration files, verified company slugs, and master Excel directories for all integrated Applicant Tracking System (ATS) platforms across CorporateGuild.

---

## 1. Directory Structure & Summary

| File | ATS Platform | Total Slugs / Entries | Description & API Format |
| :--- | :--- | :--- | :--- |
| `workable_companies.json` | **Workable** | **35 companies** | Public widget API: `https://apply.workable.com/api/v1/widget/accounts/{slug}` |
| `smartrecruiters_companies.json` | **SmartRecruiters** | **78 companies** | India & global postings: `https://api.smartrecruiters.com/v1/companies/{slug}/postings?country=in&limit=100` |
| `workday_companies.json` | **Workday** | **12,884 endpoints** | Workday CXS format: `tenant\|host_prefix\|site_name` |
| `greenhouse_companies.json` | **Greenhouse** | **7,666 endpoints** | Public board API: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true` |
| `lever_companies.json` | **Lever** | **3,006 endpoints** | Public postings API: `https://api.lever.co/v0/postings/{slug}?mode=json` |
| `ashby_companies.json` | **Ashby** | **2,576 endpoints** | Job board API: `https://api.ashbyhq.com/posting-api/job-board/{slug}` |
| `bamboohr_companies.json` | **BambooHR** | **1,793 endpoints** | Public career list: `https://{slug}.bamboohr.com/careers/list` |
| `rippling_companies.json` | **Rippling** | **8 endpoints** | Platform board API: `https://api.rippling.com/platform/api/ats/v1/board/{slug}/jobs` |
| `pinpoint_companies.json` | **Pinpoint** | **18 endpoints** | Public postings: `https://{slug}.pinpointhq.com/postings.json` |
| `comeet_companies.json` | **Comeet** | **15 endpoints** | Careers API: `https://www.comeet.co/careers-api/2.0/company/{slug}/positions` |
| `jobvite_companies.json` | **Jobvite** | **15 endpoints** | Search JSON: `https://jobs.jobvite.com/{slug}/search?format=json` |
| `oracle_companies.json` | **Oracle Cloud** | **2 endpoints** | Candidate experience search endpoints |
| `job_urls.xlsx` | **Master Directory** | **1,000+ entries** | Master multi-sheet Excel spreadsheet with verified endpoints |

**Total Ingestion Endpoints**: Over **28,200+** verified endpoints across 15 ATS engines.

---

## 2. API Endpoints & Request Specifications

### Workable
- **Endpoint Pattern**: `https://apply.workable.com/api/v1/widget/accounts/{company_slug}`
- **HTTP Method**: `GET`
- **Response Format**: Raw JSON containing `{"total": N, "jobs": [...]}`
- **Date Format**: `published_on` in ISO-8601 (`"2026-04-12T00:00:00.000Z"`), parsed directly to authentic IST.
- **Key Companies**: `writesonic`, `huggingface`, `apna`, `weekday-1`, `mercari-india`, `terrapay`, `pricelabs`, `innovaccer-analytics`, `volga-partners`, `erbity`, `c-serv`, `ai-accountant`, `navtech`, `vestd`.

### SmartRecruiters
- **India Filtered Endpoint**: `https://api.smartrecruiters.com/v1/companies/{company_slug}/postings?country=in&limit=100`
- **Global Endpoint**: `https://api.smartrecruiters.com/v1/companies/{company_slug}/postings?limit=100`
- **HTTP Method**: `GET`
- **Response Format**: Raw JSON containing `{"totalFound": N, "content": [...]}`
- **Date Format**: `releasedDate` in ISO-8601, parsed directly to authentic IST.
- **Key Companies**: `BoschGroup` (530 India jobs), `SquircleITConsultingServicesPvtLtd` (1,782 India jobs), `RAIDMAXTECHNOLOGIESPVTLTD` (1,948 India jobs), `Eurofins` (338 India jobs), `NielsenIQ`, `Continental`, `Sutherland`, `Swiggy`, `PhonePeLimited`, `Cars24`, `bytedance`, `Endava`, `Recruitrix`, `InviaPrivateLimited`, `AtosSyntel`, `Version1`, `NECSWS`.

### Workday
- **Endpoint Pattern**: `https://{tenant}.{host_prefix}.myworkdayjobs.com/wday/cxs/{tenant}/{site_name}/jobs`
- **HTTP Method**: `POST` (with JSON body `{"appliedFacets":{},"limit":20,"offset":0,"searchText":""}`)
- **Date Handling**: Supports relative posted strings (`"Posted 4 Days Ago"`, `"Posted Yesterday"`, `"Posted 30+ Days Ago"`) and ISO timestamps via `parse_date_to_ist()`.
- **Key Companies**: `Roche`, `PwC`, `Cadence`, `Cisco`, `SPGI`, `Accenture`, `Amazon`, `Google`, `Microsoft`.

---

## 3. Maintenance & Periodic Refresh

- **Hourly Periodic Refresh**: The hourly cron script `scripts/periodic_fetch_and_update.py` iterates across all configured company files and updates `data/jobs_portal.db`.
- **Adding New Companies**:
  1. Add the company slug to the appropriate JSON file (e.g. `resources/workable_companies.json` or `resources/smartrecruiters_companies.json`).
  2. Verify the endpoint responds with valid JSON and `status == 200`.
  3. Run `python3 scripts/periodic_fetch_and_update.py` or restart the backend to register the new endpoint.

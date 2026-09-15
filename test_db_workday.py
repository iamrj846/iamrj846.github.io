import httpx
from app.services.ats_service import ATSService, ATSEndpoint

ep = ATSEndpoint(
    company_name="4flow",
    ats_platform="Workday",
    endpoint_url="https://4flow.wd3.myworkdayjobs.com/wday/cxs/4flow/4flow/jobs"
)
ats = ATSService()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
payload = {
    "appliedFacets": {},
    "limit": 20,
    "offset": 0,
    "searchText": "India"
}
resp = httpx.post(ep.endpoint_url, headers=headers, json=payload)
data = resp.json()

jobs = ats._parse_workday(ep, data)
print(f"Total valid India jobs parsed: {len(jobs)}")
if jobs:
    print(jobs[0])


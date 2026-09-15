import httpx
from app.services.ats_service import ATSService, ATSEndpoint
from app.database import save_jobs_to_db

ep = ATSEndpoint(
    company_name="JPMorgan Chase",
    ats_platform="Oracle",
    endpoint_url="https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber=CX_1001;keyword=India"
)
ats = ATSService()
resp = httpx.get(ep.endpoint_url, headers={"User-Agent": "Mozilla/5.0"})
data = resp.json()

jobs = ats._parse_oracle(ep, data)
print(f"Total valid India jobs parsed: {len(jobs)}")
if jobs:
    print(jobs[0])
    save_jobs_to_db(jobs)

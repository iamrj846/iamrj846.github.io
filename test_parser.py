from app.services.ats_service import ATSService, ATSEndpoint

ep = ATSEndpoint(
    company_name="JPMorgan Chase Test",
    ats_platform="Oracle",
    endpoint_url="https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber=CX_1001"
)
ats = ATSService()

data = {
    "items": [
        {
            "requisitionList": [
                {
                    "Id": "210604941",
                    "Title": "Software Engineer",
                    "PostedDate": "2026-09-15",
                    "PrimaryLocation": "Mumbai, Maharashtra, India",
                    "WorkplaceType": "Remote",
                    "JobFunction": "Engineering",
                    "WorkerType": "Full time"
                },
                {
                    "Id": "99999",
                    "Title": "Data Analyst",
                    "PostedDate": "2026-09-14",
                    "PrimaryLocation": "Bangalore, India",
                    "WorkplaceType": "Hybrid",
                    "JobFunction": "Analytics",
                    "WorkerType": "Part time"
                }
            ]
        }
    ]
}

jobs = ats._parse_oracle(ep, data)
print(f"Parsed {len(jobs)} jobs")
for j in jobs:
    print(j)


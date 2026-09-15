import httpx
import json

url = "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber=CX_1001"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
resp = httpx.get(url, headers=headers)
data = resp.json()
if data.get('items') and data['items'][0].get('requisitionList'):
    jobs = data['items'][0]['requisitionList']
    print(f"Got {len(jobs)} jobs")
    print(json.dumps(jobs[0], indent=2))
else:
    print("No jobs found")

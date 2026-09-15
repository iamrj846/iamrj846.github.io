import httpx
import json

url = "https://4flow.wd3.myworkdayjobs.com/wday/cxs/4flow/4flow/jobs"
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

resp = httpx.post(url, headers=headers, json=payload)
print(resp.status_code)
print(json.dumps(resp.json(), indent=2)[:500])

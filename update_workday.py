import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'r') as f:
    content = f.read()

workday_parser = '''
    def _parse_workday(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobPostings", [])
        if not jobs:
            return results
            
        import re
        m = re.search(r'https://([^.]+)\.([^.]+)\.myworkdayjobs\.com/wday/cxs/([^/]+)/([^/]+)/jobs', ep.endpoint_url)
        if not m:
            return results
            
        company, wd_domain, tenant, path = m.groups()
        base_url = f"https://{company}.{wd_domain}.myworkdayjobs.com/en-US/{path}"

        for j in jobs:
            title = j.get("title", "").strip()
            loc_name = j.get("locationsText", "")
            
            # India location verification
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)
                
            external_path = j.get("externalPath", "")
            if not external_path:
                continue
                
            apply_link = f"{base_url}{external_path}"
            posted_date = j.get("postedOn", "")
            # postedOn is usually "Posted 2 Days Ago" or "Posted Today"
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)
            
            bullets = " ".join(j.get("bulletFields", []))
            tags = extract_tags(title, bullets)
            
            emp_type = normalize_employment_type(bullets, title)
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower() or "remote" in bullets.lower()))
            exp_level = normalize_experience_level(title)
            
            results.append({
                "job_title": title,
                "company_name": ep.company_name,
                "location": clean_loc,
                "apply_url": apply_link,
                "job_updated_at": ist_str,
                "raw_timestamp": raw_iso,
                "relative_time": rel_time or posted_date,
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Workday",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
            
        return results
'''

if 'def _parse_workday' not in content:
    content = content.replace('def get_ats_service():', workday_parser + '\ndef get_ats_service():')

# Update _parse_ats_data
if 'elif "workday" in platform:' not in content:
    content = re.sub(
        r'(elif "oracle" in platform:\s+return self._parse_oracle\(ep, data\))',
        r'\1\n        elif "workday" in platform:\n            return self._parse_workday(ep, data)',
        content
    )
    content = re.sub(
        r'(elif "items" in data.*self._parse_oracle\(ep, data\))',
        r'\1\n                elif "jobPostings" in data and isinstance(data["jobPostings"], list):\n                    return self._parse_workday(ep, data)',
        content
    )

# Update fetch_single_endpoint to handle POST for Workday
old_fetch = '''            try:
                resp = await client.get(ep.endpoint_url, headers=headers, timeout=self.config.scheduler.get("request_timeout_seconds", 10))
                if resp.status_code == 200:'''

new_fetch = '''            try:
                if "myworkdayjobs.com/wday/cxs" in ep.endpoint_url:
                    payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "India"}
                    resp = await client.post(ep.endpoint_url, headers=headers, json=payload, timeout=self.config.scheduler.get("request_timeout_seconds", 10))
                else:
                    resp = await client.get(ep.endpoint_url, headers=headers, timeout=self.config.scheduler.get("request_timeout_seconds", 10))
                if resp.status_code == 200:'''

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'w') as f:
    f.write(content)

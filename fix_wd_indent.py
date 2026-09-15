import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'r') as f:
    content = f.read()

content = re.sub(r'    def _parse_workday\(self, .*?return results\n', '', content, flags=re.DOTALL)

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

content = content.replace('    async def fetch_all_endpoints(', workday_parser + '\n    async def fetch_all_endpoints(')

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'w') as f:
    f.write(content)


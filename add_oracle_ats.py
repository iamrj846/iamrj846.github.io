import re

def update_ats_service():
    with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'r') as f:
        content = f.read()

    # Add oracle to _parse_ats_data
    if 'elif "oracle" in platform:' not in content:
        content = re.sub(
            r'(elif "bamboohr" in platform:\s+return self._parse_bamboohr\(ep, data\))',
            r'\1\n        elif "oracle" in platform:\n            return self._parse_oracle(ep, data)',
            content
        )
    
        # Wait, if platform is not explicit but inferred from data structure:
        content = re.sub(
            r'(elif "result" in data and isinstance\(data\["result"\], list\):\s+return self._parse_bamboohr\(ep, data\))',
            r'\1\n                elif "items" in data and data["items"] and isinstance(data["items"], list) and "requisitionList" in data["items"][0]:\n                    return self._parse_oracle(ep, data)',
            content
        )

    # Add _parse_oracle method
    oracle_method = '''
    def _parse_oracle(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        items = data.get("items", [])
        if not items:
            return results
        
        req_list = items[0].get("requisitionList", [])
        
        # Extract site number from endpoint_url or default to CX_1
        site_number = "CX_1"
        import re
        m = re.search(r'siteNumber=([A-Za-z0-9_]+)', ep.endpoint_url)
        if m:
            site_number = m.group(1)
            
        base_url = ep.endpoint_url.split('/hcmRestApi')[0]
        
        for j in req_list:
            title = j.get("Title", "").strip()
            loc_name = j.get("PrimaryLocation", "")
            
            # India location verification
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)
                
            job_id = j.get("Id", "")
            if not job_id:
                continue
                
            apply_link = f"{base_url}/hcmUI/CandidateExperience/en/sites/{site_number}/job/{job_id}"
            
            posted_date = j.get("PostedDate")
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)
            
            dept_str = j.get("JobFunction", "") or j.get("JobFamily", "") or ""
            tags = extract_tags(title, dept_str)
            
            worker_type = j.get("WorkerType", "") or j.get("JobType", "") or ""
            emp_type = normalize_employment_type(worker_type, title)
            
            wp_code = j.get("WorkplaceType", "") or j.get("WorkplaceTypeCode", "") or ""
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower() or "remote" in wp_code.lower()))
            
            exp_level = normalize_experience_level(title)
            
            results.append({
                "job_title": title,
                "company_name": ep.company_name,
                "location": clean_loc,
                "apply_url": apply_link,
                "job_updated_at": ist_str,
                "raw_timestamp": raw_iso,
                "relative_time": rel_time,
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Oracle",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
            
        return results
'''
    if 'def _parse_oracle' not in content:
        content += oracle_method

    with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'w') as f:
        f.write(content)
    print("Added _parse_oracle to ats_service.py")

update_ats_service()

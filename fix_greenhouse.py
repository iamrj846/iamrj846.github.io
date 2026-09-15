import sqlite3
import re

def fix():
    with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'r') as f:
        content = f.read()

    # Rewrite _parse_greenhouse apply_link logic
    old_code = 'apply_link = j.get("absolute_url") or f"https://boards.greenhouse.io/{ep.company_name.lower()}/jobs/{j.get(\'id\')}"'
    new_code = '''
            apply_link = j.get("absolute_url", "")
            # Ensure it's a web URL, not an API JSON endpoint
            if not apply_link or "api.greenhouse" in apply_link or "boards-api" in apply_link:
                board_match = re.search(r'boards/([^/]+)/jobs', ep.endpoint_url)
                board_token = board_match.group(1) if board_match else ep.company_name.lower()
                apply_link = f"https://boards.greenhouse.io/{board_token}/jobs/{j.get('id')}"
            elif "api." in apply_link:
                apply_link = apply_link.replace("api.", "boards.")
'''
    if old_code in content:
        content = content.replace(old_code, new_code.strip())
        with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'w') as f:
            f.write(content)
        print("Updated ats_service.py for Greenhouse URLs.")
    else:
        print("Could not find old Greenhouse code in ats_service.py")

fix()

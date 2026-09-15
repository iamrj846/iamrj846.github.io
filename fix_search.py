import re

def fix():
    with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/search_service.py', 'r') as f:
        content = f.read()

    # 1. Remove "engineer" from Software Engineer synonyms
    content = content.replace('"software engineer 1", "software engineer 2", "engineer"', '"software engineer 1", "software engineer 2"')

    # 2. Fix the any(s in r.lower()) in search_type == "company" for roles
    content = re.sub(
        r'if role_matches\(all_syns, r\) or any\(s in r\.lower\(\) for s in all_syns\):',
        r'if role_matches(all_syns, r):',
        content
    )

    # 3. Fix the tokens matching in custom search
    content = re.sub(
        r'if not tokens or any\(t in combined for t in tokens\) or role_matches\(all_syns, combined\):',
        r'if role_matches(all_syns, combined) or (tokens and all(t in combined for t in tokens)):',
        content
    )

    with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/search_service.py', 'w') as f:
        f.write(content)

fix()

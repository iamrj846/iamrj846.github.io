import re

with open('/Users/iamrj846/.gemini/antigravity/brain/fd16e1cd-5535-4d6a-beff-d83bde0d9c8b/ats_coverage_audit.md', 'r') as f:
    content = f.read()

oracle_row = "| **Oracle** | 2 | `_parse_oracle()` | ✅ Healthy / Active |\n| **Total**"
content = re.sub(r'\| \*\*Total\*\*', oracle_row, content)

with open('/Users/iamrj846/.gemini/antigravity/brain/fd16e1cd-5535-4d6a-beff-d83bde0d9c8b/ats_coverage_audit.md', 'w') as f:
    f.write(content)

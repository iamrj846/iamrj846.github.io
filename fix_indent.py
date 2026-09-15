import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'r') as f:
    content = f.read()

# Remove the incorrectly placed _parse_oracle
match = re.search(r'    def _parse_oracle\(self, .*?return results\n', content, re.DOTALL)
if match:
    oracle_code = match.group(0)
    content = content.replace(oracle_code, '')
    
    # insert it before def get_ats_service()
    content = content.replace('def get_ats_service():', oracle_code + '\ndef get_ats_service():')

    with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'w') as f:
        f.write(content)
    print("Fixed _parse_oracle position")
else:
    print("Could not find _parse_oracle")


with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'r') as f:
    lines = f.readlines()

while lines and (lines[-1].strip() == '' or 'req_list =' in lines[-1]):
    lines.pop()

with open('/Users/iamrj846/Desktop/iamrj846.github.io/app/services/ats_service.py', 'w') as f:
    f.writelines(lines)

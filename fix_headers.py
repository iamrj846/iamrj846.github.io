import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

content = content.replace(
    'const res = await fetch(`/api/admin/system_metrics?hours=${hours}`);',
    'const res = await fetch(`/api/admin/system_metrics?hours=${hours}`, { headers: getAdminHeaders() });'
)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)
print("Added headers to fetch")

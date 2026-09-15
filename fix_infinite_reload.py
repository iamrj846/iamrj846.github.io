import re
with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

content = content.replace(
    'if (res.status === 401 || res.status === 403) return adminLogout();',
    'if (res.status === 401 || res.status === 403) return;'
)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)
print("Fixed infinite reload loop")

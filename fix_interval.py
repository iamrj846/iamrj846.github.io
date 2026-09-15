import re
with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

content = content.replace(
    'setInterval(loadAdminData, 15000);',
    'setInterval(loadAdminData, 15000);\n    setInterval(fetchSystemMetrics, 15000);'
)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)
print("Added interval for metrics")

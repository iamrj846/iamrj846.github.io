import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

# Change selected option
content = content.replace('<option value="1">Last 1 Hour</option>', '<option value="1">Last 1 Hour</option>')
# Just add selected to 24
content = content.replace('<option value="24">Last 24 Hours</option>', '<option value="24" selected>Last 24 Hours</option>')

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)
print("Updated admin default time to 24h")

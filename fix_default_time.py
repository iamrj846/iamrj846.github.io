import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'r') as f:
    content = f.read()

# 1. Change selected option
content = content.replace('<option value="1h" selected>Last 1 Hour</option>', '<option value="1h">Last 1 Hour</option>')
content = content.replace('<option value="24h">Last 24 Hours</option>', '<option value="24h" selected>Last 24 Hours</option>')

# 2. Change JS defaults
content = content.replace("time_filter: '1h'", "time_filter: '24h'")
content = content.replace("document.getElementById('filterTime').value = '1h';", "document.getElementById('filterTime').value = '24h';")
content = content.replace("appliedFilters.time_filter !== '1h'", "appliedFilters.time_filter !== '24h'")
content = content.replace("|| appliedFilters.time_filter || '1h')", "|| appliedFilters.time_filter || '24h')")
content = content.replace("appliedFilters.time_filter = '1h';", "appliedFilters.time_filter = '24h';")

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'w') as f:
    f.write(content)
print("Updated default time to 24h")

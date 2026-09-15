with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'r') as f:
    content = f.read()

style_block = '''
  <style>
    .reset-filter-btn:hover {
      background: #F1F5F9 !important;
      color: #334155 !important;
    }
  </style>
</head>
'''

content = content.replace('</head>', style_block)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'w') as f:
    f.write(content)
print("Added hover CSS")

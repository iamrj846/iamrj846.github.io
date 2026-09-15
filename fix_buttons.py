import re
with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'r') as f:
    content = f.read()

new_footer = '''
        <div class="filter-footer" style="display: flex; justify-content: flex-end; margin-top: 10px;">
          <button class="reset-filter-btn" onclick="resetFilters()" style="background: none; border: none; color: #64748b; font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 4px; padding: 6px 12px; border-radius: 6px; transition: all 0.2s;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
            <span>Reset Filters</span>
          </button>
        </div>
'''

content = re.sub(r'<div class="filter-footer">.*?</div>', new_footer.strip(), content, flags=re.DOTALL)

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'w') as f:
    f.write(content)
print("Fixed buttons")

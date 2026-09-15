import re

def fix(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Make onFilterSelectionChange call applyFilters() automatically
    old_fn = r'''function onFilterSelectionChange\(\) \{
      const btn = document\.getElementById\('btnApplyFilters'\);
      if \(btn\) btn\.classList\.add\('dirty'\);
    \}'''
    
    new_fn = '''function onFilterSelectionChange() {
      const btn = document.getElementById('btnApplyFilters');
      if (btn) btn.classList.add('dirty');
      applyFilters();
    }'''
    
    content = re.sub(old_fn, new_fn, content)
    
    # Fix the broken applyFiltersAndSearch in jobs.html
    content = content.replace('applyFiltersAndSearch()', 'applyFilters()')
    
    # In index.html btnSearch event listener, make sure to call applyFilters before searching?
    # Actually, executeSearch uses appliedFilters. But searchInput is read dynamically in executeSearch.
    # So btnSearch doesn't need to call applyFilters unless we want it to. But it's fine.

    with open(filepath, 'w') as f:
        f.write(content)

fix('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/index.html')
fix('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html')

import os
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix executeSearch call
    content = re.sub(
        r'updateDynamicSeo\(data\.results \|\| \[\], data\.total_count \|\| 0, query, appliedFilters\.location, appliedFilters\.role, appliedFilters\.workplace_type, appliedFilters\.time_filter\);',
        r'updateDynamicSeo(data.results || [], data.total_count || 0, query, appliedFilters.location, appliedFilters.role, appliedFilters.workplace_type, appliedFilters.time_filter, appliedFilters.employment_type, appliedFilters.experience_level);',
        content
    )

    # Fix function signature
    content = re.sub(
        r'function updateDynamicSeo\(jobs, totalCount, query, loc, role, wp, time_filter\) \{',
        r'function updateDynamicSeo(jobs, totalCount, query, loc, role, wp, time_filter, emp_type, exp_level) {',
        content
    )

    # We will replace the body of updateDynamicSeo separately via string replacement.
    
    with open(filepath, 'w') as f:
        f.write(content)

fix_file('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/index.html')
fix_file('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html')

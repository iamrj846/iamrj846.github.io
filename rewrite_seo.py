import re

def rewrite(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    start_str = "function updateDynamicSeo(jobs, totalCount, query, loc, role, wp, time_filter, emp_type, exp_level) {"
    start_idx = content.find(start_str)
    if start_idx == -1:
        print("Could not find start str in", filepath)
        return

    end_match = re.search(r'updateSchemaJsonLd\([^;]+;\n      \} catch \(seoErr\) \{\n        console\.warn\(\'SEO metadata notice:\', seoErr\);\n      \}\n    \}', content[start_idx:])
    if not end_match:
        print("Could not find end match in", filepath)
        return
        
    end_idx = start_idx + end_match.end()
    
    new_body = """function updateDynamicSeo(jobs, totalCount, query, loc, role, wp, time_filter, emp_type, exp_level) {
      const introText = document.getElementById('seoIntroText');
      const introTime = document.getElementById('seoIntroTimestamp');
      if (!introText) return;

      const countStr = totalCount > 0 ? `${totalCount}` : '0';
      const hasSpecificRole = (searchMode === 'role' && query && query.trim()) || 
                              (role && role !== 'all') || 
                              (searchMode === 'company' && query && query.trim());

      let locStr = '';
      if (loc && loc !== 'all') locStr = loc;

      const tf = (time_filter || appliedFilters.time_filter || '1h').toLowerCase();
      let timeDesc = 'in the last 1 hour';
      let badgeTime = 'Live Feed • Last 1 Hour';
      if (tf === '1h') { timeDesc = 'in the last 1 hour'; badgeTime = 'Live Feed • Last 1 Hour'; }
      else if (tf === '12h') { timeDesc = 'in the last 12 hours'; badgeTime = 'Live Feed • Last 12h'; }
      else if (tf === '24h') { timeDesc = 'in the last 24 hours'; badgeTime = 'Live Feed • Last 24h'; }
      else if (tf === '2d') { timeDesc = 'in the last 2 days'; badgeTime = 'Live Feed • Last 2 Days'; }
      else if (tf === '7d') { timeDesc = 'in the last 7 days'; badgeTime = 'Live Feed • Last 7 Days'; }
      else if (tf === 'all') { timeDesc = 'across the past 7 days'; badgeTime = 'Live Feed • Past 7 Days'; }

      let expStr = '';
      if (exp_level && exp_level !== 'all') {
        if (exp_level === 'Entry level') expStr = 'Entry Level / Graduate ';
        else if (exp_level === 'Manager') expStr = 'Manager / Lead ';
        else expStr = exp_level + ' ';
      }

      let empStr = '';
      if (emp_type && emp_type !== 'all') {
        empStr = emp_type + ' ';
      }

      let roleStr = '';
      if (hasSpecificRole) {
        if (searchMode === 'role' && query) roleStr = query.trim();
        else if (role && role !== 'all') roleStr = role;
        else if (searchMode === 'company' && query) roleStr = query.trim();
      }

      const roleDisplay = hasSpecificRole ? escapeHtml(roleStr) + ' roles' : 'opportunities';
      const locSuffix = locStr ? ` in <strong>${escapeHtml(locStr)}</strong>` : '';
      const locSuffixPlain = locStr ? ` in ${locStr}` : '';
      
      const fullRolePlain = `${expStr}${empStr}${hasSpecificRole ? roleStr + ' roles' : 'opportunities'}`.trim();
      const fullRoleHtml = `${escapeHtml(expStr)}${escapeHtml(empStr)}<strong>${hasSpecificRole ? escapeHtml(roleStr) : 'all'}</strong> ${hasSpecificRole ? 'roles' : 'opportunities'}`.trim();

      let paragraph = '';
      let plainText = '';

      if (totalCount > 0) {
        paragraph = `Browse <strong>${countStr}</strong> active ${fullRoleHtml} posted ${timeDesc} at leading companies${locSuffix}.`;
        plainText = `Browse ${countStr} active ${fullRolePlain} posted ${timeDesc} at leading companies${locSuffixPlain}.`;
      } else {
        paragraph = `No results returned for ${fullRoleHtml} ${timeDesc} at leading companies${locSuffix}. Please try again for a different role, company, duration, or filter.`;
        plainText = `No results returned for ${fullRolePlain} ${timeDesc} at leading companies${locSuffixPlain}. Please try again for a different role, company, duration, or filter.`;
      }

      introText.innerHTML = paragraph;
      if (introTime) introTime.textContent = badgeTime;

      try {
        const metaDesc = document.querySelector('meta[name="description"]');
        if (metaDesc && typeof metaDesc.setAttribute === 'function') metaDesc.setAttribute('content', plainText);

        let ogDesc = document.querySelector('meta[property="og:description"]');
        if (!ogDesc && document.head && typeof document.createElement === 'function') {
          ogDesc = document.createElement('meta');
          ogDesc.setAttribute('property', 'og:description');
          document.head.appendChild(ogDesc);
        }
        if (ogDesc && typeof ogDesc.setAttribute === 'function') ogDesc.setAttribute('content', plainText);

        const pageTitleRole = hasSpecificRole ? roleStr : 'All Verified Opportunities';
        document.title = locStr ? `${pageTitleRole} in ${locStr} | CorporateGuild` : `${pageTitleRole} | CorporateGuild`;
        updateSchemaJsonLd(pageTitleRole, locStr, plainText, jobs);
      } catch (seoErr) {
        console.warn('SEO metadata notice:', seoErr);
      }
    }"""
    
    with open(filepath, 'w') as f:
        f.write(content[:start_idx] + new_body + content[end_idx:])

rewrite('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/index.html')
rewrite('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html')

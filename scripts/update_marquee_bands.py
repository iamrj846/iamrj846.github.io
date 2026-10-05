#!/usr/bin/env python3
"""
Updates the horizontal marquee bands across all frontend HTML files:
- Strips all count badges (<span class="chip-count">...</span>)
- Band 2 (Companies): Replaces company chips with verified active companies having real jobs in CorporateGuild database (Amazon, PwC, Barclays, Micron, Bosch, Cisco, Oracle, HP, Paytm, Swiggy, Adobe, Sanofi, Mastercard, Visa, PhonePe, Microsoft, Accenture, Google, Meta, NVIDIA).
- Completely removes companies with 0 jobs (Zomato, Apple, TCS, Infosys, Deloitte, Wipro, Flipkart).
- Preserves interactive onclick handlers for index.html & jobs.html, and standard /jobs.html?param links for static subpages.
"""

import os
import re
import glob

BUTTON_ROLES = """              <div class="marquee-band-group">
                <button type="button" class="band-chip" onclick="quickSearchRole('Software Engineer')">💻 Software Engineer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Full Stack Developer')">🚀 Full Stack Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('AI / Machine Learning Engineer')">🤖 AI &amp; ML Engineer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('DevOps / Cloud Engineer')">☁️ DevOps &amp; Cloud</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Data Scientist')">📊 Data Scientist</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Product Manager')">💼 Product Manager</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Cybersecurity Engineer')">🛡️ Cybersecurity</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('UI/UX Designer')">🎨 UI/UX Design</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Backend Developer')">⚙️ Backend Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Frontend Developer')">✨ Frontend Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Mobile Engineer')">📱 Mobile Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Business Analyst')">📈 Business Analyst</button>
                <button type="button" class="band-chip chip-all" onclick="quickSearchRole('All Roles')">🌐 Browse All Roles</button>
              </div>
              <div class="marquee-band-group" aria-hidden="true">
                <button type="button" class="band-chip" onclick="quickSearchRole('Software Engineer')">💻 Software Engineer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Full Stack Developer')">🚀 Full Stack Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('AI / Machine Learning Engineer')">🤖 AI &amp; ML Engineer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('DevOps / Cloud Engineer')">☁️ DevOps &amp; Cloud</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Data Scientist')">📊 Data Scientist</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Product Manager')">💼 Product Manager</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Cybersecurity Engineer')">🛡️ Cybersecurity</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('UI/UX Designer')">🎨 UI/UX Design</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Backend Developer')">⚙️ Backend Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Frontend Developer')">✨ Frontend Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Mobile Engineer')">📱 Mobile Developer</button>
                <button type="button" class="band-chip" onclick="quickSearchRole('Business Analyst')">📈 Business Analyst</button>
                <button type="button" class="band-chip chip-all" onclick="quickSearchRole('All Roles')">🌐 Browse All Roles</button>
              </div>"""

BUTTON_COMPANIES = """              <div class="marquee-band-group">
                <button type="button" class="band-chip" onclick="quickSearchCompany('Amazon')">🏢 Amazon</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('PwC')">🏢 PwC</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Barclays')">🏢 Barclays</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Micron')">🏢 Micron</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Bosch')">🏢 Bosch</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Cisco')">🏢 Cisco</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Oracle')">🏢 Oracle</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('HP')">🏢 HP</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Paytm')">🏢 Paytm</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Swiggy')">🏢 Swiggy</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Adobe')">🏢 Adobe</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Sanofi')">🏢 Sanofi</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Mastercard')">🏢 Mastercard</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Visa')">🏢 Visa</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('PhonePe')">🏢 PhonePe</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Microsoft')">🏢 Microsoft</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Accenture')">🏢 Accenture</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Google')">🏢 Google</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Meta')">🏢 Meta</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('NVIDIA')">🏢 NVIDIA</button>
              </div>
              <div class="marquee-band-group" aria-hidden="true">
                <button type="button" class="band-chip" onclick="quickSearchCompany('Amazon')">🏢 Amazon</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('PwC')">🏢 PwC</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Barclays')">🏢 Barclays</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Micron')">🏢 Micron</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Bosch')">🏢 Bosch</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Cisco')">🏢 Cisco</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Oracle')">🏢 Oracle</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('HP')">🏢 HP</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Paytm')">🏢 Paytm</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Swiggy')">🏢 Swiggy</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Adobe')">🏢 Adobe</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Sanofi')">🏢 Sanofi</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Mastercard')">🏢 Mastercard</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Visa')">🏢 Visa</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('PhonePe')">🏢 PhonePe</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Microsoft')">🏢 Microsoft</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Accenture')">🏢 Accenture</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Google')">🏢 Google</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('Meta')">🏢 Meta</button>
                <button type="button" class="band-chip" onclick="quickSearchCompany('NVIDIA')">🏢 NVIDIA</button>
              </div>"""

LINK_ROLES = """              <div class="marquee-band-group">
                <a href="/jobs.html?role=Software%20Engineer" class="band-chip">💻 Software Engineer</a>
                <a href="/jobs.html?role=Full%20Stack%20Developer" class="band-chip">🚀 Full Stack Developer</a>
                <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="band-chip">🤖 AI &amp; ML Engineer</a>
                <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="band-chip">☁️ DevOps &amp; Cloud</a>
                <a href="/jobs.html?role=Data%20Scientist" class="band-chip">📊 Data Scientist</a>
                <a href="/jobs.html?role=Product%20Manager" class="band-chip">💼 Product Manager</a>
                <a href="/jobs.html?role=Cybersecurity%20Engineer" class="band-chip">🛡️ Cybersecurity</a>
                <a href="/jobs.html?role=UI%2FUX%20Designer" class="band-chip">🎨 UI/UX Design</a>
                <a href="/jobs.html?role=Backend%20Developer" class="band-chip">⚙️ Backend Developer</a>
                <a href="/jobs.html?role=Frontend%20Developer" class="band-chip">✨ Frontend Developer</a>
                <a href="/jobs.html?role=Mobile%20Engineer" class="band-chip">📱 Mobile Developer</a>
                <a href="/jobs.html?role=Business%20Analyst" class="band-chip">📈 Business Analyst</a>
                <a href="/jobs.html" class="band-chip chip-all">🌐 Browse All Roles</a>
              </div>
              <div class="marquee-band-group" aria-hidden="true">
                <a href="/jobs.html?role=Software%20Engineer" class="band-chip">💻 Software Engineer</a>
                <a href="/jobs.html?role=Full%20Stack%20Developer" class="band-chip">🚀 Full Stack Developer</a>
                <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="band-chip">🤖 AI &amp; ML Engineer</a>
                <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="band-chip">☁️ DevOps &amp; Cloud</a>
                <a href="/jobs.html?role=Data%20Scientist" class="band-chip">📊 Data Scientist</a>
                <a href="/jobs.html?role=Product%20Manager" class="band-chip">💼 Product Manager</a>
                <a href="/jobs.html?role=Cybersecurity%20Engineer" class="band-chip">🛡️ Cybersecurity</a>
                <a href="/jobs.html?role=UI%2FUX%20Designer" class="band-chip">🎨 UI/UX Design</a>
                <a href="/jobs.html?role=Backend%20Developer" class="band-chip">⚙️ Backend Developer</a>
                <a href="/jobs.html?role=Frontend%20Developer" class="band-chip">✨ Frontend Developer</a>
                <a href="/jobs.html?role=Mobile%20Engineer" class="band-chip">📱 Mobile Developer</a>
                <a href="/jobs.html?role=Business%20Analyst" class="band-chip">📈 Business Analyst</a>
                <a href="/jobs.html" class="band-chip chip-all">🌐 Browse All Roles</a>
              </div>"""

LINK_COMPANIES = """              <div class="marquee-band-group">
                <a href="/jobs.html?company=Amazon" class="band-chip">🏢 Amazon</a>
                <a href="/jobs.html?company=PwC" class="band-chip">🏢 PwC</a>
                <a href="/jobs.html?company=Barclays" class="band-chip">🏢 Barclays</a>
                <a href="/jobs.html?company=Micron" class="band-chip">🏢 Micron</a>
                <a href="/jobs.html?company=Bosch" class="band-chip">🏢 Bosch</a>
                <a href="/jobs.html?company=Cisco" class="band-chip">🏢 Cisco</a>
                <a href="/jobs.html?company=Oracle" class="band-chip">🏢 Oracle</a>
                <a href="/jobs.html?company=HP" class="band-chip">🏢 HP</a>
                <a href="/jobs.html?company=Paytm" class="band-chip">🏢 Paytm</a>
                <a href="/jobs.html?company=Swiggy" class="band-chip">🏢 Swiggy</a>
                <a href="/jobs.html?company=Adobe" class="band-chip">🏢 Adobe</a>
                <a href="/jobs.html?company=Sanofi" class="band-chip">🏢 Sanofi</a>
                <a href="/jobs.html?company=Mastercard" class="band-chip">🏢 Mastercard</a>
                <a href="/jobs.html?company=Visa" class="band-chip">🏢 Visa</a>
                <a href="/jobs.html?company=PhonePe" class="band-chip">🏢 PhonePe</a>
                <a href="/jobs.html?company=Microsoft" class="band-chip">🏢 Microsoft</a>
                <a href="/jobs.html?company=Accenture" class="band-chip">🏢 Accenture</a>
                <a href="/jobs.html?company=Google" class="band-chip">🏢 Google</a>
                <a href="/jobs.html?company=Meta" class="band-chip">🏢 Meta</a>
                <a href="/jobs.html?company=NVIDIA" class="band-chip">🏢 NVIDIA</a>
              </div>
              <div class="marquee-band-group" aria-hidden="true">
                <a href="/jobs.html?company=Amazon" class="band-chip">🏢 Amazon</a>
                <a href="/jobs.html?company=PwC" class="band-chip">🏢 PwC</a>
                <a href="/jobs.html?company=Barclays" class="band-chip">🏢 Barclays</a>
                <a href="/jobs.html?company=Micron" class="band-chip">🏢 Micron</a>
                <a href="/jobs.html?company=Bosch" class="band-chip">🏢 Bosch</a>
                <a href="/jobs.html?company=Cisco" class="band-chip">🏢 Cisco</a>
                <a href="/jobs.html?company=Oracle" class="band-chip">🏢 Oracle</a>
                <a href="/jobs.html?company=HP" class="band-chip">🏢 HP</a>
                <a href="/jobs.html?company=Paytm" class="band-chip">🏢 Paytm</a>
                <a href="/jobs.html?company=Swiggy" class="band-chip">🏢 Swiggy</a>
                <a href="/jobs.html?company=Adobe" class="band-chip">🏢 Adobe</a>
                <a href="/jobs.html?company=Sanofi" class="band-chip">🏢 Sanofi</a>
                <a href="/jobs.html?company=Mastercard" class="band-chip">🏢 Mastercard</a>
                <a href="/jobs.html?company=Visa" class="band-chip">🏢 Visa</a>
                <a href="/jobs.html?company=PhonePe" class="band-chip">🏢 PhonePe</a>
                <a href="/jobs.html?company=Microsoft" class="band-chip">🏢 Microsoft</a>
                <a href="/jobs.html?company=Accenture" class="band-chip">🏢 Accenture</a>
                <a href="/jobs.html?company=Google" class="band-chip">🏢 Google</a>
                <a href="/jobs.html?company=Meta" class="band-chip">🏢 Meta</a>
                <a href="/jobs.html?company=NVIDIA" class="band-chip">🏢 NVIDIA</a>
              </div>"""


def update_file(file_path: str) -> bool:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    is_button = file_path in ["frontend/index.html", "frontend/jobs.html"]
    rep_roles = BUTTON_ROLES if is_button else LINK_ROLES
    rep_comps = BUTTON_COMPANIES if is_button else LINK_COMPANIES

    # Match the inner contents of track-speed-roles
    pattern_roles = re.compile(
        r'(<div class=["\']marquee-band-track track-speed-roles["\']>)(.*?)(</div>\s*</div>\s*</div>)',
        re.DOTALL
    )
    # Match the inner contents of track-speed-companies
    pattern_comps = re.compile(
        r'(<div class=["\']marquee-band-track track-speed-companies["\']>)(.*?)(</div>\s*</div>\s*</div>)',
        re.DOTALL
    )

    new_content, n_roles = pattern_roles.subn(r'\1\n' + rep_roles + r'\n          \3', content)
    new_content, n_comps = pattern_comps.subn(r'\1\n' + rep_comps + r'\n          \3', new_content)

    if n_roles > 0 or n_comps > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {file_path}: {n_roles} roles, {n_comps} companies")
        return True
    return False


def main():
    root = "frontend"
    all_files = glob.glob(f"{root}/**/*.html", recursive=True)
    count = 0
    for p in sorted(all_files):
        if update_file(p):
            count += 1
    print(f"\nDone! Successfully updated marquee bands across {count} HTML files.")


if __name__ == "__main__":
    main()

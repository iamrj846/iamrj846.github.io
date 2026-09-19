#!/usr/bin/env python3
"""
Update all frontend HTML pages to include the Career Guides dropdown menu in the top navigation bar.
"""
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

NAV_CSS = """
    /* Career Guides Menu Dropdown */
    .nav-item-dropdown {
      position: relative;
      display: inline-flex;
      align-items: center;
    }
    .nav-dropdown-trigger {
      display: inline-flex !important;
      align-items: center !important;
      gap: 6px !important;
      cursor: pointer;
    }
    .dropdown-chevron {
      transition: transform 0.2s ease;
      margin-left: 2px;
    }
    .nav-item-dropdown:hover .dropdown-chevron,
    .nav-item-dropdown.open .dropdown-chevron {
      transform: rotate(180deg);
    }
    .nav-dropdown-menu {
      position: absolute;
      top: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%) translateY(6px);
      width: 680px;
      max-width: 92vw;
      background: #FFFFFF;
      border: 1px solid rgba(226, 232, 240, 0.9);
      border-radius: 12px;
      box-shadow: 0 20px 45px -10px rgba(15, 23, 42, 0.16), 0 0 0 1px rgba(15, 23, 42, 0.05);
      padding: 16px 20px;
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
      transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.2s;
      z-index: 1200;
    }
    .nav-item-dropdown:hover .nav-dropdown-menu,
    .nav-item-dropdown.open .nav-dropdown-menu,
    .nav-item-dropdown:focus-within .nav-dropdown-menu {
      opacity: 1;
      visibility: visible;
      pointer-events: auto;
      transform: translateX(-50%) translateY(0);
    }
    .nav-dropdown-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 10px;
      margin-bottom: 12px;
      border-bottom: 1px solid #F1F5F9;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #64748B;
    }
    .nav-dropdown-header a {
      color: #2563EB !important;
      text-decoration: none;
      font-weight: 600 !important;
      font-size: 12px !important;
      height: auto !important;
      padding: 0 !important;
    }
    .nav-dropdown-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    .nav-dropdown-cat {
      font-size: 11px;
      font-weight: 700;
      color: #94A3B8;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 8px;
    }
    .nav-dropdown-col a {
      display: block !important;
      font-size: 13px !important;
      color: #334155 !important;
      text-decoration: none;
      padding: 5px 8px !important;
      border-radius: 6px;
      height: auto !important;
      font-weight: 500 !important;
      transition: all 0.15s ease;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .nav-dropdown-col a:hover {
      background: #EFF6FF !important;
      color: #2563EB !important;
      font-weight: 600 !important;
      transform: translateX(2px);
    }
    .nav-dropdown-footer {
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid #F1F5F9;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }
    .nav-dropdown-tags {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .nav-tag-label {
      font-size: 11px;
      color: #64748B;
      font-weight: 600;
    }
    .nav-tag-pill {
      display: inline-block !important;
      font-size: 11px !important;
      font-weight: 600 !important;
      padding: 3px 8px !important;
      border-radius: 12px;
      background: #F1F5F9 !important;
      color: #475569 !important;
      text-decoration: none;
      height: auto !important;
      line-height: normal !important;
    }
    .nav-tag-pill:hover {
      background: #E2E8F0 !important;
      color: #1E293B !important;
    }
    .nav-dropdown-all-btn {
      color: #2563EB !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      text-decoration: none;
      height: auto !important;
      padding: 0 !important;
    }
    @media (max-width: 900px) {
      .nav-item-dropdown {
        width: 100%;
        display: block;
      }
      .nav-dropdown-menu {
        position: static;
        transform: none !important;
        width: 100%;
        max-width: 100%;
        box-shadow: none;
        border: 1px solid #E2E8F0;
        margin-top: 6px;
        display: none;
        opacity: 1;
        visibility: visible;
        pointer-events: auto;
      }
      .nav-item-dropdown.mobile-expanded .nav-dropdown-menu {
        display: block;
      }
      .nav-dropdown-grid {
        grid-template-columns: 1fr;
        gap: 10px;
      }
    }
"""

DROPDOWN_HTML = """      <div class="nav-item-dropdown" id="navCareerGuidesDropdown">
        <a href="/articles.html" class="nav-dropdown-trigger" onclick="if(window.innerWidth<=900){event.preventDefault();this.parentElement.classList.toggle('mobile-expanded');}">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          Career Guides
          <svg class="dropdown-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </a>
        <div class="nav-dropdown-menu">
          <div class="nav-dropdown-header">
            <span>Career Guides (30 Specialized Tracks)</span>
            <a href="/articles.html">Browse All &rarr;</a>
          </div>
          <div class="nav-dropdown-grid">
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">Engineering &amp; Dev</div>
              <a href="/jobs/software-engineer.html">Software Engineer</a>
              <a href="/jobs/full-stack-developer.html">Full-Stack Developer</a>
              <a href="/jobs/frontend-developer.html">Frontend Developer</a>
              <a href="/jobs/backend-developer.html">Backend Developer</a>
              <a href="/jobs/devops-engineer.html">DevOps Engineer</a>
              <a href="/jobs/cloud-engineer.html">Cloud Engineer</a>
              <a href="/jobs/site-reliability-engineer.html">Site Reliability Engineer</a>
              <a href="/jobs/systems-engineer.html">Systems Engineer</a>
            </div>
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">AI, Data &amp; Security</div>
              <a href="/jobs/data-scientist.html">Data Scientist</a>
              <a href="/jobs/machine-learning-engineer.html">ML Engineer</a>
              <a href="/jobs/data-engineer.html">Data Engineer</a>
              <a href="/jobs/data-analyst.html">Data Analyst</a>
              <a href="/jobs/ai-research-scientist.html">AI Research Scientist</a>
              <a href="/jobs/cybersecurity-engineer.html">Cybersecurity Engineer</a>
              <a href="/jobs/security-engineer.html">Security Engineer</a>
              <a href="/jobs/qa-automation-engineer.html">QA Automation Engineer</a>
            </div>
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">Product, Mobile &amp; Mgmt</div>
              <a href="/jobs/product-manager.html">Product Manager</a>
              <a href="/jobs/technical-program-manager.html">Tech Program Manager</a>
              <a href="/jobs/engineering-manager.html">Engineering Manager</a>
              <a href="/jobs/ui-ux-designer.html">UI/UX Designer</a>
              <a href="/jobs/product-designer.html">Product Designer</a>
              <a href="/jobs/mobile-app-developer.html">Mobile App Developer</a>
              <a href="/jobs/ios-developer.html">iOS Developer</a>
              <a href="/jobs/android-developer.html">Android Developer</a>
            </div>
          </div>
          <div class="nav-dropdown-footer">
            <div class="nav-dropdown-tags">
              <span class="nav-tag-label">Popular Filters:</span>
              <a href="/jobs.html?role=software+engineer&location=india" class="nav-tag-pill">India Jobs</a>
              <a href="/jobs.html?workplace=remote" class="nav-tag-pill">Remote Jobs</a>
              <a href="/jobs.html?experience=entry" class="nav-tag-pill">Entry Level</a>
            </div>
            <a href="/articles.html" class="nav-dropdown-all-btn">View All 30 Guides &rarr;</a>
          </div>
        </div>
      </div>"""

OLD_LINK_REGEX = re.compile(
    r'<a\s+href="/articles\.html"(?:\s+class="[^"]*")?>\s*<svg[^>]*>.*?</svg>\s*Career Guides\s*</a>',
    re.DOTALL
)

def update_file(path: Path):
    content = path.read_text(encoding="utf-8")
    modified = False

    # Check if inside site-nav-links we have the old link
    if "Career Guides" in content and "nav-item-dropdown" not in content:
        # Match only inside <header class="site-nav"> ... </header>
        header_match = re.search(r'(<header class="site-nav">.*?</header>)', content, re.DOTALL)
        if header_match:
            orig_header = header_match.group(1)
            new_header = OLD_LINK_REGEX.sub(DROPDOWN_HTML, orig_header)
            if new_header != orig_header:
                content = content.replace(orig_header, new_header)
                modified = True

    if modified or "Career Guides Menu Dropdown" not in content:
        if "</style>" in content and "Career Guides Menu Dropdown" not in content:
            # Insert NAV_CSS before the first or last </style>
            content = content.replace("</style>", NAV_CSS + "\n  </style>", 1)
            modified = True

    if modified:
        path.write_text(content, encoding="utf-8")
        print(f"Updated: {path.relative_to(ROOT_DIR)}")
    else:
        print(f"Skipped (already updated or no match): {path.relative_to(ROOT_DIR)}")

def main():
    target_files = [
        FRONTEND_DIR / "index.html",
        FRONTEND_DIR / "jobs.html",
        FRONTEND_DIR / "portfolio.html",
        FRONTEND_DIR / "contact.html",
        FRONTEND_DIR / "privacy.html",
        FRONTEND_DIR / "disclaimer.html",
        FRONTEND_DIR / "articles.html",
        FRONTEND_DIR / "article_template.html",
    ]
    # Add all files in frontend/jobs/*.html
    for jf in sorted((FRONTEND_DIR / "jobs").glob("*.html")):
        target_files.append(jf)

    for tf in target_files:
        if tf.exists():
            update_file(tf)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Update all frontend HTML pages to include the enhanced Career Guides (50 Specialized Tracks)
dropdown menu in the top navigation bar.
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
    .nav-item-dropdown.open .dropdown-chevron,
    .nav-item-dropdown.mobile-expanded .dropdown-chevron {
      transform: rotate(180deg);
    }
    .nav-dropdown-menu {
      position: absolute;
      top: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%) translateY(6px);
      width: 820px;
      max-width: 94vw;
      max-height: calc(85vh - 50px);
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior: contain;
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
    .nav-dropdown-menu::-webkit-scrollbar {
      width: 6px;
    }
    .nav-dropdown-menu::-webkit-scrollbar-track {
      background: #F8FAFC;
      border-radius: 4px;
    }
    .nav-dropdown-menu::-webkit-scrollbar-thumb {
      background: #CBD5E1;
      border-radius: 4px;
    }
    .nav-dropdown-menu::-webkit-scrollbar-thumb:hover {
      background: #94A3B8;
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
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
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
      font-size: 12.5px !important;
      color: #334155 !important;
      text-decoration: none;
      padding: 4px 6px !important;
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
      font-weight: 700 !important;
      text-decoration: none;
      height: auto !important;
      padding: 0 !important;
    }
    @media (max-width: 900px) {
      .site-nav-links {
        max-height: calc(100dvh - 70px) !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior: contain !important;
      }
      .site-nav-links::-webkit-scrollbar {
        width: 4px;
      }
      .site-nav-links::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
      }
      .nav-item-dropdown {
        width: 100%;
        display: block;
      }
      .nav-dropdown-trigger {
        width: 100%;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
      }
      .nav-dropdown-trigger .dropdown-chevron {
        margin-left: auto;
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
        max-height: 55vh;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior: contain !important;
        padding: 12px 14px;
      }
      .nav-item-dropdown.mobile-expanded .nav-dropdown-menu {
        display: block;
      }
      .nav-dropdown-header {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 12px;
        padding-bottom: 10px;
        margin-bottom: 12px;
        border-bottom: 1px solid #F1F5F9;
      }
      .nav-dropdown-header span {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #475569;
        line-height: 1.3;
        white-space: nowrap;
      }
      .nav-dropdown-header a {
        font-size: 11.5px !important;
        font-weight: 700 !important;
        color: #2563EB !important;
        background: #EFF6FF !important;
        border: 1px solid #DBEAFE !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        white-space: nowrap !important;
        line-height: 1 !important;
        margin-left: auto;
      }
      .nav-dropdown-grid {
        grid-template-columns: 1fr;
        gap: 10px;
      }
      .nav-dropdown-col {
        background: #F8FAFC;
        border: 1px solid #F1F5F9;
        border-radius: 10px;
        padding: 10px;
      }
      .nav-dropdown-cat {
        font-size: 11px;
        font-weight: 800;
        color: #2563EB;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 1px solid #E2E8F0;
      }
      .nav-dropdown-col a {
        display: block !important;
        font-size: 12px !important;
        color: #334155 !important;
        text-decoration: none;
        padding: 5px 8px !important;
        border-radius: 6px;
        margin-bottom: 2px;
        font-weight: 500 !important;
        transition: background 0.15s ease, color 0.15s ease;
      }
      .nav-dropdown-col a:hover,
      .nav-dropdown-col a:active {
        background: #EFF6FF !important;
        color: #1D4ED8 !important;
        font-weight: 600 !important;
      }
      .nav-dropdown-footer {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
      }
      .nav-dropdown-all-btn {
        width: 100%;
        text-align: center;
        padding: 8px 12px !important;
        background: #EFF6FF;
        border-radius: 6px;
        display: block !important;
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
            <span>Career Tracks (70 Guides)</span>
            <a href="/articles.html">Browse All 70 &rarr;</a>
          </div>
          <div class="nav-dropdown-grid">
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">Engineering &amp; Web</div>
              <a href="/jobs/software-engineer.html">Software Engineer</a>
              <a href="/jobs/full-stack-developer.html">Full-Stack Developer</a>
              <a href="/jobs/frontend-developer.html">Frontend Developer</a>
              <a href="/jobs/backend-developer.html">Backend Developer</a>
              <a href="/jobs/react-developer.html">React Developer</a>
              <a href="/jobs/nodejs-developer.html">Node.js Developer</a>
              <a href="/jobs/python-developer.html">Python Developer</a>
              <a href="/jobs/java-developer.html">Java Developer</a>
              <a href="/jobs/rust-developer.html">Rust Developer</a>
              <a href="/jobs/golang-developer.html">Golang Developer</a>
              <a href="/jobs/blockchain-engineer.html">Blockchain Engineer</a>
            </div>
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">Cloud, Sys &amp; Sec</div>
              <a href="/jobs/cloud-architect.html">Cloud Architect</a>
              <a href="/jobs/devops-engineer.html">DevOps Engineer</a>
              <a href="/jobs/cloud-engineer.html">Cloud Engineer</a>
              <a href="/jobs/site-reliability-engineer.html">Site Reliability (SRE)</a>
              <a href="/jobs/kubernetes-administrator.html">Kubernetes Admin</a>
              <a href="/jobs/platform-engineer.html">Platform Engineer</a>
              <a href="/jobs/cybersecurity-engineer.html">Cybersecurity Engineer</a>
              <a href="/jobs/penetration-tester.html">Penetration Tester</a>
              <a href="/jobs/soc-analyst.html">SOC Analyst</a>
              <a href="/jobs/infosec-analyst.html">InfoSec Analyst</a>
            </div>
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">AI, Data &amp; Analytics</div>
              <a href="/jobs/generative-ai-engineer.html">Generative AI Engineer</a>
              <a href="/jobs/machine-learning-engineer.html">ML Engineer</a>
              <a href="/jobs/ai-research-scientist.html">AI Research Scientist</a>
              <a href="/jobs/mlops-engineer.html">MLOps Engineer</a>
              <a href="/jobs/data-architect.html">Data Architect</a>
              <a href="/jobs/data-scientist.html">Data Scientist</a>
              <a href="/jobs/data-engineer.html">Data Engineer</a>
              <a href="/jobs/bi-developer.html">BI Developer</a>
              <a href="/jobs/quantitative-analyst.html">Quantitative Analyst</a>
              <a href="/jobs/etl-developer.html">ETL Developer</a>
            </div>
            <div class="nav-dropdown-col">
              <div class="nav-dropdown-cat">Product, Leadership &amp; Ops</div>
              <a href="/jobs/chief-technology-officer.html">CTO (Exec Leadership)</a>
              <a href="/jobs/staff-software-engineer.html">Staff Software Engineer</a>
              <a href="/jobs/principal-software-engineer.html">Principal Engineer</a>
              <a href="/jobs/product-manager.html">Product Manager</a>
              <a href="/jobs/product-operations-manager.html">Product Operations</a>
              <a href="/jobs/engineering-manager.html">Engineering Manager</a>
              <a href="/jobs/technical-program-manager.html">Tech Program Mgr</a>
              <a href="/jobs/ui-ux-designer.html">UI/UX Designer</a>
              <a href="/jobs/solutions-architect.html">Solutions Architect</a>
              <a href="/jobs/sdet-engineer.html">SDET / Automation</a>
            </div>
          </div>
          <div class="nav-dropdown-footer">
            <div class="nav-dropdown-tags">
              <span class="nav-tag-label">Popular Filters:</span>
              <a href="/jobs.html?role=software+engineer&location=india" class="nav-tag-pill">India Jobs</a>
              <a href="/jobs.html?workplace=remote" class="nav-tag-pill">Remote Jobs</a>
              <a href="/jobs.html?experience=entry" class="nav-tag-pill">Entry Level</a>
            </div>
            <a href="/articles.html" class="nav-dropdown-all-btn">View All 70 Career Guides &rarr;</a>
          </div>
        </div>
      </div>"""

EXISTING_DROPDOWN_REGEX = re.compile(
    r'<div class="nav-item-dropdown" id="navCareerGuidesDropdown">.*?</div>\s*</div>\s*</div>',
    re.DOTALL
)

OLD_LINK_REGEX = re.compile(
    r'<a\s+href="/articles\.html"(?:\s+class="[^"]*")?>\s*<svg[^>]*>.*?</svg>\s*Career Guides\s*</a>',
    re.DOTALL
)

def update_file(path: Path):
    content = path.read_text(encoding="utf-8")
    modified = False

    # 1. If existing dropdown is present, replace it with updated 50-guide dropdown
    if "navCareerGuidesDropdown" in content:
        new_content = EXISTING_DROPDOWN_REGEX.sub(DROPDOWN_HTML, content)
        if new_content != content:
            content = new_content
            modified = True
    elif "Career Guides" in content:
        # Match only inside <header class="site-nav"> ... </header>
        header_match = re.search(r'(<header class="site-nav">.*?</header>)', content, re.DOTALL)
        if header_match:
            orig_header = header_match.group(1)
            new_header = OLD_LINK_REGEX.sub(DROPDOWN_HTML, orig_header)
            if new_header != orig_header:
                content = content.replace(orig_header, new_header)
                modified = True

    # 2. Ensure updated CSS is present
    if "/* Career Guides Menu Dropdown */" in content:
        # Update CSS block
        css_pattern = re.compile(r'/\* Career Guides Menu Dropdown \*/.*?(?=</style>)', re.DOTALL)
        new_content = css_pattern.sub(NAV_CSS.strip() + "\n  ", content)
        if new_content != content:
            content = new_content
            modified = True
    else:
        if "</style>" in content:
            content = content.replace("</style>", NAV_CSS + "\n  </style>", 1)
            modified = True

    if modified:
        path.write_text(content, encoding="utf-8")
        print(f"Updated: {path.relative_to(ROOT_DIR)}")
    else:
        print(f"Skipped (already current): {path.relative_to(ROOT_DIR)}")

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

    print(f"Updating navigation bar across {len(target_files)} HTML pages...")
    for tf in target_files:
        if tf.exists():
            update_file(tf)

if __name__ == "__main__":
    main()

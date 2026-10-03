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
    .nav-guide-pill-count {
      font-size: 10px;
      font-weight: 700;
      line-height: 1;
      padding: 2px 6px;
      border-radius: 99px;
      background: #EEF2FF;
      color: #4F46E5;
      border: 1px solid #C7D2FE;
      margin-left: 2px;
      display: inline-flex;
      align-items: center;
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
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 0 16px !important;
        height: 42px !important;
        font-size: 14px !important;
        box-sizing: border-box !important;
        border-radius: 8px !important;
        transition: background 0.15s ease, color 0.15s ease;
      }
      .nav-dropdown-trigger .dropdown-chevron {
        margin-left: auto;
      }
      .nav-item-dropdown.mobile-expanded .nav-dropdown-trigger {
        background: #EEF2FF !important;
        color: #4F46E5 !important;
        font-weight: 700 !important;
      }
      .nav-item-dropdown.mobile-expanded .nav-dropdown-trigger .nav-guide-pill-count {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
        border-color: #4F46E5 !important;
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
        flex-wrap: nowrap;
        gap: 8px;
        padding-bottom: 10px;
        margin-bottom: 12px;
        border-bottom: 1px solid #F1F5F9;
      }
      .nav-dropdown-header span {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #475569;
        line-height: 1.2;
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
        flex-shrink: 0;
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

NAV_LINK_HTML = """      <a href="/articles.html" title="100 Tech Career Guides & Engineering Roadmaps">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        <span>Career Guides</span>
      </a>"""

NAV_LINK_ACTIVE_HTML = """      <a href="/articles.html" class="active" title="100 Tech Career Guides & Engineering Roadmaps">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        <span>Career Guides</span>
      </a>"""

def update_file(path: Path):
    content = path.read_text(encoding="utf-8")
    modified = False

    replacement = NAV_LINK_ACTIVE_HTML if path.name == "articles.html" else NAV_LINK_HTML

    # If dropdown is present, replace it with direct link
    if "navCareerGuidesDropdown" in content:
        lines = content.splitlines(keepends=True)
        start_idx = None
        for i, l in enumerate(lines):
            if 'id="navCareerGuidesDropdown"' in l:
                start_idx = i
                break
        if start_idx is not None:
            depth = 0
            end_idx = None
            for i in range(start_idx, len(lines)):
                depth += lines[i].count('<div')
                depth -= lines[i].count('</div')
                if depth == 0:
                    end_idx = i
                    break
            if end_idx is not None:
                content = "".join(lines[:start_idx]) + replacement + "\n" + "".join(lines[end_idx+1:])
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

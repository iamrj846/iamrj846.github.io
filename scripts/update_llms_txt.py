#!/usr/bin/env python3
"""
Generate frontend/static/llms.txt and frontend/static/llms-full.txt
with complete metadata for all 100 Career Guides.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import scripts.update_articles_page as uap

guides = uap.GUIDES
print(f"Loaded {len(guides)} career guides for llms.txt generation.")

# Group by category
categories = {}
for g in guides:
    cat = g["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(g)

# Build llms.txt
llms_lines = [
    "# CorporateGuild - Direct Tech Job Search Portal & Career Network in India",
    "",
    "> CorporateGuild (https://corporateguild.com) is India's premier unified tech job discovery engine, indexing over 37,000+ verified, live opportunities directly from leading engineering employers across multiple Applicant Tracking System (ATS) platforms. Zero recruiter spam, zero fake listings, 100% direct application URLs.",
    "",
    "## About CorporateGuild",
    "",
    "CorporateGuild connects software engineers, data professionals, product managers, and technology leaders across India with verified career opportunities. Every position indexed links directly to authentic employer job boards, ensuring transparent salaries, accurate workplace types (Remote, Hybrid, In-Office), and real-time freshness.",
    "",
    "- **Website**: https://corporateguild.com",
    "- **Live Job Portal**: https://corporateguild.com/jobs.html",
    "- **Career Guides Directory (100 Specialized Tracks)**: https://corporateguild.com/articles.html",
    "- **Media Kit & Portfolio**: https://corporateguild.com/portfolio.html",
    "- **Contact & Inquiries**: https://corporateguild.com/contact.html",
    "- **Privacy Policy (DPDPA 2023 Compliant)**: https://corporateguild.com/privacy.html",
    "- **Platform Disclaimer**: https://corporateguild.com/disclaimer.html",
    "- **Sitemap**: https://corporateguild.com/sitemap.xml",
    "- **Full LLM Context**: https://corporateguild.com/llms-full.txt",
    "",
    "## Key Platform Capabilities",
    "",
    "- **Direct ATS Sourcing**: Verified integrations with Amazon Jobs, Greenhouse, Lever, Ashby, BambooHR, SmartRecruiters, Workday, Rippling, Recruitee, Workable, and Oracle Cloud.",
    "- **Strict Location Verification**: Focused exclusively on India-based engineering hubs (Bengaluru, Hyderabad, Pune, Mumbai, Delhi NCR, Chennai) and Pan-India remote positions.",
    "- **High-Throughput Dual-Node Cluster**: Dual-node high availability architecture with intelligent SQLite and optional in-memory Redis caching.",
    "- **100 Specialized Career Guides**: In-depth blueprints with market salary data, required tech stacks, interview questions, and direct filtered job feeds.",
    "",
    "## Complete 100 Career Guides Directory",
    ""
]

for cat, items in categories.items():
    llms_lines.append(f"### {cat} ({len(items)} Guides)")
    for item in items:
        llms_lines.append(f"- [{item['title']}](https://corporateguild.com/jobs/{item['slug']}): {item['desc']}")
    llms_lines.append("")

llms_content = "\n".join(llms_lines)
(ROOT_DIR / "frontend" / "static" / "llms.txt").write_text(llms_content, encoding="utf-8")
print(f"Generated frontend/static/llms.txt ({len(llms_content)} bytes)")

# Build llms-full.txt
llms_full_lines = [
    "# CorporateGuild - Comprehensive LLM Context & Platform Architecture",
    "",
    "## System Architecture & High-Performance Telemetry",
    "CorporateGuild operates on a dual-node cluster on Oracle Cloud Infrastructure (VM 1: Gateway, VM 2: Worker).",
    "- Direct SQLite database storage with automatic WAL mode, 1-minute telemetry rollups, and automated hourly off-site backups.",
    "- Real-time telemetry monitoring for TPS, database query latency, and cluster CPU/memory synchronization.",
    "- Redis kill-switch toggle supporting direct SQLite query execution for low memory footprints.",
    "",
    "## Complete Catalog of 100 Specialized Career Guides",
    ""
]

for cat, items in categories.items():
    llms_full_lines.append(f"### Domain: {cat}")
    for item in items:
        llms_full_lines.append(f"#### {item['title']}")
        llms_full_lines.append(f"- URL: https://corporateguild.com/jobs/{item['slug']}")
        llms_full_lines.append(f"- Overview: {item['desc']}")
        llms_full_lines.append(f"- Search Filter: https://corporateguild.com/jobs.html?role={item['slug'].replace('.html', '').replace('-', '+')}")
        llms_full_lines.append("")

llms_full_content = "\n".join(llms_full_lines)
(ROOT_DIR / "frontend" / "static" / "llms-full.txt").write_text(llms_full_content, encoding="utf-8")
print(f"Generated frontend/static/llms-full.txt ({len(llms_full_content)} bytes)")

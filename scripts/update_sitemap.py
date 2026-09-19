#!/usr/bin/env python3
"""
Generate and update frontend/static/sitemap.xml with all pages and 30 career guide articles.
"""
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent
SITEMAP_PATH = ROOT_DIR / "frontend" / "static" / "sitemap.xml"
JOBS_DIR = ROOT_DIR / "frontend" / "jobs"

now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

pages = [
    ("https://corporateguild.com/", "1.0", "daily"),
    ("https://corporateguild.com/jobs.html", "0.9", "daily"),
    ("https://corporateguild.com/articles.html", "0.9", "daily"),
    ("https://corporateguild.com/portfolio.html", "0.8", "weekly"),
    ("https://corporateguild.com/contact.html", "0.7", "monthly"),
    ("https://corporateguild.com/privacy.html", "0.5", "monthly"),
    ("https://corporateguild.com/disclaimer.html", "0.5", "monthly"),
]

article_files = sorted([f.name for f in JOBS_DIR.glob("*.html")])

xml_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
]

for url, priority, changefreq in pages:
    xml_lines.append("  <url>")
    xml_lines.append(f"    <loc>{url}</loc>")
    xml_lines.append(f"    <lastmod>{now_iso}</lastmod>")
    xml_lines.append(f"    <changefreq>{changefreq}</changefreq>")
    xml_lines.append(f"    <priority>{priority}</priority>")
    xml_lines.append("  </url>")

for article in article_files:
    xml_lines.append("  <url>")
    xml_lines.append(f"    <loc>https://corporateguild.com/jobs/{article}</loc>")
    xml_lines.append(f"    <lastmod>{now_iso}</lastmod>")
    xml_lines.append("    <changefreq>weekly</changefreq>")
    xml_lines.append("    <priority>0.8</priority>")
    xml_lines.append("  </url>")

xml_lines.append("</urlset>\n")

SITEMAP_PATH.write_text("\n".join(xml_lines), encoding="utf-8")
print(f"Successfully wrote {len(pages) + len(article_files)} URLs to {SITEMAP_PATH}")

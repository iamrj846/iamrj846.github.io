#!/usr/bin/env python3
"""
Comprehensive Builder for frontend/articles.html:
- Full SEO & LLM optimization
- Structured Data (Organization, WebSite, CollectionPage, BreadcrumbList, ItemList with 100 items, FAQPage)
- Rich semantic content & 2026 Tech Market Analysis for search engine & LLM ranking
- Direct navbar link (NO DROPDOWN)
- Interactive category tabs & live search
- Content-visibility & contain-intrinsic-size for instant loading
- Full FAQ accordion with 6 high-value questions
"""

import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.update_articles_page import GUIDES

ARTICLES_PATH = ROOT_DIR / "frontend" / "articles.html"

# Category color map & styling
CAT_CONFIG = {
    "Engineering & Architecture": {
        "slug": "engineering",
        "label": "Engineering & Architecture",
        "short_label": "Engineering & Web",
        "color": "#4F46E5",
        "bg": "#EEF2FF",
        "border": "#C7D2FE"
    },
    "Cloud, DevOps & Infrastructure": {
        "slug": "cloud-devops",
        "label": "Cloud, DevOps & Infrastructure",
        "short_label": "Cloud & DevOps",
        "color": "#0284C7",
        "bg": "#F0F9FF",
        "border": "#BAE6FD"
    },
    "AI, ML & Data": {
        "slug": "ai-data",
        "label": "AI, ML & Data",
        "short_label": "AI & Data Science",
        "color": "#7C3AED",
        "bg": "#F5F3FF",
        "border": "#DDD6FE"
    },
    "Cybersecurity & Quality": {
        "slug": "cybersecurity-quality",
        "label": "Cybersecurity & Quality",
        "short_label": "Cybersecurity & QA",
        "color": "#DC2626",
        "bg": "#FEF2F2",
        "border": "#FECACA"
    },
    "Hardware & Embedded Systems": {
        "slug": "hardware-embedded",
        "label": "Hardware & Embedded Systems",
        "short_label": "Hardware & IoT",
        "color": "#D97706",
        "bg": "#FFFBEB",
        "border": "#FDE68A"
    },
    "Product, Design & Agile": {
        "slug": "product-design",
        "label": "Product, Design & Agile",
        "short_label": "Product & Design",
        "color": "#DB2777",
        "bg": "#FDF2F8",
        "border": "#FBCFE8"
    },
    "Leadership, Strategy & Operations": {
        "slug": "leadership-ops",
        "label": "Leadership, Strategy & Operations",
        "short_label": "Leadership & Ops",
        "color": "#059669",
        "bg": "#ECFDF5",
        "border": "#A7F3D0"
    }
}

FAQS = [
    {
        "question": "What are the most in-demand and highest-paying career tracks across industries in 2026?",
        "answer": "In 2026, the highest compensation benchmarks span technical specialization, corporate leadership, and cross-functional product operations. Top brackets include Artificial Intelligence & Data Science Specialists, Cloud & Enterprise Architects, Engineering & Product Directors, Cybersecurity Leads, and Staff/Principal Systems Engineers. In global markets, senior individual contributors and department heads command total packages from $160,000 to $350,000+. In India's premier metropolitan centers (Bengaluru, Hyderabad, Mumbai, Pune, NCR), senior specialists earn between ₹25,00,000 and ₹90,00,000+ per annum."
    },
    {
        "question": "How do professionals transition across disciplines or into high-growth technical and data fields?",
        "answer": "Successful career transitions in 2026 rely on demonstrated portfolio execution rather than theoretical certificates alone. Key milestones include: 1) Translating previous domain expertise into measurable system or business outcomes; 2) Mastering production-grade workflows and domain tools (e.g. asynchronous Python, transformer fine-tuning, cloud infrastructure, or agile product telemetry); 3) Building publicly auditable case studies and open-source contributions; and 4) Developing cross-functional fluency across engineering, data analysis, and product management."
    },
    {
        "question": "How do modern corporate organizations structure technical versus managerial career paths?",
        "answer": "Modern corporate organizations utilize parallel dual-track career ladders: 1) Individual Contributor (IC) Track: Progressing from Senior to Staff, Principal, and Distinguished levels, focusing on deep architectural direction, organizational leverage, and system reliability without direct people management; 2) Management & Leadership Track: Progressing through Engineering Manager, Director, and VP of Operations, concentrating on team hiring, people mentorship, cross-team resource allocation, and organizational strategy."
    },
    {
        "question": "Are remote and hybrid employment opportunities continuing to grow in 2026?",
        "answer": "Yes. While several enterprises have established structured hybrid rhythms, high-growth technology companies, decentralized startups, and international enterprises recruit aggressively for distributed talent across engineering, product management, design, and operations. Candidates with strong asynchronous collaboration skills, disciplined autonomous ownership, and transparent sprint reporting access global compensation packages through modern Employer of Record (EOR) frameworks."
    },
    {
        "question": "How should senior candidates prepare for high-level technical and executive interview loops?",
        "answer": "Senior interview processes evaluate systemic capability and business impact: 1) Architecture & Systems Thinking: Designing scalable, fault-tolerant solutions under real-world trade-offs in consistency, latency, and operational cost; 2) Leadership & Execution: Demonstrating strategic vision, technical debt mitigation, stakeholder conflict resolution, and talent elevation. CorporateGuild provides role-tailored roadmaps with authentic interview blueprints for each discipline."
    },
    {
        "question": "How often does CorporateGuild update these 100 career guides and salary benchmarks?",
        "answer": "CorporateGuild updates these blueprints continuously. Our real-time data pipeline ingests and parses thousands of authentic job postings directly from premier enterprise Applicant Tracking Systems (ATS) including Greenhouse, Lever, Workday, and SmartRecruiters. This ensures that skills matrices, technology demand indicators, and compensation benchmarks accurately reflect live market hiring conditions."
    }
]

def build_schema_json():
    item_elements = []
    for idx, guide in enumerate(GUIDES, start=1):
        slug = guide["slug"]
        if not slug.startswith("/"):
            url = f"https://corporateguild.com/jobs/{slug}"
        else:
            url = f"https://corporateguild.com{slug}"
        item_elements.append({
            "@type": "ListItem",
            "position": idx,
            "name": guide["title"],
            "url": url,
            "description": guide["desc"]
        })

    faq_elements = []
    for faq in FAQS:
        faq_elements.append({
            "@type": "Question",
            "name": faq["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq["answer"]
            }
        })

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": "https://corporateguild.com/#organization",
                "name": "CorporateGuild",
                "alternateName": "CorporateGuild | @it_jobs_and_internships",
                "url": "https://corporateguild.com",
                "logo": "https://corporateguild.com/logo.png",
                "description": "Premier ATS job search and career community platform. Discover verified career and job opportunities across top companies with real-time ATS integration.",
                "sameAs": [
                    "https://www.instagram.com/it_jobs_and_internships",
                    "https://www.facebook.com/itjobsandinternships/",
                    "https://www.threads.net/@it_jobs_and_internships",
                    "https://www.youtube.com/@it_jobs_and_internships",
                    "https://www.linkedin.com/in/it-jobs-and-internships/"
                ],
                "contactPoint": {
                    "@type": "ContactPoint",
                    "contactType": "Customer Support & Partnerships",
                    "email": "support@corporateguild.com",
                    "url": "https://corporateguild.com/contact.html"
                }
            },
            {
                "@type": "WebSite",
                "@id": "https://corporateguild.com/#website",
                "url": "https://corporateguild.com",
                "name": "CorporateGuild",
                "publisher": {
                    "@id": "https://corporateguild.com/#organization"
                }
            },
            {
                "@type": "CollectionPage",
                "@id": "https://corporateguild.com/articles.html#collectionpage",
                "url": "https://corporateguild.com/articles.html",
                "name": "100 Career Guides, Industry Roadmaps & Job Blueprints (2026) | CorporateGuild",
                "headline": "100 Comprehensive Career Guides & Industry Roadmaps (2026)",
                "description": "Explore 100 comprehensive career guides, industry roadmaps, salary insights, skills matrices, and interview strategies across technology, engineering, product leadership, corporate operations, design, and analytics.",
                "isPartOf": {
                    "@id": "https://corporateguild.com/#website"
                },
                "breadcrumb": {
                    "@id": "https://corporateguild.com/articles.html#breadcrumb"
                },
                "inLanguage": "en-US",
                "datePublished": "2026-01-01T00:00:00+00:00",
                "dateModified": "2026-10-04T00:00:00+00:00"
            },
            {
                "@type": "BreadcrumbList",
                "@id": "https://corporateguild.com/articles.html#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": "https://corporateguild.com/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Career Guides",
                        "item": "https://corporateguild.com/articles.html"
                    }
                ]
            },
            {
                "@type": "ItemList",
                "@id": "https://corporateguild.com/articles.html#itemlist",
                "name": "100 Career Guides, Industry Roadmaps & Job Blueprints",
                "description": "Complete directory of 100 specialized career guides, salary benchmarks, and interview frameworks across all professional employment sectors.",
                "numberOfItems": len(GUIDES),
                "itemListElement": item_elements
            },
            {
                "@type": "FAQPage",
                "@id": "https://corporateguild.com/articles.html#faq",
                "mainEntity": faq_elements
            }
        ]
    }
    return json.dumps(schema, indent=2)

def generate_cards_html():
    cards = []
    for idx, g in enumerate(GUIDES):
        slug = g["slug"]
        if not slug.startswith("/"):
            href = f"/jobs/{slug}"
        else:
            href = slug
        
        cat_name = g.get("category", "Engineering & Architecture")
        cat_conf = CAT_CONFIG.get(cat_name, CAT_CONFIG["Engineering & Architecture"])
        cat_slug = cat_conf["slug"]
        color = g.get("color", cat_conf["color"])
        icon_path = g.get("icon", '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>')
        
        # Performance optimization: below fold cards receive content-visibility: auto
        # Initial fold: cards 0-5 (first 6 cards)
        deferred_class = " guide-card-deferred" if idx >= 6 else ""

        card_html = f"""      <!-- Card {idx+1}: {g['title']} -->
      <a href="{href}" class="career-guide-card-link{deferred_class}" data-title="{g['title'].lower()}" data-category="{cat_slug}" data-category-name="{cat_name.lower()}" aria-label="Explore {g['title']} Career Blueprint">
        <article class="guide-card">
          <div class="guide-card-top">
            <div class="guide-icon-box" style="background: {color}14; color: {color}; border-color: {color}30;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                {icon_path}
              </svg>
            </div>
            <div class="guide-meta-col">
              <span class="guide-cat-badge" style="color: {color}; background: {color}10; border-color: {color}25;">{cat_name}</span>
              <h2 class="guide-card-title">{g['title']}</h2>
            </div>
          </div>
          <p class="guide-card-desc">{g['desc']}</p>
          <div class="guide-card-footer">
            <span class="guide-read-text">Read Career Blueprint</span>
            <svg class="guide-read-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </div>
        </article>
      </a>"""
        cards.append(card_html)
    return "\n".join(cards)

def generate_faqs_html():
    faq_items = []
    for idx, faq in enumerate(FAQS, start=1):
        faq_items.append(f"""        <details class="faq-item" id="faq-item-{idx}">
          <summary class="faq-summary">
            <span class="faq-question-text">{faq['question']}</span>
            <span class="faq-toggle-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </span>
          </summary>
          <div class="faq-answer">
            <p>{faq['answer']}</p>
          </div>
        </details>""")
    return "\n".join(faq_items)

def build_full_html():
    schema_json = build_schema_json()
    cards_html = generate_cards_html()
    faqs_html = generate_faqs_html()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-GS94NDX6SC"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-GS94NDX6SC');
  </script>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>100 Career Guides, Industry Roadmaps & Job Blueprints (2026) | CorporateGuild</title>
  <link rel="icon" type="image/png" href="/logo.png"/>
  <link rel="shortcut icon" href="/favicon.ico"/>
  <link rel="apple-touch-icon" href="/logo.png"/>
  <meta name="description" content="Explore 100 comprehensive career guides, industry roadmaps, salary insights, skills matrices, and interview strategies across technology, engineering, product leadership, corporate operations, design, and analytics."/>
  <meta name="keywords" content="career guides, industry roadmaps, job blueprints, professional development, career path 2026, corporate careers, software engineer roadmap, product manager guide, data scientist salary, devops interview, cloud architect certifications, executive leadership, salary benchmarks 2026, corporate guild career blueprints"/>
  <meta name="author" content="CorporateGuild Editorial Team"/>
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"/>
  <link rel="canonical" href="https://corporateguild.com/articles.html"/>
  <link rel="manifest" href="/manifest.json"/>
  <link rel="author" href="/humans.txt"/>
  <link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml"/>

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website"/>
  <meta property="og:url" content="https://corporateguild.com/articles.html"/>
  <meta property="og:title" content="100 Career Guides, Industry Roadmaps & Job Blueprints (2026) | CorporateGuild"/>
  <meta property="og:description" content="Explore 100 comprehensive career guides, industry roadmaps, salary insights, skills matrices, and interview strategies across technology, engineering, product leadership, corporate operations, design, and analytics."/>
  <meta property="og:image" content="https://corporateguild.com/logo.png"/>
  <meta property="og:site_name" content="CorporateGuild"/>
  <meta property="og:locale" content="en_US"/>

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image"/>
  <meta name="twitter:site" content="@it_jobs_and_internships"/>
  <meta name="twitter:title" content="100 Career Guides, Industry Roadmaps & Job Blueprints (2026) | CorporateGuild"/>
  <meta name="twitter:description" content="Explore 100 comprehensive career guides, industry roadmaps, salary insights, skills matrices, and interview strategies across technology, engineering, product leadership, corporate operations, design, and analytics."/>
  <meta name="twitter:image" content="https://corporateguild.com/logo.png"/>

  <!-- Schema.org Structured Data -->
  <script type="application/ld+json">
{schema_json}
  </script>

  <style>
    /* ══ RESET & ROOT VARIABLES (MODERN LIGHT SaaS THEME) ══ */
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
    :root {{
      --bg: #F8FAFC;
      --card-bg: #FFFFFF;
      --card-bdr: #E2E8F0;
      --card-bdr-hover: #CBD5E1;
      --card-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
      --card-shadow-hover: 0 12px 30px -4px rgba(79, 70, 229, 0.12), 0 4px 10px -2px rgba(15, 23, 42, 0.04);
      --accent: #4F46E5;
      --accent-light: #EEF2FF;
      --accent-hover: #4338CA;
      --pink: #DB2777;
      --blue: #2563EB;
      --emerald: #059669;
      --amber: #D97706;
      --txt-main: #0F172A;
      --txt-muted: #475569;
      --txt-dim: #64748B;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background:
        radial-gradient(circle at 15% 10%, rgba(99, 102, 241, 0.06), transparent 35%),
        radial-gradient(circle at 85% 20%, rgba(219, 39, 119, 0.04), transparent 30%),
        var(--bg);
      color: var(--txt-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
      line-height: 1.6;
    }}

    /* ══ TOP GLOBAL NAVIGATION (LIGHT & MODERN) ══ */
    .site-nav {{
      position: sticky; top: 0; z-index: 1000;
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-bdr);
      padding: 0 24px;
      height: 64px;
      box-sizing: border-box;
      display: flex; align-items: center; justify-content: space-between;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }}
    .site-nav-brand {{
      display: flex; align-items: center; gap: 12px;
      text-decoration: none; color: var(--txt-main);
      transition: transform 0.2s ease;
    }}
    .site-logo-frame {{
      width: 44px; height: 44px; border-radius: 50%;
      background: #FFFFFF;
      border: 2px solid #E0E7FF;
      box-shadow: 0 4px 14px -2px rgba(79, 70, 229, 0.16), 0 2px 6px -1px rgba(15, 23, 42, 0.06);
      display: flex; align-items: center; justify-content: center;
      padding: 3px; flex-shrink: 0;
      overflow: hidden;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .site-nav-brand:hover .site-logo-frame {{
      transform: translateY(-1.5px) scale(1.05);
      border-color: #6366F1;
      box-shadow: 0 8px 22px -3px rgba(79, 70, 229, 0.28), 0 2px 6px rgba(15, 23, 42, 0.08);
    }}
    .site-logo-frame img {{
      width: 100%; height: 100%; object-fit: contain;
      border-radius: 50%;
      display: block;
    }}
    .brand-lockup {{
      display: flex; align-items: center; gap: 8px;
    }}
    .site-brand-text {{
      font-size: 19px; letter-spacing: -0.035em;
      display: inline-flex; align-items: center; line-height: 1;
    }}
    .brand-word-corporate {{
      font-weight: 850;
      background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #2563EB 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      filter: drop-shadow(0 1px 2px rgba(79, 70, 229, 0.18));
    }}
    .brand-word-guild {{
      font-weight: 900;
      background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #2563EB 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      filter: drop-shadow(0 1px 2px rgba(79, 70, 229, 0.18));
    }}
    .site-nav-links {{
      display: flex; align-items: center; gap: 4px; flex-shrink: 0; flex-wrap: nowrap;
    }}
    .site-nav-links a {{
      text-decoration: none; color: #475569; font-size: 13px; font-weight: 600;
      padding: 0 11px; height: 36px; border-radius: 8px; transition: all 0.18s ease;
      display: inline-flex; align-items: center; justify-content: center; gap: 6px;
      white-space: nowrap; flex-shrink: 0; box-sizing: border-box;
    }}
    .site-nav-links a svg {{ color: currentColor; flex-shrink: 0; }}
    .site-nav-links a:hover {{
      color: #0F172A; background: #F1F5F9;
    }}
    .site-nav-links a.active {{
      color: #4F46E5; background: #EEF2FF; font-weight: 700;
    }}

    .nav-hamburger {{
      display: none;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      background: #F1F5F9;
      border: 1px solid var(--card-bdr);
      border-radius: 10px;
      cursor: pointer;
      color: var(--txt-main);
      transition: all 0.2s ease;
    }}
    .nav-hamburger:hover {{
      background: #E2E8F0;
    }}

    /* ══ BREADCRUMBS & HERO SECTION ══ */
    .hero-section {{
      padding: 44px 20px 24px;
      background: linear-gradient(180deg, rgba(79,70,229,0.06) 0%, rgba(248,250,252,0) 100%);
      border-bottom: 1px solid rgba(226, 232, 240, 0.7);
    }}
    .hero-container {{
      max-width: 1100px;
      margin: 0 auto;
      text-align: center;
    }}
    .breadcrumb-nav {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--txt-dim);
      margin-bottom: 18px;
      font-weight: 500;
    }}
    .breadcrumb-nav a {{
      color: var(--txt-muted);
      text-decoration: none;
      transition: color 0.15s ease;
    }}
    .breadcrumb-nav a:hover {{
      color: var(--accent);
    }}
    .breadcrumb-sep {{
      color: #CBD5E1;
    }}
    .hero-badge-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 16px;
      border-radius: 99px;
      background: #EEF2FF;
      border: 1px solid #C7D2FE;
      color: #4338CA;
      font-size: 12px;
      font-weight: 750;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }}
    .hero-badge-dot {{
      width: 7px; height: 7px; border-radius: 50%;
      background: #10B981;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.8);
    }}
    .hero-h1 {{
      font-size: clamp(28px, 4.5vw, 44px);
      font-weight: 900;
      color: #0F172A;
      letter-spacing: -0.03em;
      line-height: 1.2;
      margin-bottom: 14px;
    }}
    .hero-subtitle {{
      font-size: clamp(15px, 2vw, 17.5px);
      color: var(--txt-muted);
      max-width: 760px;
      margin: 0 auto 26px;
      line-height: 1.6;
    }}
    .hero-stats-row {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 10px;
    }}
    .hero-stat-chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      padding: 7px 16px;
      border-radius: 99px;
      font-size: 13px;
      color: #334155;
      font-weight: 600;
      box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }}
    .hero-stat-chip strong {{
      color: #0F172A;
      font-weight: 800;
    }}

    /* ══ EDITORIAL OVERVIEW & MARKET ANALYSIS (SEO & LLM KNOWLEDGE BASE) ══ */
    .market-analysis-section {{
      max-width: 1140px;
      margin: 36px auto 0;
      padding: 0 20px;
    }}
    .market-analysis-card {{
      background: #FFFFFF;
      border: 1px solid var(--card-bdr);
      border-radius: 20px;
      padding: 36px 36px;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);
    }}
    .market-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #4F46E5;
      background: #EEF2FF;
      border: 1px solid #C7D2FE;
      padding: 4px 12px;
      border-radius: 99px;
      margin-bottom: 14px;
    }}
    .market-title {{
      font-size: clamp(20px, 2.8vw, 26px);
      font-weight: 850;
      color: #0F172A;
      letter-spacing: -0.02em;
      margin-bottom: 14px;
      line-height: 1.3;
    }}
    .market-lead {{
      font-size: 15px;
      color: #334155;
      line-height: 1.7;
      margin-bottom: 24px;
    }}
    .market-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }}
    .market-column {{
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 14px;
      padding: 22px;
    }}
    .market-column-title {{
      font-size: 15px;
      font-weight: 800;
      color: #0F172A;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .market-column-text {{
      font-size: 13.5px;
      color: #475569;
      line-height: 1.6;
    }}

    /* ══ INTERACTIVE FILTER & SEARCH CONSOLE ══ */
    .filter-console-section {{
      max-width: 1140px;
      margin: 32px auto 0;
      padding: 0 20px;
      position: relative;
      z-index: 10;
    }}
    .search-input-box {{
      background: #FFFFFF;
      border: 1.5px solid #CBD5E1;
      border-radius: 16px;
      box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.08);
      padding: 6px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      transition: all 0.2s ease;
      margin-bottom: 16px;
    }}
    .search-input-box:focus-within {{
      border-color: #4F46E5;
      box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.12), 0 8px 24px -4px rgba(79, 70, 229, 0.15);
    }}
    .search-input-box svg {{
      color: #94A3B8;
      flex-shrink: 0;
    }}
    .guide-search-input {{
      width: 100%;
      border: none;
      outline: none;
      font-size: 15px;
      font-weight: 500;
      color: var(--txt-main);
      background: transparent;
      padding: 8px 0;
    }}
    .guide-search-input::placeholder {{
      color: #94A3B8;
    }}
    .btn-clear-search {{
      background: none;
      border: none;
      color: #94A3B8;
      cursor: pointer;
      font-size: 20px;
      padding: 2px 8px;
      line-height: 1;
      transition: color 0.15s;
    }}
    .btn-clear-search:hover {{
      color: #0F172A;
    }}
    .search-shortcut-hint {{
      font-size: 11px;
      font-weight: 700;
      background: #F1F5F9;
      border: 1px solid #CBD5E1;
      border-radius: 6px;
      padding: 3px 7px;
      color: #64748B;
      white-space: nowrap;
      user-select: none;
    }}

    /* Category Filter Tabs */
    .category-tabs-bar {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      max-width: 100%;
      box-sizing: border-box;
      padding-bottom: 6px;
    }}
    @media (max-width: 768px) {{
      .category-tabs-bar {{
        justify-content: center;
        gap: 6px;
      }}
      .cat-tab-btn {{
        font-size: 12px;
        padding: 6px 12px;
      }}
    }}
    .cat-tab-btn {{
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      padding: 7px 14px;
      border-radius: 99px;
      font-size: 13px;
      font-weight: 600;
      color: #475569;
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.18s ease;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
      flex-shrink: 0;
    }}
    .cat-tab-btn:hover {{
      background: #F8FAFC;
      border-color: #CBD5E1;
      color: #0F172A;
    }}
    .cat-tab-btn.active {{
      background: #4F46E5;
      border-color: #4F46E5;
      color: #FFFFFF;
      font-weight: 700;
      box-shadow: 0 2px 8px rgba(79, 70, 229, 0.28);
    }}
    .cat-tab-count {{
      font-size: 11px;
      font-weight: 700;
      background: rgba(15, 23, 42, 0.08);
      color: inherit;
      padding: 1px 7px;
      border-radius: 99px;
    }}
    .cat-tab-btn.active .cat-tab-count {{
      background: rgba(255, 255, 255, 0.25);
      color: #FFFFFF;
    }}

    .filter-count-status {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 14px;
      font-size: 13.5px;
      color: var(--txt-muted);
      font-weight: 500;
      padding: 0 4px;
    }}
    .filter-count-status strong {{
      color: #0F172A;
    }}

    /* ══ CAREER GUIDES GRID & CARDS ══ */
    .guides-catalog-main {{
      max-width: 1140px;
      margin: 24px auto 48px;
      padding: 0 20px;
      width: 100%;
    }}
    .guides-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 22px;
    }}
    .career-guide-card-link {{
      text-decoration: none;
      display: block;
      color: inherit;
    }}
    .guide-card {{
      background: #FFFFFF;
      border: 1px solid var(--card-bdr);
      border-radius: 16px;
      padding: 24px;
      box-shadow: var(--card-shadow);
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
      height: 100%;
      display: flex;
      flex-direction: column;
      box-sizing: border-box;
      position: relative;
    }}
    .guide-card:hover {{
      transform: translateY(-3px);
      border-color: #A5B4FC;
      box-shadow: var(--card-shadow-hover);
    }}
    .guide-card-top {{
      display: flex;
      align-items: flex-start;
      gap: 14px;
      margin-bottom: 14px;
    }}
    .guide-icon-box {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      border: 1px solid transparent;
      transition: transform 0.2s ease;
    }}
    .guide-card:hover .guide-icon-box {{
      transform: scale(1.06);
    }}
    .guide-meta-col {{
      flex: 1;
      min-width: 0;
    }}
    .guide-cat-badge {{
      display: inline-block;
      font-size: 10.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 2px 8px;
      border-radius: 6px;
      border: 1px solid transparent;
      margin-bottom: 4px;
      line-height: 1.4;
    }}
    .guide-card-title {{
      font-size: 17.5px;
      font-weight: 750;
      color: var(--txt-main);
      margin: 0;
      line-height: 1.3;
      letter-spacing: -0.015em;
    }}
    .guide-card-desc {{
      color: var(--txt-muted);
      font-size: 13.5px;
      line-height: 1.55;
      margin: 0 0 18px;
      flex-grow: 1;
    }}
    .guide-card-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid #F1F5F9;
      padding-top: 12px;
      font-size: 13px;
      font-weight: 700;
      color: #4F46E5;
      transition: color 0.15s ease;
    }}
    .guide-card:hover .guide-card-footer {{
      color: #3730A3;
    }}
    .guide-read-arrow {{
      transition: transform 0.2s ease;
    }}
    .guide-card:hover .guide-read-arrow {{
      transform: translateX(4px);
    }}

    /* Performance optimization via Modern Web Guidance */
    /* Defer rendering calculations for offscreen content */
    .guide-card-deferred {{
      content-visibility: auto;
      contain-intrinsic-size: auto none auto 240px;
    }}

    /* Empty state */
    .no-results-card {{
      display: none;
      text-align: center;
      padding: 50px 20px;
      background: #FFFFFF;
      border: 1px dashed #CBD5E1;
      border-radius: 16px;
      margin: 20px auto;
      max-width: 500px;
    }}
    .no-results-card h3 {{
      font-size: 18px;
      font-weight: 800;
      color: #0F172A;
      margin-bottom: 6px;
    }}
    .no-results-card p {{
      font-size: 14px;
      color: #64748B;
      margin-bottom: 16px;
    }}
    .btn-reset-filter {{
      background: #4F46E5;
      color: #FFFFFF;
      border: none;
      padding: 8px 18px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
    }}

    /* ══ PAGINATION CONTROLS ══ */
    .pagination-container {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin: 36px auto 16px;
      flex-wrap: wrap;
    }}
    .pagination-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 40px;
      height: 40px;
      padding: 0 14px;
      border-radius: 10px;
      border: 1px solid var(--card-bdr);
      background: #FFFFFF;
      color: var(--txt-main);
      font-size: 13.5px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.18s ease;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
      user-select: none;
    }}
    .pagination-btn:hover:not(:disabled) {{
      background: #F1F5F9;
      border-color: #CBD5E1;
      color: #0F172A;
      transform: translateY(-1px);
    }}
    .pagination-btn.active {{
      background: #4F46E5;
      border-color: #4F46E5;
      color: #FFFFFF;
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
    }}
    .pagination-btn:disabled {{
      opacity: 0.35;
      cursor: not-allowed;
      background: #F8FAFC;
      border-color: #E2E8F0;
      color: #94A3B8;
    }}
    .pagination-ellipsis {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 28px;
      height: 40px;
      color: #94A3B8;
      font-weight: 800;
      font-size: 15px;
    }}

    /* ══ FREQUENTLY ASKED QUESTIONS SECTION ══ */
    .faq-section {{
      max-width: 900px;
      margin: 20px auto 48px;
      padding: 0 20px;
    }}
    .faq-header {{
      text-align: center;
      margin-bottom: 28px;
    }}
    .faq-title {{
      font-size: 26px;
      font-weight: 850;
      color: #0F172A;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }}
    .faq-subtitle {{
      font-size: 14.5px;
      color: var(--txt-muted);
    }}
    .faq-list {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .faq-item {{
      background: #FFFFFF;
      border: 1px solid var(--card-bdr);
      border-radius: 14px;
      overflow: hidden;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .faq-item[open] {{
      border-color: #C7D2FE;
      box-shadow: 0 4px 16px rgba(79, 70, 229, 0.08);
    }}
    .faq-summary {{
      padding: 18px 22px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      user-select: none;
      font-size: 15.5px;
      font-weight: 750;
      color: #0F172A;
      list-style: none;
    }}
    .faq-summary::-webkit-details-marker {{
      display: none;
    }}
    .faq-toggle-icon {{
      color: #64748B;
      transition: transform 0.2s ease;
      flex-shrink: 0;
    }}
    .faq-item[open] .faq-toggle-icon {{
      transform: rotate(180deg);
      color: #4F46E5;
    }}
    .faq-answer {{
      padding: 0 22px 20px;
      font-size: 14.5px;
      color: #475569;
      line-height: 1.65;
      border-top: 1px solid #F8FAFC;
    }}

    /* ══ CALL TO ACTION (JOB PORTAL & MEDIA KIT) ══ */
    .cta-banner-section {{
      max-width: 1100px;
      margin: 0 auto 56px;
      padding: 0 20px;
    }}
    .cta-banner-card {{
      background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
      border-radius: 24px;
      padding: 44px 36px;
      color: #FFFFFF;
      text-align: center;
      box-shadow: 0 16px 36px -6px rgba(79, 70, 229, 0.3);
      position: relative;
      overflow: hidden;
    }}
    .cta-banner-title {{
      font-size: clamp(22px, 3.2vw, 32px);
      font-weight: 850;
      letter-spacing: -0.02em;
      margin-bottom: 12px;
    }}
    .cta-banner-desc {{
      font-size: clamp(14.5px, 1.8vw, 16px);
      color: #E0E7FF;
      max-width: 680px;
      margin: 0 auto 28px;
      line-height: 1.6;
    }}
    .cta-actions-row {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .btn-cta-primary {{
      background: #FFFFFF;
      color: #312E81;
      font-size: 14.5px;
      font-weight: 800;
      padding: 12px 24px;
      border-radius: 12px;
      text-decoration: none;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-cta-primary:hover {{
      transform: translateY(-2px);
      background: #F8FAFC;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.22);
    }}
    .btn-cta-secondary {{
      background: rgba(255, 255, 255, 0.12);
      color: #FFFFFF;
      border: 1px solid rgba(255, 255, 255, 0.3);
      font-size: 14.5px;
      font-weight: 700;
      padding: 12px 24px;
      border-radius: 12px;
      text-decoration: none;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-cta-secondary:hover {{
      background: rgba(255, 255, 255, 0.2);
      border-color: rgba(255, 255, 255, 0.5);
    }}

    /* ══ GLOBAL FOOTER ══ */
    .site-footer {{
      background: #FFFFFF;
      border-top: 1px solid var(--card-bdr);
      padding: 32px 20px;
      text-align: center;
      font-size: 13.5px;
      color: var(--txt-dim);
      margin-top: auto;
    }}
    .site-footer a {{
      color: var(--txt-muted);
      text-decoration: none;
      font-weight: 600;
      margin: 0 6px;
      transition: color 0.15s;
    }}
    .site-footer a:hover, .site-footer a.active {{
      color: var(--accent);
    }}

    /* ══ RESPONSIVE ADAPTATIONS ══ */
    @media (max-width: 900px) {{
      .site-nav-links {{
        display: none;
        position: fixed;
        top: 64px; left: 0; right: 0;
        background: #FFFFFF;
        border-bottom: 1px solid var(--card-bdr);
        flex-direction: column;
        padding: 16px 20px;
        gap: 6px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
      }}
      .site-nav-links.open {{
        display: flex;
      }}
      .site-nav-links a {{
        width: 100%;
        justify-content: flex-start;
        height: 40px;
        padding: 0 14px;
        font-size: 14px;
      }}
      .nav-hamburger {{
        display: flex;
      }}
      .market-analysis-card {{
        padding: 24px 20px;
      }}
      .cta-banner-card {{
        padding: 32px 20px;
      }}
    }}

    @media (max-width: 640px) {{
      .hero-section {{
        padding: 24px 16px 20px !important;
      }}
      .hero-badge-pill {{
        font-size: 11px !important;
        padding: 5px 12px !important;
        margin-bottom: 12px !important;
        max-width: 100% !important;
        line-height: 1.35 !important;
      }}
      .hero-h1 {{
        font-size: 25px !important;
        line-height: 1.25 !important;
        margin-bottom: 10px !important;
      }}
      .hero-subtitle {{
        font-size: 13.5px !important;
        line-height: 1.55 !important;
        margin-bottom: 18px !important;
      }}
      .hero-stats-row {{
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 8px !important;
        width: 100% !important;
        max-width: 440px !important;
        margin: 12px auto 0 !important;
      }}
      .hero-stat-chip {{
        padding: 9px 8px !important;
        border-radius: 12px !important;
        font-size: 11.5px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        gap: 2px !important;
        min-height: 52px !important;
        box-sizing: border-box !important;
      }}
      .hero-stat-chip strong {{
        font-size: 12.5px !important;
      }}
    }}

    /* ══ DIRECT APPLY GUARANTEE BANNER ══ */
    .direct-apply-guarantee-banner {{
      background: linear-gradient(135deg, #F0FDF4 0%, #EFF6FF 100%);
      border: 1.5px solid #BBF7D0;
      border-radius: 16px;
      padding: 14px 20px;
      margin: 20px auto 16px;
      max-width: 1140px;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: 0 2px 10px rgba(16, 185, 129, 0.05);
    }}
    .guarantee-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #FFFFFF;
      border: 1px solid #86EFAC;
      color: #065F46;
      font-size: 12px;
      font-weight: 800;
      padding: 5px 12px;
      border-radius: 99px;
      white-space: nowrap;
      flex-shrink: 0;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .guarantee-text {{
      font-size: 13.5px;
      color: #1E293B;
      line-height: 1.55;
      margin: 0;
    }}
    @media (max-width: 640px) {{
      .direct-apply-guarantee-banner {{
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        padding: 12px 14px;
      }}
      .guarantee-text {{ font-size: 12.5px; }}
    }}

    /* ══ ROLES HORIZONTAL BAND ══ */
    .roles-band-container {{
      max-width: 1140px;
      margin: 0 auto 20px;
      padding: 0 4px;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 12px;
      overflow: hidden;
    }}
    .roles-band-label {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12.5px;
      font-weight: 750;
      color: #475569;
      white-space: nowrap;
      flex-shrink: 0;
    }}
    .pulse-green-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10B981;
      display: inline-block;
      animation: pulseGreen 2s infinite;
    }}
    @keyframes pulseGreen {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.3); opacity: 0.6; }}
    }}
    .roles-band-track {{
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      padding: 4px 2px;
      flex: 1;
    }}
    .roles-band-track::-webkit-scrollbar {{ display: none; }}
    .role-band-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      color: #1E293B;
      padding: 6px 13px;
      border-radius: 99px;
      font-size: 12.5px;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      user-select: none;
      text-decoration: none;
    }}
    .role-band-chip:hover {{
      border-color: #818CF8;
      background: #EEF2FF;
      color: #3730A3;
      transform: translateY(-1.5px);
      box-shadow: 0 3px 8px rgba(99, 102, 241, 0.15);
    }}
    .chip-count {{
      font-size: 11px;
      font-weight: 750;
      color: #059669;
      background: #ECFDF5;
      padding: 1px 6px;
      border-radius: 99px;
      border: 1px solid #A7F3D0;
    }}
    .role-band-chip.chip-all {{
      background: #4F46E5;
      color: #FFFFFF;
      border-color: #4F46E5;
    }}
    .role-band-chip.chip-all .chip-count {{
      background: rgba(255, 255, 255, 0.25);
      color: #FFFFFF;
      border-color: transparent;
    }}

    /* ══ ANIMATED WORD CLOUD ══ */
    .word-cloud-section {{
      max-width: 1140px;
      margin: 36px auto;
      padding: 26px 20px;
      background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
      text-align: center;
      overflow: hidden;
      box-sizing: border-box;
    }}
    .word-cloud-header {{
      margin-bottom: 20px;
    }}
    .word-cloud-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #ECFDF5;
      border: 1px solid #A7F3D0;
      color: #065F46;
      font-size: 11.5px;
      font-weight: 750;
      padding: 3px 10px;
      border-radius: 99px;
      margin-bottom: 8px;
    }}
    .word-cloud-title {{
      font-size: 20px;
      font-weight: 850;
      color: #0F172A;
      margin-bottom: 6px;
      letter-spacing: -0.02em;
    }}
    .word-cloud-subtitle {{
      font-size: 13.5px;
      color: #64748B;
      max-width: 600px;
      margin: 0 auto;
    }}
    .word-cloud-canvas {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 18px;
      overflow: hidden;
      position: relative;
    }}
    .word-cloud-canvas::before, .word-cloud-canvas::after {{
      content: "";
      position: absolute;
      top: 0; bottom: 0;
      width: 40px;
      z-index: 2;
      pointer-events: none;
    }}
    .word-cloud-canvas::before {{
      left: 0;
      background: linear-gradient(90deg, #FFFFFF 0%, transparent 100%);
    }}
    .word-cloud-canvas::after {{
      right: 0;
      background: linear-gradient(270deg, #F8FAFC 0%, transparent 100%);
    }}
    .word-cloud-stream {{
      display: flex;
      align-items: center;
      gap: 12px;
      white-space: nowrap;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
      animation-duration: 35s;
    }}
    .stream-left-to-right {{
      animation-name: marqueeLeft;
    }}
    .stream-right-to-left {{
      animation-name: marqueeRight;
    }}
    @keyframes marqueeLeft {{
      0% {{ transform: translateX(0); }}
      100% {{ transform: translateX(-50%); }}
    }}
    @keyframes marqueeRight {{
      0% {{ transform: translateX(-50%); }}
      100% {{ transform: translateX(0); }}
    }}
    .word-cloud-stream:hover {{
      animation-play-state: paused;
    }}
    .wc-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 15px;
      border-radius: 99px;
      font-size: 13px;
      font-weight: 700;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0,0,0,0.04);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      flex-shrink: 0;
      text-decoration: none;
    }}
    .wc-tag:hover {{
      transform: translateY(-2px) scale(1.04);
      box-shadow: 0 6px 16px rgba(0,0,0,0.09);
    }}
    .wc-glow-blue {{ color: #1D4ED8; border-color: #BFDBFE; background: #EFF6FF; }}
    .wc-glow-indigo {{ color: #4338CA; border-color: #C7D2FE; background: #EEF2FF; }}
    .wc-glow-emerald {{ color: #047857; border-color: #A7F3D0; background: #ECFDF5; }}
    .wc-glow-purple {{ color: #6D28D9; border-color: #DDD6FE; background: #F5F3FF; }}
    .wc-glow-pink {{ color: #BE185D; border-color: #FBCFE8; background: #FDF2F8; }}
    .wc-glow-amber {{ color: #B45309; border-color: #FDE68A; background: #FFFBEB; }}
    .wc-glow-cyan {{ color: #0E7490; border-color: #A5F3FC; background: #ECFEFF; }}
    .wc-ats {{
      font-size: 10px;
      padding: 2px 5px;
      border-radius: 4px;
      background: rgba(0,0,0,0.06);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    /* ══ TRADITIONAL JOB BOARDS VS CORPORATEGUILD TABLE ══ */
    .comparison-section {{
      max-width: 1140px;
      margin: 36px auto;
      padding: 30px 24px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
      box-sizing: border-box;
    }}
    .comparison-header {{
      text-align: center;
      margin-bottom: 22px;
    }}
    .comparison-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11.5px;
      font-weight: 750;
      color: #4338CA;
      background: #EEF2FF;
      border: 1px solid #C7D2FE;
      padding: 3px 11px;
      border-radius: 99px;
      margin-bottom: 8px;
    }}
    .comparison-title {{
      font-size: 22px;
      font-weight: 850;
      color: #0F172A;
      margin-bottom: 6px;
      letter-spacing: -0.02em;
    }}
    .comparison-subtitle {{
      font-size: 13.5px;
      color: #64748B;
      max-width: 620px;
      margin: 0 auto;
    }}
    .comparison-table-wrapper {{
      overflow-x: auto;
      margin-top: 16px;
      border-radius: 14px;
      border: 1px solid #E2E8F0;
    }}
    .comparison-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13.5px;
    }}
    .comparison-table th, .comparison-table td {{
      padding: 13px 18px;
      border-bottom: 1px solid #F1F5F9;
    }}
    .comparison-table th {{
      background: #F8FAFC;
      font-weight: 750;
      color: #334155;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .th-traditional {{
      background: #FEF2F2 !important;
      color: #991B1B !important;
    }}
    .th-corporateguild {{
      background: #ECFDF5 !important;
      color: #065F46 !important;
    }}
    .table-brand-pill {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-weight: 850;
      color: #047857;
    }}
    .td-traditional {{
      color: #64748B;
      background: rgba(254, 242, 242, 0.3);
    }}
    .td-cg {{
      background: rgba(236, 253, 245, 0.45);
      color: #0F172A;
    }}
    .cross-mark {{
      color: #DC2626;
      font-weight: 800;
      margin-right: 6px;
    }}
    .check-mark {{
      color: #059669;
      font-weight: 800;
      margin-right: 6px;
    }}
  </style>
</head>
<body>

  <!-- Top Global Navbar (Home, Job Portal, Media Kit, Career Guides, Contact, Privacy, Disclaimer) -->
  <header class="site-nav">
    <a href="/index.html" class="site-nav-brand">
      <div class="site-logo-frame">
        <img src="/logo.png" alt="CorporateGuild">
      </div>
      <div class="brand-lockup">
        <span class="site-brand-text">
          <span class="brand-word-corporate">Corporate</span><span class="brand-word-guild">Guild</span>
        </span>
      </div>
    </a>

    <!-- Hamburger Menu Button for Smaller Screens -->
    <button class="nav-hamburger" id="navHamburger" aria-label="Toggle Navigation" onclick="toggleMobileNav()">
      <svg class="hamburger-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
      </svg>
      <svg class="close-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="display: none;">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>

    <nav class="site-nav-links" id="siteNavLinks">
      <a href="/index.html">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>Home</span>
      </a>
      <a href="/jobs.html">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
        <span>Job Portal</span>
      </a>
      <a href="/portfolio.html" title="Our Portfolio and Media Kit">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        <span>Portfolio & Media Kit</span>
      </a>
      <a href="/articles.html" class="active" title="100 Tech Career Guides & Engineering Roadmaps">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        <span>Career Guides</span>
      </a>
      <a href="/contact.html">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
        <span>Contact</span>
      </a>
      <a href="/privacy.html">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span>Privacy</span>
      </a>
      <a href="/disclaimer.html">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        <span>Disclaimer</span>
      </a>
    </nav>
  </header>

  <!-- Hero & Breadcrumb Section -->
  <section class="hero-section">
    <div class="hero-container">
      <nav class="breadcrumb-nav" aria-label="Breadcrumb">
        <a href="/index.html">Home</a>
        <span class="breadcrumb-sep">/</span>
        <span style="color: var(--txt-main); font-weight: 600;">Career Guides</span>
      </nav>
      <div class="hero-badge-pill">
        <span class="hero-badge-dot"></span>
        <span>2026 Professional Career & Employment Roadmaps</span>
      </div>
      <h1 class="hero-h1">100 Comprehensive Career Guides & Industry Roadmaps</h1>
      <p class="hero-subtitle">
        Curated professional blueprints, compensation benchmarks, core competency matrices, and verified ATS recruitment roadmaps across 100 specialized employment disciplines.
      </p>
      <div class="hero-stats-row">
        <span class="hero-stat-chip"><strong>100</strong><span>Professional Blueprints</span></span>
        <span class="hero-stat-chip"><strong>7</strong><span>Employment Domains</span></span>
        <span class="hero-stat-chip"><strong>₹8L - ₹1.5Cr+</strong><span>Salary Benchmarks</span></span>
        <span class="hero-stat-chip"><strong>Real-Time</strong><span>ATS Integration</span></span>
      </div>
    </div>
  </section>

  <!-- Direct Apply Guarantee Banner (Trust & No Intermediaries) -->
  <div class="direct-apply-guarantee-banner" style="max-width: 1140px; margin: 20px auto 16px; padding: 0 20px; box-sizing: border-box;">
    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #EFF6FF 100%); border: 1.5px solid #BBF7D0; border-radius: 16px; padding: 14px 20px; display: flex; align-items: center; gap: 14px; box-shadow: 0 2px 10px rgba(16, 185, 129, 0.05); width: 100%; box-sizing: border-box;">
      <div class="guarantee-badge">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        <span>Direct Company Applications</span>
      </div>
      <p class="guarantee-text">
        Unlike traditional job aggregators that redirect you through spammy forms, ad walls, or third-party recruiters, <strong>CorporateGuild provides verified direct links to apply on official company career portals and ATS pages in one place.</strong>
      </p>
    </div>
  </div>

  <!-- Horizontal Band for Job Roles with Count of Jobs -->
  <div class="roles-band-container" style="max-width: 1140px; margin: 0 auto 20px; padding: 0 20px;" aria-label="Browse Jobs by Role">
    <div class="roles-band-label">
      <span class="pulse-green-dot"></span>
      <span>Popular Roles:</span>
    </div>
    <div class="roles-band-track" id="rolesBandTrack">
      <a href="/jobs.html?role=Software%20Engineer" class="role-band-chip">💻 Software Engineer <span class="chip-count">14.2k</span></a>
      <a href="/jobs.html?role=Full%20Stack%20Developer" class="role-band-chip">🚀 Full Stack Developer <span class="chip-count">6.8k</span></a>
      <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="role-band-chip">🤖 AI &amp; ML Engineer <span class="chip-count">3.4k</span></a>
      <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="role-band-chip">☁️ DevOps &amp; Cloud <span class="chip-count">4.1k</span></a>
      <a href="/jobs.html?role=Data%20Scientist" class="role-band-chip">📊 Data Scientist <span class="chip-count">3.9k</span></a>
      <a href="/jobs.html?role=Product%20Manager" class="role-band-chip">💼 Product Manager <span class="chip-count">1.8k</span></a>
      <a href="/jobs.html?role=Cybersecurity%20Engineer" class="role-band-chip">🛡️ Cybersecurity <span class="chip-count">1.2k</span></a>
      <a href="/jobs.html?role=UI%2FUX%20Designer" class="role-band-chip">🎨 UI/UX Design <span class="chip-count">980</span></a>
      <a href="/jobs.html?role=Backend%20Developer" class="role-band-chip">⚙️ Backend Developer <span class="chip-count">5.2k</span></a>
      <a href="/jobs.html?role=Frontend%20Developer" class="role-band-chip">✨ Frontend Developer <span class="chip-count">4.6k</span></a>
      <a href="/jobs.html?role=Mobile%20Engineer" class="role-band-chip">📱 Mobile Developer <span class="chip-count">1.6k</span></a>
      <a href="/jobs.html" class="role-band-chip chip-all">🌐 Browse All Jobs <span class="chip-count">26k+</span></a>
    </div>
  </div>

  <!-- In-Depth Tech Market Analysis & Editorial (SEO & LLM Knowledge Base) -->
  <section class="market-analysis-section">
    <article class="market-analysis-card">
      <div class="market-badge">2026 Global Employment & Career Intelligence</div>
      <h2 class="market-title">The Modern Employment Landscape: Cross-Industry Transformation, Specialization & Career Agility</h2>
      <p class="market-lead">
        The global employment and professional hiring ecosystem in 2026 has crossed a structural turning point. Across technology, product leadership, finance, operations, data intelligence, and corporate governance, top employers no longer evaluate candidates merely on conventional credentials or memorized checklists. Today's high-impact hiring managers actively seek holistic execution ability, problem-solving depth, systems design thinking, and cross-functional leadership.
      </p>

      <div class="market-grid">
        <div class="market-column">
          <h3 class="market-column-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.2"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
            Software, Systems & Web Architecture
          </h3>
          <p class="market-column-text">
            Polyglot engineering and systems agility thrive. High-concurrency systems rely on Go and Rust for memory safety and sub-millisecond latency, while Python and TypeScript power modern application layers and developer ecosystems.
          </p>
        </div>

        <div class="market-column">
          <h3 class="market-column-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>
            Cloud Infrastructure, DevOps & SRE
          </h3>
          <p class="market-column-text">
            Cloud infrastructure standardization around Kubernetes, multi-cloud governance, and automated CI/CD pipelines has elevated reliability engineering into a core discipline across global modern enterprises.
          </p>
        </div>

        <div class="market-column">
          <h3 class="market-column-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2"><circle cx="12" cy="12" r="3"/><path d="M3 9h2a7 7 0 0 1 14 0h2"/></svg>
            AI, Machine Learning & Data Platforms
          </h3>
          <p class="market-column-text">
            Data intelligence drives critical enterprise strategy. High-demand disciplines include production model deployment, agentic orchestration, data warehousing, business intelligence, and real-time streaming analytics pipelines.
          </p>
        </div>

        <div class="market-column">
          <h3 class="market-column-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Cybersecurity, Compliance & Quality Assurance
          </h3>
          <p class="market-column-text">
            With software supply chain threats and global regulatory compliance expanding, DevSecOps, identity and access governance, risk management, and rigorous automated quality assurance are mission-critical across all industries.
          </p>
        </div>

        <div class="market-column">
          <h3 class="market-column-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DB2777" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            Product Strategy, UI/UX & Agile Delivery
          </h3>
          <p class="market-column-text">
            High-converting digital experiences require unified product management, intuitive human-centered design systems, technical program management, and data-backed feature roadmaps that deliver customer value rapidly.
          </p>
        </div>

        <div class="market-column">
          <h3 class="market-column-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Corporate Leadership & Business Operations
          </h3>
          <p class="market-column-text">
            Dual-track career architectures provide autonomy for both senior individual contributors (Staff/Principal) and people leaders (Engineering Managers, Directors, Operations Leads) to align company strategy with flawless execution.
          </p>
        </div>
      </div>
    </article>
  </section>

  <!-- Interactive Filter & Search Console -->
  <section class="filter-console-section">
    <div class="search-input-box">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input
        type="text"
        id="guideSearchInput"
        class="guide-search-input"
        placeholder="Search 100 career blueprints by title, skill, or role (e.g., Full Stack, MLOps, SRE, Rust, Kubernetes, Staff Engineer)..."
        aria-label="Filter career guides"
        oninput="filterCareerGuides()"
      />
      <button type="button" id="clearGuideBtn" class="btn-clear-search" onclick="clearGuideSearch()" style="display: none;" title="Clear search">&times;</button>
      <span class="search-shortcut-hint">/</span>
    </div>

    <!-- Category Filter Tabs -->
    <div class="category-tabs-bar" role="tablist" aria-label="Filter by Domain">
      <button type="button" class="cat-tab-btn active" data-category="all" onclick="setCategoryFilter('all', this)" role="tab" aria-selected="true">
        <span>All Tracks</span>
        <span class="cat-tab-count">100</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="engineering" onclick="setCategoryFilter('engineering', this)" role="tab" aria-selected="false">
        <span>Engineering & Web</span>
        <span class="cat-tab-count">30</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="cloud-devops" onclick="setCategoryFilter('cloud-devops', this)" role="tab" aria-selected="false">
        <span>Cloud & DevOps</span>
        <span class="cat-tab-count">15</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="ai-data" onclick="setCategoryFilter('ai-data', this)" role="tab" aria-selected="false">
        <span>AI & Data Science</span>
        <span class="cat-tab-count">23</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="cybersecurity-quality" onclick="setCategoryFilter('cybersecurity-quality', this)" role="tab" aria-selected="false">
        <span>Cybersecurity & QA</span>
        <span class="cat-tab-count">11</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="hardware-embedded" onclick="setCategoryFilter('hardware-embedded', this)" role="tab" aria-selected="false">
        <span>Hardware & IoT</span>
        <span class="cat-tab-count">5</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="product-design" onclick="setCategoryFilter('product-design', this)" role="tab" aria-selected="false">
        <span>Product & Design</span>
        <span class="cat-tab-count">7</span>
      </button>
      <button type="button" class="cat-tab-btn" data-category="leadership-ops" onclick="setCategoryFilter('leadership-ops', this)" role="tab" aria-selected="false">
        <span>Leadership & Ops</span>
        <span class="cat-tab-count">9</span>
      </button>
    </div>

    <div class="filter-count-status">
      <span id="guideCountNotice">Showing all <strong>100</strong> specialized career blueprints</span>
      <span style="font-size: 12.5px; color: var(--txt-dim);">Updated October 2026</span>
    </div>
  </section>

  <!-- Main Career Guides Catalog Grid -->
  <main class="guides-catalog-main">
    <div id="guidesGrid" class="guides-grid">
{cards_html}
    </div>

    <!-- Career Guides Pagination Controls -->
    <div id="paginationContainer" class="pagination-container" role="navigation" aria-label="Career Guides Pagination"></div>

    <!-- Empty State Fallback -->
    <div id="noResultsCard" class="no-results-card">
      <h3>No career blueprints found</h3>
      <p>No guides match your active search terms. Try searching for a broader discipline or reset the active filter.</p>
      <button type="button" class="btn-reset-filter" onclick="clearGuideSearch()">Reset Search & View All 100 Guides</button>
    </div>
  </main>

  <!-- ══ ANIMATED WORD CLOUD SECTION ══ -->
  <section class="word-cloud-section" aria-label="Verified Job Sources and Roles Cloud">
    <div class="word-cloud-header">
      <div class="word-cloud-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        <span>Verified Ecosystem</span>
      </div>
      <h2 class="word-cloud-title">Verified Hiring Sources &amp; High-Growth Disciplines</h2>
      <p class="word-cloud-subtitle">Direct ATS integrations across Tier-1 tech enterprises, high-growth scale-ups, and global innovation centers</p>
    </div>
    <div class="word-cloud-canvas">
      <div class="word-cloud-stream stream-left-to-right">
        <a href="/jobs.html?q=Google" class="wc-tag wc-company wc-glow-blue">🏢 Google <small class="wc-ats">ATS Direct</small></a>
        <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="wc-tag wc-role wc-glow-indigo">🤖 Generative AI Engineer</a>
        <a href="/jobs.html?q=Microsoft" class="wc-tag wc-company wc-glow-emerald">🏢 Microsoft</a>
        <a href="/jobs.html?role=Full%20Stack%20Developer" class="wc-tag wc-role wc-glow-purple">🚀 Full-Stack Architect</a>
        <a href="/jobs.html?q=Amazon" class="wc-tag wc-company wc-glow-amber">🏢 Amazon</a>
        <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="wc-tag wc-role wc-glow-cyan">☁️ Cloud Platform Engineer</a>
        <a href="/jobs.html?q=NVIDIA" class="wc-tag wc-company wc-glow-pink">🏢 NVIDIA</a>
        <a href="/jobs.html?role=Data%20Scientist" class="wc-tag wc-role wc-glow-blue">📊 Principal Data Scientist</a>
        <a href="/jobs.html?q=Apple" class="wc-tag wc-company wc-glow-indigo">🏢 Apple</a>
        <a href="/jobs.html?role=Site%20Reliability%20Engineer" class="wc-tag wc-role wc-glow-emerald">🛡️ Site Reliability Engineer</a>
      </div>
      <div class="word-cloud-stream stream-right-to-left">
        <a href="/jobs.html?q=Workday" class="wc-tag wc-company wc-glow-purple">⚡ Workday ATS</a>
        <a href="/jobs.html?role=Software%20Engineer" class="wc-tag wc-role wc-glow-amber">💻 Senior Software Engineer</a>
        <a href="/jobs.html?q=Greenhouse" class="wc-tag wc-company wc-glow-blue">⚡ Greenhouse ATS</a>
        <a href="/jobs.html?role=Product%20Manager" class="wc-tag wc-role wc-glow-pink">💼 Technical Product Manager</a>
        <a href="/jobs.html?q=Lever" class="wc-tag wc-company wc-glow-cyan">⚡ Lever Portal</a>
        <a href="/jobs.html?role=Golang%20Developer" class="wc-tag wc-role wc-glow-emerald">⚡ Go Systems Engineer</a>
        <a href="/jobs.html?q=Meta" class="wc-tag wc-company wc-glow-indigo">🏢 Meta</a>
        <a href="/jobs.html?role=Rust%20Developer" class="wc-tag wc-role wc-glow-purple">🦀 Rust Low-Latency Systems</a>
        <a href="/jobs.html?q=SmartRecruiters" class="wc-tag wc-company wc-glow-amber">⚡ SmartRecruiters</a>
        <a href="/jobs.html?role=Cybersecurity%20Engineer" class="wc-tag wc-role wc-glow-blue">🔒 DevSecOps Lead</a>
      </div>
    </div>
  </section>

  <!-- ══ TRADITIONAL JOB BOARDS VS CORPORATEGUILD TABLE ══ -->
  <section class="comparison-section" aria-label="Traditional Job Boards vs CorporateGuild">
    <div class="comparison-header">
      <span class="comparison-badge">Transparent Comparison</span>
      <h2 class="comparison-title">Traditional Job Boards vs. CorporateGuild</h2>
      <p class="comparison-subtitle">See why thousands of candidates choose direct application over aggregator runarounds</p>
    </div>
    <div class="comparison-table-wrapper">
      <table class="comparison-table">
        <thead>
          <tr>
            <th style="width: 32%;">Key Feature</th>
            <th style="width: 34%;" class="th-traditional">Traditional Job Boards</th>
            <th style="width: 34%;" class="th-corporateguild">
              <span class="table-brand-pill">✓ CorporateGuild</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Application Destination</strong></td>
            <td class="td-traditional"><span class="cross-mark">✕</span> Spammy redirect forms &amp; third-party loops</td>
            <td class="td-cg"><span class="check-mark">✓</span> <strong>100% Direct to Official Company ATS</strong></td>
          </tr>
          <tr>
            <td><strong>Listing Freshness</strong></td>
            <td class="td-traditional"><span class="cross-mark">✕</span> Stale listings active for 60–90+ days</td>
            <td class="td-cg"><span class="check-mark">✓</span> <strong>Strict 14-Day Automated Purge Policy</strong></td>
          </tr>
          <tr>
            <td><strong>Listing Deduplication</strong></td>
            <td class="td-traditional"><span class="cross-mark">✕</span> Multiple duplicate entries for 1 position</td>
            <td class="td-cg"><span class="check-mark">✓</span> <strong>Unique Job ID &amp; Zero DB Duplication</strong></td>
          </tr>
          <tr>
            <td><strong>Candidate Privacy</strong></td>
            <td class="td-traditional"><span class="cross-mark">✕</span> Resumes sold to third-party telemarketers</td>
            <td class="td-cg"><span class="check-mark">✓</span> <strong>Zero Data Selling; 100% Private</strong></td>
          </tr>
          <tr>
            <td><strong>Access &amp; Pricing</strong></td>
            <td class="td-traditional"><span class="cross-mark">✕</span> Paid subscriptions &amp; recruiter paywalls</td>
            <td class="td-cg"><span class="check-mark">✓</span> <strong>100% Free Forever (Quick 2-min verification)</strong></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- Comprehensive FAQ Section (Rich Snippets & LLM Context) -->
  <section class="faq-section" id="faqs">
    <div class="faq-header">
      <h2 class="faq-title">Frequently Asked Questions</h2>
      <p class="faq-subtitle">Authoritative insights into professional career paths, market compensation benchmarks, and interview strategies across industries.</p>
    </div>
    <div class="faq-list">
{faqs_html}
    </div>
  </section>

  <!-- Call to Action Banner -->
  <section class="cta-banner-section">
    <div class="cta-banner-card">
      <h2 class="cta-banner-title">Ready to Explore Verified Job Openings?</h2>
      <p class="cta-banner-desc">
        Connect directly with enterprise ATS pipelines at Google, Amazon, Microsoft, and thousands of venture-backed startups with real-time application verification.
      </p>
      <div class="cta-actions-row">
        <a href="/jobs.html" class="btn-cta-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
          Explore Live Job Portal
        </a>
        <a href="/contact.html" class="btn-cta-secondary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
          Contact Inquiry Desk
        </a>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="site-footer">
    <div style="margin-bottom: 8px;">
      <a href="/index.html">Home</a> &bull;
      <a href="/jobs.html">Job Search Portal</a> &bull;
      <a href="/portfolio.html">Portfolio &amp; Media Kit</a> &bull;
      <a href="/articles.html" class="active">Career Guides</a> &bull;
      <a href="/contact.html">Contact Desk</a> &bull;
      <a href="/privacy.html">Privacy Policy</a> &bull;
      <a href="/disclaimer.html">Disclaimer</a>
    </div>
    <p style="margin-bottom: 6px; font-size: 13px;">Support &amp; Inquiries: <a href="mailto:support@corporateguild.com" style="color: inherit; text-decoration: underline; font-weight: 600;">support@corporateguild.com</a></p>
    <p>&copy; 2026 CorporateGuild. All rights reserved. Real-Time Careers Network.</p>
  </footer>

  <!-- Client Application Script (Lightweight, Accessible, Fast) -->
  <!-- Client Application Script (Lightweight, Accessible, Fast, Paginated) -->
  <script>
    const PAGE_SIZE = 16;
    let activeCategory = 'all';
    let currentPage = 1;
    let matchingCards = [];

    // Mobile Navigation Toggle
    function toggleMobileNav() {{
      const navLinks = document.getElementById('siteNavLinks');
      const navHamburger = document.getElementById('navHamburger');
      if (!navLinks || !navHamburger) return;
      const isOpen = navLinks.classList.toggle('open');
      const hamIcon = navHamburger.querySelector('.hamburger-icon');
      const closeIcon = navHamburger.querySelector('.close-icon');
      if (hamIcon && closeIcon) {{
        hamIcon.style.display = isOpen ? 'none' : 'block';
        closeIcon.style.display = isOpen ? 'block' : 'none';
      }}
    }}

    // Close mobile nav when clicking outside
    document.addEventListener('click', (e) => {{
      const siteNav = document.querySelector('.site-nav');
      const navLinks = document.getElementById('siteNavLinks');
      const navHamburger = document.getElementById('navHamburger');
      if (navLinks && navLinks.classList.contains('open') && siteNav && !siteNav.contains(e.target)) {{
        navLinks.classList.remove('open');
        if (navHamburger) {{
          const hamIcon = navHamburger.querySelector('.hamburger-icon');
          const closeIcon = navHamburger.querySelector('.close-icon');
          if (hamIcon && closeIcon) {{
            hamIcon.style.display = 'block';
            closeIcon.style.display = 'none';
          }}
        }}
      }}
    }});

    // Category Filter Selection
    function setCategoryFilter(category, btnElement) {{
      activeCategory = category;
      const buttons = document.querySelectorAll('.cat-tab-btn');
      buttons.forEach(btn => {{
        const isCurrent = btn === btnElement;
        btn.classList.toggle('active', isCurrent);
        btn.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
      }});
      currentPage = 1;
      filterCareerGuides();
    }}

    // Filter career guides by search input and active category
    function filterCareerGuides() {{
      const input = document.getElementById('guideSearchInput');
      const val = (input ? input.value : '').trim().toLowerCase();
      const clearBtn = document.getElementById('clearGuideBtn');
      if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';

      const cards = Array.from(document.querySelectorAll('.career-guide-card-link'));
      matchingCards = [];

      cards.forEach(card => {{
        const title = card.getAttribute('data-title') || '';
        const cat = card.getAttribute('data-category') || '';
        const catName = card.getAttribute('data-category-name') || '';

        const matchesQuery = !val || title.includes(val) || catName.includes(val);
        const matchesCategory = (activeCategory === 'all') || (cat === activeCategory);

        if (matchesQuery && matchesCategory) {{
          matchingCards.push(card);
        }} else {{
          card.style.display = 'none';
        }}
      }});

      renderCurrentPage();
    }}

    // Render cards for current page slice and update pagination UI
    function renderCurrentPage() {{
      const total = matchingCards.length;
      const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const startIndex = (currentPage - 1) * PAGE_SIZE;
      const endIndex = Math.min(startIndex + PAGE_SIZE, total);

      matchingCards.forEach((card, idx) => {{
        if (idx >= startIndex && idx < endIndex) {{
          card.style.display = 'block';
        }} else {{
          card.style.display = 'none';
        }}
      }});

      const notice = document.getElementById('guideCountNotice');
      if (notice) {{
        if (total === 0) {{
          notice.innerHTML = 'No career blueprints match your search';
        }} else if (total === 100) {{
          notice.innerHTML = `Showing <strong>${{startIndex + 1}}–${{endIndex}}</strong> of <strong>100</strong> career blueprints (Page ${{currentPage}} of ${{totalPages}})`;
        }} else {{
          notice.innerHTML = `Showing <strong>${{startIndex + 1}}–${{endIndex}}</strong> of <strong>${{total}}</strong> matching blueprints (Page ${{currentPage}} of ${{totalPages}})`;
        }}
      }}

      const noResults = document.getElementById('noResultsCard');
      if (noResults) {{
        noResults.style.display = (total === 0) ? 'block' : 'none';
      }}

      renderPaginationControls(totalPages);
    }}

    function goToPage(page) {{
      currentPage = page;
      renderCurrentPage();
      const consoleEl = document.querySelector('.filter-console-section');
      if (consoleEl) {{
        consoleEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }}

    function renderPaginationControls(totalPages) {{
      const container = document.getElementById('paginationContainer');
      if (!container) return;
      if (totalPages <= 1) {{
        container.innerHTML = '';
        container.style.display = 'none';
        return;
      }}

      container.style.display = 'flex';
      let html = '';

      const prevDisabled = currentPage === 1 ? 'disabled' : '';
      html += `<button type="button" class="pagination-btn" ${{prevDisabled}} onclick="goToPage(${{currentPage - 1}})" aria-label="Previous Page">&laquo; Prev</button>`;

      const pages = getPaginationNumbers(currentPage, totalPages);
      pages.forEach(p => {{
        if (p === '...') {{
          html += `<span class="pagination-ellipsis">&hellip;</span>`;
        }} else {{
          const isActive = (p === currentPage) ? 'active' : '';
          const ariaCurrent = (p === currentPage) ? 'aria-current="page"' : '';
          html += `<button type="button" class="pagination-btn ${{isActive}}" ${{ariaCurrent}} onclick="goToPage(${{p}})" aria-label="Page ${{p}}">${{p}}</button>`;
        }}
      }});

      const nextDisabled = currentPage === totalPages ? 'disabled' : '';
      html += `<button type="button" class="pagination-btn" ${{nextDisabled}} onclick="goToPage(${{currentPage + 1}})" aria-label="Next Page">Next &raquo;</button>`;

      container.innerHTML = html;
    }}

    function getPaginationNumbers(current, total) {{
      if (total <= 7) {{
        const arr = [];
        for (let i = 1; i <= total; i++) arr.push(i);
        return arr;
      }}
      if (current <= 4) {{
        return [1, 2, 3, 4, 5, '...', total];
      }}
      if (current >= total - 3) {{
        return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
      }}
      return [1, '...', current - 1, current, current + 1, '...', total];
    }}

    // Clear search
    function clearGuideSearch() {{
      const input = document.getElementById('guideSearchInput');
      if (input) {{
        input.value = '';
      }}
      activeCategory = 'all';
      currentPage = 1;
      const buttons = document.querySelectorAll('.cat-tab-btn');
      buttons.forEach(btn => {{
        const isAll = btn.getAttribute('data-category') === 'all';
        btn.classList.toggle('active', isAll);
        btn.setAttribute('aria-selected', isAll ? 'true' : 'false');
      }});
      filterCareerGuides();
      if (input) input.focus();
    }}

    // Keyboard shortcuts: '/' focuses search, 'Escape' clears search
    document.addEventListener('keydown', (e) => {{
      const input = document.getElementById('guideSearchInput');
      if (e.key === '/' && document.activeElement !== input) {{
        e.preventDefault();
        if (input) {{
          input.focus();
          input.select();
        }}
      }} else if (e.key === 'Escape' && document.activeElement === input) {{
        clearGuideSearch();
        input.blur();
      }}
    }});

    // Initialize pagination immediately on load
    document.addEventListener('DOMContentLoaded', () => {{
      filterCareerGuides();
    }});
  </script>

</body>
</html>
"""
    return html

def main():
    print(f"Generating optimized frontend/articles.html for all {len(GUIDES)} career guides...")
    full_html = build_full_html()
    with open(ARTICLES_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Successfully generated {ARTICLES_PATH}! Total bytes: {len(full_html)}")

if __name__ == "__main__":
    main()

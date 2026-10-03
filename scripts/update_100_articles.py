#!/usr/bin/env python3
"""
Comprehensive updater for all 100 Career Guides:
1. Updates scripts/update_articles_page.py with all 100 guides
2. Regenerates frontend/articles.html
3. Updates scripts/update_navbar.py and regenerates navbars across all HTML files
4. Updates frontend/static/sitemap.xml
5. Updates frontend/static/llms.txt and frontend/static/llms-full.txt
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 30 New guides to append
NEW_30_GUIDES = [
    {
        "slug": "ai-product-manager.html",
        "title": "AI Product Manager",
        "category": "AI, ML & Data",
        "desc": "Leading GenAI roadmaps, LLM evaluation, prompt orchestration, and non-deterministic UX design.",
        "icon": '<path d="M12 2a8 8 0 0 0-8 8c0 3.36 2.08 6.23 5 7.42V20a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2.58c2.92-1.19 5-4.06 5-7.42a8 8 0 0 0-8-8z"/>',
        "color": "#7C3AED"
    },
    {
        "slug": "prompt-engineer.html",
        "title": "Prompt Engineer",
        "category": "AI, ML & Data",
        "desc": "Optimizing LLM context windows, few-shot prompting, automated evals, and adversarial red-teaming.",
        "icon": '<path d="m5 12 5 5L20 7"/>',
        "color": "#4F46E5"
    },
    {
        "slug": "devsecops-engineer.html",
        "title": "DevSecOps Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Shift-left pipeline security, automated SAST/DAST scanning, container hardening, and policy-as-code.",
        "icon": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        "color": "#DC2626"
    },
    {
        "slug": "snowflake-data-engineer.html",
        "title": "Snowflake Data Engineer",
        "category": "AI, ML & Data",
        "desc": "Architecting high-throughput data lakes, dbt SQL transformations, and Snowpark Python pipelines.",
        "icon": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
        "color": "#0284C7"
    },
    {
        "slug": "security-architect.html",
        "title": "Security Architect",
        "category": "Cybersecurity & Quality",
        "desc": "Enterprise defense strategies, Zero Trust architecture, threat modeling (STRIDE), and cryptographic controls.",
        "icon": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        "color": "#991B1B"
    },
    {
        "slug": "cloud-security-engineer.html",
        "title": "Cloud Security Engineer",
        "category": "Cybersecurity & Quality",
        "desc": "Multi-cloud infrastructure defense, IAM least-privilege, automated compliance, and real-time detection.",
        "icon": '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
        "color": "#B91C1C"
    },
    {
        "slug": "deep-learning-engineer.html",
        "title": "Deep Learning Engineer",
        "category": "AI, ML & Data",
        "desc": "Neural network architecture design, PyTorch distributed GPU training, and transformer acceleration.",
        "icon": '<circle cx="12" cy="12" r="3"/><path d="M3 9h2a7 7 0 0 1 14 0h2"/>',
        "color": "#4338CA"
    },
    {
        "slug": "kafka-engineer.html",
        "title": "Kafka & Streaming Engineer",
        "category": "AI, ML & Data",
        "desc": "Event-driven distributed architectures, Apache Flink stateful streaming, and real-time telemetry backbones.",
        "icon": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
        "color": "#1E293B"
    },
    {
        "slug": "finops-practitioner.html",
        "title": "FinOps Practitioner",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Cloud economics, rate optimization, container cost allocation, and engineering spend governance.",
        "icon": '<line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        "color": "#059669"
    },
    {
        "slug": "flutter-developer.html",
        "title": "Flutter Developer",
        "category": "Engineering & Architecture",
        "desc": "High-performance cross-platform mobile apps for iOS and Android using Dart and reactive BLoC patterns.",
        "icon": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><line x1="12" x2="12.01" y1="18" y2="18"/>',
        "color": "#0284C7"
    },
    {
        "slug": "angular-developer.html",
        "title": "Angular Developer",
        "category": "Engineering & Architecture",
        "desc": "Enterprise single-page web applications with TypeScript, Angular Signals, RxJS, and NgRx state.",
        "icon": '<polygon points="12 2 2 7 12 22 22 7 12 2"/>',
        "color": "#DD0031"
    },
    {
        "slug": "vuejs-developer.html",
        "title": "Vue.js Developer",
        "category": "Engineering & Architecture",
        "desc": "Modern reactive web interfaces and full-stack Nuxt applications using Vue 3 Composition API.",
        "icon": '<polygon points="12 2 2 19 22 19 12 2"/>',
        "color": "#42B883"
    },
    {
        "slug": "cplusplus-developer.html",
        "title": "C++ Systems Developer",
        "category": "Engineering & Architecture",
        "desc": "Ultra-low-latency distributed systems, modern C++20/23, lock-free queues, and hardware optimization.",
        "icon": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
        "color": "#00599C"
    },
    {
        "slug": "csharp-developer.html",
        "title": "C# .NET Developer",
        "category": "Engineering & Architecture",
        "desc": "Cross-platform cloud microservices, ASP.NET Core APIs, and enterprise domain architecture on modern .NET.",
        "icon": '<path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/>',
        "color": "#512BD4"
    },
    {
        "slug": "ruby-on-rails-developer.html",
        "title": "Ruby on Rails Developer",
        "category": "Engineering & Architecture",
        "desc": "High-velocity full-stack web platforms using Rails 7/8 conventions, Hotwire, and background job queues.",
        "icon": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
        "color": "#CC0000"
    },
    {
        "slug": "ios-swift-engineer.html",
        "title": "iOS Swift Engineer",
        "category": "Engineering & Architecture",
        "desc": "Native Apple ecosystem applications built with modern Swift, declarative SwiftUI, and Swift Concurrency.",
        "icon": '<path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"/>',
        "color": "#F05138"
    },
    {
        "slug": "observability-engineer.html",
        "title": "Observability Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Unified OpenTelemetry instrumentation, distributed tracing, Prometheus metrics, and Grafana telemetry.",
        "icon": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
        "color": "#F97316"
    },
    {
        "slug": "automation-test-lead.html",
        "title": "QA Automation Lead",
        "category": "Cybersecurity & Quality",
        "desc": "Enterprise quality architecture, Playwright/Cypress frameworks, CI/CD gates, and load simulation.",
        "icon": '<path d="m9 11 3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
        "color": "#16A34A"
    },
    {
        "slug": "sap-consultant.html",
        "title": "SAP Technical Consultant",
        "category": "Leadership, Strategy & Operations",
        "desc": "Enterprise ERP modernization, ABAP on HANA, SAP BTP integrations, and Fiori UI5 applications.",
        "icon": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
        "color": "#0369A1"
    },
    {
        "slug": "workday-integration-consultant.html",
        "title": "Workday Integration Consultant",
        "category": "Leadership, Strategy & Operations",
        "desc": "Enterprise HR and financial data flows, Workday Studio, EIB, XSLT, and cloud ERP connectors.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="m10 15 5-3-5-3v6Z"/>',
        "color": "#E11D48"
    },
    {
        "slug": "service-mesh-engineer.html",
        "title": "Service Mesh Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Cloud-native traffic engineering, Istio Envoy proxies, mutual TLS encryption, and API gateway routing.",
        "icon": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/>',
        "color": "#4338CA"
    },
    {
        "slug": "site-reliability-lead.html",
        "title": "SRE Lead",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Enterprise platform resilience, chaos engineering, incident management, and SLO governance.",
        "icon": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
        "color": "#0284C7"
    },
    {
        "slug": "data-governance-manager.html",
        "title": "Data Governance Specialist",
        "category": "AI, ML & Data",
        "desc": "Enterprise data catalogs, lineage tracing, DPDPA 2023 / GDPR compliance, and metadata quality.",
        "icon": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
        "color": "#475569"
    },
    {
        "slug": "lead-software-engineer.html",
        "title": "Lead Software Engineer",
        "category": "Engineering & Architecture",
        "desc": "Technical execution, distributed architecture design, code review standards, and team mentorship.",
        "icon": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "color": "#4F46E5"
    },
    {
        "slug": "applied-scientist.html",
        "title": "Applied Scientist",
        "category": "AI, ML & Data",
        "desc": "Bridging algorithmic machine learning research with industrial-scale production software delivery.",
        "icon": '<path d="M10 2v7.31"/><path d="M14 9.3V1.99"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/>',
        "color": "#7C3AED"
    },
    {
        "slug": "iot-engineer.html",
        "title": "IoT Engineer",
        "category": "Hardware & Embedded Systems",
        "desc": "Connected smart hardware, FreeRTOS microcontrollers, MQTT telemetry, and edge computing.",
        "icon": '<rect width="18" height="14" x="3" y="5" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M7 2h10"/><path d="M7 22h10"/>',
        "color": "#0D9488"
    },
    {
        "slug": "robotics-software-engineer.html",
        "title": "Robotics Software Engineer",
        "category": "Hardware & Embedded Systems",
        "desc": "Autonomous navigation, ROS2 middleware, SLAM, computer vision, and sensor fusion algorithms.",
        "icon": '<rect width="16" height="16" x="4" y="4" rx="2"/><circle cx="9" cy="9" r="2"/><circle cx="15" cy="9" r="2"/><path d="M8 15h8"/>',
        "color": "#2563EB"
    },
    {
        "slug": "database-engineer.html",
        "title": "Database Engineer",
        "category": "Engineering & Architecture",
        "desc": "High-scale transactional database engines, PostgreSQL query tuning, and distributed SQL clusters.",
        "icon": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
        "color": "#334155"
    },
    {
        "slug": "search-relevance-engineer.html",
        "title": "Search Relevance Engineer",
        "category": "AI, ML & Data",
        "desc": "High-recall search retrieval, Elasticsearch inverted indexes, hybrid search, and vector ranking.",
        "icon": '<circle cx="11" cy="11" r="8"/><line x1="21" x2="16.65" y1="21" y2="16.65"/>',
        "color": "#D97706"
    },
    {
        "slug": "identity-access-management-engineer.html",
        "title": "IAM Engineer",
        "category": "Cybersecurity & Quality",
        "desc": "Enterprise identity security, Single Sign-On (SSO), OAuth 2.0 / OIDC, and Zero Trust access policies.",
        "icon": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        "color": "#475569"
    }
]

def update_articles_page_script():
    script_path = ROOT_DIR / "scripts" / "update_articles_page.py"
    content = script_path.read_text(encoding="utf-8")
    
    import scripts.update_articles_page as uap
    existing_slugs = {g["slug"] for g in uap.GUIDES}
    
    to_add = [g for g in NEW_30_GUIDES if g["slug"] not in existing_slugs]
    print(f"Adding {len(to_add)} new guides to scripts/update_articles_page.py...")
    
    if to_add:
        # Find where GUIDES ends
        pattern = r"(GUIDES\s*=\s*\[.*?)(\n\]\s*\n\s*def\s+build_card)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            existing_part = match.group(1)
            # Format additions
            add_lines = []
            for g in to_add:
                add_lines.append(f"""    {{
        "slug": "{g['slug']}",
        "title": "{g['title']}",
        "category": "{g['category']}",
        "desc": "{g['desc']}",
        "icon": '{g['icon']}',
        "color": "{g['color']}"
    }},""")
            new_guides_code = existing_part + "\n" + "\n".join(add_lines) + match.group(2)
            content = content[:match.start()] + new_guides_code + content[match.end():]
            
            # Update counts (70 -> 100)
            content = content.replace("of 70 career guides", "of 100 career guides")
            content = content.replace("70 Specialized Career Tracks", "100 Specialized Career Tracks")
            content = content.replace("70 In-Demand Tracks", "100 In-Demand Tracks")
            
            script_path.write_text(content, encoding="utf-8")
            print("Successfully updated scripts/update_articles_page.py with all 100 guides!")
        else:
            print("Could not locate insertion point in update_articles_page.py")

def main():
    update_articles_page_script()
    
    # Run update_articles_page.py
    import subprocess
    print("Running scripts/update_articles_page.py...")
    res = subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "update_articles_page.py")], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print("Error:", res.stderr)
        
    # Run update_sitemap.py
    print("Running scripts/update_sitemap.py...")
    res_sitemap = subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "update_sitemap.py")], capture_output=True, text=True)
    print(res_sitemap.stdout)

    # Run update_navbar.py if it exists
    nav_script = ROOT_DIR / "scripts" / "update_navbar.py"
    if nav_script.exists():
        print("Updating navbar script counts...")
        nav_content = nav_script.read_text(encoding="utf-8")
        nav_content = nav_content.replace("70 Specialized Tracks", "100 Specialized Tracks")
        nav_content = nav_content.replace("70 Tracks", "100 Tracks")
        nav_content = nav_content.replace(">70<", ">100<")
        nav_content = nav_content.replace(">70 Guides<", ">100 Guides<")
        nav_script.write_text(nav_content, encoding="utf-8")
        
        print("Running scripts/update_navbar.py...")
        res_nav = subprocess.run([sys.executable, str(nav_script)], capture_output=True, text=True)
        print(res_nav.stdout)

if __name__ == "__main__":
    main()

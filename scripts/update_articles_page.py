#!/usr/bin/env python3
"""
Update frontend/articles.html with all 50 career guides, domain categories,
live search filter, and interactive Career Guides navigation.
"""

from pathlib import Path
import re

WORKSPACE = Path(__file__).resolve().parent.parent
ARTICLES_HTML = WORKSPACE / "frontend" / "articles.html"

# Complete directory of all 50 Career Guides across 7 Core Domains
GUIDES = [
    # 1. Engineering & Architecture (15 guides)
    {
        "slug": "software-engineer.html",
        "title": "Software Engineer",
        "category": "Engineering & Architecture",
        "desc": "Comprehensive overview of the Software Engineer role, including skills, salary, and career progression.",
        "icon": '<path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/>',
        "color": "#4F46E5"
    },
    {
        "slug": "full-stack-developer.html",
        "title": "Full Stack Developer",
        "category": "Engineering & Architecture",
        "desc": "Mastering the complete application lifecycle across React, Next.js, Node.js, Python, and PostgreSQL.",
        "icon": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
        "color": "#4F46E5"
    },
    {
        "slug": "backend-developer.html",
        "title": "Backend Developer",
        "category": "Engineering & Architecture",
        "desc": "Architecting robust APIs, database engines, distributed caching, and scalable microservice runtimes.",
        "icon": '<rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>',
        "color": "#6366F1"
    },
    {
        "slug": "frontend-developer.html",
        "title": "Frontend Developer",
        "category": "Engineering & Architecture",
        "desc": "Crafting responsive, high-performance user interfaces using HTML5, CSS3, modern JavaScript, and React.",
        "icon": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
        "color": "#2563EB"
    },
    {
        "slug": "software-engineer-india.html",
        "title": "Software Engineer in India",
        "category": "Engineering & Architecture",
        "desc": "Market trends, top IT hubs (Bengaluru, Hyderabad, Pune, NCR), and compensation benchmarks in India.",
        "icon": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
        "color": "#F59E0B"
    },
    {
        "slug": "remote-software-engineer.html",
        "title": "Remote Software Engineer",
        "category": "Engineering & Architecture",
        "desc": "Everything you need to secure, negotiate, and thrive in global work-from-anywhere engineering roles.",
        "icon": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
        "color": "#3B82F6"
    },
    {
        "slug": "entry-level-software-engineer.html",
        "title": "Entry-Level Software Engineer",
        "category": "Engineering & Architecture",
        "desc": "Actionable roadmap for new graduates and bootcamp alumni to break into tech and land their first job.",
        "icon": '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
        "color": "#10B981"
    },
    {
        "slug": "solutions-architect.html",
        "title": "Solutions Architect",
        "category": "Engineering & Architecture",
        "desc": "Bridging business vision with enterprise system blueprints, multi-cloud strategy, and trade-off analysis.",
        "icon": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
        "color": "#0891B2"
    },
    {
        "slug": "systems-engineer.html",
        "title": "Systems Engineer",
        "category": "Engineering & Architecture",
        "desc": "Operating systems internals, Linux kernel tuning, bare-metal hardware, and low-latency networking in C/Rust.",
        "icon": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 7h10"/><path d="M7 12h10"/><path d="M7 17h10"/>',
        "color": "#475569"
    },
    {
        "slug": "mobile-app-developer.html",
        "title": "Mobile App Developer",
        "category": "Engineering & Architecture",
        "desc": "Cross-platform and native mobile architectures powering touch experiences across React Native and Flutter.",
        "icon": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><line x1="12" x2="12.01" y1="18" y2="18"/>',
        "color": "#9333EA"
    },
    {
        "slug": "ios-developer.html",
        "title": "iOS Developer",
        "category": "Engineering & Architecture",
        "desc": "Crafting premium experiences in Apple's ecosystem with Swift, SwiftUI, Combine, and App Store engineering.",
        "icon": '<path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"/>',
        "color": "#0284C7"
    },
    {
        "slug": "android-developer.html",
        "title": "Android Developer",
        "category": "Engineering & Architecture",
        "desc": "Building high-performance Android mobile apps using Kotlin, Jetpack Compose, Coroutines, and MVVM architecture.",
        "icon": '<path d="M4 10v6m16-6v6M7 16h10V9H7zM9 5l-2-3m8 3 2-3"/>',
        "color": "#16A34A"
    },
    {
        "slug": "blockchain-engineer.html",
        "title": "Blockchain & Web3 Engineer",
        "category": "Engineering & Architecture",
        "desc": "Architecting smart contracts, decentralized protocols, and dApps with Solidity, Rust, EVM, and cryptography.",
        "icon": '<rect width="8" height="8" x="2" y="2" rx="1"/><rect width="8" height="8" x="14" y="2" rx="1"/><rect width="8" height="8" x="8" y="14" rx="1"/><path d="M6 10v4h5m2-4v4h-5"/>',
        "color": "#8B5CF6"
    },
    {
        "slug": "salesforce-developer.html",
        "title": "Salesforce Developer",
        "category": "Engineering & Architecture",
        "desc": "Building bespoke business logic, Apex triggers, Lightning Web Components (LWC), and enterprise CRM integrations.",
        "icon": '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
        "color": "#0284C7"
    },
    {
        "slug": "game-developer.html",
        "title": "Game Developer",
        "category": "Engineering & Architecture",
        "desc": "Programming interactive gameplay, 3D graphics shaders, physics engines, and netcode in Unreal Engine and Unity.",
        "icon": '<polygon points="6 3 18 3 21 9 12 22 3 9 6 3"/><line x1="12" x2="12" y1="22" y2="9"/>',
        "color": "#7C2D12"
    },

    # 2. Cloud, DevOps & Infrastructure (8 guides)
    {
        "slug": "devops-engineer.html",
        "title": "DevOps Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Accelerating release frequency while safeguarding uptime with Docker, Kubernetes, Terraform, and CI/CD.",
        "icon": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
        "color": "#059669"
    },
    {
        "slug": "cloud-engineer.html",
        "title": "Cloud Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Designing scalable, fault-tolerant enterprise infrastructure across AWS, GCP, and Microsoft Azure.",
        "icon": '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
        "color": "#2563EB"
    },
    {
        "slug": "site-reliability-engineer.html",
        "title": "Site Reliability Engineer (SRE)",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Safeguarding five-nines availability through automated failover, SLIs/SLOs, Chaos Engineering, and error budgets.",
        "icon": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        "color": "#D97706"
    },
    {
        "slug": "platform-engineer.html",
        "title": "Platform Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Building Internal Developer Platforms (IDPs), golden paths, and self-service cloud infrastructure with Go and K8s.",
        "icon": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
        "color": "#3B82F6"
    },
    {
        "slug": "release-engineer.html",
        "title": "Release & Build Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Ensuring predictable, regression-free software delivery with Bazel, Gradle, monorepo caching, and canary rollouts.",
        "icon": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
        "color": "#047857"
    },
    {
        "slug": "network-engineer.html",
        "title": "Network Engineer",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Engineering global telecom and cloud backbones using BGP, OSPF, SD-WAN, Cisco, and automated NetDevOps.",
        "icon": '<rect width="18" height="12" x="3" y="4" rx="2"/><line x1="2" x2="22" y1="20" y2="20"/>',
        "color": "#0D9488"
    },
    {
        "slug": "database-administrator.html",
        "title": "Database Administrator (DBA)",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Safeguarding enterprise data integrity, query optimization, high availability, replication, and disaster recovery.",
        "icon": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>',
        "color": "#0284C7"
    },
    {
        "slug": "it-support-specialist.html",
        "title": "IT Support Specialist",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Frontline endpoint administration, identity access management (Okta/AD), MDM deployments, and hardware support.",
        "icon": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
        "color": "#0891B2"
    },

    # 3. Hardware & Embedded Systems (3 guides)
    {
        "slug": "embedded-software-engineer.html",
        "title": "Embedded Software Engineer",
        "category": "Hardware & Embedded Systems",
        "desc": "Developing deterministic real-time software for IoT, automotive ECUs, and medical devices using C/C++ and RTOS.",
        "icon": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M9 1v3m6-3v3M9 20v3m6-3v3M20 9h3m-3 6h3M1 9h3m-3 6h3"/>',
        "color": "#D97706"
    },
    {
        "slug": "firmware-engineer.html",
        "title": "Firmware Engineer",
        "category": "Hardware & Embedded Systems",
        "desc": "Writing bare-metal drivers, custom bootloaders, Board Support Packages (BSPs), and silicon bring-up routines.",
        "icon": '<path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><circle cx="12" cy="12" r="2"/>',
        "color": "#EA580C"
    },
    {
        "slug": "hardware-engineer.html",
        "title": "Hardware Engineer",
        "category": "Hardware & Embedded Systems",
        "desc": "Designing high-speed digital circuits, multi-layer PCBs, power delivery networks, and FPGA logic systems.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"/>',
        "color": "#B45309"
    },

    # 4. AI, Machine Learning & Data (10 guides)
    {
        "slug": "machine-learning-engineer.html",
        "title": "Machine Learning Engineer",
        "category": "AI, ML & Data",
        "desc": "Translating predictive research into production inference pipelines using PyTorch, TensorFlow, and Triton.",
        "icon": '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>',
        "color": "#8B5CF6"
    },
    {
        "slug": "data-scientist.html",
        "title": "Data Scientist",
        "category": "AI, ML & Data",
        "desc": "Transforming unstructured petabyte-scale data into predictive business insights, algorithms, and models.",
        "icon": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
        "color": "#6366F1"
    },
    {
        "slug": "ai-research-scientist.html",
        "title": "AI Research Scientist",
        "category": "AI, ML & Data",
        "desc": "Pushing the frontiers of intelligence across foundation models, multimodal learning, and neural synthesis.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/>',
        "color": "#7C3AED"
    },
    {
        "slug": "data-engineer.html",
        "title": "Data Engineer",
        "category": "AI, ML & Data",
        "desc": "Building robust streaming pipelines, data lakes, and lakehouse architectures with Spark, Kafka, and Snowflake.",
        "icon": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
        "color": "#06B6D4"
    },
    {
        "slug": "data-analyst.html",
        "title": "Data Analyst",
        "category": "AI, ML & Data",
        "desc": "Empowering strategic business decisions through SQL analytics, interactive Tableau/Power BI dashboards, and metrics.",
        "icon": '<line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/>',
        "color": "#0284C7"
    },
    {
        "slug": "entry-level-data-scientist.html",
        "title": "Entry-Level Data Scientist",
        "category": "AI, ML & Data",
        "desc": "Step-by-step career path to land your first data science position, build a competitive portfolio, and ace interviews.",
        "icon": '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10M6 10h10"/>',
        "color": "#10B981"
    },
    {
        "slug": "mlops-engineer.html",
        "title": "MLOps Engineer",
        "category": "AI, ML & Data",
        "desc": "Bridging machine learning and operations with automated continuous training, Kubeflow, Triton, and GPU clusters.",
        "icon": '<circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>',
        "color": "#10B981"
    },
    {
        "slug": "nlp-engineer.html",
        "title": "NLP & LLM Engineer",
        "category": "AI, ML & Data",
        "desc": "Building generative AI models, enterprise RAG pipelines, fine-tuning (LoRA), and semantic vector search systems.",
        "icon": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        "color": "#6366F1"
    },
    {
        "slug": "computer-vision-engineer.html",
        "title": "Computer Vision Engineer",
        "category": "AI, ML & Data",
        "desc": "Developing visual perception systems for robotics, autonomous vehicles, and edge devices with OpenCV and PyTorch.",
        "icon": '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
        "color": "#06B6D4"
    },
    {
        "slug": "fintech-engineer.html",
        "title": "Fintech & Algorithmic Trading Engineer",
        "category": "AI, ML & Data",
        "desc": "Engineering microsecond-latency trading platforms, low-overhead C++ execution engines, and payment ledgers.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8m4-10v2m0 8v2"/>',
        "color": "#1E3A8A"
    },

    # 5. Cybersecurity & Quality Assurance (4 guides)
    {
        "slug": "cybersecurity-engineer.html",
        "title": "Cybersecurity Engineer",
        "category": "Cybersecurity & Quality",
        "desc": "Fortifying digital perimeters against threat vectors, zero-day vulnerabilities, and adversarial actors.",
        "icon": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        "color": "#DC2626"
    },
    {
        "slug": "security-engineer.html",
        "title": "Security Engineer",
        "category": "Cybersecurity & Quality",
        "desc": "Proactive application security (AppSec), DevSecOps pipeline scanning (SAST/DAST), and cryptographic controls.",
        "icon": '<path d="m10 10 4 4m0-4-4 4"/><circle cx="12" cy="12" r="10"/>',
        "color": "#E11D48"
    },
    {
        "slug": "infosec-analyst.html",
        "title": "Information Security Analyst",
        "category": "Cybersecurity & Quality",
        "desc": "Frontline SOC monitoring, digital forensics, threat intelligence hunting, and cyber incident containment.",
        "icon": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        "color": "#991B1B"
    },
    {
        "slug": "qa-automation-engineer.html",
        "title": "QA Automation Engineer",
        "category": "Cybersecurity & Quality",
        "desc": "Ensuring zero-defect releases with Playwright, Cypress, Selenium, API testing, and CI automated test suites.",
        "icon": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "color": "#16A34A"
    },

    # 6. Product, Design & Agile (6 guides)
    {
        "slug": "product-manager.html",
        "title": "Product Manager",
        "category": "Product, Design & Agile",
        "desc": "Driving product vision, user problem discovery, roadmap prioritization, and commercial feature delivery.",
        "icon": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
        "color": "#DB2777"
    },
    {
        "slug": "remote-product-manager.html",
        "title": "Remote Product Manager",
        "category": "Product, Design & Agile",
        "desc": "Leading distributed product squads and async discovery across global time zones from anywhere.",
        "icon": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777z"/>',
        "color": "#EC4899"
    },
    {
        "slug": "technical-program-manager.html",
        "title": "Technical Program Manager (TPM)",
        "category": "Product, Design & Agile",
        "desc": "Orchestrating multifaceted multi-team engineering programs, managing dependencies, and mitigating technical risks.",
        "icon": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "color": "#B45309"
    },
    {
        "slug": "scrum-master.html",
        "title": "Scrum Master / Agile Coach",
        "category": "Product, Design & Agile",
        "desc": "Empowering engineering squads through servant leadership, impediment removal, sprint health, and delivery velocity.",
        "icon": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/>',
        "color": "#7C3AED"
    },
    {
        "slug": "ui-ux-designer.html",
        "title": "UI/UX Designer",
        "category": "Product, Design & Agile",
        "desc": "Crafting intuitive digital interfaces through user research, wireframing, Figma design systems, and usability testing.",
        "icon": '<circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>',
        "color": "#EA580C"
    },
    {
        "slug": "product-designer.html",
        "title": "Product Designer",
        "category": "Product, Design & Agile",
        "desc": "Owning end-to-end product design from problem validation and rapid prototyping to metric analysis and launch.",
        "icon": '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/>',
        "color": "#DB2777"
    },

    # 7. Leadership, Strategy & Operations (4 guides)
    {
        "slug": "engineering-manager.html",
        "title": "Engineering Manager",
        "category": "Leadership, Strategy & Operations",
        "desc": "Coaching high-performing engineering teams, hiring talent, driving technical strategy, and nurturing culture.",
        "icon": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "color": "#BE185D"
    },
    {
        "slug": "business-analyst.html",
        "title": "Business Analyst",
        "category": "Leadership, Strategy & Operations",
        "desc": "Translating complex business problems into clear technical requirements, process flows, and value-driven features.",
        "icon": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
        "color": "#2563EB"
    },
    {
        "slug": "growth-marketer.html",
        "title": "Growth Marketing Specialist",
        "category": "Leadership, Strategy & Operations",
        "desc": "Designing full-funnel acquisition, conversion rate optimization (CRO), viral retention loops, and paid performance ads.",
        "icon": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
        "color": "#BE185D"
    },
    {
        "slug": "technical-writer.html",
        "title": "Technical Writer",
        "category": "Leadership, Strategy & Operations",
        "desc": "Authoring world-class API references, SDK documentation, and developer guides using Docs-as-Code best practices.",
        "icon": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
        "color": "#475569"
    },
    # 8. Additional Modern Tech & Leadership Tracks (20 new guides - Total 70)
    {
        "slug": "cloud-architect.html",
        "title": "Cloud Architect",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Designing enterprise multi-cloud blueprints, hybrid interconnects, disaster recovery, and FinOps governance.",
        "icon": '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
        "color": "#0284C7"
    },
    {
        "slug": "generative-ai-engineer.html",
        "title": "Generative AI Engineer",
        "category": "AI, ML & Data",
        "desc": "Architecting production LLM applications, RAG retrieval pipelines, agentic workflows, and fine-tuning models.",
        "icon": '<path d="M12 2a8 8 0 0 0-8 8c0 3.3 2 6.2 5 7.4V20a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-2.6c3-1.2 5-4.1 5-7.4a8 8 0 0 0-8-8z"/><path d="M9 22h6"/>',
        "color": "#8B5CF6"
    },
    {
        "slug": "data-architect.html",
        "title": "Data Architect",
        "category": "AI, ML & Data",
        "desc": "Designing enterprise Lakehouse platforms, Star Schema data vaults, Apache Iceberg, and streaming architectures.",
        "icon": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
        "color": "#2563EB"
    },
    {
        "slug": "rust-developer.html",
        "title": "Rust Developer",
        "category": "Engineering & Architecture",
        "desc": "Building memory-safe, ultra-low-latency backend systems, Tokio services, WebAssembly, and crypto protocols.",
        "icon": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v5"/><path d="M12 16v5"/><path d="M3 12h5"/><path d="M16 12h5"/>',
        "color": "#EA580C"
    },
    {
        "slug": "golang-developer.html",
        "title": "Golang Developer",
        "category": "Engineering & Architecture",
        "desc": "Engineering high-concurrency cloud-native microservices, gRPC endpoints, and distributed systems with Go.",
        "icon": '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>',
        "color": "#00ADD8"
    },
    {
        "slug": "python-developer.html",
        "title": "Python Developer",
        "category": "Engineering & Architecture",
        "desc": "Developing scalable backend APIs, Celery task pipelines, and asynchronous microservices with FastAPI and Django.",
        "icon": '<path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.5V14h-2v2.5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1-.5-.5V12h5v-1.5a.5.5 0 0 0-.5-.5H9"/>',
        "color": "#3B82F6"
    },
    {
        "slug": "java-developer.html",
        "title": "Java Developer",
        "category": "Engineering & Architecture",
        "desc": "Building enterprise microservices, Spring Boot backends, Kafka event streams, and tuning JVM performance.",
        "icon": '<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" x2="6" y1="1" y2="4"/><line x1="10" x2="10" y1="1" y2="4"/><line x1="14" x2="14" y1="1" y2="4"/>',
        "color": "#DC2626"
    },
    {
        "slug": "react-developer.html",
        "title": "React Developer",
        "category": "Engineering & Architecture",
        "desc": "Creating dynamic web applications, Next.js server components, design systems, and responsive user experiences.",
        "icon": '<circle cx="12" cy="12" r="2"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(30 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(90 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(150 12 12)"/>',
        "color": "#06B6D4"
    },
    {
        "slug": "nodejs-developer.html",
        "title": "Node.js Developer",
        "category": "Engineering & Architecture",
        "desc": "Engineering scalable event-driven REST/GraphQL APIs, NestJS architectures, and real-time WebSockets.",
        "icon": '<polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/>',
        "color": "#16A34A"
    },
    {
        "slug": "kubernetes-administrator.html",
        "title": "Kubernetes Administrator",
        "category": "Cloud, DevOps & Infrastructure",
        "desc": "Deploying, securing, and operating large-scale production container fleets with Helm, Istio, and GitOps.",
        "icon": '<polygon points="12 2 21.5 7.5 21.5 18.5 12 24 2.5 18.5 2.5 7.5 12 2"/><circle cx="12" cy="12" r="3"/>',
        "color": "#326CE5"
    },
    {
        "slug": "chief-technology-officer.html",
        "title": "Chief Technology Officer (CTO)",
        "category": "Leadership, Strategy & Operations",
        "desc": "Defining executive technology strategy, scaling engineering organizations, tech budgeting, and innovation roadmaps.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="m12 6 2 4 4 1-3 3 1 4-4-2-4 2 1-4-3-3 4-1z"/>',
        "color": "#4338CA"
    },
    {
        "slug": "staff-software-engineer.html",
        "title": "Staff Software Engineer",
        "category": "Leadership, Strategy & Operations",
        "desc": "Setting architectural direction, authoring RFCs, resolving complex cross-team bottlenecks, and technical mentorship.",
        "icon": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
        "color": "#4F46E5"
    },
    {
        "slug": "principal-software-engineer.html",
        "title": "Principal Software Engineer",
        "category": "Leadership, Strategy & Operations",
        "desc": "Defining company-wide technical strategy, distributed consensus, high-stakes crisis response, and executive counsel.",
        "icon": '<path d="M6 3h12l4 6-10 13L2 9z"/><path d="M11 3v18"/><path d="M2 9h20"/>',
        "color": "#312E81"
    },
    {
        "slug": "penetration-tester.html",
        "title": "Penetration Tester",
        "category": "Cybersecurity & Quality",
        "desc": "Simulating real-world cyberattacks, ethical hacking, web/API vulnerability assessments, and remediation guidance.",
        "icon": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
        "color": "#E11D48"
    },
    {
        "slug": "soc-analyst.html",
        "title": "SOC Analyst",
        "category": "Cybersecurity & Quality",
        "desc": "Monitoring enterprise security telemetry, triaging SIEM/EDR alerts, and orchestrating live incident responses.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/>',
        "color": "#D97706"
    },
    {
        "slug": "product-operations-manager.html",
        "title": "Product Operations Manager",
        "category": "Product, Design & Agile",
        "desc": "Scaling product team systems, democratizing user insights, optimizing launch governance, and managing product analytics.",
        "icon": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
        "color": "#0D9488"
    },
    {
        "slug": "quantitative-analyst.html",
        "title": "Quantitative Analyst",
        "category": "AI, ML & Data",
        "desc": "Developing mathematical models, algorithmic trading strategies, derivatives pricing, and high-frequency risk modeling.",
        "icon": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
        "color": "#059669"
    },
    {
        "slug": "bi-developer.html",
        "title": "Business Intelligence Developer",
        "category": "AI, ML & Data",
        "desc": "Transforming enterprise data into actionable Power BI & Tableau dashboards, DAX metrics, and star schemas.",
        "icon": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>',
        "color": "#2563EB"
    },
    {
        "slug": "etl-developer.html",
        "title": "ETL Developer",
        "category": "AI, ML & Data",
        "desc": "Engineering automated batch and streaming data extraction, dbt transformations, and Airflow orchestration.",
        "icon": '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="m8 17 4 4 4-4"/><path d="M12 12v9"/>',
        "color": "#475569"
    },
    {
        "slug": "sdet-engineer.html",
        "title": "SDET Engineer",
        "category": "Cybersecurity & Quality",
        "desc": "Engineering automated test frameworks with Playwright, Selenium, API validation, and continuous testing in CI/CD.",
        "icon": '<path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><circle cx="12" cy="12" r="2"/>',
        "color": "#7C3AED"
    }
]

# Build the cards HTML
cards_html = ""
for g in GUIDES:
    cards_html += f"""      <!-- Card: {g['title']} -->
      <a href="/jobs/{g['slug']}" class="career-guide-card-link" data-title="{g['title'].lower()}" data-category="{g['category'].lower()}" style="text-decoration: none; display: block;">
        <div class="job-card" style="padding: 24px; border: 1px solid var(--card-bdr); border-radius: 12px; background: #fff; box-shadow: var(--card-shadow); transition: all 0.2s; height: 100%; display: flex; flex-direction: column;">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="width: 46px; height: 46px; border-radius: 10px; background: {g['color']}18; display: flex; align-items: center; justify-content: center; color: {g['color']}; flex-shrink: 0;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                {g['icon']}
              </svg>
            </div>
            <div>
              <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: {g['color']}; display: block;">{g['category']}</span>
              <h2 style="font-size: 17px; font-weight: 700; color: var(--txt); margin: 2px 0 0;">{g['title']}</h2>
            </div>
          </div>
          <p style="color: var(--txt-muted); font-size: 14px; margin: 0 0 16px; line-height: 1.5; flex-grow: 1;">{g['desc']}</p>
          <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #F1F5F9; padding-top: 12px; font-size: 13px; font-weight: 600; color: {g['color']};">
            <span>Read Career Blueprint</span>
            <span>&rarr;</span>
          </div>
        </div>
      </a>\n"""

# Search Bar HTML
search_filter_html = """
  <!-- Quick Search & Category Filter Section -->
  <div style="max-width: 800px; margin: -30px auto 30px; padding: 0 20px; position: relative; z-index: 10;">
    <div style="background: #FFFFFF; border: 1px solid var(--card-bdr); border-radius: 14px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08); padding: 10px 16px; display: flex; align-items: center; gap: 12px;">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--txt-muted)" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      <input type="text" id="guideSearchInput" placeholder="Filter 70 career guides by title or domain (e.g., Full Stack, MLOps, Blockchain, SRE, Cloud Architect)..." style="width: 100%; border: none; outline: none; font-size: 15px; color: var(--txt); background: transparent;" oninput="filterCareerGuides()" />
      <button type="button" onclick="clearGuideSearch()" id="clearGuideBtn" style="display: none; background: none; border: none; color: var(--txt-dim); cursor: pointer; font-size: 16px;">&times;</button>
    </div>
    <div id="guideCountNotice" style="text-align: center; font-size: 13px; color: var(--txt-muted); margin-top: 10px;">
      Showing all <strong>70</strong> specialized career blueprints
    </div>
  </div>
"""

# Script to inject into articles.html
filter_script = """
  <script>
    function filterCareerGuides() {
      const input = document.getElementById('guideSearchInput');
      const val = (input.value || '').trim().toLowerCase();
      const clearBtn = document.getElementById('clearGuideBtn');
      if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';
      
      const cards = document.querySelectorAll('.career-guide-card-link');
      let visibleCount = 0;
      cards.forEach(card => {
        const title = card.getAttribute('data-title') || '';
        const cat = card.getAttribute('data-category') || '';
        if (!val || title.includes(val) || cat.includes(val)) {
          card.style.display = 'block';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });
      const notice = document.getElementById('guideCountNotice');
      if (notice) {
        notice.innerHTML = `Showing <strong>${visibleCount}</strong> of 70 career guides`;
      }
    }

    function clearGuideSearch() {
      const input = document.getElementById('guideSearchInput');
      if (input) {
        input.value = '';
        filterCareerGuides();
        input.focus();
      }
    }
  </script>
"""


def main():
    print(f"Updating {ARTICLES_HTML} with all {len(GUIDES)} career guides...")
    with open(ARTICLES_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace the grid in articles.html
    grid_pattern = r'<main class="results-container"[^>]*>.*?<div id="guidesGrid"[^>]*>.*?</div>\s*</main>'
    # If guidesGrid doesn't match, fallback to general grid pattern
    if not re.search(grid_pattern, content, flags=re.DOTALL):
        grid_pattern = r'<main class="results-container"[^>]*>.*?<div style="display: grid;[^>]*>.*?</div>\s*</main>'

    replacement = f"""<main class="results-container" style="max-width: 1200px; margin: 40px auto; padding: 0 20px;">
{search_filter_html}
    <div id="guidesGrid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px;">
{cards_html}    </div>
  </main>"""

    new_content = re.sub(grid_pattern, replacement, content, flags=re.DOTALL)

    # Insert or update the filter script before </body>
    if "function filterCareerGuides" in new_content:
        # replace script block
        new_content = re.sub(r'<script>\s*function filterCareerGuides\(\).*?</script>', filter_script.strip(), new_content, flags=re.DOTALL)
    else:
        new_content = new_content.replace("</body>", f"{filter_script}\n</body>")

    with open(ARTICLES_HTML, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Successfully updated {ARTICLES_HTML} with all {len(GUIDES)} career guides!")

if __name__ == "__main__":
    main()

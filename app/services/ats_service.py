import os
import re
import json
import random
import asyncio
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from urllib.parse import urljoin
import openpyxl
import pytz
import httpx

from app.config import get_config

logger = logging.getLogger("ats_service")

IST_TZ = pytz.timezone("Asia/Kolkata")

# Canonical Indian cities, metros, IT hubs, and states (used for strict word-boundary matching)
INDIA_CITIES_AND_STATES = [
    # Top IT Hubs & Metros
    "bengaluru", "bangalore", "mumbai", "bombay", "pune", "hyderabad", "secunderabad",
    "gurugram", "gurgaon", "noida", "greater noida", "delhi", "new delhi", "chennai", "madras",
    "kolkata", "calcutta", "ahmedabad", "jaipur", "indore", "kochi", "cochin", "ernakulam",
    "chandigarh", "mohali", "panchkula", "coimbatore", "thiruvananthapuram", "trivandrum",
    "bhubaneswar", "mysore", "mysuru", "mangalore", "mangaluru", "nagpur", "surat",
    "vadodara", "baroda", "visakhapatnam", "vizag", "bhopal", "lucknow", "patna",
    "ludhiana", "agra", "nashik", "rajkot", "varanasi", "amritsar", "navi mumbai", "thane",
    "ghaziabad", "faridabad", "guwahati", "dehradun", "hubli", "dharwad", "tiruchirappalli",
    "trichy", "madurai", "vijayawada", "guntur", "warangal", "jamshedpur", "ranchi", "cuttack",
    # States & Union Territories
    "karnataka", "maharashtra", "telangana", "tamil nadu", "tamilnadu", "haryana",
    "uttar pradesh", "west bengal", "gujarat", "rajasthan", "kerala", "andhra pradesh",
    "punjab", "odisha", "orissa", "madhya pradesh", "bihar", "assam", "goa", "uttarakhand",
    "himachal pradesh", "jharkhand", "chhattisgarh"
]

FOREIGN_RESTRICTED_REMOTES = [
    r"\bus\s*only\b", r"\bus\s*remote\b", r"\bremote\s*-\s*us\b", r"\bremote\s*\(us\)\b",
    r"\bremote\s*,\s*us\b", r"\bremote\s*-\s*usa\b", r"\bremote\s*,\s*usa\b",
    r"\bamericas\b", r"\bnorth\s*america\b", r"\bemea\b", r"\blatam\b",
    r"\beurope\b", r"\buk\s*only\b", r"\bcanada\s*only\b", r"\baus\s*only\b"
]

FOREIGN_TERRITORIES = [
    "united states", "usa", "u.s.", "u.s.a.", "united kingdom", "great britain",
    "england", "scotland", "wales", "ireland", "dublin", "canada", "australia",
    "germany", "france", "spain", "italy", "netherlands", "switzerland", "sweden",
    "poland", "japan", "china", "singapore", "israel", "uae", "dubai", "hong kong",
    "new zealand", "austria", "belgium", "denmark", "norway", "finland",
    "london", "paris", "berlin", "montreal", "toronto", "vancouver", "warsaw",
    "sydney", "melbourne", "tokyo", "zurich", "geneva", "amsterdam", "madrid",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming", "indianapolis"
]

INDIA_LOCATION_KEYWORDS = [
    "india", "remote - india", "india - remote", "remote, india", "remote (india)", "anywhere in india"
] + INDIA_CITIES_AND_STATES

COMMON_TECH_TAGS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", "Go", "Golang",
    "FastAPI", "Django", "Spring Boot", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "DevOps", "AI/ML", "Machine Learning",
    "Data Engineering", "Data Science", "C++", "Rust", "Swift", "Kotlin", "Flutter",
    "Product Management", "UI/UX", "HR", "Talent Acquisition", "Sales", "Marketing",
    "Cybersecurity", "Distributed Systems", "Microservices", "REST API", "GraphQL"
]


def to_ist(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(IST_TZ)

def parse_date_to_ist(date_str: Optional[str]) -> Tuple[str, str, str]:
    """
    Returns (posted_timestamp_ist, posted_timestamp_raw, relative_time_ist)
    """
    now_ist = datetime.datetime.now(IST_TZ)
    if not date_str:
        raw_iso = now_ist.isoformat()
        ist_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
        return ist_str, raw_iso, "Just now"

    dt = None
    clean_str = str(date_str).strip()
    is_explicit_ist = False

    # Handle numeric epoch timestamp (ms or s)
    if isinstance(date_str, (int, float)) or (clean_str.isdigit() and len(clean_str) >= 9):
        try:
            val = float(clean_str)
            if val > 1e11: # Epoch in milliseconds
                val = val / 1000.0
            dt = datetime.datetime.fromtimestamp(val, tz=datetime.timezone.utc)
        except Exception:
            dt = None

    # Strip explicit IST suffix if present
    if dt is None and clean_str.endswith(" IST"):
        clean_str = clean_str[:-4].strip()
        is_explicit_ist = True

    try:
        cleaned_iso = clean_str.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(cleaned_iso)
        if is_explicit_ist and dt.tzinfo is None:
            dt = IST_TZ.localize(dt)
    except Exception:
        pass

    if dt is None:
        # Try standard datetime formats
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%b %d, %Y",
            "%B %d, %Y"
        ):
            try:
                dt = datetime.datetime.strptime(clean_str, fmt)
                dt = IST_TZ.localize(dt)
                break
            except Exception:
                continue

    if dt is None:
        # Fallback regex / email parsing
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
        except Exception:
            dt = now_ist

    ist_dt = to_ist(dt)
    if ist_dt.year < 2020 or ist_dt.year > 2030:
        ist_dt = now_ist
    raw_iso = ist_dt.isoformat()
    ist_str = ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")

    # Relative time string
    diff = now_ist - ist_dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        rel = "Just now"
    elif seconds < 3600:
        rel = f"{max(1, seconds // 60)}m ago"
    elif seconds < 86400:
        rel = f"{max(1, seconds // 3600)}h ago"
    elif seconds < 172800:
        rel = "1 day ago"
    elif seconds < 604800:
        days = seconds // 86400
        rel = f"{days} days ago"
    elif seconds < 2592000:
        weeks = max(1, seconds // 604800)
        rel = f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        rel = ist_dt.strftime("%d %b %Y")

    return ist_str, raw_iso, rel

GENERIC_REMOTE_KEYWORDS = [
    "remote", "anywhere", "worldwide", "global", "work from home", "wfh", "remote - global",
    "remote - worldwide", "work from anywhere", "anywhere in the world"
]

def is_india_location(location_str: str, country_code: str = "", workplace_type: str = "") -> bool:
    """
    Strictly verifies if a position is located in India or is an eligible unconstrained Remote role.
    Prevents false positives from US locations like Indiana/Indianapolis, and rejects foreign-only locations like Dublin/London/Atlanta.
    """
    if country_code and country_code.strip().lower() in ("in", "ind", "india"):
        return True

    loc_clean = (location_str or "").strip().lower()
    wp_clean = (workplace_type or "").strip().lower()

    if not loc_clean:
        if wp_clean == "remote":
            return True
        return False

    # 1. Eliminate false positives from US locations containing 'indian' (e.g. Indiana, Indianapolis)
    loc_without_us_indian = re.sub(
        r"\b(indiana|indianapolis|indian\s+river|indian\s+wells|indian\s+trail|indianola)\b",
        "",
        loc_clean
    )

    # 2. Check for explicit India country reference
    has_india_word = bool(re.search(r"\b(india|indian)\b", loc_without_us_indian))

    # 3. Check for recognized Indian cities, metros, and states
    has_indian_city = False
    for city in INDIA_CITIES_AND_STATES:
        if re.search(r"\b" + re.escape(city) + r"\b", loc_clean):
            has_indian_city = True
            break

    # If explicit Indian city or country is present, it is valid!
    if has_india_word or has_indian_city:
        return True

    # 4. If no Indian city/country is present:
    # A job can ONLY qualify if the location string itself is purely generic Remote (e.g. 'Remote', 'Worldwide')
    # If the location specifies a physical location (e.g. 'Atlanta', 'Boston', 'Dublin', 'Chicago'), it is NOT India!
    has_foreign_restricted = any(bool(re.search(pat, loc_clean)) for pat in FOREIGN_RESTRICTED_REMOTES)
    if has_foreign_restricted:
        return False

    has_foreign = any(re.search(r"\b" + re.escape(fc) + r"\b", loc_clean) for fc in FOREIGN_TERRITORIES)
    has_us_code = bool(re.search(r",\s*(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)\b", loc_clean))
    if has_foreign or has_us_code:
        return False

    # Check if the string is purely generic remote terms (e.g. 'Remote', 'Remote / Work From Home')
    stripped = loc_clean
    for kw in GENERIC_REMOTE_KEYWORDS:
        stripped = re.sub(r"\b" + re.escape(kw) + r"\b", "", stripped)
    stripped = re.sub(r"[\s,\-–—/|()]+", "", stripped)

    if not stripped and (wp_clean == "remote" or any(kw in loc_clean for kw in GENERIC_REMOTE_KEYWORDS)):
        return True

    return False

def extract_india_location(location_str: str) -> str:
    """
    Extracts the clean Indian location from a multi-location string.
    Example: 'Bengaluru, Karnataka, India; Berlin, Germany; Dublin, Ireland' -> 'Bengaluru, Karnataka, India'
             'London, New York, Singapore, Boston, Bangalore' -> 'Bangalore, India'
    """
    if not location_str:
        return "India"
    s = location_str.strip()

    # Semicolon, pipe, or newline delimited multi-locations
    delims = [";", "|", "\n"]
    for d in delims:
        if d in s:
            parts = [p.strip() for p in s.split(d) if p.strip()]
            for part in parts:
                p_lower = part.lower()
                clean_p = re.sub(r"\b(indiana|indianapolis|indian\s+river|indian\s+wells|indian\s+trail|indianola)\b", "", p_lower)
                if re.search(r"\b(india|indian)\b", clean_p) or any(re.search(r"\b" + re.escape(c) + r"\b", p_lower) for c in INDIA_CITIES_AND_STATES):
                    return part

    # Comma-delimited list of worldwide cities (e.g. 'Montreal, Bangalore, Warsaw' or 'London & Bangalore')
    norm_s = s.replace(" & ", ", ").replace(" and ", ", ")
    if "," in norm_s:
        parts = [p.strip() for p in norm_s.split(",") if p.strip()]
        if len(parts) >= 2:
            has_foreign_part = any(any(re.search(r"\b" + re.escape(fc) + r"\b", p.lower()) for fc in FOREIGN_TERRITORIES) for p in parts)
            if has_foreign_part:
                for part in parts:
                    p_lower = part.lower()
                    clean_p = re.sub(r"\b(indiana|indianapolis|indian\s+river|indian\s+wells|indian\s+trail|indianola)\b", "", p_lower)
                    if re.search(r"\b(india|indian)\b", clean_p) or any(re.search(r"\b" + re.escape(c) + r"\b", p_lower) for c in INDIA_CITIES_AND_STATES):
                        if "india" in p_lower:
                            return part
                        return f"{part}, India"

    return s

ROLE_TAXONOMY_MAP = {
    "UI/UX Designer": {
        "synonyms": [
            "UI/UX Designer", "Product Designer", "User Experience Designer", "User Interface Designer",
            "UX Designer", "UI Designer", "UX Researcher", "Interaction Designer", "Visual Designer",
            "Design System Designer", "Web Designer", "Experience Designer", "Lead Product Designer",
            "Senior Product Designer", "Staff Product Designer", "Principal Product Designer",
            "UI / UX Designer", "UI-UX Designer", "UI UX Designer", "Figma Designer"
        ],
        "skills": ["User Interface Design", "User Experience", "Wireframing", "Prototyping", "Design Systems", "Figma", "User Research", "Usability Testing", "Information Architecture", "Visual Design", "Design Thinking", "Interaction Design", "Mockups"]
    },
    "Graphic / Brand Designer": {
        "synonyms": ["Graphic Designer", "Brand Designer", "Visual Designer", "Creative Designer", "Brand Strategist", "Motion Designer", "Illustrator"],
        "skills": ["Graphic Design", "Brand Identity", "Visual Communication", "Adobe Creative Suite", "Typography", "Color Theory", "Vector Illustration", "Marketing Collateral", "Digital Media", "Creative Direction", "Asset Creation"]
    },
    "Frontend Engineer": {
        "synonyms": [
            "Frontend Engineer", "Frontend Developer", "Front End Engineer", "Front End Developer",
            "Front-End Engineer", "Front-End Developer", "UI Developer", "UI Engineer",
            "Web Developer", "Frontend Web Developer", "Client Side Engineer", "Client Engineer",
            "React Developer", "React Engineer", "Angular Developer", "Vue Developer",
            "Next.js Developer", "Frontend Architect", "Lead Frontend Engineer", "Senior Frontend Engineer"
        ],
        "skills": ["JavaScript", "TypeScript", "HTML5", "CSS3", "Responsive Web Design", "DOM Manipulation", "State Management", "Single Page Applications", "Web Performance", "Component Architecture", "Cross-Browser Compatibility", "REST APIs", "Git", "Front End Engineering"]
    },
    "Backend Engineer": {
        "synonyms": [
            "Backend Engineer", "Backend Developer", "Server Side Developer", "API Developer",
            "Distributed Systems Engineer", "Backend Software Engineer", "Microservices Developer",
            "Python Developer", "Java Developer", "Golang Developer", "Go Developer", "Node.js Developer",
            "C++ Developer", "Spring Boot Developer"
        ],
        "skills": ["REST APIs", "Microservices", "System Design", "Database Design", "SQL", "High Availability", "API Gateway", "Caching", "Message Queues", "Scalability", "Backend Architecture", "Concurrency", "Unit Testing", "Server Architecture"]
    },
    "Full Stack Engineer": {
        "synonyms": [
            "Full Stack Engineer", "Full Stack Developer", "Fullstack Developer", "Fullstack Engineer",
            "Full-Stack Engineer", "Full-Stack Developer", "Web Application Developer", "End to End Developer",
            "Full Stack Software Engineer", "MERN Developer", "MEAN Developer"
        ],
        "skills": ["Frontend Development", "Backend Development", "REST APIs", "Database Design", "SQL", "JavaScript", "HTML5", "CSS3", "System Architecture", "Version Control", "Web Applications", "API Integration", "Full Lifecycle Development", "Microservices"]
    },
    "Mobile Engineer": {
        "synonyms": [
            "Mobile Engineer", "Mobile Developer", "iOS Developer", "Android Developer",
            "Mobile Application Developer", "App Developer", "Flutter Developer", "React Native Developer",
            "Swift Developer", "Kotlin Developer"
        ],
        "skills": ["Mobile Application Development", "iOS Development", "Android Development", "Swift", "Kotlin", "Flutter", "React Native", "Mobile UI", "App Store Deployment", "Mobile Architecture", "REST APIs", "Offline Storage", "Push Notifications"]
    },
    "AI / Machine Learning Engineer": {
        "synonyms": [
            "AI Engineer", "Machine Learning Engineer", "ML Engineer", "Artificial Intelligence Engineer",
            "Deep Learning Engineer", "GenAI Developer", "NLP Engineer", "Computer Vision Engineer", "LLM Engineer"
        ],
        "skills": ["Machine Learning", "Artificial Intelligence", "Deep Learning", "Neural Networks", "Model Training", "Feature Engineering", "Data Preprocessing", "Model Evaluation", "NLP", "Computer Vision", "MLOps", "Model Deployment", "Python", "Large Language Models"]
    },
    "Data Scientist": {
        "synonyms": ["Data Scientist", "Data Science Specialist", "Applied Scientist", "Quantitative Analyst", "Statistical Modeler", "Data Science", "Research Scientist"],
        "skills": ["Data Science", "Machine Learning", "Statistical Analysis", "Python", "SQL", "Data Modeling", "Hypothesis Testing", "Predictive Modeling", "Data Visualization", "Exploratory Data Analysis", "Pandas", "NumPy", "Quantitative Research", "Business Insights"]
    },
    "Data Engineer": {
        "synonyms": ["Data Engineer", "Big Data Engineer", "Data Platform Engineer", "ETL Developer", "Data Pipeline Engineer", "Data Infrastructure Engineer"],
        "skills": ["ETL Pipelines", "Data Warehousing", "Data Modeling", "SQL", "Big Data", "Distributed Computing", "Batch Processing", "Streaming Data", "Database Architecture", "Data Quality", "Data Governance", "Python", "Data Infrastructure", "Data Lakes"]
    },
    "Data Analyst / BI": {
        "synonyms": ["Data Analyst", "Business Intelligence Analyst", "BI Developer", "Reporting Analyst", "Analytics Consultant", "Product Analyst", "Tableau Developer", "Power BI Developer"],
        "skills": ["Data Analysis", "Business Intelligence", "SQL Querying", "Data Visualization", "Dashboard Development", "Tableau", "Power BI", "KPI Reporting", "Metrics Analysis", "Spreadsheets", "Descriptive Analytics", "Trend Analysis", "Data Storytelling"]
    },
    "DevOps / Cloud Engineer": {
        "synonyms": ["DevOps Engineer", "Cloud Engineer", "Cloud Architect", "Infrastructure Engineer", "Platform Engineer", "Cloud Operations Engineer", "AWS Engineer", "Azure Engineer", "GCP Engineer"],
        "skills": ["Cloud Infrastructure", "CI/CD Pipelines", "Docker", "Kubernetes", "Infrastructure as Code", "Terraform", "Linux Administration", "Cloud Monitoring", "Automation Scripting", "Cloud Architecture", "Configuration Management", "GitOps", "Site Reliability"]
    },
    "Site Reliability Engineer (SRE)": {
        "synonyms": ["Site Reliability Engineer", "SRE", "Reliability Engineer", "Production Engineer", "Systems Engineer", "Infrastructure Reliability"],
        "skills": ["High Availability", "Incident Management", "System Observability", "Prometheus", "Grafana", "SLO / SLA Monitoring", "Disaster Recovery", "Capacity Planning", "Linux Systems", "Kubernetes", "Root Cause Analysis", "Performance Tuning", "Automation"]
    },
    "Cybersecurity Engineer": {
        "synonyms": ["Cybersecurity Engineer", "Information Security Specialist", "Security Analyst", "Penetration Tester", "AppSec Engineer", "Cloud Security Engineer", "SOC Analyst"],
        "skills": ["Cybersecurity", "Network Security", "Application Security", "Threat Modeling", "Vulnerability Assessment", "Penetration Testing", "Security Compliance", "Identity & Access Management", "Incident Response", "Cryptography", "Security Architecture", "Risk Mitigation"]
    },
    "QA / SDET": {
        "synonyms": ["QA Engineer", "SDET", "Software Development Engineer in Test", "Quality Assurance Engineer", "Test Automation Engineer", "Software Tester", "Quality Assurance", "Quality Engineer", "Automation Tester"],
        "skills": ["Test Automation", "Quality Assurance", "Selenium", "API Testing", "Automation Frameworks", "Regression Testing", "Bug Tracking", "Test Case Design", "Continuous Testing", "Integration Testing", "Defect Management", "Performance Testing", "Quality Engineering"]
    },
    "Hardware / Embedded Engineer": {
        "synonyms": ["Hardware Engineer", "Embedded Systems Engineer", "Firmware Engineer", "IoT Engineer", "Electronics Engineer", "Embedded Engineer"],
        "skills": ["Embedded Systems", "Firmware Development", "C / C++", "Microcontrollers", "PCB Design", "Hardware Testing", "IoT Protocols", "Device Drivers", "Circuit Design", "Signal Processing"]
    },
    "Solutions Architect": {
        "synonyms": ["Solutions Architect", "Enterprise Architect", "Cloud Solutions Architect", "Technical Architect", "Solution Engineer"],
        "skills": ["System Architecture", "Cloud Solutions", "Enterprise Architecture", "Technical Consulting", "Integration Architecture", "Scalable Systems", "Client Engagement", "Proof of Concept", "Technology Selection", "Architecture Blueprint", "Design Reviews"]
    },
    "Engineering Manager / Lead": {
        "synonyms": ["Engineering Manager", "Tech Lead", "Director of Engineering", "Software Engineering Manager", "Lead Software Engineer", "Engineering Leadership", "VP Engineering", "CTO", "Chief Technology Officer", "Head of Engineering", "VP of Engineering"],
        "skills": ["Engineering Management", "Technical Leadership", "People Management", "Sprint Planning", "Team Mentorship", "Architecture Review", "Agile Delivery", "Project Management", "Hiring & Talent", "Code Quality", "Resource Allocation", "System Scalability"]
    },
    "Technical Program Manager": {
        "synonyms": ["Technical Program Manager", "TPM", "Program Manager", "Scrum Master", "Agile Coach", "Project Manager"],
        "skills": ["Program Management", "Agile Methodologies", "Scrum Framework", "Cross-Functional Collaboration", "Risk Management", "Release Management", "Sprint Execution", "Timeline Tracking", "Stakeholder Alignment", "Dependency Management", "Jira"]
    },
    "Product Manager": {
        "synonyms": ["Product Manager", "Associate Product Manager", "Technical Product Manager", "Product Owner", "Product Lead", "Product Management", "Head of Product"],
        "skills": ["Product Management", "Product Strategy", "Roadmap Planning", "Feature Prioritization", "Agile / Scrum", "User Stories", "Stakeholder Management", "A/B Testing", "Data Driven Decision Making", "Product Discovery", "User Experience", "Market Research", "Customer Empathy"]
    },
    "Human Resources / Recruiter": {
        "synonyms": [
            "HR Specialist", "Talent Acquisition Specialist", "Talent Acquisition", "Technical Recruiter",
            "Recruiter", "Senior Recruiter", "HR Generalist", "People Operations Manager", "People Operations",
            "People Partner", "HR Business Partner", "HRBP", "Talent Partner"
        ],
        "skills": ["Talent Acquisition", "Technical Recruiting", "Candidate Sourcing", "Interviewing", "Employee Relations", "HR Policies", "Onboarding", "Performance Management", "Compensation & Benefits", "HR Operations", "Talent Management"]
    },
    "Sales / Business Development": {
        "synonyms": [
            "Business Development Executive", "Business Development Representative", "BDR", "SDR",
            "Account Executive", "Sales Manager", "B2B Sales Representative", "Sales Development Representative",
            "Sales Executive", "Enterprise Sales", "Inside Sales", "Outbound Sales"
        ],
        "skills": ["B2B Sales", "Business Development", "Lead Generation", "Pipeline Management", "Client Prospecting", "Negotiation", "Sales Strategy", "CRM Software", "Revenue Growth", "Customer Acquisition", "Relationship Management", "Solution Selling"]
    },
    "Customer Success / Account Manager": {
        "synonyms": ["Customer Success Manager", "Account Manager", "Client Relationship Manager", "Customer Support Specialist", "Customer Experience Manager", "Client Partner"],
        "skills": ["Customer Success", "Client Relationship Management", "Customer Retention", "Onboarding & Training", "Account Growth", "Customer Satisfaction", "Issue Resolution", "Support Operations", "Churn Prevention", "Client Communication"]
    },
    "Marketing / Growth Specialist": {
        "synonyms": ["Marketing Specialist", "Growth Marketer", "Digital Marketing Manager", "Performance Marketer", "Marketing Manager", "Demand Generation", "Brand Manager"],
        "skills": ["Digital Marketing", "Growth Marketing", "Campaign Management", "Performance Marketing", "Social Media Marketing", "Email Marketing", "Content Strategy", "Analytics & Conversion", "Customer Acquisition", "Brand Awareness", "Funnel Optimization"]
    },
    "Content Writer / Copywriter": {
        "synonyms": ["Content Writer", "Copywriter", "Technical Writer", "Content Strategist", "Creative Writer", "Blog Specialist"],
        "skills": ["Content Creation", "Copywriting", "Technical Writing", "Content Strategy", "SEO Copywriting", "Editing & Proofreading", "Creative Writing", "Storytelling", "Research & Synthesis", "Documentation", "Blog Writing"]
    },
    "SEO / SEM Specialist": {
        "synonyms": ["SEO Specialist", "SEM Manager", "Search Engine Optimization", "Organic Growth Specialist", "Search Marketer", "PPC Specialist"],
        "skills": ["Search Engine Optimization", "On-Page SEO", "Technical SEO", "Keyword Research", "Link Building", "Google Analytics", "Search Console", "Organic Traffic", "SEM / Paid Search", "SERP Ranking", "Content Optimization"]
    },
    "Finance / Accounting": {
        "synonyms": ["Finance Specialist", "Financial Analyst", "Accountant", "Finance Manager", "Corporate Finance", "Taxation Specialist", "Chartered Accountant", "Auditor"],
        "skills": ["Financial Analysis", "Accounting Principles", "Budgeting & Forecasting", "Financial Modeling", "Auditing", "General Ledger", "Taxation", "Financial Reporting", "Variance Analysis", "ERP Systems", "Cost Control"]
    },
    "Operations / Supply Chain": {
        "synonyms": ["Operations Specialist", "Operations Manager", "Operations Associate", "Supply Chain Analyst", "Logistics Coordinator", "Process Improvement Specialist", "Warehouse Lead"],
        "skills": ["Business Operations", "Process Optimization", "Supply Chain Management", "Logistics Coordination", "Vendor Management", "Workflow Automation", "Operational Efficiency", "Inventory Management", "Quality Control", "Standard Operating Procedures"]
    },
    "Legal / Compliance Specialist": {
        "synonyms": ["Legal Counsel", "Compliance Specialist", "Legal Advisor", "Regulatory Affairs", "Corporate Counsel", "Paralegal", "Compliance Analyst"],
        "skills": ["Corporate Law", "Regulatory Compliance", "Contract Negotiation", "Legal Drafting", "Risk Assessment", "Intellectual Property", "Policy Development", "Corporate Governance", "Statutory Compliance", "Legal Advisory"]
    },
    "Technical Support / IT": {
        "synonyms": [
            "IT Support Engineer", "Technical Support Specialist", "Technical Support Engineer", "Technical Support", 
            "Support Engineer", "Customer Support Engineer", "Application Support Engineer", "Desktop Support", 
            "System Administrator", "IT Helpdesk", "IT Administrator", "Service Desk Analyst", "Help Desk Technician"
        ],
        "skills": ["Technical Support", "IT Infrastructure", "Troubleshooting", "Hardware Diagnostics", "Network Configuration", "Operating Systems", "User Provisioning", "Helpdesk Support", "IT Service Management", "Remote Assistance"]
    },
    "Network Engineer": {
        "synonyms": [
            "Network Engineer", "Network Administrator", "CCNA", "CCNP", "Cisco Network Engineer", 
            "Network Security Engineer", "Telecom Engineer", "Infrastructure Network", "Network Specialist", 
            "Cloud Network Engineer", "NOC Engineer"
        ],
        "skills": ["Network Engineering", "Cisco Routing & Switching", "BGP", "OSPF", "TCP/IP", "Firewalls", "VPN Configuration", "Network Security", "Subnetting", "Network Monitoring", "Wireshark"]
    },
    "Hardware / Embedded Engineer": {
        "synonyms": [
            "Hardware Engineer", "Embedded Systems Engineer", "Firmware Engineer", "IoT Engineer", 
            "Electronics Engineer", "Embedded Engineer"
        ],
        "skills": ["Embedded Systems", "Firmware Development", "C / C++", "Microcontrollers", "PCB Design", "Hardware Testing", "IoT Protocols", "Device Drivers", "Circuit Design", "Signal Processing"]
    },
    "Embedded Software Engineer": {
        "synonyms": [
            "Embedded Software Engineer", "Embedded Software", "Embedded Systems Developer", 
            "Embedded C++", "Embedded C", "IoT Software Engineer", "Embedded Linux Engineer"
        ],
        "skills": ["Embedded C", "Embedded C++", "RTOS", "Device Drivers", "Microcontrollers", "Embedded Linux", "Communication Protocols", "UART", "SPI", "I2C", "Debugging Tools"]
    },
    "Firmware Engineer": {
        "synonyms": [
            "Firmware Engineer", "Firmware Developer", "Microcontroller Developer", 
            "BSP Engineer", "Board Support Package", "RTOS Engineer", "Device Driver Developer"
        ],
        "skills": ["Firmware Development", "C / C++", "Microcontrollers", "ARM Cortex", "Board Support Packages", "RTOS", "Hardware Debugging", "JTAG", "Oscilloscopes", "Low-Level Programming"]
    },
    "Hardware Engineer": {
        "synonyms": [
            "Hardware Engineer", "Hardware Design Engineer", "Electronics Engineer", 
            "PCB Design Engineer", "FPGA Engineer", "VLSI Design Engineer", "ASIC Engineer"
        ],
        "skills": ["Hardware Design", "PCB Design", "Schematic Capture", "Altium", "FPGA", "Verilog / VHDL", "VLSI", "Circuit Analysis", "Signal Integrity", "Hardware Verification"]
    },
    "Database Administrator (DBA)": {
        "synonyms": [
            "Database Administrator", "DBA", "SQL DBA", "Oracle DBA", "Postgres DBA", 
            "MongoDB DBA", "Database Engineer", "Data Architect DBA", "DB Admin"
        ],
        "skills": ["Database Administration", "PostgreSQL", "MySQL", "Oracle Database", "Performance Tuning", "Query Optimization", "Database Replication", "Backup & Recovery", "High Availability", "Database Security"]
    },
    "MLOps Engineer": {
        "synonyms": [
            "MLOps Engineer", "Machine Learning Operations", "ML Platform Engineer", 
            "AI Platform Engineer", "Model Deployment Engineer", "ML Infrastructure Engineer"
        ],
        "skills": ["MLOps", "Model Deployment", "MLflow", "Kubeflow", "Docker", "Kubernetes", "CI/CD for ML", "Feature Stores", "Model Monitoring", "Cloud AI", "Python", "Data Versioning"]
    },
    "NLP / LLM Engineer": {
        "synonyms": [
            "NLP Engineer", "LLM Engineer", "Natural Language Processing", "Prompt Engineer", 
            "AI Prompt Engineer", "Large Language Model", "LLM Developer", "NLP Scientist", "GenAI Engineer"
        ],
        "skills": ["Natural Language Processing", "Large Language Models", "Transformers", "LangChain", "LlamaIndex", "Hugging Face", "Fine-Tuning", "Vector Databases", "Prompt Engineering", "Python", "PyTorch"]
    },
    "Computer Vision Engineer": {
        "synonyms": [
            "Computer Vision Engineer", "Computer Vision", "CV Engineer", "Image Processing Engineer", 
            "Perception Engineer", "Deep Learning Vision", "Vision AI Engineer"
        ],
        "skills": ["Computer Vision", "OpenCV", "Image Processing", "Object Detection", "Image Segmentation", "Deep Learning", "Convolutional Neural Networks", "PyTorch", "TensorFlow", "Video Analysis"]
    },
    "Platform / Infrastructure Engineer": {
        "synonyms": [
            "Platform Engineer", "Infrastructure Engineer", "Cloud Platform Engineer", 
            "Core Platform Developer", "Systems Infrastructure", "Developer Platform", "Developer Tooling"
        ],
        "skills": ["Platform Engineering", "Infrastructure as Code", "Terraform", "Kubernetes", "Developer Experience", "CI/CD", "Internal Developer Platforms", "Cloud Architecture", "Observability", "Linux"]
    },
    "Blockchain / Web3 Engineer": {
        "synonyms": [
            "Blockchain Engineer", "Web3 Engineer", "Smart Contract Developer", "Solidity Developer", 
            "Ethereum Developer", "Web3 Developer", "Blockchain Developer", "Crypto Engineer", "DeFi Engineer"
        ],
        "skills": ["Blockchain", "Smart Contracts", "Solidity", "Ethereum", "Web3.js", "Ethers.js", "Rust", "Cryptography", "DeFi", "Consensus Algorithms", "Hardhat", "Truffle"]
    },
    "Release / Build Engineer": {
        "synonyms": [
            "Release Engineer", "Build Engineer", "Release Manager", "CI CD Engineer", 
            "DevOps Release", "Deployment Engineer", "Configuration Manager", "Build and Release"
        ],
        "skills": ["Build Automation", "Release Management", "CI/CD Pipelines", "Jenkins", "GitHub Actions", "Artifact Management", "Deployment Automation", "Version Tagging", "Environment Management"]
    },
    "Information Security Analyst": {
        "synonyms": [
            "Information Security Analyst", "InfoSec Analyst", "Security Analyst", "SOC Analyst", 
            "Cyber Defense Analyst", "Threat Intelligence Analyst", "Incident Response Analyst", "SecOps Analyst"
        ],
        "skills": ["Information Security", "SIEM Tools", "Log Analysis", "Incident Response", "Vulnerability Scanning", "Threat Hunting", "Security Operations", "Security Frameworks (NIST/ISO)", "Forensics"]
    },
    "Salesforce Developer": {
        "synonyms": [
            "Salesforce Developer", "Salesforce", "Salesforce Administrator", "Salesforce Engineer", 
            "Apex Developer", "Salesforce Architect", "Lightning Developer", "SFDC Developer"
        ],
        "skills": ["Salesforce CRM", "Apex", "Lightning Web Components", "Visualforce", "SOQL / SOSL", "Salesforce Integration", "Workflow Automation", "Process Builder", "Platform Events"]
    },
    "Game Developer": {
        "synonyms": [
            "Game Developer", "Unity Developer", "Unreal Engine Developer", "Game Programmer", 
            "Game Designer", "Gameplay Engineer", "3D Game Developer", "Unreal Developer", "Unity 3D"
        ],
        "skills": ["Game Development", "Unity 3D", "Unreal Engine", "C#", "C++", "3D Math & Physics", "Game Mechanics", "Shader Programming", "Animation Systems", "Game Optimization"]
    },
    "Fintech / Algorithmic Trading Engineer": {
        "synonyms": [
            "Fintech Engineer", "Algorithmic Trading Engineer", "Quant Developer", "Quantitative Developer", 
            "Trading Systems Engineer", "Low Latency Engineer", "HFT Developer", "Financial Software Engineer"
        ],
        "skills": ["Low Latency Systems", "High Frequency Trading", "C++", "Order Execution Systems", "Financial Markets", "FIX Protocol", "Algorithms", "Market Data Feeds", "Performance Profiling"]
    },
    "Business Analyst": {
        "synonyms": [
            "Business Analyst", "Technical Business Analyst", "Functional Analyst", 
            "IT Business Analyst", "Senior Business Analyst", "Lead Business Analyst", "Business Analysis"
        ],
        "skills": ["Business Analysis", "Requirements Elicitation", "Use Case Modeling", "BRD / FRD Creation", "Stakeholder Management", "User Stories", "Agile / Scrum", "Process Mapping", "SQL Basics", "Data Analysis"]
    },
    "Scrum Master / Agile Coach": {
        "synonyms": [
            "Scrum Master", "Agile Coach", "Certified Scrum Master", "CSM", 
            "Agile Project Manager", "Kanban Coach", "Agile Facilitator", "Scrum Lead"
        ],
        "skills": ["Agile Frameworks", "Scrum Ceremonies", "Sprint Retrospectives", "Backlog Refinement", "Kanban", "Agile Coaching", "Continuous Improvement", "Team Facilitation", "Jira", "Velocity Tracking"]
    },
    "Growth Marketing Specialist": {
        "synonyms": [
            "Growth Marketing Specialist", "Growth Marketer", "Growth Hacker", "Acquisition Marketer", 
            "Lifecycle Marketer", "Growth Marketing Manager", "Demand Generation", "Growth Lead Marketing"
        ],
        "skills": ["Growth Marketing", "A/B Testing", "Funnel Optimization", "Customer Acquisition", "CAC / LTV Optimization", "Retention Strategies", "Marketing Automation", "Performance Analytics", "Attribution Modeling"]
    },
    "Technical Writer": {
        "synonyms": [
            "Technical Writer", "Tech Writer", "API Documenter", "Documentation Engineer", 
            "Technical Documentation", "Content Developer Tech", "SDK Documenter"
        ],
        "skills": ["Technical Writing", "API Documentation", "Markdown", "Developer Portals", "SDK Guides", "Release Notes", "Information Architecture", "Content Management", "Technical Editing"]
    },
    "IT Support Specialist": {
        "synonyms": [
            "IT Support Specialist", "IT Support Engineer", "IT Technician", "Desktop Support Engineer", 
            "Help Desk Technician", "Service Desk Analyst", "Workstation Support", "IT Desk Engineer"
        ],
        "skills": ["IT Support", "Desktop Support", "Troubleshooting", "Windows / macOS Administration", "Active Directory", "Hardware Maintenance", "Ticketing Systems", "Customer Service", "Remote Support"]
    },
    "Intern / Trainee": {
        "synonyms": ["Software Intern", "Engineering Intern", "Graduate Trainee", "Summer Intern", "College Intern", "Apprentice"],
        "skills": ["Learning Agility", "Software Engineering Fundamentals", "Problem Solving", "Academic Projects", "Team Collaboration", "Version Control", "Technical Curiosity", "Fast Learner", "Continuous Learning", "Hands-on Development"]
    },
    "Chief of Staff / Founder's Office": {
        "synonyms": ["Chief of Staff", "Founder's Office Associate", "Executive Assistant", "Strategic Initiatives Lead", "Special Projects Manager"],
        "skills": ["Strategic Initiatives", "Executive Support", "Cross-Functional Coordination", "Business Operations", "High-Impact Projects", "Organizational Strategy", "Executive Communication", "Program Management", "Problem Solving"]
    },
    "Business Analyst / Strategy": {
        "synonyms": ["Business Analyst", "Strategy Consultant", "Corporate Strategy Analyst", "Business Operations Analyst", "Functional Consultant"],
        "skills": ["Business Analysis", "Requirements Gathering", "Process Modeling", "Strategic Planning", "Stakeholder Communication", "Cost-Benefit Analysis", "Gap Analysis", "Market Analysis", "Business Process Mapping", "Data Driven Strategy"]
    },
    "Software Engineer": {
        "synonyms": ["Software Engineer", "Software Development Engineer", "SDE", "SWE", "Software Developer", "Programmer", "Application Developer", "Software Architecture"],
        "skills": ["Data Structures", "Algorithms", "System Design", "Object Oriented Programming", "REST APIs", "Git", "Code Review", "Unit Testing", "Debugging", "Clean Code", "Design Patterns", "Problem Solving", "Scalability", "High Availability"]
    },
    "Traditional / Core Engineering": {
        "synonyms": [
            "Mechanical Engineer", "Civil Engineer", "Chemical Engineer", "Materials Engineer", "Project Engineer", 
            "Structural Engineer", "Electrical Design Engineer", "Industrial Engineer", "Core Engineering", 
            "Process Engineer", "Manufacturing Engineer", "Technical Assistant", "Manufacturing", "Shop Floor", 
            "Technician", "Machinist", "Operator"
        ],
        "skills": ["Mechanical Engineering", "Civil Engineering", "Chemical Engineering", "AutoCAD", "Thermodynamics", "Materials Science", "Project Management", "Site Engineering", "Structural Analysis", "Process Engineering", "Manufacturing Operations", "Quality Standards"]
    }
}

POPULAR_TECH_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust", "C++", "C#", ".NET",
    "React", "Angular", "Vue", "Next.js", "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "SQL Server", "DynamoDB",
    "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform",
    "Linux", "Git", "GitHub", "GitLab", "CI/CD", "Jenkins", "Ansible", "GraphQL", "REST", "gRPC",
    "Kafka", "RabbitMQ", "Apache Spark", "Hadoop", "Airflow", "Snowflake", "Databricks", "Tableau",
    "Power BI", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn", "Hugging Face", "LLM",
    "LangChain", "Selenium", "Cypress", "Playwright", "Postman", "Jira", "Figma", "Swift", "Kotlin", "Flutter"
]

def classify_job_canonical_role(title: str, role_cat: str = "") -> str:
    combined = f"{title} {role_cat}".lower()
    title_lower = title.lower()

    # 1. UI/UX Design protection: if title clearly indicates UI/UX, product design, or interaction design,
    # prevent it from being hijacked by 'growth', 'marketing', or generic engineering
    if any(re.search(p, title_lower) for p in [
        r"\bui\s*/\s*ux\b", r"\bproduct\s+designer\b", r"\bux\s+designer\b", r"\bui\s+designer\b",
        r"\binteraction\s+designer\b", r"\buser\s+experience\b", r"\buser\s+interface\s+design(er)?\b",
        r"\bux\s+researcher\b", r"\bvisual\s+designer\b", r"\bdesign\s+system\b", r"\bexperience\s+designer\b"
    ]):
        return "UI/UX Designer"

    # 2. Engineering Management overrides
    if any(re.search(p, title_lower) for p in [
        r"\bengineering\s+manager\b", r"\bdirector\s+of\s+engineering\b", 
        r"\bvp\s+(of\s+)?engineering\b", r"\bsoftware\s+engineering\s+manager\b", r"\bhead\s+of\s+engineering\b"
    ]):
        return "Engineering Manager / Lead"

    # 3. Engineering specializations overrides (handles 'Software Engineer - Frontend', 'SDE 2 - Backend', etc.)
    if any(re.search(p, title_lower) for p in [r"\bfull[\s\-_]*stack\b", r"\bmern\b", r"\bmean\b"]):
        return "Full Stack Engineer"
    if any(re.search(p, title_lower) for p in [r"\bfront[\s\-_]*end\b", r"\bui\s+developer\b", r"\bui\s+engineer\b", r"\bweb\s+developer\b", r"\breact\b", r"\bangular\b", r"\bvue\b"]):
        return "Frontend Engineer"
    if any(re.search(p, title_lower) for p in [r"\bback[\s\-_]*end\b", r"\bserver\s+side\b", r"\bmicroservices\b"]):
        return "Backend Engineer"
    if any(re.search(p, title_lower) for p in [r"\bmobile\b", r"\bios\b", r"\bandroid\b", r"\bflutter\b", r"\breact[\s\-_]*native\b", r"\bswift\b", r"\bkotlin\b"]) and "cloud" not in title_lower:
        return "Mobile Engineer"
    if any(re.search(p, title_lower) for p in [r"\bmachine\s+learning\b", r"\bml\s+engineer\b", r"\bdeep\s+learning\b", r"\bnlp\b", r"\bllm\b", r"\bcomputer\s+vision\b", r"\bgenai\b", r"\bgenerative\s+ai\b"]):
        return "AI / Machine Learning Engineer"
    if any(re.search(p, title_lower) for p in [r"\bdata\s+scientist\b", r"\bapplied\s+scientist\b", r"\bquantitative\s+analyst\b", r"\bresearch\s+scientist\b"]):
        return "Data Scientist"
    if any(re.search(p, title_lower) for p in [r"\bdata\s+engineer\b", r"\bbig\s+data\b", r"\betl\b", r"\bdata\s+platform\b", r"\bdata\s+pipeline\b"]):
        return "Data Engineer"
    if any(re.search(p, title_lower) for p in [r"\bdevops\b", r"\bcloud\s+engineer\b", r"\bcloud\s+architect\b", r"\binfrastructure\s+engineer\b", r"\bplatform\s+engineer\b"]):
        return "DevOps / Cloud Engineer"
    if any(re.search(p, title_lower) for p in [r"\bsre\b", r"\bsite\s+reliability\b"]) and "director" not in title_lower:
        return "Site Reliability Engineer (SRE)"
    if any(re.search(p, title_lower) for p in [r"\bsdet\b", r"\bqa\b", r"\bquality\s+assurance\b", r"\btest\s+automation\b", r"\bsoftware\s+tester\b", r"\btest\s+engineer\b", r"\bquality\s+engineer\b"]):
        return "QA / SDET"

    # Network Engineer overrides
    if any(re.search(p, title_lower) for p in [r"\bnetwork\s+engineer\b", r"\bnetwork\s+administrator\b", r"\bccna\b", r"\bccnp\b", r"\bcisco\b", r"\bcloud\s+network\b", r"\bnoc\s+engineer\b"]):
        return "Network Engineer"

    # Technical Support / IT overrides
    if any(re.search(p, title_lower) for p in [r"\btechnical\s+support\b", r"\bsupport\s+engineer\b", r"\bapplication\s+support\b", r"\bdesktop\s+support\b", r"\bit\s+support\b", r"\bhelpdesk\b", r"\bservice\s+desk\b"]):
        return "Technical Support / IT"

    # Hardware / Embedded / Firmware overrides
    if any(re.search(p, title_lower) for p in [r"\bfirmware\b", r"\bbsp\s+engineer\b"]):
        return "Firmware Engineer"
    if any(re.search(p, title_lower) for p in [r"\bhardware\s+engineer\b", r"\bhardware\s+design\b", r"\bpcb\s+design\b", r"\bvlsi\b", r"\basic\b", r"\bfpga\b"]):
        return "Hardware Engineer"
    if any(re.search(p, title_lower) for p in [r"\bembedded\s+software\b", r"\bembedded\s+systems?\s+developer\b"]):
        return "Embedded Software Engineer"

    # Database Administrator overrides
    if any(re.search(p, title_lower) for p in [r"\bdatabase\s+administrator\b", r"\bdba\b", r"\bsql\s+dba\b", r"\bpostgres\s+dba\b", r"\boracle\s+dba\b"]):
        return "Database Administrator (DBA)"

    # Manufacturing / Assistant / Operations overrides
    if any(re.search(p, title_lower) for p in [r"\bmanufacturing\b", r"\btechnical\s+assistant\b", r"\bshop\s+floor\b", r"\btechnician\b", r"\bmachinist\b", r"\boperator\b"]):
        return "Traditional / Core Engineering"

    # 4. Specific non-engineering precedence overrides
    if any(re.search(p, combined) for p in [r"\baccount(s|ing)?\b", r"\breceivable\b", r"\bpayable\b", r"\bfinance\b", r"\btax\b", r"\baudit\b", r"\bbilling\b"]) and "engineer" not in combined:
        return "Finance / Accounting"
    if any(re.search(p, combined) for p in [r"\bart\s+director\b", r"\bgraphic\b", r"\bcreative\s+director\b", r"\billustrator\b", r"\bmotion\s+designer\b"]):
        return "Graphic / Brand Designer"
    if any(re.search(p, combined) for p in [r"\banalytics\b", r"\bdata\s+analyst\b", r"\bbi\s+developer\b"]) and "engineer" not in combined:
        return "Data Analyst / BI"
    if any(re.search(p, combined) for p in [r"\baccount\s+manager\b", r"\bcustomer\s+success\b", r"\baircover\b", r"\bclient\s+success\b"]) and "engineer" not in combined:
        return "Customer Success / Account Manager"
    if any(re.search(p, combined) for p in [r"\btalent\s+acquisition\b", r"\brecruiter\b", r"\bpeople\s+partner\b", r"\bpeople\s+operations\b"]):
        return "Human Resources / Recruiter"
    if any(re.search(p, combined) for p in [r"\bbdr\b", r"\bsdr\b", r"\bbusiness\s+development\s+rep", r"\baccount\s+executive\b", r"\boutbound\s+sales\b"]):
        return "Sales / Business Development"
    if any(re.search(p, combined) for p in [r"\bmarket\s+manager\b", r"\bmarketing\b", r"\bgrowth\b", r"\bbrand\b"]) and "engineer" not in combined and "designer" not in combined:
        return "Marketing / Growth Specialist"
    if any(re.search(p, combined) for p in [r"\boperations\s+associate\b", r"\boperations\s+manager\b", r"\blogistics\b", r"\bwarehouse\b"]):
        return "Operations / Supply Chain"
    if any(re.search(p, combined) for p in [r"\blegal\s+counsel\b", r"\bparalegal\b", r"\bcompliance\s+analyst\b", r"\bcompliance\s+officer\b"]):
        return "Legal / Compliance Specialist"

    # Core / Non-software engineering overrides (chemical, civil, mechanical, materials, etc.)
    non_sw_patterns = [
        r"\bchemical\b", r"\bmaterials?\s+engineer(ing)?\b", r"\bcivil\b", r"\bmechanical\b",
        r"\bproject\s+engineer\b", r"\bsite\s+engineer\b", r"\bstructural\b", r"\bpetroleum\b",
        r"\bmining\b", r"\bpiping\b", r"\bhvac\b", r"\binstrumentation\b", r"\benvironmental\s+engineer\b",
        r"\bsafety\s+engineer\b", r"\bprocess\s+engineer\b", r"\bcontrol\s+panel\b", r"\beica\b",
        r"\bcommissioning\s+(\(?cx\)?\s+)?engineer\b", r"\bmetallurg\b", r"\bwelding\b", r"\bsubsurface\b",
        r"\belectrical\s+design\b", r"\belectrical\s+engineer\b", r"\belectrical\s+drafter\b",
        r"\bmanufacturing\b", r"\btechnical\s+assistant\b", r"\bshop\s+floor\b"
    ]
    is_non_sw_eng = any(re.search(p, combined) for p in non_sw_patterns)
    has_sw_keyword = any(re.search(p, combined) for p in [r"\bsoftware\b", r"\bdeveloper\b", r"\bsde\b", r"\bswe\b", r"\bfirmware\b", r"\bembedded\b", r"\bfull[\s\-_]*stack\b", r"\bfront[\s\-_]*end\b", r"\bback[\s\-_]*end\b"])
    if is_non_sw_eng and not has_sw_keyword:
        return "Traditional / Core Engineering"

    # 5. Iterate through ordered taxonomy map (specific specializations are evaluated first)
    for role_name, data in ROLE_TAXONOMY_MAP.items():
        syns = [role_name.lower()] + [s.lower() for s in data["synonyms"]]
        for s in syns:
            if re.search(rf"\b{re.escape(s)}\b", combined):
                return role_name
            if " " in s and s in combined:
                return role_name

    # 6. Intelligent fallback based on title keywords
    is_support_or_net = any(re.search(p, combined) for p in [r"\bnetwork\b", r"\bsupport\b", r"\bhelpdesk\b", r"\bhardware\b", r"\bmanufacturing\b", r"\bassistant\b", r"\btechnician\b"])
    if any(k in combined for k in ["software engineer", "developer", "software", "programmer", "sde", "swe", "software architect"]):
        if not is_support_or_net:
            return "Software Engineer"
    if re.search(r"\bengineer\b", combined) and not is_non_sw_eng and not is_support_or_net:
        return "Software Engineer"
    if is_non_sw_eng:
        return "Traditional / Core Engineering"
    if is_support_or_net:
        if "network" in combined:
            return "Network Engineer"
        if "support" in combined or "helpdesk" in combined:
            return "Technical Support / IT"
        return "Traditional / Core Engineering"
    if any(k in combined for k in ["designer", "design", "creative"]):
        return "UI/UX Designer"
    if any(k in combined for k in ["sales", "bdr", "sdr", "account executive"]):
        return "Sales / Business Development"
    if any(k in combined for k in ["recruit", "talent", "hr", "people"]):
        return "Human Resources / Recruiter"
    if any(k in combined for k in ["operations", "logistics", "warehouse"]):
        return "Operations / Supply Chain"
    if any(k in combined for k in ["analyst", "strategy", "consultant", "business ops"]):
        return "Business Analyst / Strategy"

    return "Business Analyst / Strategy"

def generate_job_tags(
    title: str,
    company: str = "",
    location: str = "",
    role_category: str = "",
    workplace_type: str = "",
    experience_level: str = "",
    employment_type: str = "",
    dept: str = "",
    raw_text: str = ""
) -> List[str]:
    canonical_role = classify_job_canonical_role(title, role_category)
    role_info = ROLE_TAXONOMY_MAP.get(canonical_role, ROLE_TAXONOMY_MAP["Software Engineer"])

    tags: List[str] = []
    seen_lower = set()

    def add_tag(t: str):
        if not t:
            return
        clean_t = re.sub(r"[\[\]'\"#]", "", str(t)).strip()
        if len(clean_t) < 2 or len(clean_t) > 45:
            return
        tl = clean_t.lower()
        if tl not in seen_lower:
            seen_lower.add(tl)
            tags.append(clean_t)

    # 1. Canonical Role & Synonyms (5-7 tags)
    add_tag(canonical_role)
    for syn in role_info["synonyms"][:6]:
        add_tag(syn)

    # 2. Domain Core Competencies & Skills (10-12 tags)
    for skill in role_info["skills"][:12]:
        add_tag(skill)

    # 3. Dynamic extracted technology keywords from title, dept, text (3-8 tags)
    search_corpus = f"{title} {role_category} {dept} {raw_text}".lower()
    for tech in POPULAR_TECH_KEYWORDS:
        pattern = rf"\b{re.escape(tech.lower())}\b"
        if re.search(pattern, search_corpus):
            add_tag(tech)
        if len(tags) >= 24:
            break

    # 4. Seniority / Experience Level (2-3 tags)
    exp_lower = f"{experience_level} {title}".lower()
    if "intern" in exp_lower or "trainee" in exp_lower:
        add_tag("Internship Opportunity")
        add_tag("College Trainee")
    elif "director" in exp_lower or "vp" in exp_lower or "vice president" in exp_lower:
        add_tag("Director Level")
        add_tag("Executive Leadership")
    elif "manager" in exp_lower or "lead" in exp_lower or "principal" in exp_lower:
        add_tag("Technical Leadership")
        add_tag("Engineering Management")
    elif "senior" in exp_lower or "sr." in exp_lower or "staff" in exp_lower:
        add_tag("Senior Level")
        add_tag("Senior Professional")
    else:
        add_tag("Entry Level")
        add_tag("Junior Professional")

    # 5. Workplace Mode (2-3 tags)
    wp_lower = f"{workplace_type} {location}".lower()
    if "remote" in wp_lower or "wfh" in wp_lower or "work from home" in wp_lower:
        add_tag("Remote")
        add_tag("Work From Home")
        add_tag("Remote India")
    elif "hybrid" in wp_lower:
        add_tag("Hybrid")
        add_tag("Flexible Workplace")
        add_tag("Hybrid Model")
    else:
        add_tag("In-Office")
        add_tag("On-Site Opportunity")

    # 6. Location & Geography (2-4 tags)
    loc_lower = (location or "").lower()
    add_tag("India")
    add_tag("India Tech Industry")
    if "bangalore" in loc_lower or "bengaluru" in loc_lower:
        add_tag("Bengaluru")
        add_tag("Bangalore Tech Hub")
        add_tag("Karnataka")
    elif "gurgaon" in loc_lower or "gurugram" in loc_lower or "delhi" in loc_lower or "noida" in loc_lower:
        add_tag("Gurugram")
        add_tag("Delhi NCR")
    elif "pune" in loc_lower:
        add_tag("Pune")
        add_tag("Maharashtra")
    elif "mumbai" in loc_lower:
        add_tag("Mumbai")
        add_tag("Maharashtra")
    elif "hyderabad" in loc_lower:
        add_tag("Hyderabad")
        add_tag("Telangana")
    elif "chennai" in loc_lower:
        add_tag("Chennai")
        add_tag("Tamil Nadu")

    # 7. Employment Type (2 tags)
    emp_lower = f"{employment_type} {title}".lower()
    if "intern" in emp_lower:
        add_tag("Paid Internship")
        add_tag("Internship Role")
    elif "contract" in emp_lower:
        add_tag("Contract Position")
        add_tag("Contract Opportunity")
    else:
        add_tag("Full Time")
        add_tag("Permanent Role")

    # 8. Company Tag (1-2 tags)
    if company and company.lower() not in ("direct", "ats"):
        add_tag(f"{company} Careers")
        add_tag(company)

    # Fallback padding if less than 25
    if len(tags) < 25:
        fallbacks = ["Tech Careers", "Software Industry", "Professional Growth", "Engineering Excellence", "Agile Workflow", "Continuous Learning", "Team Collaboration"]
        for fb in fallbacks:
            add_tag(fb)
            if len(tags) >= 25:
                break

    # Cap at 32 tags
    return tags[:32]

def extract_tags(title: str, dept: str = "", raw_text: str = "") -> List[str]:
    """Generates 25-35 rich, genuine tags for the role."""
    return generate_job_tags(title=title, dept=dept, raw_text=raw_text)


def normalize_employment_type(emp_str: str, title: str) -> str:
    s = f"{emp_str} {title}".lower()
    if "intern" in s or "trainee" in s:
        return "Internship"
    if "contract" in s or "temp" in s:
        return "Contract"
    if "freelance" in s:
        return "Freelance"
    if "part" in s and "time" in s:
        return "Part time"
    return "Full time"

def normalize_workplace(loc_str: str, workplace_str: str = "", is_remote: bool = False) -> str:
    s = f"{loc_str} {workplace_str}".lower()
    if is_remote or "remote" in s or "work from home" in s or "wfh" in s:
        return "Remote"
    if "hybrid" in s or "flexible" in s:
        return "Hybrid"
    return "In office"

def normalize_experience_level(title: str, exp_str: str = "") -> str:
    s = f"{title} {exp_str}".lower()
    if "director" in s or "vp" in s or "vice president" in s:
        return "Director"
    if "executive" in s or "cxo" in s or "head of" in s or "chief" in s:
        return "Executive"
    if "manager" in s or "lead" in s or "principal" in s:
        return "Manager"
    if "senior" in s or "sr." in s or "sr " in s or "staff" in s or "iii" in s or "iv" in s:
        return "Senior"
    return "Entry level"


class ATSEndpoint:
    def __init__(self, company_name: str, ats_platform: str, endpoint_url: str):
        self.company_name = company_name.strip()
        self.ats_platform = ats_platform.strip().capitalize()
        self.endpoint_url = endpoint_url.strip()

    def __repr__(self):
        return f"<ATSEndpoint {self.company_name} ({self.ats_platform}): {self.endpoint_url}>"


class ATSService:
    def __init__(self):
        self.config = get_config()
        self.endpoints: List[ATSEndpoint] = []
        self.verified_bamboohr_urls: set = set()
        self._load_endpoints_from_excel()

    def _load_endpoints_from_excel(self):
        excel_path = self.config.excel_path
        seen = set()

        # Load verified India-hiring BambooHR endpoints if available
        bamboo_json_path = excel_path.parent / "bamboohr_verified.json"
        if not bamboo_json_path.exists():
            bamboo_json_path = Path(__file__).resolve().parent.parent / "resources" / "bamboohr_verified.json"
        if bamboo_json_path.exists():
            try:
                with open(bamboo_json_path, "r") as f:
                    b_list = json.load(f)
                    for item in b_list:
                        u_clean = item["url"].split("?")[0].lower()
                        self.verified_bamboohr_urls.add(u_clean)
                        k = (item["company"].lower(), u_clean)
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(item["company"], "BambooHR", item["url"]))
                logger.info(f"Loaded {len(self.verified_bamboohr_urls)} verified India-hiring BambooHR endpoints.")
            except Exception as e:
                logger.warning(f"Error loading verified BambooHR list: {e}")

        if excel_path.exists():
            try:
                wb = openpyxl.load_workbook(str(excel_path), read_only=True, data_only=True)
                sheet_name = self.config.resources.get("master_sheet", "Master ATS Directory (1000+)")
                if sheet_name not in wb.sheetnames:
                    sheet_name = wb.sheetnames[0]
                ws = wb[sheet_name]

                # Header is typically row index 3 (4th row)
                header_idx = self.config.resources.get("header_row_index", 3)

                row_idx = 0
                for row in ws.iter_rows(values_only=True):
                    row_idx += 1
                    if row_idx <= header_idx + 1:
                        continue
                    if not row or not any(row):
                        continue

                    # Robust dynamic URL & platform extraction across all row formats in job_urls.xlsx
                    http_col = None
                    for idx, cell in enumerate(row):
                        if cell and str(cell).strip().startswith(('http://', 'https://')):
                            http_col = idx
                            break

                    if http_col is not None:
                        ep_url = str(row[http_col]).strip()
                        plat = ""
                        c_name = ""

                        # Search preceding columns for recognized ATS platform keywords
                        for idx in range(http_col):
                            val = str(row[idx] or '').strip()
                            if val.lower() in ("ashby", "greenhouse", "lever", "bamboohr", "smartrecruiters", "oracle", "workday", "recruitee", "breezy", "workable", "rippling"):
                                plat = val
                                # Company name is the nearest preceding non-numeric column
                                for c_idx in range(idx - 1, -1, -1):
                                    c_val = str(row[c_idx] or '').strip()
                                    if c_val and not c_val.isdigit():
                                        c_name = c_val
                                        break
                                break

                        if not plat:
                            if http_col >= 2:
                                plat = str(row[http_col - 1] or 'Direct').strip()
                                c_name = str(row[http_col - 2] or '').strip()
                            elif http_col >= 1:
                                plat = "Direct"
                                c_name = str(row[0] or '').strip()

                        if c_name and ep_url and ep_url.startswith("http"):
                            k = (c_name.lower(), ep_url.split("?")[0].lower())
                            if k not in seen:
                                seen.add(k)
                                self.endpoints.append(ATSEndpoint(c_name, plat, ep_url))

                logger.info(f"Loaded {len(self.endpoints)} ATS endpoints from Excel directory.")
            except Exception as e:
                logger.error(f"Error loading Excel file via openpyxl read_only stream: {e}", exc_info=True)
        else:
            logger.warning(f"Excel file not found at: {excel_path}")

        # Curated top-tier and modern ATS endpoints (Rippling, Workable, Recruitee, Breezy HR, SmartRecruiters)
        curated = [
            # High-yield SmartRecruiters tech endpoints (India & Global Remote)
            ("PhonePe", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/PhonePeLimited/postings?limit=100"),
            ("Swiggy", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/swiggy/postings?limit=100"),
            ("Freshworks", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/freshworks/postings?limit=100"),
            ("Mindtickle", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/mindtickle/postings?limit=100"),
            ("Netskope", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/netskope/postings?limit=100"),
            ("HackerRank", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/hackerrank/postings?limit=100"),
            ("Innovaccer", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/innovaccer/postings?limit=100"),
            ("BrowserStack", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/browserstack/postings?limit=100"),
            ("Visa", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/visa/postings?limit=100"),
            ("Bosch", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/bosch/postings?limit=100"),
            ("Publicis Sapient", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/publicissapient/postings?limit=100"),
            ("EPAM Systems", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/epam/postings?limit=100"),
            ("Ubisoft", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/ubisoft/postings?limit=100"),
            ("Eurofins", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/Eurofins/postings?limit=100"),
            ("H&M Group", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/HMGroup/postings?limit=100"),
            ("SGS", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/SGS/postings?limit=100"),
            ("Avery Dennison", "SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/averydennison/postings?limit=100"),
            # Rippling ATS public JSON endpoints (India & Global Tech)
            ("Rippling", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/rippling/jobs"),
            ("Heads Up Technologies", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/heads-up-technologies/jobs"),
            ("Cerby", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/cerby/jobs"),
            ("Quotapath", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/quotapath/jobs"),
            ("Framework", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/framework/jobs"),
            ("Dockwa", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/dockwa/jobs"),
            ("Inn-Flow", "Rippling", "https://api.rippling.com/platform/api/ats/v1/board/inn-flow/jobs"),
            # Top Workable public JSON endpoints (India & Global Remote)
            ("Apna", "Workable", "https://apply.workable.com/api/v1/widget/accounts/apna"),
            ("Mercari India", "Workable", "https://apply.workable.com/api/v1/widget/accounts/mercari-india"),
            ("Volga Partners", "Workable", "https://apply.workable.com/api/v1/widget/accounts/volga-partners"),
            ("Erbity", "Workable", "https://apply.workable.com/api/v1/widget/accounts/erbity"),
            ("CXG", "Workable", "https://apply.workable.com/api/v1/widget/accounts/cxg"),
            ("QuantumLoopAI", "Workable", "https://apply.workable.com/api/v1/widget/accounts/quantumloopai"),
            # Recruitee public JSON endpoints
            ("Bunq", "Recruitee", "https://bunq.recruitee.com/api/offers"),
            ("Transifex", "Recruitee", "https://transifex.recruitee.com/api/offers"),
            ("Tactile Games", "Recruitee", "https://tactilegames.recruitee.com/api/offers"),
            ("Framer", "Recruitee", "https://framer.recruitee.com/api/offers"),
            ("Uscreen", "Recruitee", "https://uscreen.recruitee.com/api/offers"),
            ("Sendcloud", "Recruitee", "https://sendcloud.recruitee.com/api/offers"),
            ("Hotjar", "Recruitee", "https://hotjar.recruitee.com/api/offers"),
            # Breezy HR public JSON endpoints
            ("Buffer", "Breezy HR", "https://buffer.breezy.hr/json"),
            ("Doist", "Breezy HR", "https://doist.breezy.hr/json"),
            ("Toggl", "Breezy HR", "https://toggl.breezy.hr/json"),
            ("Scopely", "Breezy HR", "https://scopely.breezy.hr/json"),
            # Top Greenhouse Tech Endpoints
            ("Stripe", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true"),
            ("Figma", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/figma/jobs?content=true"),
            ("Coinbase", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/coinbase/jobs?content=true"),
            ("Cloudflare", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/cloudflare/jobs?content=true"),
            ("Reddit", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/reddit/jobs?content=true"),
            ("Groww", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/groww/jobs?content=true"),
            ("Razorpay", "Greenhouse", "https://boards-api.greenhouse.io/v1/boards/razorpaysoftwareprivatelimited/jobs?content=true"),
            # Top Lever Tech Endpoints
            ("Spotify", "Lever", "https://api.lever.co/v0/postings/spotify?mode=json"),
            ("Cred", "Lever", "https://api.lever.co/v0/postings/cred?mode=json"),
            ("Palantir", "Lever", "https://api.lever.co/v0/postings/palantir?mode=json"),
            # Top Ashby Tech Endpoints
            ("Linear", "Ashby", "https://api.ashbyhq.com/posting-api/job-board/linear"),
            ("Ramp", "Ashby", "https://api.ashbyhq.com/posting-api/job-board/ramp"),
            ("Notion", "Ashby", "https://api.ashbyhq.com/posting-api/job-board/notion")
        ]
        for c_name, plat, ep_url in curated:
            k = (c_name.lower(), ep_url.split("?")[0].lower())
            if k not in seen:
                seen.add(k)
                self.endpoints.append(ATSEndpoint(c_name, plat, ep_url))

        # Load directories from resources/
        resources_dir = excel_path.parent if excel_path.parent.exists() else (Path(__file__).resolve().parent.parent.parent / "resources")
        if not resources_dir.exists():
            resources_dir = Path(__file__).resolve().parent.parent / "resources"

        # 1. SmartRecruiters
        sr_file = resources_dir / "smartrecruiters_companies.json"
        if sr_file.exists():
            try:
                with open(sr_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug, "SmartRecruiters", u))
            except Exception as e:
                logger.warning(f"Error loading smartrecruiters_companies.json: {e}")

        # 2. Greenhouse
        gh_file = resources_dir / "greenhouse_companies.json"
        if gh_file.exists():
            try:
                with open(gh_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Greenhouse", u))
            except Exception as e:
                logger.warning(f"Error loading greenhouse_companies.json: {e}")

        # 3. Ashby
        ashby_file = resources_dir / "ashby_companies.json"
        if ashby_file.exists():
            try:
                with open(ashby_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Ashby", u))
            except Exception as e:
                logger.warning(f"Error loading ashby_companies.json: {e}")

        # 4. Lever
        lever_file = resources_dir / "lever_companies.json"
        if lever_file.exists():
            try:
                with open(lever_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Lever", u))
            except Exception as e:
                logger.warning(f"Error loading lever_companies.json: {e}")

        # 5. Pinpoint
        pp_file = resources_dir / "pinpoint_companies.json"
        if pp_file.exists():
            try:
                with open(pp_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://{slug}.pinpointhq.com/postings.json"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Pinpoint", u))
            except Exception as e:
                logger.warning(f"Error loading pinpoint_companies.json: {e}")

        # 6. Comeet
        cm_file = resources_dir / "comeet_companies.json"
        if cm_file.exists():
            try:
                with open(cm_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://www.comeet.co/careers-api/2.0/company/{slug}/positions"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Comeet", u))
            except Exception as e:
                logger.warning(f"Error loading comeet_companies.json: {e}")

        # 7. Jobvite
        jv_file = resources_dir / "jobvite_companies.json"
        if jv_file.exists():
            try:
                with open(jv_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://jobs.jobvite.com/{slug}/search?format=json"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Jobvite", u))
            except Exception as e:
                logger.warning(f"Error loading jobvite_companies.json: {e}")

        # 8. Workday
        wd_file = resources_dir / "workday_companies.json"
        if wd_file.exists():
            try:
                with open(wd_file, "r") as f:
                    for line in json.load(f):
                        parts = line.split("|")
                        if len(parts) >= 3:
                            tenant, host_prefix, site_name = parts[0], parts[1], parts[2]
                            u = f"https://{tenant}.{host_prefix}.myworkdayjobs.com/wday/cxs/{tenant}/{site_name}/jobs"
                            k = (tenant.lower(), u.lower())
                            if k not in seen:
                                seen.add(k)
                                self.endpoints.append(ATSEndpoint(tenant.title(), "Workday", u))
            except Exception as e:
                logger.warning(f"Error loading workday_companies.json: {e}")

        # 9. Workable
        wb_file = resources_dir / "workable_companies.json"
        if wb_file.exists():
            try:
                with open(wb_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Workable", u))
            except Exception as e:
                logger.warning(f"Error loading workable_companies.json: {e}")

        # 10. Rippling
        rip_file = resources_dir / "rippling_companies.json"
        if rip_file.exists():
            try:
                with open(rip_file, "r") as f:
                    for slug in json.load(f):
                        u = f"https://api.rippling.com/platform/api/ats/v1/board/{slug}/jobs"
                        k = (slug.lower(), u.lower())
                        if k not in seen:
                            seen.add(k)
                            self.endpoints.append(ATSEndpoint(slug.title(), "Rippling", u))
            except Exception as e:
                logger.warning(f"Error loading rippling_companies.json: {e}")

        logger.info(f"Total unified ATS endpoints active: {len(self.endpoints)}")

    def get_all_companies(self) -> List[str]:
        companies = sorted(list({ep.company_name for ep in self.endpoints if ep.company_name}))
        return companies

    async def fetch_single_endpoint(self, client: httpx.AsyncClient, ep: ATSEndpoint) -> List[Dict[str, Any]]:
        """
        Fetches an ATS JSON endpoint with retries, timeouts, and rate limits.
        Parses and returns valid India-specific job dictionaries.
        """
        headers = {
            "User-Agent": "CorporateGuildJobSearch/1.0 (+https://corporateguild.com)",
            "Accept": "application/json"
        }
        retries = self.config.scheduler.get("max_retries", 3)
        backoff = self.config.scheduler.get("backoff_factor", 1.5)

        # SmartRecruiters query enhancement: auto-append limit=100
        req_url = ep.endpoint_url
        if "api.smartrecruiters.com" in req_url and "limit=" not in req_url:
            req_url += ("&limit=100" if "?" in req_url else "?limit=100")

        for attempt in range(retries):
            try:
                if "myworkdayjobs.com/wday/cxs" in req_url:
                    payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "India"}
                    resp = await client.post(req_url, headers=headers, json=payload, timeout=self.config.scheduler.get("request_timeout_seconds", 10))
                else:
                    resp = await client.get(req_url, headers=headers, timeout=self.config.scheduler.get("request_timeout_seconds", 10))
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_ats_data(ep, data)
                elif resp.status_code == 429:
                    await asyncio.sleep(backoff * (attempt + 1) + random.uniform(0.1, 0.5))
                else:
                    break
            except Exception as e:
                if attempt == retries - 1:
                    logger.debug(f"Failed fetching {ep.company_name} ({req_url}): {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
        return []

    def _parse_ats_data(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        platform = ep.ats_platform.lower()
        if "greenhouse" in platform:
            return self._parse_greenhouse(ep, data)
        elif "ashby" in platform:
            return self._parse_ashby(ep, data)
        elif "smartrecruiters" in platform:
            return self._parse_smartrecruiters(ep, data)
        elif "lever" in platform:
            return self._parse_lever(ep, data)
        elif "bamboohr" in platform:
            return self._parse_bamboohr(ep, data)
        elif "recruitee" in platform:
            return self._parse_recruitee(ep, data)
        elif "breezy" in platform:
            return self._parse_breezy(ep, data)
        elif "workable" in platform:
            return self._parse_workable(ep, data)
        elif "rippling" in platform:
            return self._parse_rippling(ep, data)
        elif "oracle" in platform:
            return self._parse_oracle(ep, data)
        elif "workday" in platform:
            return self._parse_workday(ep, data)
        elif "pinpoint" in platform:
            return self._parse_pinpoint(ep, data)
        elif "comeet" in platform:
            return self._parse_comeet(ep, data)
        elif "jobvite" in platform:
            return self._parse_jobvite(ep, data)
        else:
            # Try generic detection
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    if "workLocation" in data[0] or "uuid" in data[0]:
                        return self._parse_rippling(ep, data)
                    elif "url_active_page" in data[0] or "url_apply_page" in data[0]:
                        return self._parse_comeet(ep, data)
                    elif "application_form_url" in data[0] or "key_responsibilities" in data[0]:
                        return self._parse_pinpoint(ep, data)
                    elif "detailUrl" in data[0] or "jobId" in data[0]:
                        return self._parse_jobvite(ep, data)
                return self._parse_lever(ep, data)
            elif isinstance(data, dict):
                if "jobs" in data and isinstance(data["jobs"], list):
                    if data.get("name") and any("shortcode" in x or "telecommuting" in x for x in data["jobs"] if isinstance(x, dict)):
                        return self._parse_workable(ep, data)
                    return self._parse_greenhouse(ep, data)
                elif "content" in data and isinstance(data["content"], list):
                    return self._parse_smartrecruiters(ep, data)
                elif "result" in data and isinstance(data["result"], list):
                    return self._parse_bamboohr(ep, data)
                elif "offers" in data and isinstance(data["offers"], list):
                    return self._parse_recruitee(ep, data)
                elif "items" in data and data["items"] and isinstance(data["items"], list) and "requisitionList" in data["items"][0]:
                    return self._parse_oracle(ep, data)
                elif "positions" in data and isinstance(data["positions"], list):
                    return self._parse_comeet(ep, data)
                elif "requisitions" in data and isinstance(data["requisitions"], list):
                    return self._parse_jobvite(ep, data)
                elif "data" in data and isinstance(data["data"], list):
                    return self._parse_pinpoint(ep, data)
        return []

    def _parse_greenhouse(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobs", [])
        for j in jobs:
            loc_obj = j.get("location") or {}
            loc_name = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
            title = j.get("title", "").strip()
            
            # India location verification
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)

            apply_link = j.get("absolute_url", "")
            # Ensure it's a web URL, not an API JSON endpoint
            if not apply_link or "api.greenhouse" in apply_link or "boards-api" in apply_link:
                board_match = re.search(r'boards/([^/]+)/jobs', ep.endpoint_url)
                board_token = board_match.group(1) if board_match else ep.company_name.lower()
                apply_link = f"https://boards.greenhouse.io/{board_token}/jobs/{j.get('id')}"
            elif "api." in apply_link:
                apply_link = apply_link.replace("api.", "boards.")
            updated_at = j.get("updated_at") or j.get("first_published")
            ist_str, raw_iso, rel_time = parse_date_to_ist(updated_at)
            
            dept_names = [d.get("name", "") for d in j.get("departments", []) if isinstance(d, dict)]
            dept_str = " ".join(dept_names)
            emp_type = normalize_employment_type(j.get("employment_type", ""), title)
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower()))
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept_str)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Greenhouse",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    def _parse_ashby(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobs", [])
        for j in jobs:
            title = j.get("title", "").strip()
            loc_name = j.get("location", "")
            is_remote = bool(j.get("isRemote", False))
            workplace_type_raw = j.get("workplaceType", "")
            
            # Check secondary locations for India
            sec_locs = [str(sl.get("location", "")) for sl in j.get("secondaryLocations", []) if isinstance(sl, dict)]
            combined_loc = f"{loc_name}; {'; '.join(sec_locs)}".strip("; ")
            if not is_india_location(combined_loc, workplace_type=workplace_type_raw):
                if not combined_loc.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(combined_loc)

            apply_link = j.get("applyUrl") or j.get("jobUrl") or f"https://jobs.ashbyhq.com/{ep.company_name.lower()}/{j.get('id')}"
            published_at = j.get("publishedAt")
            ist_str, raw_iso, rel_time = parse_date_to_ist(published_at)

            dept = j.get("department", "")
            emp_type = normalize_employment_type(j.get("employmentType", ""), title)
            workplace = normalize_workplace(loc_name, workplace_type_raw, is_remote)
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Ashby",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    def _parse_smartrecruiters(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        items = data.get("content", [])
        for j in items:
            title = j.get("name", "").strip()
            loc_obj = j.get("location") or {}
            city = loc_obj.get("city", "")
            region = loc_obj.get("region", "")
            country = loc_obj.get("country", "")
            full_loc = loc_obj.get("fullLocation", "")
            is_rem = bool(loc_obj.get("remote", False))
            is_hyb = bool(loc_obj.get("hybrid", False))

            loc_str = full_loc or f"{city}, {region}, {country}".strip(", ")
            wp_hint = "Remote" if is_rem else ("Hybrid" if is_hyb else "")

            if not is_india_location(loc_str, country_code=country, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            comp_name = j.get("company", {}).get("name") or ep.company_name
            comp_identifier = j.get("company", {}).get("identifier") or ep.company_name
            job_id = j.get("id")
            
            # Construct direct public job application URL (never use j.get('ref') which is an internal API endpoint returning raw JSON)
            posting_url = j.get("postingUrl")
            if posting_url and "jobs.smartrecruiters.com" in str(posting_url):
                apply_link = posting_url
            elif job_id:
                apply_link = f"https://jobs.smartrecruiters.com/{comp_identifier}/{job_id}"
            else:
                apply_link = f"https://jobs.smartrecruiters.com/{comp_identifier}"
            released_at = j.get("releasedDate")
            ist_str, raw_iso, rel_time = parse_date_to_ist(released_at)

            type_obj = j.get("typeOfEmployment") or {}
            type_label = type_obj.get("label", "") if isinstance(type_obj, dict) else str(type_obj)
            exp_obj = j.get("experienceLevel") or {}
            exp_label = exp_obj.get("label", "") if isinstance(exp_obj, dict) else str(exp_obj)

            emp_type = normalize_employment_type(type_label, title)
            workplace = "Remote" if is_rem else ("Hybrid" if is_hyb else normalize_workplace(loc_str))
            exp_level = normalize_experience_level(title, exp_label)
            dept_label = j.get("function", {}).get("label", "") if isinstance(j.get("function"), dict) else str(j.get("function") or "")
            tags = generate_job_tags(title=title, company=comp_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept_label)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": comp_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "SmartRecruiters",
                "ingested_at": now_str
            })
        return results

    def _parse_lever(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        jobs = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
        if not isinstance(jobs, list):
            return []

        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = j.get("text", "").strip()
            cats = j.get("categories") or {}
            loc_str = cats.get("location", "")
            workplace_type_raw = cats.get("workplaceType", "")
            
            # India location verification
            if not is_india_location(loc_str, workplace_type=workplace_type_raw):
                if not loc_str.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = j.get("hostedUrl") or j.get("applyUrl") or f"https://jobs.lever.co/{ep.company_name.lower()}/{j.get('id')}"
            created_at = j.get("createdAt")
            ist_str, raw_iso, rel_time = parse_date_to_ist(created_at)

            dept = cats.get("department", "") or cats.get("team", "")
            emp_type = normalize_employment_type(cats.get("commitment", ""), title)
            workplace = normalize_workplace(loc_str, workplace_type_raw, is_remote=("remote" in loc_str.lower()))
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Lever",
                "ingested_at": datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            })
        return results

    def _parse_bamboohr(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if not isinstance(data, dict):
            return []
        items = data.get("result", [])
        if not isinstance(items, list):
            return []

        for j in items:
            if not isinstance(j, dict):
                continue
            title = j.get("jobOpeningName", "").strip()
            
            # Check both location and atsLocation objects
            loc_obj = j.get("location") or {}
            ats_loc = j.get("atsLocation") or {}

            city = (ats_loc.get("city") or loc_obj.get("city") or "").strip()
            state = (ats_loc.get("state") or ats_loc.get("province") or loc_obj.get("state") or "").strip()
            country = (ats_loc.get("country") or "").strip()
            
            loc_parts = [p for p in [city, state, country] if p]
            loc_str = ", ".join(loc_parts)

            is_rem = bool(j.get("isRemote")) or str(j.get("locationType", "")).strip() == "1"
            wp_hint = "Remote" if is_rem else ""

            # India location verification
            if not is_india_location(loc_str, country_code=country, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            job_id = str(j.get("id", "")).strip()
            base_careers = ep.endpoint_url.split("/careers/list")[0]
            apply_link = f"{base_careers}/careers/{job_id}" if job_id else ep.endpoint_url
            
            now_ist = datetime.datetime.now(IST_TZ)
            ist_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            raw_iso = now_ist.isoformat()
            rel_time = "Recently"

            dept = j.get("departmentLabel", "") or ""
            emp_type = normalize_employment_type(j.get("employmentStatusLabel", ""), title)
            workplace = "Remote" if is_rem else normalize_workplace(loc_str)
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "BambooHR",
                "ingested_at": ist_str
            })
        return results

    def _parse_recruitee(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        offers = data.get("offers", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for j in offers:
            if not isinstance(j, dict):
                continue
            title = j.get("title", "").strip()
            city = j.get("city", "") or ""
            state = j.get("state_name", "") or j.get("state_code", "") or ""
            country = j.get("country", "") or ""
            country_code = j.get("country_code", "") or ""
            is_rem = bool(j.get("remote", False))
            is_hyb = bool(j.get("hybrid", False))

            loc_parts = [p for p in [city, state, country] if p]
            loc_str = ", ".join(loc_parts)
            wp_hint = "Remote" if is_rem else ("Hybrid" if is_hyb else "")

            if not is_india_location(loc_str, country_code=country_code, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = j.get("careers_apply_url") or j.get("careers_url") or ep.endpoint_url
            created_at = j.get("published_at") or j.get("created_at")
            ist_str, raw_iso, rel_time = parse_date_to_ist(created_at)

            dept = j.get("department", "") or ""
            emp_type = normalize_employment_type(j.get("employment_type_code", "") or "", title)
            workplace = "Remote" if is_rem else ("Hybrid" if is_hyb else normalize_workplace(loc_str))
            exp_level = normalize_experience_level(title, j.get("experience_code", "") or "")
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Recruitee",
                "ingested_at": now_str
            })
        return results

    def _parse_breezy(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        jobs = data if isinstance(data, list) else (data.get("positions", []) if isinstance(data, dict) else [])
        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = j.get("name", "").strip()
            loc_obj = j.get("location") or {}
            city = loc_obj.get("city", "") if isinstance(loc_obj, dict) else str(loc_obj)
            country_obj = loc_obj.get("country", {}) if isinstance(loc_obj, dict) else {}
            country_name = country_obj.get("name", "") if isinstance(country_obj, dict) else str(country_obj)
            is_rem = bool(loc_obj.get("is_remote", False)) if isinstance(loc_obj, dict) else False

            loc_parts = [p for p in [city, country_name] if p]
            loc_str = ", ".join(loc_parts)
            wp_hint = "Remote" if is_rem else ""

            if not is_india_location(loc_str, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = j.get("url") or ep.endpoint_url
            published_at = j.get("published_date") or j.get("created_at")
            ist_str, raw_iso, rel_time = parse_date_to_ist(published_at)

            dept = j.get("department", "") or ""
            type_obj = j.get("type", {})
            type_name = type_obj.get("name", "") if isinstance(type_obj, dict) else str(type_obj)
            emp_type = normalize_employment_type(type_name, title)
            workplace = "Remote" if is_rem else normalize_workplace(loc_str)
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "ats_platform": "Breezy HR",
                "ingested_at": now_str
            })
        return results

    def _parse_workable(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if not isinstance(data, dict):
            return []
        jobs = data.get("jobs", [])
        if not isinstance(jobs, list):
            return []

        company_display = data.get("name") or ep.company_name

        for j in jobs:
            if not isinstance(j, dict):
                continue
            title = (j.get("title") or "").strip()
            if not title:
                continue

            city = (j.get("city") or "").strip()
            state = (j.get("state") or "").strip()
            country = (j.get("country") or "").strip()
            loc_parts = [p for p in [city, state, country] if p]
            loc_str = ", ".join(loc_parts)

            is_rem = bool(j.get("telecommuting"))
            wp_hint = "Remote" if is_rem else ""

            country_code = ""
            locations_list = j.get("locations") or []
            if isinstance(locations_list, list) and locations_list:
                for subloc in locations_list:
                    if isinstance(subloc, dict):
                        cc = subloc.get("countryCode") or ""
                        if cc:
                            country_code = cc
                            break

            # India location verification
            if not is_india_location(loc_str, country_code=country_code or country, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, country_code=country_code or country, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = (j.get("application_url") or j.get("url") or j.get("shortlink") or "").strip()
            if not apply_link:
                shortcode = j.get("shortcode")
                apply_link = f"https://apply.workable.com/j/{shortcode}" if shortcode else ep.endpoint_url

            pub_date = j.get("published_on") or j.get("created_at") or ""
            ist_str, raw_iso, rel_time = parse_date_to_ist(pub_date)

            emp_type = normalize_employment_type(j.get("employment_type", ""), title)
            workplace = "Remote" if is_rem else normalize_workplace(loc_str)
            exp_level = normalize_experience_level(f"{title} {j.get('experience', '')}")
            dept = j.get("department") or j.get("function") or ""
            tags = generate_job_tags(title=title, company=company_display, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")

            results.append({
                "company_name": company_display,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "salary_range": "Competitive Market CTC",
                "role_category": title,
                "skills": tags[:5],
                "description": f"Verified open position at {company_display} for {title}.",
                "ats_platform": "Workable",
                "ingested_at": now_str
            })

        return results

    def _parse_rippling(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if not isinstance(data, list):
            return results

        company_display = ep.company_name.strip()
        now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")

        for j in data:
            if not isinstance(j, dict):
                continue
            title = j.get("name", "").strip()
            if not title:
                continue

            work_loc = j.get("workLocation") or {}
            loc_name = work_loc.get("label", "") if isinstance(work_loc, dict) else str(work_loc)

            # Strict India filtering & validation
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)

            job_uuid = j.get("uuid") or ""
            apply_link = j.get("url")
            if not apply_link or "api.rippling" in apply_link:
                slug = ep.endpoint_url.split("/board/")[1].split("/")[0] if "/board/" in ep.endpoint_url else company_display.lower()
                apply_link = f"https://ats.rippling.com/{slug}/jobs/{job_uuid}"

            ist_str, raw_iso, rel_time = parse_date_to_ist(None)

            dept_obj = j.get("department") or {}
            dept_name = dept_obj.get("label", "") if isinstance(dept_obj, dict) else ""
            emp_type = normalize_employment_type("", title)
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower() or "remote" in title.lower()))
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=company_display, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept_name)

            results.append({
                "company_name": company_display,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "salary_range": "Competitive Market CTC",
                "role_category": title,
                "skills": tags[:5],
                "description": f"Verified open position at {company_display} for {title}.",
                "ats_platform": "Rippling",
                "ingested_at": now_str,
                "source_url": ep.endpoint_url
            })

        return results

    def _parse_oracle(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        items = data.get("items", [])
        if not items:
            return results
        
        req_list = items[0].get("requisitionList", [])
        
        site_number = "CX_1"
        m = re.search(r'siteNumber=([A-Za-z0-9_]+)', ep.endpoint_url)
        if m:
            site_number = m.group(1)
            
        base_url = ep.endpoint_url.split('/hcmRestApi')[0]
        
        for j in req_list:
            title = j.get("Title", "").strip()
            loc_name = j.get("PrimaryLocation", "")
            
            # India location verification
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)
                
            job_id = j.get("Id", "")
            if not job_id:
                continue
                
            apply_link = f"{base_url}/hcmUI/CandidateExperience/en/sites/{site_number}/job/{job_id}"
            
            posted_date = j.get("PostedDate")
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)
            
            dept_str = j.get("JobFunction", "") or j.get("JobFamily", "") or ""
            worker_type = j.get("WorkerType", "") or j.get("JobType", "") or ""
            emp_type = normalize_employment_type(worker_type, title)
            wp_code = j.get("WorkplaceType", "") or j.get("WorkplaceTypeCode", "") or ""
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower() or "remote" in wp_code.lower()))
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept_str)
            
            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time,
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Oracle",
                "ingested_at": now_str
            })
            
        return results

    def _parse_workday(self, ep: ATSEndpoint, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        jobs = data.get("jobPostings", [])
        if not jobs:
            return results
            
        m = re.search(r'https://([^.]+)\.([^.]+)\.myworkdayjobs\.com/wday/cxs/([^/]+)/([^/]+)/jobs', ep.endpoint_url)
        if not m:
            return results
            
        company, wd_domain, tenant, path = m.groups()
        base_url = f"https://{company}.{wd_domain}.myworkdayjobs.com/en-US/{path}"

        for j in jobs:
            title = j.get("title", "").strip()
            loc_name = j.get("locationsText", "")
            
            # India location verification
            if not is_india_location(loc_name):
                if not loc_name.strip() and is_india_location(title):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_name)
                
            external_path = j.get("externalPath", "")
            if not external_path:
                continue
                
            apply_link = f"{base_url}{external_path}"
            posted_date = j.get("postedOn", "")
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)
            
            bullets = " ".join(j.get("bulletFields", []))
            emp_type = normalize_employment_type(bullets, title)
            workplace = normalize_workplace(loc_name, is_remote=("remote" in loc_name.lower() or "remote" in bullets.lower()))
            exp_level = normalize_experience_level(title)
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=bullets)
            
            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time or posted_date,
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Workday",
                "ingested_at": now_str
            })
            
        return results

    def _parse_pinpoint(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if isinstance(data, dict):
            postings = data.get("data") or data.get("postings") or data.get("jobs") or []
        elif isinstance(data, list):
            postings = data
        else:
            return []

        for p in postings:
            if not isinstance(p, dict):
                continue
            item = p.get("attributes", p) if isinstance(p.get("attributes"), dict) else p
            title = str(item.get("title") or item.get("name") or "").strip()
            if not title:
                continue

            loc_obj = item.get("location") or item.get("location_name") or {}
            if isinstance(loc_obj, dict):
                city = loc_obj.get("city") or loc_obj.get("name") or ""
                region = loc_obj.get("region") or loc_obj.get("subdivision") or ""
                country = loc_obj.get("country") or ""
                loc_str = f"{city}, {region}, {country}".strip(", ")
            else:
                loc_str = str(loc_obj or "")

            wp_raw = str(item.get("workplace_type") or item.get("workplace_type_text") or "")
            is_rem = "remote" in wp_raw.lower() or bool(item.get("remote", False)) or "remote" in loc_str.lower()
            is_hyb = "hybrid" in wp_raw.lower() or "hybrid" in loc_str.lower()
            wp_hint = "Remote" if is_rem else ("Hybrid" if is_hyb else "")

            if not is_india_location(loc_str, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = item.get("application_form_url") or item.get("url") or item.get("path") or ep.endpoint_url
            if apply_link and not str(apply_link).startswith("http"):
                apply_link = urljoin(ep.endpoint_url, str(apply_link))

            posted_date = item.get("created_at") or item.get("updated_at")
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)

            emp_type_raw = str(item.get("employment_type_text") or item.get("employment_type") or "")
            emp_type = normalize_employment_type(emp_type_raw, title)
            workplace = "Remote" if is_rem else ("Hybrid" if is_hyb else normalize_workplace(loc_str))
            exp_level = normalize_experience_level(title, str(item.get("experience_level") or ""))
            dept = str(item.get("department") or item.get("department_name") or "")
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time or "",
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Pinpoint",
                "ingested_at": now_str
            })
        return results

    def _parse_comeet(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if isinstance(data, list):
            positions = data
        elif isinstance(data, dict):
            positions = data.get("positions") or data.get("jobs") or []
        else:
            return []

        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = str(pos.get("name") or pos.get("title") or "").strip()
            if not title:
                continue

            loc_obj = pos.get("location") or {}
            if isinstance(loc_obj, dict):
                city = loc_obj.get("city", "")
                country = loc_obj.get("country", "")
                state = loc_obj.get("state", "")
                loc_str = f"{city}, {state}, {country}".strip(", ")
                is_rem = bool(loc_obj.get("is_remote", False))
            else:
                loc_str = str(loc_obj or "")
                is_rem = "remote" in loc_str.lower()

            wp_hint = "Remote" if is_rem or "remote" in loc_str.lower() else ""

            if not is_india_location(loc_str, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = pos.get("url_active_page") or pos.get("url_apply_page") or ep.endpoint_url
            posted_date = pos.get("time_updated") or pos.get("time_created")
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)

            emp_type = normalize_employment_type(str(pos.get("employment_type") or ""), title)
            workplace = "Remote" if is_rem else normalize_workplace(loc_str)
            exp_level = normalize_experience_level(title, str(pos.get("experience_level") or ""))
            dept = str(pos.get("department") or "")
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time or "",
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Comeet",
                "ingested_at": now_str
            })
        return results

    def _parse_jobvite(self, ep: ATSEndpoint, data: Any) -> List[Dict[str, Any]]:
        results = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("requisitions") or data.get("jobs") or data.get("job") or []
        else:
            return []

        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("name") or "").strip()
            if not title:
                continue

            loc_str = str(item.get("location") or item.get("city") or "")
            job_type = str(item.get("jobType") or item.get("type") or "")
            is_rem = "remote" in job_type.lower() or "remote" in loc_str.lower()
            wp_hint = "Remote" if is_rem else ""

            if not is_india_location(loc_str, workplace_type=wp_hint):
                if not loc_str.strip() and is_india_location(title, workplace_type=wp_hint):
                    clean_loc = "India"
                else:
                    continue
            else:
                clean_loc = extract_india_location(loc_str)

            apply_link = item.get("detailUrl") or item.get("applyUrl") or ep.endpoint_url
            posted_date = item.get("date") or item.get("postedDate")
            ist_str, raw_iso, rel_time = parse_date_to_ist(posted_date)

            emp_type = normalize_employment_type(job_type, title)
            workplace = "Remote" if is_rem else normalize_workplace(loc_str)
            exp_level = normalize_experience_level(title)
            dept = str(item.get("category") or item.get("department") or "")
            tags = generate_job_tags(title=title, company=ep.company_name, location=clean_loc, workplace_type=workplace, experience_level=exp_level, employment_type=emp_type, dept=dept)

            now_str = datetime.datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
            results.append({
                "company_name": ep.company_name,
                "role_name": title,
                "title": title,
                "location": clean_loc or "India",
                "apply_link": apply_link,
                "apply_url": apply_link,
                "posted_timestamp_ist": ist_str,
                "posted_timestamp_raw": raw_iso,
                "relative_time_ist": rel_time or "",
                "tags": tags,
                "employment_type": emp_type,
                "workplace_type": workplace,
                "experience_level": exp_level,
                "ats_platform": "Jobvite",
                "ingested_at": now_str
            })
        return results

    async def fetch_all_endpoints(self, max_concurrent: int = 12, sample_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetches configured endpoints asynchronously with rate limiting.
        Applies stratified sampling across all ATS platforms to ensure equitable
        distribution of Ashby, Greenhouse, Lever, BambooHR, SmartRecruiters, Workday, Recruitee, Breezy HR.
        """
        all_jobs: List[Dict[str, Any]] = []

        if sample_limit and sample_limit < len(self.endpoints):
            # Group endpoints by platform
            from collections import defaultdict
            by_platform = defaultdict(list)
            for ep in self.endpoints:
                plat_key = ep.ats_platform.lower()
                by_platform[plat_key].append(ep)

            selected_endpoints: List[ATSEndpoint] = []
            
            # Always include 100% of smaller / high-yield platforms
            always_full = ["smartrecruiters", "recruitee", "breezy hr", "breezy", "workable", "rippling", "oracle", "pinpoint", "comeet", "jobvite"]
            remaining_quota = sample_limit
            for plat in always_full:
                if plat in by_platform:
                    selected_endpoints.extend(by_platform[plat])
                    remaining_quota -= len(by_platform[plat])

            # Always prioritize 100% of verified India-hiring BambooHR employers
            bamboo_eps = by_platform.get("bamboohr", [])
            if bamboo_eps:
                verified_bamboo = [ep for ep in bamboo_eps if ep.endpoint_url.split("?")[0].lower() in self.verified_bamboohr_urls]
                other_bamboo = [ep for ep in bamboo_eps if ep.endpoint_url.split("?")[0].lower() not in self.verified_bamboohr_urls]
                selected_endpoints.extend(verified_bamboo)
                remaining_quota -= len(verified_bamboo)
                by_platform["bamboohr"] = other_bamboo

            # For larger platforms (ashby, greenhouse, lever, bamboohr, workday)
            large_platforms = [p for p in by_platform.keys() if p not in always_full]
            if large_platforms and remaining_quota > 0:
                quota_per_platform = remaining_quota // len(large_platforms)
                extra = remaining_quota % len(large_platforms)
                for idx, p in enumerate(large_platforms):
                    take = quota_per_platform + (1 if idx < extra else 0)
                    eps = by_platform[p]
                    if eps:
                        sampled = random.sample(eps, min(take, len(eps)))
                        selected_endpoints.extend(sampled)
            
            random.shuffle(selected_endpoints)
            endpoints_to_query = selected_endpoints
        else:
            endpoints_to_query = list(self.endpoints)
            random.shuffle(endpoints_to_query)

        semaphore = asyncio.Semaphore(max_concurrent)

        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            async def worker(ep: ATSEndpoint):
                async with semaphore:
                    try:
                        jobs = await self.fetch_single_endpoint(client, ep)
                        return jobs
                    except Exception as e:
                        logger.debug(f"Error fetching {ep.company_name}: {e}")
                        return []

            # Throttled execution in chunks of 25 with 50ms pauses to yield event loop and prevent CPU spikes
            chunk_size = 25
            for i in range(0, len(endpoints_to_query), chunk_size):
                chunk = endpoints_to_query[i:i + chunk_size]
                tasks = [worker(ep) for ep in chunk]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, list):
                        all_jobs.extend(res)
                if i + chunk_size < len(endpoints_to_query):
                    await asyncio.sleep(0.05)

        logger.info(f"Fetched {len(all_jobs)} India-specific jobs across {len(endpoints_to_query)} ATS endpoints.")
        return all_jobs

_ats_service: Optional[ATSService] = None

def get_ats_service() -> ATSService:
    global _ats_service
    if _ats_service is None:
        _ats_service = ATSService()
    return _ats_service

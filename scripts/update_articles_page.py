#!/usr/bin/env python3
"""
Update frontend/articles.html with all 30 career guides, domain categories,
live search filter, and interactive Career Guides dropdown in the top navbar.
"""

from pathlib import Path
import re

WORKSPACE = Path(__file__).resolve().parent.parent
ARTICLES_HTML = WORKSPACE / "frontend" / "articles.html"

# List of all 30 Career Guides with Category and Metadata
GUIDES = [
    # 1. Engineering & Architecture
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
        "icon": '<path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 1.29 0 2.5-1.06 4-1.06 2.33 0 4.22 1.89 4.22 4.22 0 1.5-.72 2.87-1.84 3.75l-6.38 5.09-6.38-5.09A4.69 4.69 0 0 1 3.78 25.16C3.78 22.83 5.67 20.94 8 20.94c1.5 0 2.71 1.06 4 1.06z"/>',
        "color": "#0284C7"
    },
    {
        "slug": "android-developer.html",
        "title": "Android Developer",
        "category": "Engineering & Architecture",
        "desc": "Engineering scalable Android apps with modern Kotlin, Jetpack Compose, Coroutines, and Material Design.",
        "icon": '<rect width="16" height="16" x="4" y="4" rx="2"/><circle cx="9" cy="9" r="1"/><circle cx="15" cy="9" r="1"/>',
        "color": "#16A34A"
    },

    # 2. Data, AI & Machine Learning
    {
        "slug": "data-scientist.html",
        "title": "Data Scientist",
        "category": "Data, AI & Machine Learning",
        "desc": "Applying advanced statistical modeling, predictive algorithms, and machine learning to solve business problems.",
        "icon": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
        "color": "#8B5CF6"
    },
    {
        "slug": "entry-level-data-scientist.html",
        "title": "Entry-Level Data Scientist",
        "category": "Data, AI & Machine Learning",
        "desc": "How to transition into data science, showcase Kaggle portfolios, master SQL/Python, and crack interviews.",
        "icon": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
        "color": "#059669"
    },
    {
        "slug": "machine-learning-engineer.html",
        "title": "Machine Learning Engineer",
        "category": "Data, AI & Machine Learning",
        "desc": "Deploying transformer architectures, LLMs, and low-latency inference pipelines with PyTorch and MLOps.",
        "icon": '<circle cx="12" cy="12" r="3"/><circle cx="19" cy="6" r="2"/><circle cx="5" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><circle cx="5" cy="18" r="2"/><line x1="7" y1="7" x2="10" y2="10"/><line x1="17" y1="7" x2="14" y2="10"/><line x1="7" y1="17" x2="10" y2="14"/><line x1="17" y1="17" x2="14" y2="14"/>',
        "color": "#7C3AED"
    },
    {
        "slug": "data-engineer.html",
        "title": "Data Engineer",
        "category": "Data, AI & Machine Learning",
        "desc": "Designing high-throughput data highways with Apache Spark, Kafka, Airflow, Snowflake, BigQuery, and dbt.",
        "icon": '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4 4 4-4"/>',
        "color": "#0D9488"
    },
    {
        "slug": "data-analyst.html",
        "title": "Data Analyst",
        "category": "Data, AI & Machine Learning",
        "desc": "Transforming raw figures into strategic insights using advanced SQL, Tableau, Power BI, and experimentation.",
        "icon": '<circle cx="12" cy="12" r="10"/><path d="m14 10-4 4"/><path d="m10 10 4 4"/>',
        "color": "#D97706"
    },
    {
        "slug": "ai-research-scientist.html",
        "title": "AI Research Scientist",
        "category": "Data, AI & Machine Learning",
        "desc": "Pioneering novel foundation models, multimodal intelligence, and publishing at NeurIPS, ICML, and ICLR.",
        "icon": '<path d="M12 2a4 4 0 0 0-4 4c0 2 2 3 2 6h4c0-3 2-4 2-6a4 4 0 0 0-4-4z"/><path d="M10 18h4"/><path d="M11 22h2"/>',
        "color": "#4338CA"
    },

    # 3. Cloud, DevOps & Security
    {
        "slug": "devops-engineer.html",
        "title": "DevOps Engineer",
        "category": "Cloud, DevOps & Security",
        "desc": "Automating continuous integration and delivery with Docker, Kubernetes, Terraform, and GitHub Actions.",
        "icon": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        "color": "#059669"
    },
    {
        "slug": "cloud-engineer.html",
        "title": "Cloud Engineer",
        "category": "Cloud, DevOps & Security",
        "desc": "Architecting resilient multi-cloud infrastructures, VPC networking, IAM security, and FinOps across AWS/GCP/Azure.",
        "icon": '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
        "color": "#0284C7"
    },
    {
        "slug": "site-reliability-engineer.html",
        "title": "Site Reliability Engineer (SRE)",
        "category": "Cloud, DevOps & Security",
        "desc": "Guarding five-nines uptime, managing SLOs and error budgets, incident postmortems, and chaos engineering.",
        "icon": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        "color": "#2563EB"
    },
    {
        "slug": "cybersecurity-engineer.html",
        "title": "Cybersecurity Engineer",
        "category": "Cloud, DevOps & Security",
        "desc": "Defending enterprise perimeters with threat modeling, SIEM threat hunting, penetration testing, and zero-trust.",
        "icon": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        "color": "#DC2626"
    },
    {
        "slug": "security-engineer.html",
        "title": "Security Engineer",
        "category": "Cloud, DevOps & Security",
        "desc": "Proactive application security (AppSec), DevSecOps pipeline scanning (SAST/DAST), and cryptographic controls.",
        "icon": '<path d="m10 10 4 4m0-4-4 4"/><circle cx="12" cy="12" r="10"/>',
        "color": "#E11D48"
    },
    {
        "slug": "qa-automation-engineer.html",
        "title": "QA Automation Engineer",
        "category": "Cloud, DevOps & Security",
        "desc": "Ensuring zero-defect releases with Playwright, Cypress, Selenium, API testing, and CI automated test suites.",
        "icon": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "color": "#16A34A"
    },

    # 4. Product, Design & Leadership
    {
        "slug": "product-manager.html",
        "title": "Product Manager",
        "category": "Product, Design & Leadership",
        "desc": "Driving product vision, user problem discovery, roadmap prioritization, and commercial feature delivery.",
        "icon": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
        "color": "#DB2777"
    },
    {
        "slug": "remote-product-manager.html",
        "title": "Remote Product Manager",
        "category": "Product, Design & Leadership",
        "desc": "Leading distributed product squads and async discovery across global time zones from anywhere.",
        "icon": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777z"/>',
        "color": "#EC4899"
    },
    {
        "slug": "technical-program-manager.html",
        "title": "Technical Program Manager (TPM)",
        "category": "Product, Design & Leadership",
        "desc": "Orchestrating multifaceted multi-team engineering programs, managing dependencies, and mitigating technical risks.",
        "icon": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "color": "#B45309"
    },
    {
        "slug": "engineering-manager.html",
        "title": "Engineering Manager",
        "category": "Product, Design & Leadership",
        "desc": "Coaching high-performing engineering teams, hiring talent, driving technical strategy, and nurturing culture.",
        "icon": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "color": "#BE185D"
    },
    {
        "slug": "ui-ux-designer.html",
        "title": "UI/UX Designer",
        "category": "Product, Design & Leadership",
        "desc": "Crafting intuitive digital interfaces through user research, wireframing, Figma design systems, and usability testing.",
        "icon": '<circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>',
        "color": "#EA580C"
    },
    {
        "slug": "product-designer.html",
        "title": "Product Designer",
        "category": "Product, Design & Leadership",
        "desc": "Owning end-to-end product design from problem validation and rapid prototyping to metric analysis and launch.",
        "icon": '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/>',
        "color": "#DB2777"
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
      <input type="text" id="guideSearchInput" placeholder="Filter 30 career guides by title or domain (e.g., Full Stack, DevOps, Data, SRE)..." style="width: 100%; border: none; outline: none; font-size: 15px; color: var(--txt); background: transparent;" oninput="filterCareerGuides()" />
      <button type="button" onclick="clearGuideSearch()" id="clearGuideBtn" style="display: none; background: none; border: none; color: var(--txt-dim); cursor: pointer; font-size: 16px;">&times;</button>
    </div>
    <div id="guideCountNotice" style="text-align: center; font-size: 13px; color: var(--txt-muted); margin-top: 10px;">
      Showing all <strong>30</strong> specialized career blueprints
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
        notice.innerHTML = `Showing <strong>${visibleCount}</strong> of 30 career guides`;
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

# Read existing articles.html
with open(ARTICLES_HTML, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the grid in articles.html
grid_pattern = r'<main class="results-container"[^>]*>.*?<div style="display: grid;[^>]*>.*?</div>\s*</main>'
replacement = f"""<main class="results-container" style="max-width: 1200px; margin: 40px auto; padding: 0 20px;">
{search_filter_html}
    <div id="guidesGrid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px;">
{cards_html}    </div>
  </main>"""

new_content = re.sub(grid_pattern, replacement, content, flags=re.DOTALL)

# Insert the filter script before </body>
if "function filterCareerGuides" not in new_content:
    new_content = new_content.replace("</body>", f"{filter_script}\n</body>")

with open(ARTICLES_HTML, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Successfully updated {ARTICLES_HTML} with all 30 career guides!")

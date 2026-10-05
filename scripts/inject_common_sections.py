#!/usr/bin/env python3
import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMON_CSS = """
    /* ══ TOP VERIFIED DIRECT APPLY LINKS PANEL (2 MARQUEE BANDS) ══ */
    .verified-direct-apply-panel {
      max-width: 1060px;
      margin: 24px auto 18px;
      padding: 22px 18px 18px;
      background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
      text-align: center;
      box-sizing: border-box;
      width: calc(100% - 24px);
    }
    .direct-apply-badge {
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
    }
    .direct-apply-title {
      font-size: 21px;
      font-weight: 850;
      color: #0F172A;
      margin: 0 0 6px;
      letter-spacing: -0.02em;
    }
    .direct-apply-subtitle {
      font-size: 13.5px;
      color: #475569;
      max-width: 720px;
      margin: 0 auto 16px;
      line-height: 1.5;
    }
    .direct-apply-bands-wrap {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .marquee-band-row {
      display: flex;
      align-items: center;
      gap: 10px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 99px;
      padding: 4px 6px 4px 12px;
      box-shadow: 0 1px 3px rgba(15,23,42,0.02);
      overflow: hidden;
      box-sizing: border-box;
      width: 100%;
    }
    .band-label-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11.5px;
      font-weight: 800;
      color: #334155;
      white-space: nowrap;
      flex-shrink: 0;
      padding-right: 8px;
      border-right: 1.5px solid #E2E8F0;
    }
    .pulse-green-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10B981;
      display: inline-block;
      animation: pulseGreen 2s infinite;
    }
    .pulse-blue-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #3B82F6;
      display: inline-block;
      animation: pulseGreen 2s infinite;
    }
    @keyframes pulseGreen {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.6; }
    }
    .marquee-band-viewport {
      flex: 1;
      overflow: hidden;
      position: relative;
      mask-image: linear-gradient(90deg, transparent, #000 16px, #000 calc(100% - 16px), transparent);
      -webkit-mask-image: linear-gradient(90deg, transparent, #000 16px, #000 calc(100% - 16px), transparent);
    }
    .marquee-band-track {
      display: flex;
      width: max-content;
      user-select: none;
    }
    .track-speed-roles { animation: marqueeScroll 45s linear infinite; }
    .track-speed-companies { animation: marqueeScrollReverse 48s linear infinite; }
    .marquee-band-track:hover { animation-play-state: paused; }
    .marquee-band-group {
      display: flex;
      align-items: center;
      gap: 8px;
      padding-right: 8px;
      flex-shrink: 0;
    }
    @keyframes marqueeScroll {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    @keyframes marqueeScrollReverse {
      0% { transform: translateX(-50%); }
      100% { transform: translateX(0); }
    }
    .band-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      color: #1E293B;
      padding: 5px 12px;
      border-radius: 99px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 1px 2px rgba(0,0,0,0.02);
      text-decoration: none;
    }
    .band-chip:hover {
      border-color: #818CF8;
      background: #EEF2FF;
      color: #3730A3;
      transform: translateY(-1px);
    }
    .chip-count {
      font-size: 10.5px;
      font-weight: 750;
      color: #059669;
      background: #ECFDF5;
      padding: 1px 5px;
      border-radius: 99px;
      border: 1px solid #A7F3D0;
    }
    .chip-count-blue {
      color: #1D4ED8;
      background: #EFF6FF;
      border-color: #BFDBFE;
    }
    .band-chip.chip-all {
      background: #4F46E5;
      color: #FFFFFF;
      border-color: #4F46E5;
    }
    .band-chip.chip-all .chip-count {
      background: rgba(255, 255, 255, 0.25);
      color: #FFFFFF;
      border-color: transparent;
    }
    .band-chip.chip-all:hover {
      background: #4338CA;
      color: #FFFFFF;
    }
    @media (max-width: 680px) {
      .verified-direct-apply-panel {
        margin: 14px auto;
        padding: 16px 10px 14px;
        border-radius: 16px;
        width: calc(100% - 16px);
      }
      .direct-apply-title { font-size: 18px; }
      .direct-apply-subtitle { font-size: 12.5px; margin-bottom: 12px; }
      .marquee-band-row {
        border-radius: 12px;
        padding: 4px 6px;
      }
      .band-label-pill {
        font-size: 11px;
        padding-right: 6px;
      }
    }
    @media print {
      .verified-direct-apply-panel {
        display: none !important;
      }
    }
"""

BANNER_AND_ROLES_HTML = """  <!-- ══ TOP VERIFIED DIRECT APPLY LINKS PANEL (2 MARQUEE BANDS) ══ -->
  <div class="verified-direct-apply-panel" aria-label="Verified Direct Apply Links">
    <div class="direct-apply-badge">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      <span>100% Verified Direct Applications</span>
    </div>
    <h2 class="direct-apply-title">Verified Direct Apply Links</h2>
    <p class="direct-apply-subtitle">Direct application links across all industries, companies, diverse job roles, official enterprise ATS portals, premier job networks (LinkedIn, Naukri, Indeed, Foundit), and authentic employer career websites in one place with zero recruiter spam and no ad walls.</p>

    <div class="direct-apply-bands-wrap">
      <!-- Band 1: Popular Roles -->
      <div class="marquee-band-row" aria-label="Popular Roles Band">
        <div class="band-label-pill">
          <span class="pulse-green-dot"></span>
          <span>Roles:</span>
        </div>
        <div class="marquee-band-viewport">
          <div class="marquee-band-track track-speed-roles">
            <div class="marquee-band-group">
              <a href="/jobs.html?role=Software%20Engineer" class="band-chip">💻 Software Engineer <span class="chip-count">14.2k</span></a>
              <a href="/jobs.html?role=Full%20Stack%20Developer" class="band-chip">🚀 Full Stack Developer <span class="chip-count">6.8k</span></a>
              <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="band-chip">🤖 AI &amp; ML Engineer <span class="chip-count">3.4k</span></a>
              <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="band-chip">☁️ DevOps &amp; Cloud <span class="chip-count">4.1k</span></a>
              <a href="/jobs.html?role=Data%20Scientist" class="band-chip">📊 Data Scientist <span class="chip-count">3.9k</span></a>
              <a href="/jobs.html?role=Product%20Manager" class="band-chip">💼 Product Manager <span class="chip-count">1.8k</span></a>
              <a href="/jobs.html?role=Cybersecurity%20Engineer" class="band-chip">🛡️ Cybersecurity <span class="chip-count">1.2k</span></a>
              <a href="/jobs.html?role=UI%2FUX%20Designer" class="band-chip">🎨 UI/UX Design <span class="chip-count">980</span></a>
              <a href="/jobs.html?role=Backend%20Developer" class="band-chip">⚙️ Backend Developer <span class="chip-count">5.2k</span></a>
              <a href="/jobs.html?role=Frontend%20Developer" class="band-chip">✨ Frontend Developer <span class="chip-count">4.6k</span></a>
              <a href="/jobs.html?role=Mobile%20Engineer" class="band-chip">📱 Mobile Developer <span class="chip-count">1.6k</span></a>
              <a href="/jobs.html?role=Business%20Analyst" class="band-chip">📈 Business Analyst <span class="chip-count">2.1k</span></a>
              <a href="/jobs.html" class="band-chip chip-all">🌐 Browse All Roles <span class="chip-count">26k+</span></a>
            </div>
            <div class="marquee-band-group" aria-hidden="true">
              <a href="/jobs.html?role=Software%20Engineer" class="band-chip">💻 Software Engineer <span class="chip-count">14.2k</span></a>
              <a href="/jobs.html?role=Full%20Stack%20Developer" class="band-chip">🚀 Full Stack Developer <span class="chip-count">6.8k</span></a>
              <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="band-chip">🤖 AI &amp; ML Engineer <span class="chip-count">3.4k</span></a>
              <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="band-chip">☁️ DevOps &amp; Cloud <span class="chip-count">4.1k</span></a>
              <a href="/jobs.html?role=Data%20Scientist" class="band-chip">📊 Data Scientist <span class="chip-count">3.9k</span></a>
              <a href="/jobs.html?role=Product%20Manager" class="band-chip">💼 Product Manager <span class="chip-count">1.8k</span></a>
              <a href="/jobs.html?role=Cybersecurity%20Engineer" class="band-chip">🛡️ Cybersecurity <span class="chip-count">1.2k</span></a>
              <a href="/jobs.html?role=UI%2FUX%20Designer" class="band-chip">🎨 UI/UX Design <span class="chip-count">980</span></a>
              <a href="/jobs.html?role=Backend%20Developer" class="band-chip">⚙️ Backend Developer <span class="chip-count">5.2k</span></a>
              <a href="/jobs.html?role=Frontend%20Developer" class="band-chip">✨ Frontend Developer <span class="chip-count">4.6k</span></a>
              <a href="/jobs.html?role=Mobile%20Engineer" class="band-chip">📱 Mobile Developer <span class="chip-count">1.6k</span></a>
              <a href="/jobs.html?role=Business%20Analyst" class="band-chip">📈 Business Analyst <span class="chip-count">2.1k</span></a>
              <a href="/jobs.html" class="band-chip chip-all">🌐 Browse All Roles <span class="chip-count">26k+</span></a>
            </div>
          </div>
        </div>
      </div>

      <!-- Band 2: Leading Companies -->
      <div class="marquee-band-row" aria-label="Leading Companies Band">
        <div class="band-label-pill">
          <span class="pulse-blue-dot"></span>
          <span>Companies:</span>
        </div>
        <div class="marquee-band-viewport">
          <div class="marquee-band-track track-speed-companies">
            <div class="marquee-band-group">
              <a href="/jobs.html?company=Google" class="band-chip">🏢 Google <span class="chip-count chip-count-blue">850+</span></a>
              <a href="/jobs.html?company=Microsoft" class="band-chip">🏢 Microsoft <span class="chip-count chip-count-blue">720+</span></a>
              <a href="/jobs.html?company=Amazon" class="band-chip">🏢 Amazon <span class="chip-count chip-count-blue">1.1k</span></a>
              <a href="/jobs.html?company=NVIDIA" class="band-chip">🏢 NVIDIA <span class="chip-count chip-count-blue">410+</span></a>
              <a href="/jobs.html?company=Apple" class="band-chip">🏢 Apple <span class="chip-count chip-count-blue">380+</span></a>
              <a href="/jobs.html?company=Meta" class="band-chip">🏢 Meta <span class="chip-count chip-count-blue">290+</span></a>
              <a href="/jobs.html?company=TCS" class="band-chip">🏢 TCS <span class="chip-count chip-count-blue">2.4k</span></a>
              <a href="/jobs.html?company=Infosys" class="band-chip">🏢 Infosys <span class="chip-count chip-count-blue">1.8k</span></a>
              <a href="/jobs.html?company=Accenture" class="band-chip">🏢 Accenture <span class="chip-count chip-count-blue">2.1k</span></a>
              <a href="/jobs.html?company=Deloitte" class="band-chip">🏢 Deloitte <span class="chip-count chip-count-blue">1.3k</span></a>
              <a href="/jobs.html?company=Wipro" class="band-chip">🏢 Wipro <span class="chip-count chip-count-blue">1.2k</span></a>
              <a href="/jobs.html?company=IBM" class="band-chip">🏢 IBM <span class="chip-count chip-count-blue">950+</span></a>
              <a href="/jobs.html?company=Oracle" class="band-chip">🏢 Oracle <span class="chip-count chip-count-blue">820+</span></a>
              <a href="/jobs.html?company=Flipkart" class="band-chip">🏢 Flipkart <span class="chip-count chip-count-blue">340+</span></a>
              <a href="/jobs.html?company=Swiggy" class="band-chip">🏢 Swiggy <span class="chip-count chip-count-blue">280+</span></a>
              <a href="/jobs.html?company=Zomato" class="band-chip">🏢 Zomato <span class="chip-count chip-count-blue">210+</span></a>
            </div>
            <div class="marquee-band-group" aria-hidden="true">
              <a href="/jobs.html?company=Google" class="band-chip">🏢 Google <span class="chip-count chip-count-blue">850+</span></a>
              <a href="/jobs.html?company=Microsoft" class="band-chip">🏢 Microsoft <span class="chip-count chip-count-blue">720+</span></a>
              <a href="/jobs.html?company=Amazon" class="band-chip">🏢 Amazon <span class="chip-count chip-count-blue">1.1k</span></a>
              <a href="/jobs.html?company=NVIDIA" class="band-chip">🏢 NVIDIA <span class="chip-count chip-count-blue">410+</span></a>
              <a href="/jobs.html?company=Apple" class="band-chip">🏢 Apple <span class="chip-count chip-count-blue">380+</span></a>
              <a href="/jobs.html?company=Meta" class="band-chip">🏢 Meta <span class="chip-count chip-count-blue">290+</span></a>
              <a href="/jobs.html?company=TCS" class="band-chip">🏢 TCS <span class="chip-count chip-count-blue">2.4k</span></a>
              <a href="/jobs.html?company=Infosys" class="band-chip">🏢 Infosys <span class="chip-count chip-count-blue">1.8k</span></a>
              <a href="/jobs.html?company=Accenture" class="band-chip">🏢 Accenture <span class="chip-count chip-count-blue">2.1k</span></a>
              <a href="/jobs.html?company=Deloitte" class="band-chip">🏢 Deloitte <span class="chip-count chip-count-blue">1.3k</span></a>
              <a href="/jobs.html?company=Wipro" class="band-chip">🏢 Wipro <span class="chip-count chip-count-blue">1.2k</span></a>
              <a href="/jobs.html?company=IBM" class="band-chip">🏢 IBM <span class="chip-count chip-count-blue">950+</span></a>
              <a href="/jobs.html?company=Oracle" class="band-chip">🏢 Oracle <span class="chip-count chip-count-blue">820+</span></a>
              <a href="/jobs.html?company=Flipkart" class="band-chip">🏢 Flipkart <span class="chip-count chip-count-blue">340+</span></a>
              <a href="/jobs.html?company=Swiggy" class="band-chip">🏢 Swiggy <span class="chip-count chip-count-blue">280+</span></a>
              <a href="/jobs.html?company=Zomato" class="band-chip">🏢 Zomato <span class="chip-count chip-count-blue">210+</span></a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>"""


def clean_head_css(head_content):
    """
    Remove any previous injected guarantee banner, ticker, roles band, and word cloud CSS
    from the <head> block and append a single clean COMMON_CSS before the primary </style>.
    """
    # Regex to strip previous CSS injections
    cleaned = re.sub(
        r'/\*\s*══\s*(?:DIRECT APPLY GUARANTEE BANNER|TOP VERIFIED DIRECT APPLY LINKS PANEL)[\s\S]*?(?=(?:/\*\s*══|\n\s*</style>))',
        '',
        head_content
    )
    # Also clean orphaned blocks if any
    cleaned = re.sub(
        r'\.direct-apply-guarantee-banner[\s\S]*?(?=(?:/\*\s*══|\n\s*</style>))',
        '',
        cleaned
    )
    cleaned = re.sub(
        r'\.roles-headline-ticker[\s\S]*?(?=(?:/\*\s*══|\n\s*</style>))',
        '',
        cleaned
    )
    cleaned = re.sub(
        r'\.verified-direct-apply-panel[\s\S]*?(?=(?:/\*\s*══|\n\s*</style>))',
        '',
        cleaned
    )
    cleaned = re.sub(
        r'/\*\s*══\s*ANIMATED WORD CLOUD[\s\S]*?(?=(?:/\*\s*══|\n\s*</style>))',
        '',
        cleaned
    )
    cleaned = re.sub(
        r'\.word-cloud-section[\s\S]*?(?=(?:/\*\s*══|\n\s*</style>))',
        '',
        cleaned
    )
    # Insert COMMON_CSS right before the first </style>
    if "</style>" in cleaned:
        cleaned = cleaned.replace("</style>", COMMON_CSS.strip() + "\n</style>", 1)
    return cleaned


def remove_element_by_class(html, tag, class_name):
    pattern = re.compile(rf"(?:<!--[^\n]*?-->\s*)?<({tag})\b[^>]*class=[\"\x27][^\"]*?\b{class_name}\b[^\"]*[\"\x27][^>]*>", re.IGNORECASE)
    while True:
        m = pattern.search(html)
        if not m:
            break
        start_idx = m.start()
        curr = m.end()
        depth = 1
        tag_re = re.compile(rf"<\s*(/)?\s*{tag}\b[^>]*>", re.IGNORECASE)
        while curr < len(html) and depth > 0:
            tm = tag_re.search(html, curr)
            if not tm:
                break
            if tm.group(1):
                depth -= 1
            else:
                depth += 1
            curr = tm.end()
        html = html[:start_idx] + html[curr:]
    return html


def clean_body_html(body_content):
    """
    Remove any previous injected banner and word cloud from the <body>,
    and insert BANNER_AND_ROLES_HTML right above the footer.
    """
    # 1. Strip any existing top panel / guarantee banner / word cloud using DOM-depth matching
    cleaned = remove_element_by_class(body_content, "div", "verified-direct-apply-panel")
    cleaned = remove_element_by_class(cleaned, "section", "word-cloud-section")
    cleaned = remove_element_by_class(cleaned, "div", "direct-apply-guarantee-banner")
    cleaned = remove_element_by_class(cleaned, "div", "roles-headline-ticker")

    # Clean up empty comments
    cleaned = re.sub(r'<!--\s*══\s*TOP VERIFIED DIRECT APPLY LINKS PANEL[^\n]*-->', '', cleaned)
    cleaned = re.sub(r'<!--\s*══\s*ANIMATED WORD CLOUD[^\n]*-->', '', cleaned)

    # 2. Insert above footer
    insertion = "\n" + BANNER_AND_ROLES_HTML + "\n"
    if '<footer class="site-footer">' in cleaned:
        cleaned = cleaned.replace('<footer class="site-footer">', insertion + '<footer class="site-footer">', 1)
    elif '<footer' in cleaned:
        cleaned = re.sub(r'(<footer\b)', insertion + r'\1', cleaned, count=1)
    elif '</body>' in cleaned:
        cleaned = cleaned.replace('</body>', insertion + '</body>', 1)

    return cleaned


def process_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")

    # Split into head and body to avoid touching other styles or body scripts
    if "</head>" in content:
        head_part, body_part = content.split("</head>", 1)
        head_part = clean_head_css(head_part)
        body_part = clean_body_html(body_part)
        new_content = head_part + "</head>" + body_part
    else:
        new_content = clean_body_html(content)

    # Ensure clean overflow-x hidden on html, body
    new_content = re.sub(r'(?:html,\s*)+body\s*\{\s*max-width:\s*100%;\s*overflow-x:\s*hidden;\s*position:\s*relative;\s*\}\s*', '', new_content)
    new_content = re.sub(
        r'(\bbody\s*\{)',
        r'html, body { max-width: 100%; overflow-x: hidden; position: relative; }\n    \1',
        new_content,
        count=1
    )

    path.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    targets = [
        "frontend/portfolio.html",
        "frontend/contact.html",
        "frontend/privacy.html",
        "frontend/disclaimer.html",
        "frontend/article_template.html",
    ]
    for t in targets:
        print(f"Processing {t}...")
        process_file(ROOT / t)

    job_articles = glob.glob(str(ROOT / "frontend/jobs/*.html"))
    print(f"Processing {len(job_articles)} job articles...")
    for j in job_articles:
        process_file(j)
    print("All pages successfully processed!")

#!/usr/bin/env python3
import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMON_CSS = """
    /* ══ DIRECT APPLY GUARANTEE BANNER (CENTERED & CONCISE) ══ */
    .direct-apply-guarantee-banner {
      background: linear-gradient(135deg, rgba(236,253,245,0.92) 0%, rgba(240,249,255,0.92) 100%);
      border: 1.5px solid #A7F3D0;
      border-radius: 99px;
      padding: 7px 18px;
      margin: 10px auto 16px;
      max-width: 880px;
      width: calc(100% - 24px);
      box-sizing: border-box;
      display: flex;
      justify-content: center;
      align-items: center;
      box-shadow: 0 1px 4px rgba(16, 185, 129, 0.06);
    }
    .guarantee-inner {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-wrap: wrap;
      gap: 8px;
      text-align: center;
    }
    .guarantee-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: #FFFFFF;
      border: 1px solid #6EE7B7;
      color: #065F46;
      font-size: 11.5px;
      font-weight: 800;
      padding: 3px 10px;
      border-radius: 99px;
      white-space: nowrap;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      flex-shrink: 0;
    }
    .guarantee-text {
      font-size: 13px;
      font-weight: 600;
      color: #1E293B;
      line-height: 1.4;
      text-align: center;
      margin: 0;
    }
    @media (max-width: 640px) {
      .direct-apply-guarantee-banner {
        border-radius: 12px;
        padding: 8px 12px;
        margin: 8px auto 14px;
        width: calc(100% - 16px);
      }
      .guarantee-text { font-size: 12px; }
    }

    /* ══ POPULAR ROLES MOVING HEADLINE TICKER ══ */
    .roles-headline-ticker {
      max-width: 1060px;
      margin: 0 auto 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 99px;
      padding: 4px 6px 4px 12px;
      box-shadow: 0 1px 4px rgba(15,23,42,0.03);
      overflow: hidden;
      box-sizing: border-box;
      width: calc(100% - 24px);
    }
    .roles-ticker-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
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
    @keyframes pulseGreen {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.3); opacity: 0.6; }
    }
    .roles-ticker-viewport {
      flex: 1;
      overflow: hidden;
      position: relative;
      mask-image: linear-gradient(90deg, transparent, #000 16px, #000 calc(100% - 16px), transparent);
      -webkit-mask-image: linear-gradient(90deg, transparent, #000 16px, #000 calc(100% - 16px), transparent);
    }
    .roles-ticker-track {
      display: flex;
      width: max-content;
      animation: rolesHeadlineMarquee 42s linear infinite;
    }
    .roles-ticker-track:hover {
      animation-play-state: paused;
    }
    .roles-ticker-group {
      display: flex;
      align-items: center;
      gap: 8px;
      padding-right: 8px;
      flex-shrink: 0;
    }
    @keyframes rolesHeadlineMarquee {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    .role-band-chip {
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
      user-select: none;
      text-decoration: none;
    }
    .role-band-chip:hover {
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
    .role-band-chip.chip-all {
      background: #4F46E5;
      color: #FFFFFF;
      border-color: #4F46E5;
    }
    .role-band-chip.chip-all .chip-count {
      background: rgba(255, 255, 255, 0.25);
      color: #FFFFFF;
      border-color: transparent;
    }
    .role-band-chip.chip-all:hover {
      background: #4338CA;
      color: #FFFFFF;
    }
    @media (max-width: 640px) {
      .roles-headline-ticker {
        border-radius: 12px;
        padding: 4px 6px;
        margin: 0 auto 14px;
        width: calc(100% - 16px);
      }
      .roles-ticker-badge {
        font-size: 11px;
        padding-right: 6px;
      }
    }

    /* ══ ANIMATED WORD CLOUD ══ */
    .word-cloud-section {
      max-width: 1060px;
      margin: 24px auto;
      padding: 24px 20px;
      background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
      text-align: center;
      overflow: hidden;
      box-sizing: border-box;
      width: calc(100% - 24px);
    }
    .word-cloud-header {
      margin-bottom: 16px;
    }
    .word-cloud-badge {
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
    .word-cloud-title {
      font-size: 20px;
      font-weight: 850;
      color: #0F172A;
      margin-bottom: 6px;
      letter-spacing: -0.02em;
    }
    .word-cloud-subtitle {
      font-size: 13px;
      color: #64748B;
      max-width: 600px;
      margin: 0 auto;
    }
    .word-cloud-canvas {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 16px;
      overflow: hidden;
      position: relative;
      width: 100%;
      max-width: 100%;
      box-sizing: border-box;
    }
    .word-cloud-canvas::before, .word-cloud-canvas::after {
      content: "";
      position: absolute;
      top: 0; bottom: 0;
      width: 40px;
      z-index: 2;
      pointer-events: none;
    }
    .word-cloud-canvas::before {
      left: 0;
      background: linear-gradient(90deg, #FFFFFF 0%, transparent 100%);
    }
    .word-cloud-canvas::after {
      right: 0;
      background: linear-gradient(270deg, #F8FAFC 0%, transparent 100%);
    }
    .word-cloud-stream {
      display: flex;
      align-items: center;
      gap: 12px;
      white-space: nowrap;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
      animation-duration: 35s;
    }
    .stream-left-to-right {
      animation-name: marqueeLeft;
    }
    .stream-right-to-left {
      animation-name: marqueeRight;
    }
    @keyframes marqueeLeft {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    @keyframes marqueeRight {
      0% { transform: translateX(-50%); }
      100% { transform: translateX(0); }
    }
    .word-cloud-stream:hover {
      animation-play-state: paused;
    }
    .wc-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 99px;
      font-size: 12.5px;
      font-weight: 700;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      cursor: pointer;
      box-shadow: 0 1px 4px rgba(0,0,0,0.03);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      flex-shrink: 0;
      text-decoration: none;
    }
    .wc-tag:hover {
      transform: translateY(-2px) scale(1.03);
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .wc-glow-blue { color: #1D4ED8; border-color: #BFDBFE; background: #EFF6FF; }
    .wc-glow-indigo { color: #4338CA; border-color: #C7D2FE; background: #EEF2FF; }
    .wc-glow-emerald { color: #047857; border-color: #A7F3D0; background: #ECFDF5; }
    .wc-glow-purple { color: #6D28D9; border-color: #DDD6FE; background: #F5F3FF; }
    .wc-glow-pink { color: #BE185D; border-color: #FBCFE8; background: #FDF2F8; }
    .wc-glow-amber { color: #B45309; border-color: #FDE68A; background: #FFFBEB; }
    .wc-glow-cyan { color: #0E7490; border-color: #A5F3FC; background: #ECFEFF; }
    .wc-ats {
      font-size: 10px;
      padding: 1px 5px;
      border-radius: 4px;
      background: rgba(0,0,0,0.06);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    @media (max-width: 680px) {
      .word-cloud-section {
        margin: 18px auto;
        padding: 18px 12px;
        border-radius: 16px;
        width: calc(100% - 16px);
      }
      .word-cloud-title { font-size: 18px; }
    }
    @media print {
      .direct-apply-guarantee-banner, .roles-headline-ticker, .word-cloud-section {
        display: none !important;
      }
    }
"""

BANNER_AND_ROLES_HTML = """  <!-- Direct Apply Guarantee Banner (Trust & No Intermediaries) -->
  <div class="direct-apply-guarantee-banner">
    <div class="guarantee-inner">
      <span class="guarantee-pill"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Direct ATS Apply</span>
      <span class="guarantee-text">Apply directly on official company career portals &bull; 100% verified links with zero recruiter spam &amp; ad walls</span>
    </div>
  </div>

  <!-- Popular Roles Moving Headline Ticker -->
  <div class="roles-headline-ticker" aria-label="Popular Roles Ticker">
    <div class="roles-ticker-badge">
      <span class="pulse-green-dot"></span>
      <span>Popular Roles:</span>
    </div>
    <div class="roles-ticker-viewport">
      <div class="roles-ticker-track">
        <div class="roles-ticker-group">
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
        <div class="roles-ticker-group" aria-hidden="true">
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
    </div>
  </div>"""

WORD_CLOUD_HTML = """  <!-- Animated Word Cloud -->
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
  </section>"""


def process_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")

    # 1. Update or inject CSS
    if "/* ══ DIRECT APPLY GUARANTEE BANNER" in content:
        content = re.sub(
            r'/\*\s*══\s*DIRECT APPLY GUARANTEE BANNER[\s\S]*?(?=@media print[\s\S]*?\}[\s\S]*?\n\s*\*/|\*/|\n\s*</style>)',
            COMMON_CSS.strip() + "\n",
            content
        )
    else:
        content = content.replace("</style>", COMMON_CSS + "\n</style>", 1)

    # 2. Update existing banner and roles or insert new ones
    if "direct-apply-guarantee-banner" in content:
        content = re.sub(
            r'<!--\s*Direct Apply Guarantee Banner[\s\S]*?<!--\s*Animated Word Cloud',
            BANNER_AND_ROLES_HTML + "\n\n  <!-- Animated Word Cloud",
            content
        )
    else:
        if '<footer class="site-footer">' in content:
            content = content.replace(
                '<footer class="site-footer">',
                BANNER_AND_ROLES_HTML + "\n" + WORD_CLOUD_HTML + "\n" + '<footer class="site-footer">',
                1
            )
        elif '</footer>' in content:
            content = content.replace(
                '</footer>',
                BANNER_AND_ROLES_HTML + "\n" + WORD_CLOUD_HTML + "\n" + '</footer>',
                1
            )

    # Ensure overflow-x hidden on html, body
    if "overflow-x: hidden" not in content[:2000]:
        content = content.replace("body {", "html, body { max-width: 100%; overflow-x: hidden; position: relative; }\n    body {", 1)

    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    targets = [
        "frontend/portfolio.html",
        "frontend/contact.html",
        "frontend/privacy.html",
        "frontend/disclaimer.html",
        "frontend/article_template.html",
    ]
    for t in targets:
        process_file(ROOT / t)

    job_articles = glob.glob(str(ROOT / "frontend/jobs/*.html"))
    print(f"Processing {len(job_articles)} job articles...")
    for j in job_articles:
        process_file(j)
    print("All pages successfully processed!")

#!/usr/bin/env python3
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMON_CSS = """
    /* ══ DIRECT APPLY GUARANTEE BANNER ══ */
    .direct-apply-guarantee-banner {
      background: linear-gradient(135deg, #F0FDF4 0%, #EFF6FF 100%);
      border: 1.5px solid #BBF7D0;
      border-radius: 16px;
      padding: 14px 20px;
      margin: 20px auto 16px;
      max-width: 1060px;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: 0 2px 10px rgba(16, 185, 129, 0.05);
    }
    .guarantee-badge {
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
    }
    .guarantee-text {
      font-size: 13.5px;
      color: #1E293B;
      line-height: 1.55;
      margin: 0;
    }
    .guarantee-text strong {
      color: #0F172A;
      font-weight: 700;
    }
    @media (max-width: 640px) {
      .direct-apply-guarantee-banner {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        padding: 12px 14px;
      }
      .guarantee-text { font-size: 12.5px; }
    }

    /* ══ ROLES HORIZONTAL BAND ══ */
    .roles-band-container {
      max-width: 1060px;
      margin: 0 auto 20px;
      padding: 0 4px;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 12px;
      overflow: hidden;
    }
    .roles-band-label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12.5px;
      font-weight: 750;
      color: #475569;
      white-space: nowrap;
      flex-shrink: 0;
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
    .roles-band-track {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      padding: 4px 2px;
      flex: 1;
    }
    .roles-band-track::-webkit-scrollbar { display: none; }
    .role-band-chip {
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
    }
    .role-band-chip:hover {
      border-color: #818CF8;
      background: #EEF2FF;
      color: #3730A3;
      transform: translateY(-1.5px);
      box-shadow: 0 3px 8px rgba(99, 102, 241, 0.15);
    }
    .chip-count {
      font-size: 11px;
      font-weight: 750;
      color: #059669;
      background: #ECFDF5;
      padding: 1px 6px;
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

    /* ══ ANIMATED WORD CLOUD ══ */
    .word-cloud-section {
      max-width: 1060px;
      margin: 36px auto;
      padding: 26px 20px;
      background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
      text-align: center;
      overflow: hidden;
      box-sizing: border-box;
    }
    .word-cloud-header {
      margin-bottom: 20px;
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
      font-size: 13.5px;
      color: #64748B;
      max-width: 600px;
      margin: 0 auto;
    }
    .word-cloud-canvas {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 18px;
      overflow: hidden;
      position: relative;
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
    }
    .wc-tag:hover {
      transform: translateY(-2px) scale(1.04);
      box-shadow: 0 6px 16px rgba(0,0,0,0.09);
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
      padding: 2px 5px;
      border-radius: 4px;
      background: rgba(0,0,0,0.06);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    @media print {
      .direct-apply-guarantee-banner, .roles-band-container, .word-cloud-section {
        display: none !important;
      }
    }
"""

BANNER_AND_ROLES_HTML = """
  <!-- Direct Apply Guarantee Banner -->
  <div class="direct-apply-guarantee-banner">
    <div class="guarantee-badge">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      <span>Direct Company Applications</span>
    </div>
    <p class="guarantee-text">
      Unlike traditional job aggregators that redirect you through spammy forms, ad walls, or third-party recruiters, <strong>CorporateGuild provides verified direct links to apply on official company career portals and ATS pages in one place.</strong>
    </p>
  </div>

  <!-- Horizontal Band for Job Roles with Count of Jobs -->
  <div class="roles-band-container" aria-label="Browse Jobs by Role">
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
"""

WORD_CLOUD_HTML = """
  <!-- Animated Word Cloud -->
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
"""

def process_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    
    # 1. Add CSS before </style> if not present
    if "/* ══ DIRECT APPLY GUARANTEE BANNER ══ */" not in content:
        content = content.replace("</style>", COMMON_CSS + "\n</style>", 1)
        
    # 2. Add BANNER_AND_ROLES_HTML and WORD_CLOUD_HTML
    if "direct-apply-guarantee-banner" not in content:
        # Place before footer
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
            
    path.write_text(content, encoding="utf-8")
    print(f"Injected components into {filepath}")

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

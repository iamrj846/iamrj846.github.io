import os
import re
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
      margin: 0 auto 16px;
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
      margin: 0 auto 18px;
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
      box-shadow: var(--card-shadow);
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

    /* ══ INTERACTIVE BENEFITS FLOW DIAGRAM ══ */
    .benefits-flow-section {
      max-width: 1060px;
      margin: 36px auto;
      padding: 30px 24px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: var(--card-shadow);
      box-sizing: border-box;
    }
    .flow-header {
      text-align: center;
      margin-bottom: 24px;
    }
    .flow-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11.5px;
      font-weight: 750;
      color: #065F46;
      background: #ECFDF5;
      border: 1px solid #A7F3D0;
      padding: 3px 11px;
      border-radius: 99px;
      margin-bottom: 8px;
    }
    .flow-title {
      font-size: 22px;
      font-weight: 850;
      color: #0F172A;
      margin-bottom: 6px;
      letter-spacing: -0.02em;
    }
    .flow-subtitle {
      font-size: 13.5px;
      color: #64748B;
      max-width: 620px;
      margin: 0 auto;
    }
    .flow-steps-grid {
      display: grid;
      grid-template-columns: 1fr auto 1fr auto 1fr;
      align-items: center;
      gap: 12px;
      margin-top: 14px;
    }
    @media (max-width: 820px) {
      .flow-steps-grid {
        grid-template-columns: 1fr;
        gap: 10px;
      }
      .flow-arrow-connector {
        transform: rotate(90deg);
        margin: 0 auto;
      }
    }
    .flow-step-card {
      background: #F8FAFC;
      border: 1.5px solid #E2E8F0;
      border-radius: 16px;
      padding: 18px 16px;
      text-align: center;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
    }
    .flow-step-card:hover, .flow-step-card.active {
      background: #FFFFFF;
      border-color: #6366F1;
      transform: translateY(-2px);
      box-shadow: 0 8px 24px -4px rgba(79, 70, 229, 0.14);
    }
    .step-num-badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 850;
      color: #4F46E5;
      background: #EEF2FF;
      border: 1px solid #C7D2FE;
      padding: 2px 8px;
      border-radius: 99px;
      margin-bottom: 10px;
    }
    .step-icon {
      font-size: 26px;
      margin-bottom: 8px;
    }
    .step-title {
      font-size: 15px;
      font-weight: 750;
      color: #0F172A;
      margin-bottom: 6px;
    }
    .step-desc {
      font-size: 12.5px;
      color: #64748B;
      line-height: 1.45;
      margin-bottom: 10px;
    }
    .step-highlight {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      color: #059669;
      background: #ECFDF5;
      padding: 2px 8px;
      border-radius: 6px;
    }
    .flow-arrow-connector {
      color: #94A3B8;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .flow-interactive-detail {
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 12px;
      padding: 14px 18px;
      margin-top: 18px;
      font-size: 13.5px;
      color: #334155;
      line-height: 1.6;
    }
    .flow-interactive-detail strong {
      display: block;
      color: #0F172A;
      font-size: 14px;
      margin-bottom: 4px;
    }

    /* ══ TRADITIONAL JOB BOARDS VS CORPORATEGUILD TABLE ══ */
    .comparison-section {
      max-width: 1060px;
      margin: 36px auto;
      padding: 30px 24px;
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 20px;
      box-shadow: var(--card-shadow);
      box-sizing: border-box;
    }
    .comparison-header {
      text-align: center;
      margin-bottom: 22px;
    }
    .comparison-badge {
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
    }
    .comparison-title {
      font-size: 22px;
      font-weight: 850;
      color: #0F172A;
      margin-bottom: 6px;
      letter-spacing: -0.02em;
    }
    .comparison-subtitle {
      font-size: 13.5px;
      color: #64748B;
      max-width: 620px;
      margin: 0 auto;
    }
    .comparison-table-wrapper {
      overflow-x: auto;
      margin-top: 16px;
      border-radius: 14px;
      border: 1px solid #E2E8F0;
    }
    .comparison-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13.5px;
    }
    .comparison-table th, .comparison-table td {
      padding: 13px 18px;
      border-bottom: 1px solid #F1F5F9;
    }
    .comparison-table th {
      background: #F8FAFC;
      font-weight: 750;
      color: #334155;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .th-traditional {
      background: #FEF2F2 !important;
      color: #991B1B !important;
    }
    .th-corporateguild {
      background: #ECFDF5 !important;
      color: #065F46 !important;
    }
    .table-brand-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-weight: 850;
      color: #047857;
    }
    .td-traditional {
      color: #64748B;
      background: rgba(254, 242, 242, 0.3);
    }
    .td-cg {
      background: rgba(236, 253, 245, 0.45);
      color: #0F172A;
    }
    .cross-mark {
      color: #DC2626;
      font-weight: 800;
      margin-right: 6px;
    }
    .check-mark {
      color: #059669;
      font-weight: 800;
      margin-right: 6px;
    }

    /* ══ MODERN JOB RESULT CARD ENHANCEMENTS ══ */
    .company-avatar-frame {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: #EEF2FF;
      border: 1.5px solid #C7D2FE;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      font-weight: 800;
      color: #4338CA;
      flex-shrink: 0;
      box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .job-title-group {
      flex: 1;
      min-width: 0;
    }
    .job-header-left {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      flex: 1;
      min-width: 240px;
    }
    .job-company-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 14px;
      font-weight: 650;
      color: #334155;
    }
    .verified-tick-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      font-weight: 750;
      color: #065F46;
      background: #ECFDF5;
      border: 1px solid #A7F3D0;
      padding: 2px 7px;
      border-radius: 99px;
    }
    .job-header-badges {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .actively-hiring-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11.5px;
      font-weight: 750;
      color: #15803D;
      background: #DCFCE7;
      border: 1px solid #86EFAC;
      padding: 3px 9px;
      border-radius: 99px;
      white-space: nowrap;
    }
    .hiring-pulse-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #16A34A;
      display: inline-block;
      animation: hiringPulse 2s infinite ease-in-out;
    }
    @keyframes hiringPulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.4); opacity: 0.6; }
    }
    .job-id-pill {
      font-size: 11px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      color: #64748B;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      padding: 2px 7px;
      border-radius: 6px;
      font-weight: 600;
    }
    .job-trust-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #059669;
    }
    .guest-mode-pill {
      background: #EEF2FF;
      color: #4338CA;
      border: 1px solid #C7D2FE;
      padding: 1px 7px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 750;
    }
"""

def update_jobs_page(filepath):
    print(f"Updating {filepath}...")
    with open(filepath, "r", encoding="utf-8") as fp:
        content = fp.read()

    # 1. Add CSS before </style>
    if "/* ══ DIRECT APPLY GUARANTEE BANNER ══ */" not in content:
        content = content.replace("</style>", COMMON_CSS + "\n</style>", 1)

    # 2. Extract hero-social-row and move it below search card
    social_m = re.search(r'(<!-- Social Media & Contact Links -->\s*<div class="hero-social-row">.*?</div>\s*</div>)', content, re.DOTALL)
    if not social_m:
        social_m = re.search(r'(<div class="hero-social-row">.*?</div>\s*</div>)', content, re.DOTALL)
    
    if social_m:
        social_block = social_m.group(1)
        # Remove it from hero
        content = content.replace(social_block, "")
        # Insert after </section> of searchFilterConsole
        search_card_end = '</section>\n\n  <!-- Job Cards Result Area -->'
        if search_card_end in content:
            new_placement = f'</section>\n\n  <!-- Social Media & Contact Links (Moved below search & filter console) -->\n  {social_block}\n\n  <!-- Job Cards Result Area -->'
            content = content.replace(search_card_end, new_placement, 1)

    # 3. Add Direct Apply Banner & Horizontal Roles Band above search card
    banner_and_band = """
    <!-- Direct Apply Guarantee Banner (Trust & No Intermediaries) -->
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
        <button type="button" class="role-band-chip" onclick="quickSearch('Software Engineer')">💻 Software Engineer <span class="chip-count">14.2k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Full Stack Developer')">🚀 Full Stack Developer <span class="chip-count">6.8k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('AI / Machine Learning Engineer')">🤖 AI &amp; ML Engineer <span class="chip-count">3.4k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('DevOps / Cloud Engineer')">☁️ DevOps &amp; Cloud <span class="chip-count">4.1k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Data Scientist')">📊 Data Scientist <span class="chip-count">3.9k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Product Manager')">💼 Product Manager <span class="chip-count">1.8k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Cybersecurity Engineer')">🛡️ Cybersecurity <span class="chip-count">1.2k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('UI/UX Designer')">🎨 UI/UX Design <span class="chip-count">980</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Backend Developer')">⚙️ Backend Developer <span class="chip-count">5.2k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Frontend Developer')">✨ Frontend Developer <span class="chip-count">4.6k</span></button>
        <button type="button" class="role-band-chip" onclick="quickSearch('Mobile Engineer')">📱 Mobile Developer <span class="chip-count">1.6k</span></button>
        <button type="button" class="role-band-chip chip-all" onclick="quickSearch('All Roles')">🌐 Browse All Jobs <span class="chip-count">26k+</span></button>
      </div>
    </div>
"""
    if '<div class="direct-apply-guarantee-banner">' not in content:
        target_bc = '<nav class="job-breadcrumbs"'
        if target_bc in content:
            content = content.replace(target_bc, banner_and_band + "\n    " + target_bc, 1)

    # 4. Remove 5 free searches wording
    content = content.replace("5 Free Searches Limit Reached", "Verification Required")
    content = content.replace("You have used your 5 free searches. Log in or create a free account to unlock unlimited real-time job searches across top verified companies.", "Please sign up or log in to continue searching verified jobs. It’s a short 2-minute process that helps us verify genuine users and unlocks unlimited access.")
    content = content.replace("openAuthModal('signup', 'You have reached your 5 free searches limit. Please log in or sign up to unlock Unlimited Access.')", "openAuthModal('signup', 'Please sign up or log in to continue searching. It’s a short 2-minute process that helps us verify genuine users.')")
    content = content.replace('<span id="quotaText">Remaining free searches: <strong class="quota-counter" id="remainingSearches">5</strong></span>', '<span id="quotaText"><span class="guest-mode-pill">Guest Access</span> • Sign up in 2 mins to verify &amp; unlock unlimited searches</span>')
    content = content.replace('(limited to 5 free searches)', '')

    # 5. Hide search overview card by default
    content = re.sub(
        r'<section class="seo-intro-card" id="seoIntroCard" aria-label="Job Search Overview"(?!\s*style=)',
        '<section class="seo-intro-card" id="seoIntroCard" aria-label="Job Search Overview" style="display: none;"',
        content
    )

    # 6. Add Word Cloud, Flow Diagram, and Comparison Table after </main>
    extra_sections = """
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
        <span class="wc-tag wc-company wc-glow-blue" onclick="quickSearch('Google')">🏢 Google <small class="wc-ats">ATS Direct</small></span>
        <span class="wc-tag wc-role wc-glow-indigo" onclick="quickSearch('AI / Machine Learning Engineer')">🤖 Generative AI Engineer</span>
        <span class="wc-tag wc-company wc-glow-emerald" onclick="quickSearch('Microsoft')">🏢 Microsoft</span>
        <span class="wc-tag wc-role wc-glow-purple" onclick="quickSearch('Full Stack Developer')">🚀 Full-Stack Architect</span>
        <span class="wc-tag wc-company wc-glow-amber" onclick="quickSearch('Amazon')">🏢 Amazon</span>
        <span class="wc-tag wc-role wc-glow-cyan" onclick="quickSearch('DevOps / Cloud Engineer')">☁️ Cloud Platform Engineer</span>
        <span class="wc-tag wc-company wc-glow-pink" onclick="quickSearch('NVIDIA')">🏢 NVIDIA</span>
        <span class="wc-tag wc-role wc-glow-blue" onclick="quickSearch('Data Scientist')">📊 Principal Data Scientist</span>
        <span class="wc-tag wc-company wc-glow-indigo" onclick="quickSearch('Apple')">🏢 Apple</span>
        <span class="wc-tag wc-role wc-glow-emerald" onclick="quickSearch('Site Reliability Engineer')">🛡️ Site Reliability Engineer</span>
      </div>
      <div class="word-cloud-stream stream-right-to-left">
        <span class="wc-tag wc-company wc-glow-purple" onclick="quickSearch('Workday')">⚡ Workday ATS</span>
        <span class="wc-tag wc-role wc-glow-amber" onclick="quickSearch('Software Engineer')">💻 Senior Software Engineer</span>
        <span class="wc-tag wc-company wc-glow-blue" onclick="quickSearch('Greenhouse')">⚡ Greenhouse ATS</span>
        <span class="wc-tag wc-role wc-glow-pink" onclick="quickSearch('Product Manager')">💼 Technical Product Manager</span>
        <span class="wc-tag wc-company wc-glow-cyan" onclick="quickSearch('Lever')">⚡ Lever Portal</span>
        <span class="wc-tag wc-role wc-glow-emerald" onclick="quickSearch('Golang Developer')">⚡ Go Systems Engineer</span>
        <span class="wc-tag wc-company wc-glow-indigo" onclick="quickSearch('Meta')">🏢 Meta</span>
        <span class="wc-tag wc-role wc-glow-purple" onclick="quickSearch('Rust Developer')">🦀 Rust Low-Latency Systems</span>
        <span class="wc-tag wc-company wc-glow-amber" onclick="quickSearch('SmartRecruiters')">⚡ SmartRecruiters</span>
        <span class="wc-tag wc-role wc-glow-blue" onclick="quickSearch('Cybersecurity Engineer')">🔒 DevSecOps Lead</span>
      </div>
    </div>
  </section>

  <!-- ══ INTERACTIVE BENEFITS FLOW DIAGRAM ══ -->
  <section class="benefits-flow-section" aria-label="How CorporateGuild Works">
    <div class="flow-header">
      <span class="flow-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        The CorporateGuild Direct Advantage
      </span>
      <h2 class="flow-title">How Direct ATS Application Works</h2>
      <p class="flow-subtitle">Eliminating middleman recruiter walls, stale ghost postings, and scraper spam in 3 simple steps</p>
    </div>
    <div class="flow-interactive-wrapper">
      <div class="flow-steps-grid">
        <div class="flow-step-card active" id="flowCard1" onclick="selectFlowStep(1)">
          <div class="step-num-badge">01</div>
          <div class="step-icon">🏢</div>
          <h3 class="step-title">Direct Enterprise ATS Ingestion</h3>
          <p class="step-desc">Hourly synchronization directly from official employer Workday, Greenhouse, Lever, and career feeds.</p>
          <span class="step-highlight">Zero Scraper Spam</span>
        </div>
        <div class="flow-arrow-connector">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
        <div class="flow-step-card" id="flowCard2" onclick="selectFlowStep(2)">
          <div class="step-num-badge">02</div>
          <div class="step-icon">🛡️</div>
          <h3 class="step-title">Deduplication &amp; 14-Day Purge</h3>
          <p class="step-desc">Deterministic unique Job IDs eliminate duplicates across database. Stale jobs older than 14 days are auto-purged.</p>
          <span class="step-highlight">100% Verified Active</span>
        </div>
        <div class="flow-arrow-connector">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
        <div class="flow-step-card" id="flowCard3" onclick="selectFlowStep(3)">
          <div class="step-num-badge">03</div>
          <div class="step-icon">⚡</div>
          <h3 class="step-title">1-Click Direct Employer Apply</h3>
          <p class="step-desc">Click Direct Apply and land straight on the company’s official ATS submission page. Zero resume selling.</p>
          <span class="step-highlight">Direct to Employer</span>
        </div>
      </div>
      <div class="flow-interactive-detail" id="flowStepDetail">
        <strong id="flowDetailTitle">Step 1: Direct Enterprise ATS Ingestion</strong>
        <p id="flowDetailText" style="margin: 0;">We index directly from authorized company career portals and enterprise applicant tracking systems every hour. Your application reaches employer hiring managers directly without intermediary agency brokers.</p>
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
"""
    if '<section class="word-cloud-section"' not in content:
        main_end = '</main>'
        if main_end in content:
            content = content.replace(main_end, main_end + '\n' + extra_sections, 1)

    # 7. Update JavaScript functions
    # 7a. selectFlowStep helper
    if "function selectFlowStep" not in content:
        js_hook = "function selectMatchingOption"
        flow_js = """
    function selectFlowStep(step) {
      document.querySelectorAll('.flow-step-card').forEach(c => c.classList.remove('active'));
      const activeCard = document.getElementById('flowCard' + step);
      if (activeCard) activeCard.classList.add('active');
      const titleEl = document.getElementById('flowDetailTitle');
      const textEl = document.getElementById('flowDetailText');
      if (step === 1) {
        if (titleEl) titleEl.textContent = 'Step 1: Direct Enterprise ATS Ingestion';
        if (textEl) textEl.textContent = 'We index directly from authorized company career portals and enterprise applicant tracking systems every hour. Your application reaches employer hiring managers directly without intermediary agency brokers.';
      } else if (step === 2) {
        if (titleEl) titleEl.textContent = 'Step 2: Deduplication & 14-Day Purge';
        if (textEl) textEl.textContent = 'Deterministic normalized URL hashes ensure each job is assigned a unique Job ID. Expired listings are purged hourly under our strict 14-day recency guarantee so you never waste time applying to ghost jobs.';
      } else if (step === 3) {
        if (titleEl) titleEl.textContent = 'Step 3: 1-Click Direct Employer Apply';
        if (textEl) textEl.textContent = 'When you find a matching role, click Direct Apply to land immediately on the employer’s official ATS career page. You submit directly to the company with zero middleman resume selling or hidden paywalls.';
      }
    }
"""
        content = content.replace(js_hook, flow_js + "\n\n    " + js_hook, 1)

    # 7b. Update updateQuotaDisplay
    quota_func_old = re.search(r'function updateQuotaDisplay\([^)]*\)\s*\{.*?\}', content, re.DOTALL)
    if quota_func_old:
        new_quota_func = """function updateQuotaDisplay(remaining, isAuthenticated) {
      const textEl = document.getElementById('quotaText');
      if (!textEl) return;
      if (isAuthenticated) {
        textEl.innerHTML = `<span style="color: #10B981; font-weight: 700;">✓ Active Member with Unlimited Searches</span>`;
      } else {
        textEl.innerHTML = `<span class="guest-mode-pill">Guest Access</span> • Sign up in 2 mins to verify &amp; unlock unlimited searches`;
      }
    }"""
        content = content.replace(quota_func_old.group(0), new_quota_func, 1)

    # 7c. Update renderJobCards to include Unique Job ID, Actively Hiring, Verified tags, and avatar
    job_cards_func_old = re.search(r'function renderJobCards\(jobs\)\s*\{.*?container\.innerHTML = jobs\.map\(j => `.*?`\)\.join\(\'\'\);\s*\}', content, re.DOTALL)
    if job_cards_func_old:
        new_job_cards_func = """function renderJobCards(jobs) {
      const container = document.getElementById('jobsList');
      const introCard = document.getElementById('seoIntroCard');
      if (!jobs.length) {
        if (introCard) introCard.style.display = 'none';
        container.innerHTML = `
          <div style="text-align: center; padding: 50px 20px; background: #FFFFFF; border-radius: 20px; border: 1px solid var(--card-bdr); box-shadow: var(--card-shadow);">
            <div style="font-size: 38px; margin-bottom: 12px;">🔍</div>
            <h3 style="font-size: 18px; margin-bottom: 6px; color: var(--txt-main);">No matching opportunities found</h3>
            <p style="color: var(--txt-muted); font-size: 14px;">Try clearing some filters or searching for another company or role keyword.</p>
          </div>
        `;
        return;
      }

      if (introCard) introCard.style.display = 'block';

      container.innerHTML = jobs.map(j => {
        const comp = (j.company_name || 'Tech Enterprise').trim();
        const initial = comp.charAt(0).toUpperCase() || 'C';
        const role = escapeHtml(j.title || j.role_name || 'Software Professional');
        const rawId = (j.id || '').replace(/^job_/, '');
        const jobId = rawId ? rawId.substring(0, 8).toUpperCase() : 'VERIFIED';
        const loc = escapeHtml(j.location || 'India');
        const emp = escapeHtml(j.employment_type || 'Full time');
        const wp = escapeHtml(j.workplace_type || 'In office');
        const exp = escapeHtml(j.experience_level || 'Mid-Senior');
        const ats = escapeHtml(j.ats_platform || 'Direct ATS');

        return `
        <article class="job-card">
          <div class="job-header">
            <div class="job-header-left">
              <div class="company-avatar-frame">${initial}</div>
              <div class="job-title-group">
                <h2 class="job-role">${role}</h2>
                <div class="job-company-row">
                  <span>🏢 ${escapeHtml(comp)}</span>
                  <span class="verified-tick-pill">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                    Verified Portal
                  </span>
                  ${ats ? `<span class="ats-badge">${ats}</span>` : ''}
                </div>
              </div>
            </div>
            <div class="job-header-badges">
              <span class="actively-hiring-pill"><span class="hiring-pulse-dot"></span> Actively Hiring</span>
              <span class="job-id-pill" title="Unique Job ID">#CG-${jobId}</span>
            </div>
          </div>

          <div class="job-details">
            <div class="job-pill">📍 <strong>${loc}</strong></div>
            <div class="job-pill">💼 ${emp}</div>
            <div class="job-pill">🏢 ${wp}</div>
            <div class="job-pill">⭐ ${exp}</div>
          </div>

          <div class="job-footer">
            <div class="job-trust-indicator">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              <span>Verified Direct ATS &bull; Zero Aggregator Spam</span>
            </div>
            <a 
              href="${escapeHtml(j.apply_link || '#')}" 
              target="_blank" 
              rel="noopener noreferrer" 
              class="apply-btn"
              onclick="trackJobClick('${escapeQuotes(j.company_name)}', '${escapeQuotes(j.title || j.role_name)}', '${escapeQuotes(j.apply_link || '')}')"
            >
              Direct Apply ↗
            </a>
          </div>
        </article>
        `;
      }).join('');
    }"""
        content = content.replace(job_cards_func_old.group(0), new_job_cards_func, 1)

    # 7d. Update executeSearch catch block to never show technical errors
    err_block_old = re.search(r'\} catch \(err\) \{\s*console\.error\(\'Search execution error:\', err\);.*?const bar = document\.getElementById\(\'paginationBar\'\);\s*if \(bar\) bar\.style\.display = \'none\';\s*\}', content, re.DOTALL)
    if err_block_old:
        new_err_block = """} catch (err) {
        console.error('Search execution error:', err);
        document.getElementById('loader').style.display = 'none';
        document.getElementById('jobsList').innerHTML = `
          <div style="text-align: center; padding: 48px 20px; background: #FFFFFF; border-radius: 16px; border: 1px solid var(--card-bdr); box-shadow: var(--card-shadow); margin: 20px auto; max-width: 520px;">
            <div style="width: 44px; height: 44px; margin: 0 auto 12px; border-radius: 50%; background: #EEF2FF; display: flex; align-items: center; justify-content: center; color: #4F46E5;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
            </div>
            <h3 style="font-size: 16.5px; font-weight: 750; color: var(--txt-main); margin-bottom: 6px;">Unable to load opportunities right now</h3>
            <p style="font-size: 13.5px; color: var(--txt-muted); margin-bottom: 16px;">Please try again in a moment.</p>
            <button type="button" onclick="executeSearch(${page}, false, true)" style="background: #4F46E5; color: white; border: none; padding: 9px 22px; border-radius: 10px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s;">Retry Search</button>
          </div>
        `;
        const meta = document.getElementById('resultsMeta');
        if (meta) meta.style.display = 'none';
        const bar = document.getElementById('paginationBar');
        if (bar) bar.style.display = 'none';
        const introCard = document.getElementById('seoIntroCard');
        if (introCard) introCard.style.display = 'none';
      }"""
        content = content.replace(err_block_old.group(0), new_err_block, 1)

    # 7e. Remove renderSearchPromptPlaceholder and call executeSearch on clean load
    content = re.sub(
        r'function renderSearchPromptPlaceholder\(\)\s*\{.*?function quickSearch',
        'function quickSearch',
        content,
        flags=re.DOTALL
    )
    content = content.replace(
        'renderSearchPromptPlaceholder();\n        return;',
        'executeSearch(1, false, false);\n        return;'
    )

    with open(filepath, "w", encoding="utf-8") as fp:
        fp.write(content)
    print(f"Successfully updated {filepath}")

def update_other_static_pages():
    for fpath in ["frontend/portfolio.html", "frontend/privacy.html", "frontend/contact.html", "frontend/disclaimer.html"]:
        p = ROOT / fpath
        if not p.exists():
            continue
        print(f"Updating static page {fpath}...")
        txt = p.read_text(encoding="utf-8")
        txt = txt.replace("5 Free Searches Limit Reached", "Verification Required")
        txt = txt.replace("(limited to 5 free searches)", "")
        txt = txt.replace("limited to 5 free searches", "unlimited free searches")
        txt = txt.replace("You have reached your 5 free searches limit. Please log in or sign up to unlock Unlimited Access.", "Please sign up or log in to continue searching. It’s a short 2-minute process that helps us verify genuine users.")
        p.write_text(txt, encoding="utf-8")

def update_all_job_articles():
    files = glob.glob(str(ROOT / "frontend/jobs/*.html"))
    print(f"Updating {len(files)} career guide blueprint articles...")
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as fp:
            txt = fp.read()
        txt = txt.replace("5 Free Searches Limit Reached", "Verification Required")
        txt = txt.replace("You have reached your 5 free searches limit. Please log in or sign up to unlock Unlimited Access.", "Please sign up or log in to continue searching. It’s a short 2-minute process that helps us verify genuine users.")
        txt = txt.replace("(limited to 5 free searches)", "")
        txt = re.sub(r'textEl\.innerHTML = `Remaining free searches: <strong class=\"quota-counter\" id=\"remainingSearches\"[^>]*>\$\{remaining\}<\/strong>`;', 'textEl.innerHTML = `<span class="guest-mode-pill">Guest Access</span> • Sign up in 2 mins to verify &amp; unlock unlimited searches`;', txt)
        with open(fpath, "w", encoding="utf-8") as fp:
            fp.write(txt)
    print("Finished updating career guide blueprint articles.")

if __name__ == "__main__":
    update_jobs_page("frontend/jobs.html")
    update_jobs_page("frontend/index.html")
    update_other_static_pages()
    update_all_job_articles()

#!/usr/bin/env python3
import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMON_CSS = """
    /* ══ TOP VERIFIED DIRECT APPLY LINKS PANEL (3 MARQUEE BANDS) ══ */
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
    .pulse-purple-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #8B5CF6;
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
    .track-speed-ats { animation: marqueeScroll 42s linear infinite; }
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
    .chip-count-purple {
      color: #6D28D9;
      background: #F5F3FF;
      border-color: #DDD6FE;
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
      mask-image: linear-gradient(90deg, transparent, #000 24px, #000 calc(100% - 24px), transparent);
      -webkit-mask-image: linear-gradient(90deg, transparent, #000 24px, #000 calc(100% - 24px), transparent);
    }
    .word-cloud-stream {
      display: flex;
      align-items: center;
      gap: 10px;
      width: max-content;
      user-select: none;
    }
    .stream-left-to-right {
      animation: wcMarqueeLTR 48s linear infinite;
    }
    .stream-right-to-left {
      animation: wcMarqueeRTL 52s linear infinite;
    }
    .word-cloud-stream:hover {
      animation-play-state: paused;
    }
    @keyframes wcMarqueeLTR {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }
    @keyframes wcMarqueeRTL {
      0% { transform: translateX(-50%); }
      100% { transform: translateX(0); }
    }
    .wc-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 99px;
      font-size: 13px;
      font-weight: 650;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      border: 1px solid transparent;
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
      .verified-direct-apply-panel, .word-cloud-section {
        display: none !important;
      }
    }
"""

BANNER_AND_ROLES_HTML = """  <!-- ══ TOP VERIFIED DIRECT APPLY LINKS PANEL (3 MARQUEE BANDS) ══ -->
  <div class="verified-direct-apply-panel" aria-label="Verified Direct Apply Links">
    <div class="direct-apply-badge">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      <span>100% Verified Direct Applications</span>
    </div>
    <h2 class="direct-apply-title">Verified Direct Apply Links</h2>
    <p class="direct-apply-subtitle">Direct application links across all industries, companies, diverse job roles, official enterprise ATS portals, and authentic hiring channels in one place with zero recruiter spam and no ad walls.</p>

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

      <!-- Band 3: ATS & Verified Sources -->
      <div class="marquee-band-row" aria-label="ATS and Verified Sources Band">
        <div class="band-label-pill">
          <span class="pulse-purple-dot"></span>
          <span>Sources:</span>
        </div>
        <div class="marquee-band-viewport">
          <div class="marquee-band-track track-speed-ats">
            <div class="marquee-band-group">
              <a href="/jobs.html?ats=Workday" class="band-chip">⚡ Workday ATS <span class="chip-count chip-count-purple">8.4k</span></a>
              <a href="/jobs.html?ats=Greenhouse" class="band-chip">⚡ Greenhouse ATS <span class="chip-count chip-count-purple">6.1k</span></a>
              <a href="/jobs.html?ats=Lever" class="band-chip">⚡ Lever Portal <span class="chip-count chip-count-purple">4.2k</span></a>
              <a href="/jobs.html?ats=SmartRecruiters" class="band-chip">⚡ SmartRecruiters <span class="chip-count chip-count-purple">3.8k</span></a>
              <a href="/jobs.html?ats=Taleo" class="band-chip">⚡ Taleo Enterprise <span class="chip-count chip-count-purple">2.9k</span></a>
              <a href="/jobs.html?ats=SAP%20SuccessFactors" class="band-chip">⚡ SAP SuccessFactors <span class="chip-count chip-count-purple">3.5k</span></a>
              <a href="/jobs.html?ats=BambooHR" class="band-chip">⚡ BambooHR <span class="chip-count chip-count-purple">1.8k</span></a>
              <a href="/jobs.html?ats=Ashby" class="band-chip">⚡ Ashby ATS <span class="chip-count chip-count-purple">1.4k</span></a>
              <a href="/jobs.html?ats=Jobvite" class="band-chip">⚡ Jobvite <span class="chip-count chip-count-purple">1.2k</span></a>
              <a href="/jobs.html?ats=iCIMS" class="band-chip">⚡ iCIMS <span class="chip-count chip-count-purple">2.3k</span></a>
              <a href="/jobs.html" class="band-chip">⚡ Official Career Portals <span class="chip-count chip-count-purple">5.6k</span></a>
            </div>
            <div class="marquee-band-group" aria-hidden="true">
              <a href="/jobs.html?ats=Workday" class="band-chip">⚡ Workday ATS <span class="chip-count chip-count-purple">8.4k</span></a>
              <a href="/jobs.html?ats=Greenhouse" class="band-chip">⚡ Greenhouse ATS <span class="chip-count chip-count-purple">6.1k</span></a>
              <a href="/jobs.html?ats=Lever" class="band-chip">⚡ Lever Portal <span class="chip-count chip-count-purple">4.2k</span></a>
              <a href="/jobs.html?ats=SmartRecruiters" class="band-chip">⚡ SmartRecruiters <span class="chip-count chip-count-purple">3.8k</span></a>
              <a href="/jobs.html?ats=Taleo" class="band-chip">⚡ Taleo Enterprise <span class="chip-count chip-count-purple">2.9k</span></a>
              <a href="/jobs.html?ats=SAP%20SuccessFactors" class="band-chip">⚡ SAP SuccessFactors <span class="chip-count chip-count-purple">3.5k</span></a>
              <a href="/jobs.html?ats=BambooHR" class="band-chip">⚡ BambooHR <span class="chip-count chip-count-purple">1.8k</span></a>
              <a href="/jobs.html?ats=Ashby" class="band-chip">⚡ Ashby ATS <span class="chip-count chip-count-purple">1.4k</span></a>
              <a href="/jobs.html?ats=Jobvite" class="band-chip">⚡ Jobvite <span class="chip-count chip-count-purple">1.2k</span></a>
              <a href="/jobs.html?ats=iCIMS" class="band-chip">⚡ iCIMS <span class="chip-count chip-count-purple">2.3k</span></a>
              <a href="/jobs.html" class="band-chip">⚡ Official Career Portals <span class="chip-count chip-count-purple">5.6k</span></a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>"""

WORD_CLOUD_HTML = """  <!-- ══ ANIMATED WORD CLOUD SECTION ══ -->
  <section class="word-cloud-section" aria-label="Verified Job Sources and Roles Cloud">
    <div class="word-cloud-header">
      <div class="word-cloud-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        <span>Interactive Word Cloud</span>
      </div>
      <h2 class="word-cloud-title">Explore Job Ecosystem Word Cloud</h2>
      <p class="word-cloud-subtitle">Interactive streaming word cloud of high-demand roles, leading employers, and official hiring sources</p>
    </div>
    <div class="word-cloud-canvas">
      <div class="word-cloud-stream stream-left-to-right">
        <a href="/jobs.html?company=Google" class="wc-tag wc-company wc-glow-blue">🏢 Google <small class="wc-ats">ATS Direct</small></a>
        <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="wc-tag wc-role wc-glow-indigo">🤖 Generative AI Engineer</a>
        <a href="/jobs.html?company=Microsoft" class="wc-tag wc-company wc-glow-emerald">🏢 Microsoft</a>
        <a href="/jobs.html?role=Full%20Stack%20Developer" class="wc-tag wc-role wc-glow-purple">🚀 Full-Stack Architect</a>
        <a href="/jobs.html?company=Amazon" class="wc-tag wc-company wc-glow-amber">🏢 Amazon</a>
        <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="wc-tag wc-role wc-glow-cyan">☁️ Cloud Platform Engineer</a>
        <a href="/jobs.html?company=NVIDIA" class="wc-tag wc-company wc-glow-pink">🏢 NVIDIA</a>
        <a href="/jobs.html?role=Data%20Scientist" class="wc-tag wc-role wc-glow-blue">📊 Principal Data Scientist</a>
        <a href="/jobs.html?company=Apple" class="wc-tag wc-company wc-glow-indigo">🏢 Apple</a>
        <a href="/jobs.html?role=Site%20Reliability%20Engineer" class="wc-tag wc-role wc-glow-emerald">🛡️ Site Reliability Engineer</a>
        <!-- Duplicated for seamless infinite marquee loop -->
        <a href="/jobs.html?company=Google" class="wc-tag wc-company wc-glow-blue" aria-hidden="true">🏢 Google <small class="wc-ats">ATS Direct</small></a>
        <a href="/jobs.html?role=AI%20%2F%20Machine%20Learning%20Engineer" class="wc-tag wc-role wc-glow-indigo" aria-hidden="true">🤖 Generative AI Engineer</a>
        <a href="/jobs.html?company=Microsoft" class="wc-tag wc-company wc-glow-emerald" aria-hidden="true">🏢 Microsoft</a>
        <a href="/jobs.html?role=Full%20Stack%20Developer" class="wc-tag wc-role wc-glow-purple" aria-hidden="true">🚀 Full-Stack Architect</a>
        <a href="/jobs.html?company=Amazon" class="wc-tag wc-company wc-glow-amber" aria-hidden="true">🏢 Amazon</a>
        <a href="/jobs.html?role=DevOps%20%2F%20Cloud%20Engineer" class="wc-tag wc-role wc-glow-cyan" aria-hidden="true">☁️ Cloud Platform Engineer</a>
        <a href="/jobs.html?company=NVIDIA" class="wc-tag wc-company wc-glow-pink" aria-hidden="true">🏢 NVIDIA</a>
        <a href="/jobs.html?role=Data%20Scientist" class="wc-tag wc-role wc-glow-blue" aria-hidden="true">📊 Principal Data Scientist</a>
        <a href="/jobs.html?company=Apple" class="wc-tag wc-company wc-glow-indigo" aria-hidden="true">🏢 Apple</a>
        <a href="/jobs.html?role=Site%20Reliability%20Engineer" class="wc-tag wc-role wc-glow-emerald" aria-hidden="true">🛡️ Site Reliability Engineer</a>
      </div>
      <div class="word-cloud-stream stream-right-to-left">
        <a href="/jobs.html?ats=Workday" class="wc-tag wc-company wc-glow-purple">⚡ Workday ATS</a>
        <a href="/jobs.html?role=Software%20Engineer" class="wc-tag wc-role wc-glow-amber">💻 Senior Software Engineer</a>
        <a href="/jobs.html?ats=Greenhouse" class="wc-tag wc-company wc-glow-blue">⚡ Greenhouse ATS</a>
        <a href="/jobs.html?role=Product%20Manager" class="wc-tag wc-role wc-glow-pink">💼 Technical Product Manager</a>
        <a href="/jobs.html?ats=Lever" class="wc-tag wc-company wc-glow-cyan">⚡ Lever Portal</a>
        <a href="/jobs.html?role=Golang%20Developer" class="wc-tag wc-role wc-glow-emerald">⚡ Go Systems Engineer</a>
        <a href="/jobs.html?company=Meta" class="wc-tag wc-company wc-glow-indigo">🏢 Meta</a>
        <a href="/jobs.html?role=Rust%20Developer" class="wc-tag wc-role wc-glow-purple">🦀 Rust Low-Latency Systems</a>
        <a href="/jobs.html?ats=SmartRecruiters" class="wc-tag wc-company wc-glow-amber">⚡ SmartRecruiters</a>
        <a href="/jobs.html?role=Cybersecurity%20Engineer" class="wc-tag wc-role wc-glow-blue">🔒 DevSecOps Lead</a>
        <!-- Duplicated for seamless infinite marquee loop -->
        <a href="/jobs.html?ats=Workday" class="wc-tag wc-company wc-glow-purple" aria-hidden="true">⚡ Workday ATS</a>
        <a href="/jobs.html?role=Software%20Engineer" class="wc-tag wc-role wc-glow-amber" aria-hidden="true">💻 Senior Software Engineer</a>
        <a href="/jobs.html?ats=Greenhouse" class="wc-tag wc-company wc-glow-blue" aria-hidden="true">⚡ Greenhouse ATS</a>
        <a href="/jobs.html?role=Product%20Manager" class="wc-tag wc-role wc-glow-pink" aria-hidden="true">💼 Technical Product Manager</a>
        <a href="/jobs.html?ats=Lever" class="wc-tag wc-company wc-glow-cyan" aria-hidden="true">⚡ Lever Portal</a>
        <a href="/jobs.html?role=Golang%20Developer" class="wc-tag wc-role wc-glow-emerald" aria-hidden="true">⚡ Go Systems Engineer</a>
        <a href="/jobs.html?company=Meta" class="wc-tag wc-company wc-glow-indigo" aria-hidden="true">🏢 Meta</a>
        <a href="/jobs.html?role=Rust%20Developer" class="wc-tag wc-role wc-glow-purple" aria-hidden="true">🦀 Rust Low-Latency Systems</a>
        <a href="/jobs.html?ats=SmartRecruiters" class="wc-tag wc-company wc-glow-amber" aria-hidden="true">⚡ SmartRecruiters</a>
        <a href="/jobs.html?role=Cybersecurity%20Engineer" class="wc-tag wc-role wc-glow-blue" aria-hidden="true">🔒 DevSecOps Lead</a>
      </div>
    </div>
  </section>"""


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
    # Insert COMMON_CSS right before the first </style>
    if "</style>" in cleaned:
        cleaned = cleaned.replace("</style>", COMMON_CSS.strip() + "\n</style>", 1)
    return cleaned


def clean_body_html(body_content):
    """
    Remove any previous injected banner and word cloud from the <body>,
    and insert BANNER_AND_ROLES_HTML and WORD_CLOUD_HTML right above the footer.
    """
    # 1. Strip any existing top panel / guarantee banner
    cleaned = re.sub(
        r'<!--\s*(?:══\s*TOP VERIFIED DIRECT APPLY LINKS PANEL|Direct Apply Guarantee Banner)[\s\S]*?</div>\s*</div>(?:\s*</div>)?',
        '',
        body_content
    )
    # 2. Strip any existing word cloud section
    cleaned = re.sub(
        r'<!--\s*(?:══\s*ANIMATED WORD CLOUD SECTION|Animated Word Cloud)[\s\S]*?</section>',
        '',
        cleaned
    )

    # 3. Insert above footer
    insertion = "\n" + BANNER_AND_ROLES_HTML + "\n\n" + WORD_CLOUD_HTML + "\n"
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

    # Ensure overflow-x hidden on html, body
    if "overflow-x: hidden" not in new_content[:2000]:
        new_content = new_content.replace(
            "body {",
            "html, body { max-width: 100%; overflow-x: hidden; position: relative; }\n    body {",
            1
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

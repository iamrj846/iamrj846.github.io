import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

if 'cdn.jsdelivr.net/npm/chart.js' not in content:
    content = content.replace('</head>', '  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>')

# Add Tab link
if 'data-tab="metrics"' not in content:
    content = content.replace('<button class="nav-btn" data-tab="db">', '<button class="nav-btn" data-tab="metrics">\n        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>\n        System Metrics\n      </button>\n      <button class="nav-btn" data-tab="db">')

# Add Tab content
metrics_html = '''
    <div class="tab-pane" id="tab-metrics">
      <div class="header-section">
        <h2 style="font-size: 22px; font-weight: 700; color: var(--txt); display: flex; align-items: center; gap: 8px;">
          <svg width="24" height="24" fill="none" stroke="var(--accent)" stroke-width="2" viewBox="0 0 24 24"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>
          System Performance Metrics
        </h2>
        <div>
          <select id="metricsTimeRange" onchange="fetchSystemMetrics()" style="padding: 8px 12px; border-radius: 8px; border: 1px solid var(--bdr); font-size: 14px; background: white;">
            <option value="1">Last 1 Hour</option>
            <option value="6">Last 6 Hours</option>
            <option value="12">Last 12 Hours</option>
            <option value="24">Last 24 Hours</option>
          </select>
          <button onclick="fetchSystemMetrics()" class="btn btn-primary" style="margin-left: 10px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
            Refresh
          </button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 20px;">
        <div class="metric-card" style="padding: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 15px;">CPU Utilisation (%)</h3>
          <canvas id="cpuChart" style="width:100%; height:250px;"></canvas>
        </div>
        <div class="metric-card" style="padding: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 15px;">Memory Utilisation (%)</h3>
          <canvas id="memChart" style="width:100%; height:250px;"></canvas>
        </div>
        <div class="metric-card" style="padding: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 15px;">TPS Metrics (req/sec)</h3>
          <canvas id="tpsChart" style="width:100%; height:250px;"></canvas>
        </div>
        <div class="metric-card" style="padding: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 15px;">Job Search Latency (ms)</h3>
          <canvas id="latSearchChart" style="width:100%; height:250px;"></canvas>
        </div>
        <div class="metric-card" style="padding: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 15px;">Redis Latency (ms)</h3>
          <canvas id="latRedisChart" style="width:100%; height:250px;"></canvas>
        </div>
        <div class="metric-card" style="padding: 20px;">
          <h3 style="font-size: 16px; margin-bottom: 15px;">Database Latency (ms)</h3>
          <canvas id="latDbChart" style="width:100%; height:250px;"></canvas>
        </div>
      </div>
    </div>
'''
if 'id="tab-metrics"' not in content:
    content = content.replace('<div class="tab-pane" id="tab-db">', metrics_html + '\n    <div class="tab-pane" id="tab-db">')

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)

print("Patched admin.html HTML structure")

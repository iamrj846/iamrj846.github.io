import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

# Add metrics tab button
if 'switchAnalyticsTab(\'metrics\'' not in content:
    content = content.replace(
        '<button type="button" class="analytics-tab-btn" onclick="switchAnalyticsTab(\'distributions\', this)">📊 Workplace &amp; Exp</button>',
        '<button type="button" class="analytics-tab-btn" onclick="switchAnalyticsTab(\'distributions\', this)">📊 Workplace &amp; Exp</button>\n          <button type="button" class="analytics-tab-btn" onclick="switchAnalyticsTab(\'metrics\', this)">📈 System Metrics</button>'
    )

metrics_html = '''
      <!-- Tab Content: System Metrics -->
      <div id="tabMetrics" class="analytics-tab-content" style="display: none;">
        <div style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
          <select id="metricsTimeRange" onchange="fetchSystemMetrics()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid var(--bdr); font-size: 13px; background: white;">
            <option value="1">Last 1 Hour</option>
            <option value="6">Last 6 Hours</option>
            <option value="12">Last 12 Hours</option>
            <option value="24">Last 24 Hours</option>
          </select>
          <button onclick="fetchSystemMetrics()" class="btn-primary" style="margin-left: 10px; padding: 6px 12px; font-size: 13px;">Refresh</button>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px;">
          <div class="metric-card" style="padding: 15px; border: 1px solid var(--bdr); border-radius: 12px; background: white;">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--txt-muted);">CPU Utilisation (%)</h3>
            <div style="height:200px;"><canvas id="cpuChart"></canvas></div>
          </div>
          <div class="metric-card" style="padding: 15px; border: 1px solid var(--bdr); border-radius: 12px; background: white;">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--txt-muted);">Memory Utilisation (%)</h3>
            <div style="height:200px;"><canvas id="memChart"></canvas></div>
          </div>
          <div class="metric-card" style="padding: 15px; border: 1px solid var(--bdr); border-radius: 12px; background: white;">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--txt-muted);">TPS Metrics (req/sec)</h3>
            <div style="height:200px;"><canvas id="tpsChart"></canvas></div>
          </div>
          <div class="metric-card" style="padding: 15px; border: 1px solid var(--bdr); border-radius: 12px; background: white;">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--txt-muted);">Job Search Latency (ms)</h3>
            <div style="height:200px;"><canvas id="latSearchChart"></canvas></div>
          </div>
          <div class="metric-card" style="padding: 15px; border: 1px solid var(--bdr); border-radius: 12px; background: white;">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--txt-muted);">Redis Latency (ms)</h3>
            <div style="height:200px;"><canvas id="latRedisChart"></canvas></div>
          </div>
          <div class="metric-card" style="padding: 15px; border: 1px solid var(--bdr); border-radius: 12px; background: white;">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--txt-muted);">Database Latency (ms)</h3>
            <div style="height:200px;"><canvas id="latDbChart"></canvas></div>
          </div>
        </div>
      </div>
'''

if 'id="tabMetrics"' not in content:
    content = content.replace(
        '<!-- Users Table Card -->',
        metrics_html + '\n    <!-- Users Table Card -->'
    )

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)
print("Added correct metrics tab HTML")

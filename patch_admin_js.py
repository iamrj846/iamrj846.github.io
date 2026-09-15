with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'r') as f:
    content = f.read()

js_code = '''
  let charts = {};

  async function fetchSystemMetrics() {
    const hours = document.getElementById('metricsTimeRange').value;
    try {
      const res = await fetch(`/api/admin/system_metrics?hours=${hours}`);
      if (res.status === 401 || res.status === 403) return showLogin();
      const data = await res.json();
      if (data.success) {
        renderCharts(data.metrics.reverse()); // Metrics come from newest to oldest due to LPUSH, so reverse for chronological
      }
    } catch(e) {
      console.error("Error fetching system metrics:", e);
    }
  }

  function renderCharts(metrics) {
    const labels = metrics.map(m => {
      const d = new Date(m.ts * 1000);
      return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
    });

    const createOrUpdateChart = (id, datasets) => {
      const ctx = document.getElementById(id);
      if (charts[id]) {
        charts[id].data.labels = labels;
        charts[id].data.datasets = datasets;
        charts[id].update();
      } else {
        charts[id] = new Chart(ctx, {
          type: 'line',
          data: { labels, datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            elements: { point: { radius: 1 }, line: { tension: 0.3, borderWidth: 2 } },
            plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } } },
            scales: {
              x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } },
              y: { beginAtZero: true }
            }
          }
        });
      }
    };

    // 1. CPU
    createOrUpdateChart('cpuChart', [{
      label: 'CPU %', data: metrics.map(m => m.cpu), borderColor: '#4F46E5', backgroundColor: '#4F46E533', fill: true
    }]);

    // 2. Mem
    createOrUpdateChart('memChart', [{
      label: 'Memory %', data: metrics.map(m => m.mem), borderColor: '#DB2777', backgroundColor: '#DB277733', fill: true
    }]);

    // 3. TPS
    createOrUpdateChart('tpsChart', [
      { label: 'Search TPS', data: metrics.map(m => m.tps_search), borderColor: '#059669', backgroundColor: '#05966933' },
      { label: 'Click TPS', data: metrics.map(m => m.tps_click), borderColor: '#D97706', backgroundColor: '#D9770633' }
    ]);

    // Helper for latency
    const getLatDatasets = (key) => [
      { label: 'P99', data: metrics.map(m => m[key].p99), borderColor: '#EF4444' },
      { label: 'P95', data: metrics.map(m => m[key].p95), borderColor: '#F59E0B' },
      { label: 'P90', data: metrics.map(m => m[key].p90), borderColor: '#3B82F6' },
      { label: 'P85', data: metrics.map(m => m[key].p85), borderColor: '#8B5CF6' },
      { label: 'Avg', data: metrics.map(m => m[key].avg), borderColor: '#10B981', borderDash: [5, 5] }
    ];

    // 4. Job Search Latency
    createOrUpdateChart('latSearchChart', getLatDatasets('lat_search'));
    // 5. Redis Latency
    createOrUpdateChart('latRedisChart', getLatDatasets('lat_redis'));
    // 6. DB Latency
    createOrUpdateChart('latDbChart', getLatDatasets('lat_db'));
  }
'''

if 'fetchSystemMetrics()' not in content:
    # insert before window.onload
    content = content.replace('window.onload = () => {', js_code + '\n  window.onload = () => {\n    fetchSystemMetrics();')

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/admin.html', 'w') as f:
    f.write(content)

print("Patched admin.js")

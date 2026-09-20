/**
 * CorporateGuild Universal Telemetry Tracker
 * Tracks:
 * 1. Visits: Page load and refresh events with unique session identification.
 * 2. Clicks: Every link (<a>), button (<button>), dropdown (<select>), tab, and search execution.
 */
(function () {
  function getOrCreateSessionId() {
    let sid = localStorage.getItem('cg_browser_session_id');
    if (!sid) {
      sid = 'sess_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
      localStorage.setItem('cg_browser_session_id', sid);
    }
    return sid;
  }

  function sendTelemetry(endpoint, payload) {
    const jsonStr = JSON.stringify(payload);
    if (navigator.sendBeacon) {
      try {
        const blob = new Blob([jsonStr], { type: 'application/json' });
        navigator.sendBeacon(endpoint, blob);
        return;
      } catch (e) {}
    }
    try {
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonStr,
        keepalive: true
      }).catch(function () {});
    } catch (e) {}
  }

  // 1. Visit telemetry on load / refresh
  function trackVisit() {
    const sid = getOrCreateSessionId();
    sendTelemetry('/api/telemetry/visit', {
      session_id: sid,
      path: window.location.pathname || '/',
      referrer: document.referrer || ''
    });
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    trackVisit();
  } else {
    document.addEventListener('DOMContentLoaded', trackVisit);
  }

  // 2. Click telemetry on any button or link (excluding direct job apply links which have dedicated tracking)
  document.addEventListener('click', function (e) {
    const target = e.target.closest('a, button, input[type="submit"], select, .mode-tab, .suggestion-item, .page-btn, .apply-btn, .breadcrumb-item a');
    if (!target) return;

    // Direct job apply links have dedicated tracking via /api/jobs/click
    if (target.closest('.btn-apply, [onclick*="trackJobClick"]')) {
      return;
    }

    const sid = getOrCreateSessionId();
    const label = (target.innerText || target.value || target.getAttribute('aria-label') || target.title || target.tagName).trim().substring(0, 100);
    const tag = target.tagName.toLowerCase();

    sendTelemetry('/api/telemetry/click', {
      session_id: sid,
      element_type: tag,
      element_label: label,
      path: window.location.pathname || '/'
    });
  }, true);
})();

/**
 * Universal Resilient Fetch with Exponential Backoff Retries
 * Handles intermittent network drops and transient proxy/gateway errors (502, 503, 504)
 */
window.fetchWithRetry = async function (url, options = {}, maxRetries = 3, baseDelayMs = 500) {
  let attempt = 0;
  while (true) {
    attempt++;
    try {
      const res = await fetch(url, options);
      if (!res.ok && (res.status === 502 || res.status === 503 || res.status === 504) && attempt <= maxRetries) {
        const delay = baseDelayMs * Math.pow(1.5, attempt - 1);
        console.warn(`[fetchWithRetry] HTTP ${res.status} on attempt ${attempt}/${maxRetries} for ${url}. Retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      return res;
    } catch (err) {
      if (attempt <= maxRetries) {
        const delay = baseDelayMs * Math.pow(1.5, attempt - 1);
        console.warn(`[fetchWithRetry] Network failure on attempt ${attempt}/${maxRetries} for ${url}: ${err.message || err}. Retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
};

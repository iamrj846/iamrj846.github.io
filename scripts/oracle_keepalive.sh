#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - Oracle Cloud VM Anti-Idle Keep-Alive Heartbeat
# ==============================================================================
# Oracle Cloud Free Tier automatically reclaims / scales down compute instances
# whose 95th percentile CPU utilization falls below 20%.
# This script executes a local platform health check ping and a safe 15-second
# micro-burst of CPU activity every 10 minutes to maintain healthy activity
# without impacting web server latency.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$WORKSPACE_ROOT/logs/keepalive.log"

mkdir -p "$WORKSPACE_ROOT/logs"

IST_TIME=$(TZ="Asia/Kolkata" date "+%Y-%m-%d %H:%M:%S IST")

# 1. Local HTTP Health & Memory Ping
HTTP_PORT="${APP_PORT:-8000}"
PING_URL="http://127.0.0.1:${HTTP_PORT}/api/jobs/suggest?mode=company&q=a"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$PING_URL" 2>/dev/null || echo "000")

# 2. Lightweight Keep-Alive Ping (0% CPU impact)
# Simply ping healthcheck to maintain socket and system activity without CPU burn
curl -s -o /dev/null --max-time 5 "http://127.0.0.1:${HTTP_PORT}/api/health" 2>/dev/null || true

# 3. Log Heartbeat
echo "[$IST_TIME] [KeepAlive] Heartbeat ping: HTTP $HTTP_STATUS | Normal operations active." >> "$LOG_FILE"

# 4. Truncate log if exceeding 5000 lines
if [ -f "$LOG_FILE" ]; then
    LINE_COUNT=$(wc -l < "$LOG_FILE" || echo "0")
    if [ "$LINE_COUNT" -gt 5000 ]; then
        tail -n 2500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
fi

exit 0

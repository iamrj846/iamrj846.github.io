#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - Cron Job Setup for Oracle Cloud Keep-Alive
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEEPALIVE_SCRIPT="$WORKSPACE_ROOT/scripts/oracle_keepalive.sh"
LOG_FILE="$WORKSPACE_ROOT/logs/keepalive.log"

CRON_CMD="*/10 * * * * /bin/bash $KEEPALIVE_SCRIPT >> $LOG_FILE 2>&1"

echo "========================================================================"
echo "  🕒 Setting up 10-Minute Anti-Idle Keep-Alive Cron Job"
echo "========================================================================"
echo "Command to schedule:"
echo "  $CRON_CMD"
echo ""

# Attempt to install to user crontab
if command -v crontab &> /dev/null; then
    EXISTING_CRON=$(crontab -l 2>/dev/null || true)
    if echo "$EXISTING_CRON" | grep -q "oracle_keepalive.sh"; then
        echo "✅ Keep-Alive cron job is already installed in user crontab."
    else
        echo "⚙️ Adding keep-alive entry to user crontab..."
        (echo "$EXISTING_CRON"; echo "# CorporateGuild Oracle Cloud Anti-Idle KeepAlive (Every 10 Minutes)"; echo "$CRON_CMD") | crontab -
        echo "🎉 Successfully installed! Current crontab entries:"
        crontab -l | tail -n 3
    fi
else
    echo "⚠️ 'crontab' binary not found. You can add the following line to your system cron:"
    echo "  $CRON_CMD"
fi

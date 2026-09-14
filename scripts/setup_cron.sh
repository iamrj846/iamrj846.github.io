#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - Cron Job Setup for Oracle Cloud (Backup & Keep-Alive)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_SCRIPT="$WORKSPACE_ROOT/scripts/backup_to_oci.sh"
KEEPALIVE_SCRIPT="$WORKSPACE_ROOT/scripts/oracle_keepalive.sh"

mkdir -p "$WORKSPACE_ROOT/logs" "$WORKSPACE_ROOT/backups"
chmod +x "$BACKUP_SCRIPT" "$KEEPALIVE_SCRIPT" 2>/dev/null || true

BACKUP_CRON="0 */2 * * * /bin/bash $BACKUP_SCRIPT >> $WORKSPACE_ROOT/logs/backup.log 2>&1"
KEEPALIVE_CRON="*/10 * * * * /bin/bash $KEEPALIVE_SCRIPT >> $WORKSPACE_ROOT/logs/keepalive.log 2>&1"

echo "========================================================================"
echo "  🕒 Setting up CorporateGuild Production Cron Jobs"
echo "========================================================================"
echo "1. 2-Hour SQLite Backup to OCI Object Storage:"
echo "   $BACKUP_CRON"
echo "2. 10-Minute Anti-Idle Keep-Alive:"
echo "   $KEEPALIVE_CRON"
echo ""

if command -v crontab &> /dev/null; then
    EXISTING_CRON=$(crontab -l 2>/dev/null | grep -v "backup_to_oci.sh" | grep -v "oracle_keepalive.sh" || true)
    
    (
        if [ -n "$EXISTING_CRON" ]; then
            echo "$EXISTING_CRON"
        fi
        echo "# CorporateGuild 2-Hour SQLite Backup to OCI Object Storage"
        echo "$BACKUP_CRON"
        echo "# CorporateGuild 10-Minute Anti-Idle Keep-Alive"
        echo "$KEEPALIVE_CRON"
    ) | crontab -

    echo "🎉 Successfully installed! Active crontab entries:"
    crontab -l
else
    echo "⚠️ 'crontab' binary not found. Please install cron or add manually."
fi

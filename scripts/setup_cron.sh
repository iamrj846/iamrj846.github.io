#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - Cron Job Setup for Oracle Cloud (Backup, Keep-Alive, DB Sync)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_SCRIPT="$WORKSPACE_ROOT/scripts/backup_to_oci.sh"
KEEPALIVE_SCRIPT="$WORKSPACE_ROOT/scripts/oracle_keepalive.sh"
SYNC_SCRIPT="$WORKSPACE_ROOT/scripts/sync_cluster_db.sh"

mkdir -p "$WORKSPACE_ROOT/logs" "$WORKSPACE_ROOT/backups"
chmod +x "$BACKUP_SCRIPT" "$KEEPALIVE_SCRIPT" "$SYNC_SCRIPT" 2>/dev/null || true

BACKUP_CRON="0 */2 * * * /bin/bash $BACKUP_SCRIPT >> $WORKSPACE_ROOT/logs/backup.log 2>&1"
KEEPALIVE_CRON="*/10 * * * * /bin/bash $KEEPALIVE_SCRIPT >> $WORKSPACE_ROOT/logs/keepalive.log 2>&1"
SYNC_CRON="*/10 * * * * /bin/bash $SYNC_SCRIPT >> $WORKSPACE_ROOT/logs/cluster_sync.log 2>&1"

# Detect if current machine is Gateway (VM 1) or Worker (VM 2)
MY_IPS=$(hostname -I 2>/dev/null || true)
IS_GATEWAY=false
if echo "$MY_IPS" | grep -q "10.0.0.136"; then
    IS_GATEWAY=true
fi

echo "========================================================================"
echo "  🕒 Setting up CorporateGuild Production Cron Jobs"
echo "========================================================================"
echo "1. 2-Hour SQLite Backup to OCI Object Storage:"
echo "   $BACKUP_CRON"
echo "2. 10-Minute Anti-Idle Keep-Alive:"
echo "   $KEEPALIVE_CRON"
if [ "$IS_GATEWAY" = true ]; then
echo "3. 10-Minute Cluster DB Synchronizer (VM 1 -> VM 2):"
echo "   $SYNC_CRON"
fi
echo ""

if command -v crontab &> /dev/null; then
    EXISTING_CRON=$(crontab -l 2>/dev/null | grep -v "backup_to_oci.sh" | grep -v "oracle_keepalive.sh" | grep -v "sync_cluster_db.sh" || true)
    
    (
        if [ -n "$EXISTING_CRON" ]; then
            echo "$EXISTING_CRON"
        fi
        echo "# CorporateGuild 2-Hour SQLite Backup to OCI Object Storage"
        echo "$BACKUP_CRON"
        echo "# CorporateGuild 10-Minute Anti-Idle Keep-Alive"
        echo "$KEEPALIVE_CRON"
        if [ "$IS_GATEWAY" = true ]; then
            echo "# CorporateGuild 10-Minute Cluster DB Synchronizer"
            echo "$SYNC_CRON"
        fi
    ) | crontab -

    echo "🎉 Successfully installed! Active crontab entries:"
    crontab -l
else
    echo "⚠️ 'crontab' binary not found. Please install cron or add manually."
fi

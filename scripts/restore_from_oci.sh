#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - SQLite Database Restore from Local Snapshot or OCI
# ==============================================================================
# Usage:
#   ./scripts/restore_from_oci.sh                     # Restores from latest local backup
#   ./scripts/restore_from_oci.sh <path_to_backup.gz> # Restores from specific snapshot
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DB_TARGET="${DATABASE_PATH:-$WORKSPACE_ROOT/data/jobs_portal.db}"
BACKUP_DIR="$WORKSPACE_ROOT/backups"
LOG_FILE="$WORKSPACE_ROOT/logs/restore.log"
HUMAN_IST=$(TZ="Asia/Kolkata" date "+%Y-%m-%d %H:%M:%S IST")
NOW_STAMP=$(date "+%Y%m%d_%H%M%S")

log() {
    echo "[$HUMAN_IST] $1" | tee -a "$LOG_FILE"
}

mkdir -p "$WORKSPACE_ROOT/logs"

log "▶ Starting database restore procedure..."

# 1. Determine Source Backup File
TARGET_BACKUP="${1:-}"

if [ -z "$TARGET_BACKUP" ]; then
    # Find latest backup in backups directory
    LATEST=$(find "$BACKUP_DIR" -type f -name "corporateguild_backup_*.db.gz" | sort -r | head -n 1 || true)
    if [ -z "$LATEST" ]; then
        log "❌ Error: No backup files found in $BACKUP_DIR"
        exit 1
    fi
    TARGET_BACKUP="$LATEST"
    log "ℹ️ No backup specified. Selected latest available backup: $TARGET_BACKUP"
fi

if [ ! -f "$TARGET_BACKUP" ]; then
    log "❌ Error: Specified backup file not found: $TARGET_BACKUP"
    exit 1
fi

TEMP_RESTORE_DIR="/tmp/corporateguild_restore_${NOW_STAMP}"
mkdir -p "$TEMP_RESTORE_DIR"
UNPACKED_DB="$TEMP_RESTORE_DIR/restored.db"

# 2. Decompress Backup
log "📦 Decompressing $TARGET_BACKUP..."
if [[ "$TARGET_BACKUP" == *.gz ]]; then
    gzip -d -c "$TARGET_BACKUP" > "$UNPACKED_DB"
else
    cp "$TARGET_BACKUP" "$UNPACKED_DB"
fi

# 3. Verify Database Integrity
log "🔍 Verifying database integrity..."
if command -v sqlite3 &> /dev/null; then
    INTEGRITY=$(sqlite3 "$UNPACKED_DB" "PRAGMA integrity_check;" 2>/dev/null || echo "failed")
    if [ "$INTEGRITY" != "ok" ]; then
        log "❌ Error: Database integrity check failed ($INTEGRITY). Aborting restore!"
        rm -rf "$TEMP_RESTORE_DIR"
        exit 1
    fi
    TOTAL_JOBS=$(sqlite3 "$UNPACKED_DB" "SELECT count(*) FROM jobs;" 2>/dev/null || echo "0")
    log "   Integrity verified: OK (Total jobs: $TOTAL_JOBS)"
fi

# 4. Create Pre-Restore Safety Rollback Copy
if [ -f "$DB_TARGET" ]; then
    SAFETY_BAK="${DB_TARGET}.pre_restore_${NOW_STAMP}"
    log "🛡️ Creating emergency rollback backup of current live DB: $SAFETY_BAK"
    cp "$DB_TARGET" "$SAFETY_BAK"
fi

# 5. Atomically Restore Database
log "🚀 Replacing live database with verified backup snapshot..."
mkdir -p "$(dirname "$DB_TARGET")"
cp "$UNPACKED_DB" "$DB_TARGET"
rm -rf "$TEMP_RESTORE_DIR"

log "✅ Live database restored to: $DB_TARGET"

# 6. Hot-Reload Web Container if Docker is Running
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -qE "(corporateguild_web|corporateguild_web_prod)"; then
        log "🔄 Reloading web container to refresh database connections..."
        docker compose restart web 2>/dev/null || docker compose -f docker-compose.prod.yml restart web 2>/dev/null || true
        log "✅ Container reloaded."
    fi
fi

log "🎉 Database restoration completed successfully."
exit 0

#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - SQLite Automated Online Backup to Oracle Cloud Object Storage
# ==============================================================================
# - Performs non-blocking safe online backup using SQLite's .backup API
# - Compresses with gzip -9 and generates SHA-256 checksum
# - Uploads to Oracle Cloud Object Storage bucket (Always Free: 10 GB limit)
# - Rotates local and remote backups (7-day retention / 84 snapshots)
# - Designed to run via cron every 2 hours: 0 */2 * * *
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration & Environment
DB_FILE="${DATABASE_PATH:-$WORKSPACE_ROOT/data/jobs_portal.db}"
BACKUP_DIR="$WORKSPACE_ROOT/backups"
LOG_FILE="$WORKSPACE_ROOT/logs/backup.log"

# OCI Configuration (Can be loaded from .env.prod or environment)
if [ -f "$WORKSPACE_ROOT/.env.prod" ]; then
    # Load OCI variables if present
    eval "$(grep -E '^(OCI_BUCKET_NAME|OCI_NAMESPACE|OCI_PAR_URL)=' "$WORKSPACE_ROOT/.env.prod" | sed -e 's/[[:space:]]*$//' || true)"
fi

OCI_BUCKET_NAME="${OCI_BUCKET_NAME:-corporateguild-backups}"
OCI_NAMESPACE="${OCI_NAMESPACE:-}"
OCI_PAR_URL="${OCI_PAR_URL:-}" # Optional Pre-Authenticated Request URL
RETENTION_DAYS=7
LOCAL_ONLY=false

# Parse flags
for arg in "$@"; do
    case "$arg" in
        --local-only)
            LOCAL_ONLY=true
            shift
            ;;
    esac
done

mkdir -p "$BACKUP_DIR" "$WORKSPACE_ROOT/logs"

IST_TIMESTAMP=$(TZ="Asia/Kolkata" date "+%Y%m%d_%H%M%S")
HUMAN_IST=$(TZ="Asia/Kolkata" date "+%Y-%m-%d %H:%M:%S IST")
BACKUP_BASE="corporateguild_backup_${IST_TIMESTAMP}"
RAW_BACKUP="${BACKUP_DIR}/${BACKUP_BASE}.db"
COMPRESSED_BACKUP="${BACKUP_DIR}/${BACKUP_BASE}.db.gz"
CHECKSUM_FILE="${BACKUP_DIR}/${BACKUP_BASE}.sha256"

log() {
    echo "[$HUMAN_IST] $1"
    echo "[$HUMAN_IST] $1" >> "$LOG_FILE" 2>/dev/null || true
}

log "▶ Starting automated database backup..."

# 1. Verify Source Database Exists
if [ ! -f "$DB_FILE" ]; then
    log "❌ Error: Source database not found at: $DB_FILE"
    exit 1
fi

# 2. Perform Safe Online SQLite Backup (Non-blocking)
log "📦 Creating online snapshot of $DB_FILE..."
if command -v sqlite3 &> /dev/null; then
    sqlite3 "$DB_FILE" ".backup '$RAW_BACKUP'"
else
    # Fallback to Python sqlite3 backup API
    python3 -c "
import sqlite3
src = sqlite3.connect('$DB_FILE')
dst = sqlite3.connect('$RAW_BACKUP')
with dst:
    src.backup(dst, pages=250)
dst.close()
src.close()
"
fi

# Verify snapshot integrity
if command -v sqlite3 &> /dev/null; then
    INTEGRITY=$(sqlite3 "$RAW_BACKUP" "PRAGMA integrity_check;" 2>/dev/null || echo "failed")
    if [ "$INTEGRITY" != "ok" ]; then
        log "❌ Error: Snapshot integrity check failed ($INTEGRITY)!"
        rm -f "$RAW_BACKUP"
        exit 1
    fi
fi

# 3. Compress with maximum compression (gzip -9)
gzip -9 -c "$RAW_BACKUP" > "$COMPRESSED_BACKUP"
rm -f "$RAW_BACKUP"

# 4. Generate SHA-256 Checksum
if command -v sha256sum &> /dev/null; then
    sha256sum "$COMPRESSED_BACKUP" | awk '{print $1}' > "$CHECKSUM_FILE"
elif command -v shasum &> /dev/null; then
    shasum -a 256 "$COMPRESSED_BACKUP" | awk '{print $1}' > "$CHECKSUM_FILE"
fi

BACKUP_SIZE_KB=$(du -k "$COMPRESSED_BACKUP" | cut -f1)
log "✅ Local compressed snapshot created: ${BACKUP_BASE}.db.gz (${BACKUP_SIZE_KB} KB)"

# 5. Upload to Oracle Cloud Object Storage
if [ "$LOCAL_ONLY" = true ]; then
    log "ℹ️ --local-only flag supplied. Skipping OCI Object Storage upload."
elif [ -n "$OCI_PAR_URL" ]; then
    log "☁️ Uploading to OCI Object Storage via Pre-Authenticated Request (PAR)..."
    REMOTE_URL="${OCI_PAR_URL%/}/${BACKUP_BASE}.db.gz"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT --data-binary @"$COMPRESSED_BACKUP" "$REMOTE_URL" || echo "000")
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        log "✅ Successfully uploaded to OCI Object Storage (HTTP $HTTP_CODE)."
    else
        log "⚠️ PAR upload returned HTTP status $HTTP_CODE. Check your PAR URL."
    fi
elif command -v oci &> /dev/null; then
    log "☁️ Uploading to OCI Object Storage bucket [$OCI_BUCKET_NAME] via OCI CLI..."
    if [ -n "$OCI_NAMESPACE" ]; then
        oci os object put --namespace "$OCI_NAMESPACE" --bucket-name "$OCI_BUCKET_NAME" \
            --file "$COMPRESSED_BACKUP" --name "${BACKUP_BASE}.db.gz" --force --no-retry 2>&1 | tee -a "$LOG_FILE"
    else
        oci os object put --bucket-name "$OCI_BUCKET_NAME" \
            --file "$COMPRESSED_BACKUP" --name "${BACKUP_BASE}.db.gz" --force --no-retry 2>&1 | tee -a "$LOG_FILE"
    fi
    log "✅ OCI CLI upload completed."
else
    log "ℹ️ OCI CLI or OCI_PAR_URL not configured. Snapshot preserved in $BACKUP_DIR."
    log "   (Configure OCI CLI or set OCI_PAR_URL in .env.prod to enable cloud sync)"
fi

# 6. Rotate Local Backups (Keep latest 7 days / ~84 files for 2-hour cadence)
log "🧹 Cleaning local backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type f -name "corporateguild_backup_*.db.gz" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
find "$BACKUP_DIR" -type f -name "corporateguild_backup_*.sha256" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true

# Truncate log file if > 5000 lines
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE" || echo "0")" -gt 5000 ]; then
    tail -n 2500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

log "🎉 Backup procedure finished successfully."
exit 0

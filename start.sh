#!/usr/bin/env bash
# ==============================================================================
# CorporateGuild - Production India Job Search Portal Local Runner
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================================"
echo "  🚀 Starting CorporateGuild India Job Search Portal & Platform Services"
echo "========================================================================"

# 1. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not installed."
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# 3. Install/verify requirements
echo "📥 Installing / verifying dependencies from requirements.txt..."
python3 -m pip install -q -r requirements.txt

# 4. Redis Node Setup
echo "🔍 Checking local Redis node on 127.0.0.1:6379..."
REDIS_RUNNING=false
if command -v nc &> /dev/null && nc -z 127.0.0.1 6379 2>/dev/null; then
    REDIS_RUNNING=true
fi

if [ "$REDIS_RUNNING" = false ]; then
    echo "⚙️ Local Redis node not detected on port 6379. Initiating node..."
    # Check for redis-server binary
    REDIS_BIN=""
    if command -v redis-server &> /dev/null; then
        REDIS_BIN="redis-server"
    elif [ -f "/opt/homebrew/bin/redis-server" ]; then
        REDIS_BIN="/opt/homebrew/bin/redis-server"
    elif [ -f "/usr/local/bin/redis-server" ]; then
        REDIS_BIN="/usr/local/bin/redis-server"
    fi

    if [ -n "$REDIS_BIN" ]; then
        echo "⚡ Starting native Redis server ($REDIS_BIN)..."
        $REDIS_BIN --daemonize yes 2>/dev/null || $REDIS_BIN &
        sleep 1
    else
        echo "⚡ Starting integrated standalone Redis service on 127.0.0.1:6379..."
        python3 -c "
import threading, time
from app.redis_client import start_embedded_redis_server_if_needed
start_embedded_redis_server_if_needed(6379)
while True:
    time.sleep(3600)
" &
        REDIS_PID=$!
        echo "   (Embedded Redis Service PID: $REDIS_PID)"
        sleep 1
    fi
else
    echo "✅ Redis server is already active on 127.0.0.1:6379."
fi

# 5. Connect or Create SQL Database
mkdir -p data logs
echo "🗄️ Checking / Initializing SQLite Database (data/jobs_portal.db)..."
python3 -c "
from app.database import init_db, get_admin_metrics
init_db()
print('   ✅ Connected to SQL Database. Verified Admin and Metrics initialized.')
"

# 6. Prepopulate real data from ATS APIs & seed pool
echo "📊 Prepopulating real job data from ATS feeds into Redis..."
python3 -c "
import asyncio
from app.services.ingestion_service import get_ingestion_manager
from app.redis_client import get_redis_client

mgr = get_ingestion_manager()
seeded = mgr.seed_initial_jobs()
print(f'   ✅ Seeded {seeded} core verified India tech positions.')

# Quick non-blocking sync attempt
async def sync():
    try:
        await asyncio.wait_for(mgr.run_ingestion_cycle(full_sync=False), timeout=15)
    except Exception as e:
        pass
asyncio.run(sync())

client = get_redis_client()
print(f'   ✅ Redis active job hashes: {len(client.keys(\"*|*\"))}')
"

echo "========================================================================"
echo "  🎉 All Systems Live & Ready!"
echo "  🌐 Job Search Portal:      http://localhost:8000/jobs.html (or http://localhost:8000/)"
echo "  📊 Creator Portfolio:       http://localhost:8000/portfolio.html"
echo "  📩 Contact Us:             http://localhost:8000/contact.html"
echo "  🔒 Privacy Policy:         http://localhost:8000/privacy.html"
echo "  ⚖️ Disclaimer:             http://localhost:8000/disclaimer.html"
echo "  🔐 Admin Dashboard:        http://localhost:8000/admin-dashboard"
echo "     Admin Username:         ${ADMIN_USERNAME:-admin}"
echo "     Admin Password:         (Configured in .env)"
echo "  📁 SQL Database Path:      data/jobs_portal.db"
echo "  ⚡ Redis Service:          127.0.0.1:6379"
echo "  🕒 Anti-Idle KeepAlive:    scripts/oracle_keepalive.sh (Run: ./scripts/setup_cron.sh)"
echo "========================================================================"
echo "🚀 Booting FastAPI Web Server on http://0.0.0.0:8000..."

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# CorporateGuild — India Job Search Portal & Platform

A high-speed, production-grade job discovery and career intelligence platform specifically architected for the Indian technology ecosystem. Integrates non-authenticated public ATS endpoints (Greenhouse, Ashby, SmartRecruiters) from over 900 top employers, stores active jobs in an optimized Redis hash structure with a 7-day TTL, provides semantic search and filtering, and maintains strict Indian Standard Time (IST, UTC+5:30) timestamping.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Quick Start with Docker Compose](#quick-start-with-docker-compose)
3. [Quick Start (Local Python Machine)](#quick-start-local-python-machine)
4. [Production Deployment on Oracle Cloud ($0 Always Free)](#production-deployment-on-oracle-cloud-0-always-free)
5. [Automated 2-Hour SQLite Database Backups](#automated-2-hour-sqlite-database-backups)
6. [Page URLs & Navigation](#page-urls--navigation)
7. [Admin Dashboard & Credentials](#admin-dashboard--credentials)
8. [Viewing & Managing Redis Data](#viewing--managing-redis-data)
9. [Viewing & Managing SQLite Database](#viewing--managing-sqlite-database)
10. [System Architecture](#system-architecture)
11. [Configuration (`application.yml` & `.env`)](#configuration-applicationyml--env)

---

## Key Features

- **Real-Time ATS Ingestion**: Background scheduler batch-pulls postings from 918+ configured companies every 10 minutes across Greenhouse, Ashby, and SmartRecruiters.
- **Strict India Filtering**: Intelligent token and city matching (Bengaluru, Gurugram, Pune, Mumbai, Hyderabad, Chennai, Noida, Delhi NCR, Remote - India).
- **Indian Standard Time (IST)**: All timestamps are normalized to IST (`Asia/Kolkata`) with human-friendly relative offsets (e.g. `2h ago`, `Yesterday at 4:30 PM IST`).
- **Redis Hash Architecture**:
  - **Hash**: `{company_name}|{role_name}`
  - **Field**: Posting Timestamp in IST
  - **Value**: Structured JSON with up to 5 smart tags, workplace type, experience level, and direct application link.
  - **TTL**: 7 days with automatic pruning of older records.
- **Fast Semantic Search**:
  - Search by Company Name or Role Name with live autocomplete from fixed sets in `resources/job_urls.xlsx`.
  - Semantic synonym matching (e.g. `Software Engineer` matches `SDE`, `SWE`, `Backend Developer`).
  - **Locked Filter Flow**: Filters are unlocked only after an initial search term is selected and results are populated.
- **Search Quota & Guest Tracking**:
  - Up to 5 free searches for guests (tracked by client IP in SQLite).
  - Prompts registration / login on the 6th search.
  - Email OTP-based signup with automatic login, and password-based login.
  - Persistent sessions via HTTP-only cookies (`cg_session`).
- **Responsive Modern UI**:
  - Clean, professional light SaaS design system with cohesive styling, high-contrast typography, and modern cards across all pages.
  - Comprehensive media queries ensuring flawless alignment across mobile, tablet, desktop, ultra-wide, and print.
  - Standardized top navigation bar ordering across all pages: `Home` -> `Job Portal` -> `Portfolio & Media Kit` -> `Contact` -> `Privacy` -> `Disclaimer`.
  - Natural internal backlinks linking job searches, creator media kit, contact inquiries, privacy, and disclaimer across all pages.
- **Dedicated Admin Control Center**: Live metrics, user directory telemetry, and on-demand ingestion trigger.

---

## Quick Start with Docker Compose

CorporateGuild is fully containerized with multi-arch Docker support (x86_64 and ARM64 / Apple Silicon / Ampere). You can spin up the application and Redis with a single command:

```bash
# 1. Build and run the stack
docker compose up -d --build

# 2. Check service health
docker compose ps

# 3. Follow application logs
docker compose logs -f web
```

- **Web Application**: [http://localhost:8000](http://localhost:8000)
- **Data Persistence**: SQLite database is automatically persisted to `./data/jobs_portal.db`
- **Redis Cache**: Redis 7 Alpine with append-only persistence
- **Stop stack**: `docker compose down`

---

## Quick Start (Local Python Machine)

### Automated Single-Command Startup
The included `start.sh` script manages environment creation, dependency installation, Redis node activation, database initialization, real ATS pre-population, and boots the FastAPI server:

```bash
chmod +x start.sh
./start.sh
```

### Manual Step-by-Step Startup

1. **Clone or Navigate to Repository**:
   ```bash
   cd /Users/iamrj846/Desktop/iamrj846.github.io
   ```

2. **Create and Activate Python Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Redis**:
   - If Redis is installed natively:
     ```bash
     redis-server --daemonize yes
     ```
   - If Redis is not installed, the platform automatically starts an embedded standalone Redis service on `127.0.0.1:6379`.

5. **Initialize Database and Seed Jobs**:
   ```bash
   python3 -c "from app.database import init_db; init_db()"
   python3 -c "from app.services.ingestion_service import get_ingestion_manager; get_ingestion_manager().seed_initial_jobs()"
   ```

6. **Start the FastAPI Server**:
   ```bash
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## Production Deployment on Oracle Cloud ($0 Always Free)

CorporateGuild is ready for enterprise-grade production deployment on **Oracle Cloud Infrastructure (Always Free)** with zero hosting costs, automated Let's Encrypt SSL via Caddy reverse proxy, automated 2-hour SQLite backups, and automated GitHub Actions CI/CD on push to `master`.

> [!TIP]
> For the master deep-dive document covering APM monitoring, email alarms, and tenancy architecture, see **[DEPLOYMENT_GUIDE.md](file:///Users/iamrj846/Desktop/iamrj846.github.io/DEPLOYMENT_GUIDE.md)**.

### Complete Step-by-Step Server Setup Guide

#### Step 1: Connect to your Oracle Cloud VM
Fix permissions on your private key (required by SSH):
```bash
chmod 400 /path/to/your/ssh-key.key
```
Connect to your VM via SSH:
```bash
ssh -i /path/to/your/ssh-key.key ubuntu@<YOUR_ORACLE_PUBLIC_IP>
```

---

#### Step 2: Configure 2 GB Swap Memory (Essential for 1 GB AMD instance)
Oracle gives 47 GB fast SSD storage. Adding 2 GB of swap memory gives your VM 3 GB of total working memory, preventing any out-of-memory issues:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

---

#### Step 3: Open Ubuntu Host Firewall for Web Traffic
Oracle Cloud Ubuntu images block ports 80 and 443 in `iptables` by default. Run this to allow web traffic:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p udp --dport 443 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || sudo iptables-save | sudo tee /etc/iptables/rules.v4
```
*(Also ensure Port 80 and 443 TCP/UDP ingress rules are added to your OCI VCN Security List).*

---

#### Step 4: Install Docker, Docker Compose & Git
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git sqlite3
sudo usermod -aG docker ubuntu
newgrp docker
```
Verify installation:
```bash
docker --version && docker compose version
```

---

#### Step 5: Clone Repository & Configure Environment
```bash
cd /home/ubuntu
git clone https://github.com/iamrj846/iamrj846.github.io.git
cd iamrj846.github.io

# Create production environment configuration
cp .env.example .env.prod
nano .env.prod
```
Update `.env.prod`:
```ini
APP_ENV=production
ADMIN_USERNAME=iamrj846
ADMIN_PASSWORD=your_secure_password
COOKIE_SECRET=create_a_random_32_character_string_here
SECRET_KEY=create_another_random_32_character_string_here
DATABASE_PATH=/app/data/jobs_portal.db
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL_SECONDS=604800
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=False
TIMEZONE=Asia/Kolkata
SYNC_INTERVAL_MINUTES=10
```

---

#### Step 6: Launch Production Stack via Docker Compose
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Inspect container health:
```bash
docker compose -f docker-compose.prod.yml ps
```
Follow real-time Caddy SSL & web logs:
```bash
docker compose -f docker-compose.prod.yml logs -f caddy
```

---

#### Step 7: Configure Namecheap Custom Domain (`corporateguild.com`)
1. In your [Namecheap Dashboard](https://ap.www.namecheap.com/) &rarr; Domain List &rarr; Click **Manage** next to `corporateguild.com`.
2. Click **Advanced DNS** tab.
3. Remove any old GitHub Pages records (e.g. `185.199.108.153`, etc.).
4. Add the following records:
   - **A Record**: Host `@` &rarr; Value `<YOUR_ORACLE_PUBLIC_IP>` (TTL: Automatic or 1 min)
   - **CNAME Record**: Host `www` &rarr; Value `corporateguild.com.` (TTL: Automatic or 1 min)
5. Caddy will automatically detect the domain, negotiate with Let's Encrypt, issue trusted SSL certificates, and serve HTTPS with A+ security grade!

---

#### Step 8: Setup Automated 2-Hour SQLite Database Backups
To ensure zero data loss, backups run every 2 hours using SQLite's safe online `.backup` API, compressed with `gzip -9`, and uploaded to Oracle Cloud Object Storage:

1. In OCI Console: **Storage &rarr; Buckets &rarr; Create Bucket** named `corporateguild-backups` (Tier: Standard, 10 GB free).
2. Click the bucket &rarr; **Pre-Authenticated Requests** &rarr; **Create Pre-Authenticated Request** (Access: Permit object writes) &rarr; Copy the URL.
3. Add the URL to your `.env.prod`:
   ```ini
   OCI_PAR_URL=https://objectstorage.<region>.oraclecloud.com/p/.../n/<namespace>/b/corporateguild-backups/o/
   ```
4. Schedule backup in crontab (`crontab -e`):
   ```cron
   0 */2 * * * /bin/bash /home/ubuntu/iamrj846.github.io/scripts/backup_to_oci.sh >> /home/ubuntu/iamrj846.github.io/logs/backup.log 2>&1
   ```
5. **Disaster Recovery / Restore from Snapshot**:
   ```bash
   # Restore from latest verified snapshot
   ./scripts/restore_from_oci.sh
   ```

---

#### Step 9: Setup 10-Minute Anti-Idle Keep-Alive Cron Job
Oracle Cloud reclaims idle VMs if 7-day average CPU falls below 20%. The included keep-alive utility runs a safe 15-second CPU burst and health ping every 10 minutes:

Add to crontab (`crontab -e`):
```cron
*/10 * * * * /bin/bash /home/ubuntu/iamrj846.github.io/scripts/oracle_keepalive.sh >> /home/ubuntu/iamrj846.github.io/logs/keepalive.log 2>&1
```

---

#### Step 10: Setup Automated GitHub Actions CI/CD
Deploy automatically on every `git push origin master`:
1. In your GitHub repo: **Settings &rarr; Secrets and variables &rarr; Actions &rarr; New repository secret**.
2. Add the following secrets:
   - `OCI_VM_HOST`: Your Oracle VM Public IP (e.g. `129.154.43.222`)
   - `OCI_VM_USER`: `ubuntu`
   - `OCI_SSH_KEY`: Contents of your private key (`ssh-key-2026-09-13.key`)
3. Pushing any code to `master` will trigger `.github/workflows/deploy.yml` and deploy live in under 60 seconds with zero downtime!

---

## Page URLs & Navigation

| Route | File Location | Description |
| :--- | :--- | :--- |
| `http://localhost:8000/` | `frontend/index.html` | **Homepage**: Primary India Job Search Portal with breadcrumbs & real-time IST updates |
| `http://localhost:8000/jobs` | `frontend/jobs.html` | Direct Job Search Portal route |
| `http://localhost:8000/portfolio` | `frontend/portfolio.html` | CorporateGuild Creator Media Kit & Portfolio (242K+ Reach) |
| `http://localhost:8000/home` | `frontend/index.html` | Homepage alias |
| `http://localhost:8000/contact` | `frontend/contact.html` | Contact page with verified social cards (60K Facebook, 152K Instagram) |
| `http://localhost:8000/privacy` | `frontend/privacy.html` | Privacy Policy with data usage transparency |
| `http://localhost:8000/disclaimer` | `frontend/disclaimer.html` | Career opportunity aggregator disclaimer |
| `http://localhost:8000/admin-dashboard` | `frontend/admin.html` | Admin Control Center & Telemetry Analytics |

---

## Admin Dashboard & Credentials

- **URL**: [http://localhost:8000/admin-dashboard](http://localhost:8000/admin-dashboard) (configured in `application.yml`)
- **Username**: `iamrj846`
- **Password**: `iamrj846`

### Admin Capabilities:
- View real-time KPI metrics: Total Registered Users, Active Sessions, Total Searches, Total Clicks, Total Visits.
- Inspect the live User Directory table with per-user telemetry (Visits, Clicks, Searches, Last Login IST, IP).
- Monitor Redis hash counts and memory utilization.
- Trigger manual ATS ingestion on-demand via the **"⚡ Trigger ATS Ingestion"** button.

---

## Viewing & Managing Redis Data

The system uses standard Redis on `127.0.0.1:6379`.

### 1. Using `redis-cli` in Terminal
Connect to the local Redis instance:
```bash
redis-cli
```

#### Common Inspection Commands:
```redis
# Check server health
PING

# List all job hashes (pattern: Company|Role)
KEYS "*|*"

# Count total job hashes
DBSIZE

# Inspect a specific company & role hash
HGETALL "Stripe|Software Engineer, Backend"

# Inspect all timestamps in a hash
HKEYS "Stripe|Software Engineer, Backend"

# Check TTL (time-to-live in seconds, should be <= 604800 for 7 days)
TTL "Stripe|Software Engineer, Backend"

# View memory stats
INFO memory
```

### 2. Inspecting Redis via Python
Run this command in terminal to view a summary of stored jobs:
```bash
.venv/bin/python -c "
import json
from app.redis_client import get_redis_client

r = get_redis_client()
keys = r.keys('*|*')
print(f'Total Redis Hashes: {len(keys)}')
for k in keys[:5]:
    hdata = r.hgetall(k)
    print(f'\nHash: {k} (Entries: {len(hdata)})')
    for ts, val in list(hdata.items())[:1]:
        data = json.loads(val)
        print(f'  - Time IST: {data.get(\"posted_timestamp_ist\")}')
        print(f'  - Location: {data.get(\"location\")}')
        print(f'  - Tags:     {data.get(\"tags\")}')
"
```

---

## Viewing & Managing SQLite Database

The SQLite database file is located at `data/jobs_portal.db`.

### 1. Using the `sqlite3` CLI
```bash
sqlite3 data/jobs_portal.db
```

#### Useful Queries:
```sql
-- View all database tables (users, jobs, site_telemetry, guest_quotas, user_activity_logs)
.tables

-- View registered users (iamrj846 admin)
SELECT id, name, email, is_admin, total_visits, total_clicks, total_searches, last_login 
FROM users;

-- View persistent jobs in SQLite
SELECT COUNT(*) AS total_jobs FROM jobs WHERE is_active = 1;
SELECT id, title, company, location, workplace_type, experience_level, posted_at FROM jobs LIMIT 5;

-- View real-time site telemetry (clicks on buttons/links, visits, searches)
SELECT event_type, COUNT(*) AS event_count FROM site_telemetry GROUP BY event_type;
SELECT session_id, event_type, target_element, target_label, page_path, timestamp 
FROM site_telemetry ORDER BY id DESC LIMIT 10;

-- View guest search quota records by IP
SELECT * FROM guest_quotas;

-- Exit sqlite
.quit
```

### 2. Inspecting SQLite via Python
```bash
.venv/bin/python -c "
from app.database import get_admin_metrics, get_all_users, get_total_jobs_in_db

print('Metrics:', get_admin_metrics())
print('Total Jobs in SQLite:', get_total_jobs_in_db())
print('\nUsers:')
for u in get_all_users():
    print(f\"#{u['id']} | {u['name']} | {u['email']} | Visits: {u['total_visits']} | Clicks: {u['total_clicks']} | Searches: {u['total_searches']}\")
"
```

---

## Environment Variables & Secrets (`.env.local` & `.env.prod`)

Sensitive credentials and environment overrides are strictly isolated between local development and production environments:

- **Local Development**: Loaded from `.env.local` by default (when `APP_ENV=local` or unset).
- **Production Deployment**: Loaded from `.env.prod` (or `.env.production`) when `APP_ENV=production`.
- **Git Safety**: All `.env`, `.env.*`, `.env.local`, `.env.prod` files are included in `.gitignore` to prevent any secret leaks.
- **Reference Template**: See `.env.example` for all configurable environment variables.

### Supported Variables:
- `APP_ENV`: Environment stage (`local` or `production`)
- `APP_HOST`: Host interface (`127.0.0.1` locally, `0.0.0.0` in production)
- `APP_PORT`: Server port (default: `8000`)
- `APP_DEBUG`: Debug mode toggle (`True` locally, `False` in production)
- `ADMIN_USERNAME`: Admin login username (default: `iamrj846`)
- `ADMIN_PASSWORD`: Admin login password (default: `iamrj846`)
- `SECRET_KEY`: Application cryptographic secret key
- `COOKIE_SECRET`: Secret key for session cookie encryption
- `DATABASE_PATH`: SQLite database file path (default: `data/jobs_portal.db`)
- `REDIS_HOST`: Redis host (default: `127.0.0.1`)
- `REDIS_PORT`: Redis port (default: `6379`)

---

## System Architecture

```
                                  ┌────────────────────────┐
                                  │   resources/           │
                                  │   job_urls.xlsx        │
                                  └───────────┬────────────┘
                                              │ (918+ Endpoints)
                                              ▼
┌──────────────────────────────────────────────────────────┐
│              CorporateGuild Ingestion Engine             │
│  - Greenhouse API: boards-api.greenhouse.io              │
│  - Ashby API:      api.ashbyhq.com                       │
│  - SmartRecruiters: api.smartrecruiters.com              │
│  - Rate Limiter & Concurrency Pool (15 workers)          │
│  - India Location Detector & IST Timestamp Converter     │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                   Redis Storage Engine                   │
│  - Hash:  {company_name}|{role_name}                     │
│  - Field: Posting Timestamp (IST)                        │
│  - Value: JSON (Tags, Workplace, Exp, Apply Link)        │
│  - TTL:   7 Days (Rolling Stale Pruning)                 │
└─────────────────────────────▲────────────────────────────┘
                              │
                    Query / Semantic Match
                              │
┌─────────────────────────────┴────────────────────────────┐
│                    FastAPI Backend                       │
│  - /api/jobs/suggest: Company & Role Autocomplete        │
│  - /api/jobs/search:  Redis Hash Search & Filter Pipeline│
│  - /api/jobs/click:   Telemetry Click Tracker            │
│  - /api/auth/*:       Guest Quota (5 free) & Email OTP   │
│  - /api/admin/*:      Admin Stats & Manual Sync          │
└─────────────────────────────▲────────────────────────────┘
                              │
                    Responsive Dark UI
                              │
┌─────────────────────────────┴────────────────────────────┐
│                  Modern Frontend Client                  │
│  - Dark Gradient, Glassmorphism & Neomorphic 3D Cards    │
│  - 3 Search Modes (Company, Role, Others)                │
│  - Locked Filter Panel (Activates on Initial Result)     │
│  - Shareable Query URL Params (history.pushState)        │
│  - Cookie Consent Banner & Modals                        │
└──────────────────────────────────────────────────────────┘
```

---

## Configuration (`application.yml`)

The platform is dynamically configured via `application.yml`:

```yaml
app:
  name: "CorporateGuild Job Search Portal"
  port: 8000
  timezone: "Asia/Kolkata"

resources:
  excel_path: "resources/job_urls.xlsx"
  master_sheet: "Master ATS Directory (1000+)"

redis:
  host: "127.0.0.1"
  port: 6379
  ttl_seconds: 604800 # 7 days

database:
  engine: "sqlite"
  path: "data/jobs_portal.db"

admin:
  dashboard_url: "/admin-dashboard"
  username: "iamrj846"
  plain_password_fallback: "iamrj846"

scheduler:
  sync_interval_minutes: 10
  lookback_minutes: 10
  max_concurrent_requests: 15

guest:
  free_search_limit: 5
```

---

## Oracle Cloud VM Anti-Idle Keep-Alive Cron Job

Oracle Cloud Free Tier automatically reclaims or stops VMs if the 95th percentile of CPU utilization falls below 20% over 7 days. This can lead to unexpected downtime when new traffic attempts to connect.

To prevent idle scale-down without degrading web performance, the platform includes an automated keep-alive utility:

### 1. Manual Keep-Alive Execution
```bash
bash scripts/oracle_keepalive.sh
```
- Performs a local API ping to `http://127.0.0.1:8000/` ensuring memory and network activity.
- Executes a safe, controlled 15-second CPU computation (hashing and floating point) safely above the 20% threshold.
- Appends an IST timestamped log entry to `logs/keepalive.log`.

### 2. Setting Up the 10-Minute Cron Job
Run the automated installer:
```bash
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh
```
This automatically configures the system crontab:
```cron
*/10 * * * * /bin/bash /home/ubuntu/iamrj846.github.io/scripts/oracle_keepalive.sh >> /home/ubuntu/iamrj846.github.io/logs/keepalive.log 2>&1
```

### 3. Monitoring Heartbeat Logs
```bash
tail -f logs/keepalive.log
```

---

## License & Attribution

© 2026 CorporateGuild. All rights reserved. Job postings are aggregated from verified public ATS career endpoints for informational purposes.

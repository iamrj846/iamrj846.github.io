# CorporateGuild - Production Deployment & Operations Guide
## Oracle Cloud Infrastructure (Always Free) + Docker Compose + Automated Backups + CI/CD + Namecheap SSL

This guide provides end-to-end instructions to deploy CorporateGuild to **Oracle Cloud Infrastructure (OCI) Always Free Tier** at **\$0/month forever**, orchestrating the FastAPI backend, Redis cache, and Caddy reverse proxy with automated Let's Encrypt SSL, automated 2-hour SQLite backups to OCI Object Storage, and push-to-deploy GitHub Actions CI/CD.

---

## Table of Contents
1. [Always Free Zero-Cost Guarantee & Architecture](#1-always-free-zero-cost-guarantee--architecture)
2. [Local Testing with Docker Compose](#2-local-testing-with-docker-compose)
3. [Oracle Cloud Infrastructure Setup (Compute & IP)](#3-oracle-cloud-infrastructure-setup-compute--ip)
4. [VCN Security Lists & Host Firewall Configuration](#4-vcn-security-lists--host-firewall-configuration)
5. [Server Setup & Repository Provisioning](#5-server-setup--repository-provisioning)
6. [OCI Object Storage Setup for 2-Hour Database Backups](#6-oci-object-storage-setup-for-2-hour-database-backups)
7. [Automated Backup & Disaster Recovery (Restore)](#7-automated-backup--disaster-recovery-restore)
8. [Connecting Namecheap Custom Domain (`corporateguild.com`)](#8-connecting-namecheap-custom-domain-corporateguildcom)
9. [Automated SSL / HTTPS with Let's Encrypt & Caddy](#9-automated-ssl--https-with-lets-encrypt--caddy)
10. [Decommissioning GitHub Pages](#10-decommissioning-github-pages)
11. [Preventing Oracle VM Inactivity Idle Scale-Down](#11-preventing-oracle-vm-inactivity-idle-scale-down)
12. [Free OCI Monitoring, Logging & APM](#12-free-oci-monitoring-logging--apm)
13. [Setting Up Automated GitHub Actions CI/CD](#13-setting-up-automated-github-actions-cicd)
14. [Operations, Maintenance & Troubleshooting Cheat Sheet](#14-operations-maintenance--troubleshooting-cheat-sheet)

---

## 1. Always Free Zero-Cost Guarantee & Architecture

Oracle Cloud provides one of the most generous Always Free tiers in the industry. As long as you stay within the following allocations, your monthly bill will strictly be **\$0.00**:

| Resource | Always Free Allocation | CorporateGuild Usage | Cost |
| :--- | :--- | :--- | :--- |
| **Compute (Ampere A1 Flex)** | Up to 4 OCPUs, 24 GB RAM | 2 OCPUs, 12 GB RAM (or 1 OCPU, 6 GB) | **\$0.00** |
| **Compute (AMD E2.1.Micro)** | 2 VMs, 1/8 OCPU, 1 GB RAM each | Alternative fallback | **\$0.00** |
| **Boot Volume** | 200 GB total across tenancy | 50 GB Boot Volume | **\$0.00** |
| **Public IPv4 Address** | 1 Reserved Public IP | 1 Reserved Public IP | **\$0.00** |
| **Object Storage** | 10 GB Standard + 50,000 requests/mo | ~50 MB database backups (360 req/mo) | **\$0.00** |
| **Outbound Data Transfer** | 10 TB per month | ~20–50 GB/month | **\$0.00** |
| **OCI Monitoring & Logging**| Included metrics, alarms & logs | System metrics & custom logs | **\$0.00** |

```
                              [Internet / Users]
                                      │
                         (corporateguild.com:80/443)
                                      ▼
                        ┌───────────────────────────┐
                        │    Oracle Cloud VM        │
                        │ ┌───────────────────────┐ │
                        │ │     Caddy Proxy       │ │  (Auto Let's Encrypt SSL,
                        │ │  (ports 80, 443, UDP) │ │   Gzip/Zstd, Sec Headers)
                        │ └───────────┬───────────┘ │
                        │             │ :8000       │
                        │             ▼             │
                        │ ┌───────────────────────┐ │
                        │ │   FastAPI Backend     │ │  (Job Search, Autocomplete,
                        │ │   + Frontend Assets   │ │   Auth, Telemetry, Ingestion)
                        │ └───────┬───────────┬───┘ │
                        │         │           │     │
                        │         ▼           ▼     │
                        │   ┌───────────┐ ┌────────┐│
                        │   │  SQLite   │ │ Redis  ││
                        │   │Database   │ │ Cache  ││
                        │   └─────┬─────┘ └────────┘│
                        └─────────┼─────────────────┘
                                  │
                 Cron: Every 2h   │ Safe Online .backup + gzip
                                  ▼
                 ┌──────────────────────────────────┐
                 │  OCI Object Storage Bucket       │
                 │  (corporateguild-backups)        │
                 │  7-Day Rotating Snapshots        │
                 └──────────────────────────────────┘
```

---

## 2. Local Testing with Docker Compose

Before pushing to the VM, test the full stack locally on your computer.

### Step 2.1: Start Docker Desktop
Ensure Docker Desktop is running on your Mac. You can launch it from Applications or Spotlight.

### Step 2.2: Launch Local Stack
From the repository root:
```bash
# Build and run containers in background
docker compose up -d --build

# Inspect container status
docker compose ps
```

You should see two healthy containers:
- `corporateguild_web` running on port `8000`
- `corporateguild_redis` running on port `6379`

### Step 2.3: Verify Local Endpoints
Test the running application using `curl` or open your browser at [http://localhost:8000](http://localhost:8000):
```bash
# 1. Health check & current user info
curl -s http://localhost:8000/api/auth/me

# 2. Test Role Autocomplete
curl -s "http://localhost:8000/api/jobs/suggest?mode=role&q=soft"

# 3. Test Company Autocomplete
curl -s "http://localhost:8000/api/jobs/suggest?mode=company&q=str"

# 4. Test Job Search
curl -s "http://localhost:8000/api/jobs/search?page=1&page_size=3"

# 5. Check Redis Client Health
docker compose exec redis redis-cli ping
```

### Step 2.4: Test the 2-Hour SQLite Backup Script Locally
Run the backup script with the `--local-only` flag to verify local snapshot creation, gzip compression, and SHA-256 generation:
```bash
./scripts/backup_to_oci.sh --local-only
```
Check the output in `backups/`:
```bash
ls -lh backups/
```

### Step 2.5: Test Local Database Restoration
Test restoring the snapshot to ensure integrity validation works:
```bash
./scripts/restore_from_oci.sh
```

### Step 2.6: Stop Local Stack
```bash
docker compose down
```

---

## 3. Oracle Cloud Infrastructure Setup (Compute & IP)

### Step 3.1: Sign Up / Sign In
1. Visit [cloud.oracle.com](https://cloud.oracle.com) and create an account or sign in.
2. Select your nearest Home Region (e.g., `ap-mumbai-1`, `ap-hyderabad-1`, `us-ashburn-1`, `eu-frankfurt-1`). *Note: Always Free resources are anchored to your Home Region.*

### Step 3.2: Create Compute Instance
1. In the OCI Console, navigate to: **Menu &rarr; Compute &rarr; Instances &rarr; Create Instance**.
2. **Name**: `corporateguild-prod`
3. **Placement**: Select any Availability Domain that displays the **Always Free Eligible** tag.
4. **Image and Shape**:
   - **Image**: Click **Change image** &rarr; Select **Canonical Ubuntu 22.04 Minimal** or **Ubuntu 22.04 LTS** (or **Oracle Linux 8/9**).
   - **Shape**:
     - *Recommended Choice*: **Ampere ARM (VM.Standard.A1.Flex)**. Allocate **2 OCPUs** and **12 GB RAM** (Always Free up to 4 OCPUs / 24 GB).
     - *Alternative Choice*: **AMD (VM.Standard.E2.1.Micro)**. 1 OCPU, 1 GB RAM (Always Free).
5. **Networking**:
   - Create new Virtual Cloud Network (VCN) & public subnet (or select existing default VCN).
   - Check: **Assign a public IPv4 address**.
6. **Add SSH Keys**:
   - Select **Generate a key pair for me** (and download private + public key files), OR paste your existing `~/.ssh/id_rsa.pub`.
7. **Boot Volume**:
   - Default is 46.6 GB (Within the 200 GB Always Free tier).
8. Click **Create**. The instance will be active within 60 seconds.

### Step 3.3: Reserve a Permanent Public IPv4 Address (Always Free)
To prevent your IP from changing if the VM is rebooted:
1. Navigate to: **Networking &rarr; IP Management &rarr; Reserved Public IPs**.
2. Click **Reserve Public IP Address**.
3. Name: `corporateguild-ip`. Select **Always Free Eligible**.
4. Once created, click the three dots &rarr; **Assign IP**.
5. Select your `corporateguild-prod` instance VNIC.
6. Note down your static public IP (e.g., `129.154.xx.xx`).

---

## 4. VCN Security Lists & Host Firewall Configuration

By default, Oracle Cloud blocks incoming traffic on all ports except 22 (SSH). You must open ports 80 and 443 in both the **VCN Security List** (cloud level) and the **Host OS Firewall** (VM level).

### Step 4.1: OCI VCN Ingress Rules (Cloud Level)
1. In the OCI Console, navigate to: **Networking &rarr; Virtual Cloud Networks**.
2. Click your VCN &rarr; **Security Lists** &rarr; Click **Default Security List for `<vcn-name>`**.
3. Under **Ingress Rules**, click **Add Ingress Rules**:
   - **Rule 1 (HTTP)**:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: `TCP`
     - Destination Port Range: `80`
     - Description: `CorporateGuild HTTP (Cert validation & redirect)`
   - **Rule 2 (HTTPS TCP)**:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: `TCP`
     - Destination Port Range: `443`
     - Description: `CorporateGuild HTTPS Web Traffic`
   - **Rule 3 (HTTPS UDP for HTTP/3 QUIC)**:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: `UDP`
     - Destination Port Range: `443`
     - Description: `CorporateGuild HTTP/3 QUIC Traffic`
4. Click **Add Ingress Rules**.

### Step 4.2: Host OS Firewall (VM Level)
SSH into your Oracle VM:
```bash
ssh -i /path/to/your/private_key ubuntu@<ORACLE_PUBLIC_IP>
```
*(If using Oracle Linux, replace `ubuntu` with `opc`)*

Run the following commands to open ports:

**For Ubuntu (UFW / iptables):**
```bash
# Allow HTTP, HTTPS, and SSH through UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp
sudo ufw --force enable

# Oracle Cloud Ubuntu images include strict iptables rules by default.
# Ensure iptables explicitly permits ports 80 and 443:
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p udp --dport 443 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

**For Oracle Linux (firewalld):**
```bash
sudo firewall-cmd --zone=public --permanent --add-port=80/tcp
sudo firewall-cmd --zone=public --permanent --add-port=443/tcp
sudo firewall-cmd --zone=public --permanent --add-port=443/udp
sudo firewall-cmd --reload
```

---

## 5. Server Setup & Repository Provisioning

### Step 5.1: Install Docker & Docker Compose on Oracle VM
Inside your SSH session:
```bash
# Update package lists
sudo apt-get update && sudo apt-get upgrade -y

# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg lsb-release sqlite3 git

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow current user to run Docker without sudo
sudo usermod -aG docker $USER
newgrp docker
```

Verify Docker works:
```bash
docker --version && docker compose version
```

### Step 5.2: Clone Repository on the VM
```bash
cd /home/ubuntu
git clone https://github.com/iamrj846/iamrj846.github.io.git
cd iamrj846.github.io
```

### Step 5.3: Configure Production Environment File
Copy `.env.example` to `.env.prod`:
```bash
cp .env.example .env.prod
```
Edit `.env.prod`:
```bash
nano .env.prod
```
Fill in production values:
```ini
APP_ENV=production
ADMIN_USERNAME=iamrj846
ADMIN_PASSWORD=your_strong_admin_password
COOKIE_SECRET=change_this_to_a_random_64_character_secret_string
SECRET_KEY=change_this_to_another_random_64_character_secret_string

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

# OCI Object Storage Backup Settings
OCI_BUCKET_NAME=corporateguild-backups
OCI_PAR_URL=https://objectstorage.<region>.oraclecloud.com/p/.../n/<namespace>/b/corporateguild-backups/o/
```

---

## 6. OCI Object Storage Setup for 2-Hour Database Backups

Oracle Cloud gives you **10 GB of Standard Object Storage** and **50,000 monthly API requests** for free. Backups every 2 hours total 360 requests/month (less than 1% of your quota).

### Step 6.1: Create Object Storage Bucket
1. In the OCI Console, navigate to: **Storage &rarr; Buckets**.
2. Click **Create Bucket**.
3. **Bucket Name**: `corporateguild-backups`
4. **Default Storage Tier**: Select **Standard** *(Do NOT select Archive)*.
5. Check: **Emit Object Events** (Optional, for notifications).
6. Click **Create**.

### Step 6.2: Create Pre-Authenticated Request (PAR) for Simple Zero-Config Uploads
A Pre-Authenticated Request provides a secure URL that allows the backup script to upload snapshots with simple `curl`, requiring no OCI CLI or complex signing keys.
1. Click on the bucket name: `corporateguild-backups`.
2. Under **Resources** (left sidebar), click **Pre-Authenticated Requests**.
3. Click **Create Pre-Authenticated Request**.
4. **Name**: `backup-uploader`
5. **Pre-Authenticated Request Target**: Select **Bucket**.
6. **Access Type**: Select **Permit object writes** (or **Permit object reads and writes** if you also want easy restore downloads).
7. **Expiration**: Choose 5 years in the future (e.g., 2031).
8. Click **Create Pre-Authenticated Request**.
9. **CRITICAL**: Copy the **Pre-Authenticated Request URL** immediately (Oracle will not show it again).
   It will look like:
   `https://objectstorage.ap-mumbai-1.oraclecloud.com/p/aBcDeFg.../n/yournamespace/b/corporateguild-backups/o/`
10. Paste this URL into your VM's `.env.prod` under `OCI_PAR_URL=`.

---

## 7. Automated Backup & Disaster Recovery (Restore)

### Step 7.1: Schedule 2-Hour Backup Cron Job
Run the automated backup script every 2 hours on the host VM:
```bash
# Open crontab
crontab -e
```
Add the following line:
```cron
# CorporateGuild Automated SQLite Backup to OCI Object Storage (Every 2 Hours)
0 */2 * * * /bin/bash /home/ubuntu/iamrj846.github.io/scripts/backup_to_oci.sh >> /home/ubuntu/iamrj846.github.io/logs/backup.log 2>&1
```
Save and exit.

### Step 7.2: Test Manual Backup
Trigger a test backup to confirm it uploads to Oracle Cloud Object Storage:
```bash
/home/ubuntu/iamrj846.github.io/scripts/backup_to_oci.sh
```
Check `logs/backup.log` to confirm:
```bash
cat /home/ubuntu/iamrj846.github.io/logs/backup.log | tail -n 10
```
In your OCI Console under `corporateguild-backups`, you will see your new `.db.gz` and `.sha256` snapshot files!

### Step 7.3: Disaster Recovery / Restoring Database
If you ever need to restore your database:
```bash
# 1. Restore from latest snapshot
/home/ubuntu/iamrj846.github.io/scripts/restore_from_oci.sh

# 2. Or restore from a specific snapshot file
/home/ubuntu/iamrj846.github.io/scripts/restore_from_oci.sh /home/ubuntu/iamrj846.github.io/backups/corporateguild_backup_20260913_120000.db.gz
```
The script will:
- Check database integrity (`PRAGMA integrity_check`)
- Create an emergency safety copy of the current live database
- Atomically restore the database
- Automatically reload the `web` container

---

## 8. Connecting Namecheap Custom Domain (`corporateguild.com`)

### Step 8.1: Log into Namecheap
1. Go to [namecheap.com](https://www.namecheap.com) and log into your dashboard.
2. Under **Domain List**, locate `corporateguild.com` and click **Manage**.
3. Click the **Advanced DNS** tab.

### Step 8.2: Configure DNS Records
Add or update the following DNS records:

| Type | Host | Value | TTL |
| :--- | :--- | :--- | :--- |
| **A Record** | `@` | `<YOUR_ORACLE_PUBLIC_IP>` (e.g., `129.154.xx.xx`) | Automatic (or 1 min) |
| **CNAME Record** | `www` | `corporateguild.com.` | Automatic (or 1 min) |

> [!WARNING]
> Remove any old GitHub Pages A records (such as `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`) or old URL Redirect Records. Only your Oracle Public IP should be present for `@`.

### Step 8.3: Verify DNS Propagation
From your terminal:
```bash
dig +short corporateguild.com
# Should return your Oracle Public IP!
```

---

## 9. Automated SSL / HTTPS with Let's Encrypt & Caddy

CorporateGuild uses **Caddy 2** as its reverse proxy. Caddy handles:
- Zero-touch Let's Encrypt / ZeroSSL TLS certificate procurement and auto-renewal.
- Automatic HTTP &rarr; HTTPS 301 redirection.
- `www.corporateguild.com` &rarr; `https://corporateguild.com` canonical redirect.
- HTTP/2 and modern HTTP/3 (QUIC) support over UDP 443.
- HSTS, MIME sniffing protection, Clickjacking protection headers.

### Step 9.1: Start Production Stack
On the Oracle VM:
```bash
cd /home/ubuntu/iamrj846.github.io
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 9.2: Inspect Caddy SSL Issuance
```bash
docker compose -f docker-compose.prod.yml logs -f caddy
```
You will see Caddy successfully obtaining the Let's Encrypt certificate:
```text
[INFO] [corporateguild.com] Certificate obtained successfully
[INFO] [corporateguild.com] Serving HTTPS on :443
```

Visit [https://corporateguild.com](https://corporateguild.com) in your browser. You will see a valid SSL padlock and an A+ SSL rating!

---

## 10. Decommissioning GitHub Pages

Because GitHub Pages only supports static HTML and cannot run the FastAPI backend, Redis, or SQLite ingestion engine, decommission it to prevent domain routing conflicts:

1. Open your repository on GitHub: `https://github.com/iamrj846/iamrj846.github.io`.
2. Go to **Settings &rarr; Pages**.
3. Under **Custom domain**, click **Remove** (or clear `corporateguild.com` and save).
4. Under **Build and deployment &rarr; Source**, change from **Deploy from a branch** to **None** (or disable Pages).
5. In your local repository, remove the root `CNAME` file so GitHub Pages does not automatically re-enable itself on push:
   ```bash
   git rm CNAME
   git commit -m "chore: decommission GitHub Pages CNAME in favor of Oracle Cloud"
   git push origin master
   ```

---

## 11. Preventing Oracle VM Inactivity Idle Scale-Down

Oracle Cloud's Always Free tier has an **Idle Instance Reclamation Policy**: If the 95th percentile CPU utilization falls below 20% over a rolling 7-day period, Oracle marks the instance as idle and may reclaim it.

We provide two solutions. **Method 1 is pre-configured in this repository.**

### Method 1: Automated 10-Minute Anti-Idle Keep-Alive Cron (Pre-configured)
The included script `scripts/oracle_keepalive.sh` performs a local HTTP health ping and executes a safe 15-second controlled CPU micro-burst every 10 minutes. This guarantees the instance stays well above the idle threshold without affecting web performance.

To enable it on your VM:
```bash
chmod +x /home/ubuntu/iamrj846.github.io/scripts/setup_cron.sh
/home/ubuntu/iamrj846.github.io/scripts/setup_cron.sh
```
Verify crontab:
```bash
crontab -l
```
You will see:
```cron
*/10 * * * * /bin/bash /home/ubuntu/iamrj846.github.io/scripts/oracle_keepalive.sh >> /home/ubuntu/iamrj846.github.io/logs/keepalive.log 2>&1
```

### Method 2: Upgrade Tenancy to Pay As You Go (Zero Charges)
Oracle's official policy explicitly states: **Paid / Pay As You Go (PAYG) accounts are exempt from idle instance reclamation**.
1. Navigate to: **OCI Console &rarr; Billing & Cost Management &rarr; Upgrade to Paid**.
2. Add a credit card for identity verification (Oracle places a temporary ~$100 hold that is immediately refunded).
3. **Important**: As long as your instance uses Always Free shapes (Ampere A1 up to 4 OCPUs/24GB RAM, or AMD Micro) and stay within 200GB boot volume and 10GB object storage, **your bill remains $0.00 forever**, and Oracle will **never** touch or reclaim your VM!

---

## 12. Free OCI Monitoring, Logging & APM

### Step 12.1: Enable OCI Monitoring Agent
1. In OCI Console: **Compute &rarr; Instances &rarr; corporateguild-prod**.
2. Under **Oracle Cloud Agent** tab, verify the following are **Enabled**:
   - **Compute Instance Monitoring**
   - **Custom Logs Monitoring**
3. Once enabled, navigate to the **Metrics** section of your instance to view real-time CPU, Memory, Disk, and Network graphs for free.

### Step 12.2: Free Custom Log Ingestion
1. Navigate to: **Observability & Management &rarr; Logging &rarr; Log Groups**.
2. Create Log Group: `corporateguild-logs`.
3. Click **Enable Log** &rarr; Select **Custom Logs**.
4. Log Name: `app-server-logs`.
5. Specify Log Input Path: `/home/ubuntu/iamrj846.github.io/logs/*.log`.
6. Now all application events and keep-alive heartbeats are searchable in Oracle Cloud Logging with 1-month retention for free!

### Step 12.3: Create Free High-Memory Email Alarm
1. Navigate to: **Observability & Management &rarr; Monitoring &rarr; Alarm Definitions**.
2. Click **Create Alarm**.
3. **Alarm Name**: `CorporateGuild-High-Memory`.
4. **Metric Compartment**: Select your compartment.
5. **Metric Namespace**: `oci_computeagent`.
6. **Metric Name**: `MemoryUtilization`.
7. **Trigger Rule**: Greater than `85%`.
8. **Destination**: Create a Topic with your email address.
9. Click **Save Alarm**. You will receive an email if memory ever exceeds 85%.

### Step 12.4: Application Performance Monitoring (APM)
1. Navigate to: **Observability & Management &rarr; Application Performance Monitoring &rarr; APM Domains**.
2. Click **Create APM Domain**.
3. Name: `corporateguild-apm`.
4. Check **Always Free Eligible**.
5. This provides free distributed transaction tracing and synthetic monitoring.

---

## 13. Setting Up Automated GitHub Actions CI/CD

Whenever you push new changes to the `master` branch of `iamrj846/iamrj846.github.io`, GitHub Actions will automatically SSH into your Oracle Cloud VM, pull the latest code, and restart the production containers with zero downtime.

### Step 13.1: Generate SSH Key for Deployment
On your local machine (or use existing key):
```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/oci_deploy_key
```
Add the public key (`~/.ssh/oci_deploy_key.pub`) to your Oracle VM's `~/.ssh/authorized_keys`:
```bash
cat ~/.ssh/oci_deploy_key.pub | ssh -i ~/.ssh/your_current_key ubuntu@<ORACLE_PUBLIC_IP> "cat >> ~/.ssh/authorized_keys"
```

### Step 13.2: Configure GitHub Repository Secrets
1. Go to: `https://github.com/iamrj846/iamrj846.github.io/settings/secrets/actions`.
2. Click **New repository secret** and add the following 3 secrets:

| Secret Name | Value | Example |
| :--- | :--- | :--- |
| `OCI_VM_HOST` | Your Oracle Cloud Static Public IP | `129.154.xx.xx` |
| `OCI_VM_USER` | SSH Username on the VM | `ubuntu` (or `opc`) |
| `OCI_SSH_KEY` | Contents of private key `~/.ssh/oci_deploy_key` | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

### Step 13.3: Test CI/CD Pipeline
Push any commit to `master`:
```bash
git add .
git commit -m "feat: deploy to oracle cloud always free"
git push origin master
```
Go to the **Actions** tab in your GitHub repository. You will see the **Production Deployment to OCI VM** workflow execute, build the container, and pass all health checks in under 60 seconds!

---

## 14. Operations, Maintenance & Troubleshooting Cheat Sheet

### Common Docker Commands
```bash
# View all running containers
docker compose -f docker-compose.prod.yml ps

# Follow live backend logs
docker compose -f docker-compose.prod.yml logs -f web

# Follow live reverse proxy / SSL logs
docker compose -f docker-compose.prod.yml logs -f caddy

# Restart all services cleanly
docker compose -f docker-compose.prod.yml restart

# Rebuild containers after manual code changes
docker compose -f docker-compose.prod.yml up -d --build
```

### Database & Cache Maintenance
```bash
# Query SQLite job count directly
sqlite3 data/jobs_portal.db "SELECT count(*) FROM jobs;"

# Inspect Redis cache stats
docker compose -f docker-compose.prod.yml exec redis redis-cli info memory

# Clear Redis cache without restarting
docker compose -f docker-compose.prod.yml exec redis redis-cli flushdb
```

### Backup & Cron Verification
```bash
# Check scheduled cron jobs
crontab -l

# View recent backup history
tail -n 30 logs/backup.log

# View keep-alive anti-idle heartbeats
tail -n 20 logs/keepalive.log
```

### Troubleshooting SSL
If SSL does not immediately issue on `https://corporateguild.com`:
1. Check DNS: `dig +short corporateguild.com` &rarr; Ensure it returns your Oracle Public IP.
2. Check Caddy logs: `docker compose -f docker-compose.prod.yml logs caddy` &rarr; Look for ACME challenge errors.
3. Verify host firewall: Ensure port 80 and 443 are open in both VCN Security Lists and VM iptables.

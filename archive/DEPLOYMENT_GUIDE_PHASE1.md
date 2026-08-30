> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# Phase 1 Deployment Guide to Production

**Target Server:** 13.49.245.174  
**Project Path:** `/var/www/usam/backend`  
**Current Status:** Base platform running, Phase 1 features missing

---

## What Will Be Deployed

### New Apps (7)
1. **apps/search/** - Typesense search infrastructure
2. **apps/skills/** - ESCO/O*NET taxonomy + Apache AGE
3. **apps/verification/** - 6-stage Direct Apply verification
4. **apps/vectors/** - Qdrant vector search + embeddings
5. **apps/events/** - Event logging system
6. **apps/intelligence/** - AI/LLM layer with cost tracking
7. **apps/scraper/** updates - New ATS scrapers + pipeline

### New Services Required
- **Qdrant** (v1.11.3) - Vector database
- **Typesense** (v27.1) - Search engine
- **PostgreSQL extensions** - Apache AGE, pgvector

### New Dependencies
- qdrant-client==1.11.3
- typesense==0.21.0
- apache-age-python==0.0.6
- playwright==1.45.0
- docling==2.5.0

---

## Step 1: Prepare Local Changes for Push

### 1.1 Commit All Changes

```bash
# Navigate to project root (on your local machine)
cd "m:/job already web for jobs/E-Career/backend"

# Check status
git status

# Add all new files
git add .

# Commit with descriptive message
git commit -m "feat: Phase 1 implementation - Search, Skills, Verification, Vectors, Events, AI

- Add Typesense search with keyword + semantic + hybrid modes
- Add ESCO/O*NET skills taxonomy with Apache AGE graph
- Add 6-stage Direct Apply verification engine (blocks aggregators)
- Add Qdrant vector search with Cohere embeddings
- Add event logging system (50+ event types)
- Add AI intelligence layer (Bedrock, circuit breaker, cost tracking)
- Add new ATS scrapers (SmartRecruiters, Workable, Teamtailor, Workday)
- Add Common Crawl company discovery
- Add skill extraction pipeline
- Add CV parser with Docling integration
- Update docker-compose with Qdrant and Typesense
- Add comprehensive tests for all modules

Implements tasks 1.1-1.72 (Weeks 2-7)
"
```

### 1.2 Push to Git Repository

```bash
# Push to your repository (adjust branch name as needed)
git push origin main

# Or if you use a different branch:
# git push origin develop
```

**Note:** If you don't have a git remote set up yet:
```bash
# Add your git remote (replace with your actual repo URL)
git remote add origin https://github.com/yourusername/ecareer.git
# OR
git remote add origin git@github.com:yourusername/ecareer.git

# Then push
git push -u origin main
```

---

## Step 2: Pull Changes on Production Server

### 2.1 SSH into Server

```bash
ssh ubuntu@13.49.245.174
```

### 2.2 Navigate and Pull

```bash
cd /var/www/usam/backend

# Backup current state
sudo cp -r /var/www/usam/backend /var/www/usam/backend.backup.$(date +%Y%m%d_%H%M%S)

# Stash any local changes (if any)
git stash

# Pull latest code
git pull origin main

# Check what changed
git log -1 --stat
```

---

## Step 3: Install New Dependencies

### 3.1 Activate Virtual Environment

```bash
cd /var/www/usam/backend
source venv/bin/activate
```

### 3.2 Update Python Packages

```bash
# Install all new requirements
pip install -r requirements/base.txt

# Key new packages that will be installed:
# - qdrant-client==1.11.3
# - typesense==0.21.0
# - apache-age-python==0.0.6
# - playwright==1.45.0
# - docling==2.5.0

# Install Playwright browsers (needed for Workday scraper)
playwright install chromium

# Verify installations
pip list | grep -E "qdrant|typesense|apache-age|playwright|docling"
```

---

## Step 4: Setup PostgreSQL Extensions

### 4.1 Install Apache AGE Extension

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL shell:
\c usam_db

-- Create AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE
LOAD 'age';

-- Set search path
ALTER DATABASE usam_db SET search_path = ag_catalog, "$user", public;

-- Grant permissions
GRANT USAGE ON SCHEMA ag_catalog TO ubuntu;

-- Verify
SELECT extname, extversion FROM pg_extension WHERE extname = 'age';

-- Exit
\q
```

**If AGE is not installed:**
```bash
# Install Apache AGE (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y postgresql-16-age

# Or build from source if package not available:
cd /tmp
git clone https://github.com/apache/age.git
cd age
make PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config
sudo make PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config install
```

### 4.2 Install pgvector Extension (Optional - fallback)

```bash
sudo -u postgres psql -d usam_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Step 5: Deploy Qdrant and Typesense

### 5.1 Install Docker (if not already installed)

```bash
# Check if Docker is installed
docker --version

# If not installed:
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Logout and login again for group to take effect
exit
ssh ubuntu@13.49.245.174
```

### 5.2 Create Docker Compose File

```bash
cd /var/www/usam

# Create docker-compose.yml for services
cat > docker-compose.services.yml << 'EOF'
version: '3.8'

services:
  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.11.3
    container_name: usam_qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY:-usam_qdrant_key_2024}
      QDRANT__SERVICE__ENABLE_CORS: "true"
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Typesense Search Engine
  typesense:
    image: typesense/typesense:27.1
    container_name: usam_typesense
    restart: unless-stopped
    ports:
      - "8108:8108"
    volumes:
      - typesense_data:/data
    environment:
      TYPESENSE_DATA_DIR: /data
      TYPESENSE_API_KEY: ${TYPESENSE_API_KEY:-usam_typesense_key_2024}
      TYPESENSE_ENABLE_CORS: "true"
    command: '--data-dir /data --api-key=${TYPESENSE_API_KEY:-usam_typesense_key_2024} --enable-cors'
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8108/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  qdrant_data:
  typesense_data:
EOF
```

### 5.3 Start Services

```bash
cd /var/www/usam

# Start Qdrant and Typesense
docker-compose -f docker-compose.services.yml up -d

# Verify services are running
docker ps

# Check logs
docker logs usam_qdrant
docker logs usam_typesense

# Test health endpoints
curl http://localhost:6333/health
curl http://localhost:8108/health
```

---

## Step 6: Update Environment Variables

### 6.1 Update .env File

```bash
cd /var/www/usam/backend

# Backup existing .env
cp .env .env.backup

# Add new environment variables
cat >> .env << 'EOF'

# ── Typesense Configuration ──────────────────────────────────────
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http
TYPESENSE_API_KEY=usam_typesense_key_2024
SEARCH_TRUST_SCORE_THRESHOLD=0.4

# ── Qdrant Configuration ─────────────────────────────────────────
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=usam_qdrant_key_2024

# ── AWS Bedrock (for AI/Embeddings) ──────────────────────────────
# You need to add your AWS credentials here
AWS_ACCESS_KEY_ID=your-aws-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-here
AWS_DEFAULT_REGION=us-east-1

# ── AI Configuration ─────────────────────────────────────────────
AI_USER_DAILY_TOKEN_LIMIT=50000
EOF

# Edit to add your actual AWS credentials
nano .env
# OR
vim .env
```

**IMPORTANT:** Replace `your-aws-key-here` with actual AWS credentials that have access to Bedrock.

---

## Step 7: Run Database Migrations

```bash
cd /var/www/usam/backend
source venv/bin/activate

# Check for new migrations
python manage.py showmigrations

# Run migrations for new apps
python manage.py migrate skills
python manage.py migrate verification
python manage.py migrate events

# Run all pending migrations
python manage.py migrate

# Verify migration status
python manage.py showmigrations | grep -E "skills|verification|events|vectors"
```

---

## Step 8: Setup Vector Collections

```bash
cd /var/www/usam/backend
source venv/bin/activate

# Create Qdrant collections
python manage.py setup_vector_collections

# Expected output:
# Setting up vector collections
# 
# Job listings with embeddings: jobs
#   Creating collection...
#   ✓ Collection created
# 
# User profiles with embeddings: users
#   Creating collection...
#   ✓ Collection created
# 
# ESCO skills with embeddings: skills
#   Creating collection...
#   ✓ Collection created

# Verify
curl http://localhost:6333/collections
```

---

## Step 9: Import ESCO/O*NET Data (Optional but Recommended)

### 9.1 Download ESCO Dataset

```bash
cd /tmp

# Download ESCO data (if not already downloaded)
# ESCO portal: https://ec.europa.eu/esco/portal/download
# You'll need to download these files manually or via direct links:
# - skills_en.csv
# - occupations_en.csv
# - occupationSkillRelations.csv

# For now, let's skip this and do it later when you have the data
echo "ESCO import can be done later with actual dataset files"
```

### 9.2 Setup AGE Graph (Optional - can be done after ESCO import)

```bash
cd /var/www/usam/backend
source venv/bin/activate

# This will create the graph structure (empty until ESCO data imported)
python manage.py setup_age_graph

# Or wait until ESCO data is imported to populate it
```

---

## Step 10: Collect Static Files

```bash
cd /var/www/usam/backend
source venv/bin/activate

# Collect static files
python manage.py collectstatic --noinput

# Set permissions
sudo chown -R www-data:www-data /var/www/usam/backend/staticfiles
```

---

## Step 11: Restart Application Services

### 11.1 Restart Gunicorn

```bash
# If using systemd service
sudo systemctl restart gunicorn

# Or if using supervisor
sudo supervisorctl restart usam

# Check status
sudo systemctl status gunicorn
# OR
sudo supervisorctl status usam
```

### 11.2 Restart Celery (if running)

```bash
# Restart Celery worker
sudo systemctl restart celery-worker

# Restart Celery beat (for scheduled tasks)
sudo systemctl restart celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

**If Celery is not set up yet, here's how to configure it:**

```bash
# Create Celery systemd service
sudo nano /etc/systemd/system/celery-worker.service
```

Add this content:
```ini
[Unit]
Description=Celery Worker for USAM
After=network.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
EnvironmentFile=/var/www/usam/backend/.env
WorkingDirectory=/var/www/usam/backend
ExecStart=/var/www/usam/backend/venv/bin/celery -A config worker -l info --detach --pidfile=/var/run/celery/worker.pid --logfile=/var/log/celery/worker.log
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Create Celery Beat service
sudo nano /etc/systemd/system/celery-beat.service
```

Add this content:
```ini
[Unit]
Description=Celery Beat for USAM
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
EnvironmentFile=/var/www/usam/backend/.env
WorkingDirectory=/var/www/usam/backend
ExecStart=/var/www/usam/backend/venv/bin/celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler --pidfile=/var/run/celery/beat.pid --logfile=/var/log/celery/beat.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Create log and pid directories
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown -R ubuntu:ubuntu /var/log/celery /var/run/celery

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

---

## Step 12: Configure Nginx (if needed)

### 12.1 Update Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/usam
```

Add these locations (if not already present):
```nginx
location /api/v1/search/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/v1/vectors/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Step 13: Verification & Testing

### 13.1 Health Checks

```bash
# API health
curl http://13.49.245.174/health/

# Search health
curl http://13.49.245.174/api/v1/search/health/

# Vector health
curl http://13.49.245.174/api/v1/vectors/health/

# Qdrant health
curl http://localhost:6333/health

# Typesense health
curl http://localhost:8108/health
```

### 13.2 Verify New Apps Loaded

```bash
cd /var/www/usam/backend
source venv/bin/activate

# Check installed apps
python manage.py shell << EOF
from django.conf import settings
apps = [app for app in settings.INSTALLED_APPS if 'apps.' in app]
print("Installed apps:")
for app in apps:
    print(f"  - {app}")
EOF
```

Expected output should include:
- apps.search
- apps.skills
- apps.verification
- apps.vectors
- apps.events
- apps.intelligence

### 13.3 Test API Endpoints

```bash
# Test semantic search (will return empty until jobs are embedded)
curl "http://13.49.245.174/api/v1/vectors/search/semantic/?q=developer"

# Test keyword search
curl "http://13.49.245.174/api/v1/search/jobs/?q=engineer"

# Test API documentation
curl http://13.49.245.174/api/schema/

# Open in browser
echo "Visit: http://13.49.245.174/api/docs/"
```

### 13.4 Check Logs for Errors

```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Application logs (if configured)
sudo tail -f /var/www/usam/backend/logs/django.log

# Celery logs
sudo tail -f /var/log/celery/worker.log
sudo tail -f /var/log/celery/beat.log
```

---

## Step 14: Optional - Bulk Embed Existing Jobs

**Note:** This requires AWS Bedrock access and will incur costs (~$0.20 per 10k jobs)

```bash
cd /var/www/usam/backend
source venv/bin/activate

# First, verify AWS credentials are set
python -c "import boto3; print(boto3.client('bedrock-runtime', region_name='us-east-1'))"

# If successful, run embedding
# Test with 10 jobs first
python manage.py embed_jobs --limit 10

# If that works, embed all jobs
python manage.py embed_jobs

# Embed top 500 skills
python manage.py embed_skills --limit 500
```

---

## Troubleshooting

### Issue: ModuleNotFoundError for new apps

**Solution:**
```bash
# Make sure all apps are in INSTALLED_APPS
grep -A 20 "INSTALLED_APPS" /var/www/usam/backend/config/settings/base.py

# Restart services
sudo systemctl restart gunicorn celery-worker
```

### Issue: Qdrant/Typesense connection errors

**Solution:**
```bash
# Check if services are running
docker ps

# Check logs
docker logs usam_qdrant
docker logs usam_typesense

# Restart services
docker-compose -f docker-compose.services.yml restart

# Check firewall (should allow localhost connections)
sudo ufw status
```

### Issue: Database migration errors

**Solution:**
```bash
# Check migration status
python manage.py showmigrations

# Fake migrations if needed (only if you're sure schema is correct)
python manage.py migrate --fake apps.skills

# Or reset specific app migrations
python manage.py migrate apps.skills zero
python manage.py migrate apps.skills
```

### Issue: Static files not loading

**Solution:**
```bash
# Collect static files again
python manage.py collectstatic --noinput --clear

# Fix permissions
sudo chown -R www-data:www-data /var/www/usam/backend/staticfiles
sudo chmod -R 755 /var/www/usam/backend/staticfiles
```

---

## Quick Deployment Commands (Summary)

**On your local machine:**
```bash
cd "m:/job already web for jobs/E-Career/backend"
git add .
git commit -m "feat: Phase 1 implementation"
git push origin main
```

**On production server:**
```bash
# Pull code
cd /var/www/usam/backend
git pull origin main

# Install dependencies
source venv/bin/activate
pip install -r requirements/base.txt
playwright install chromium

# Start services
cd /var/www/usam
docker-compose -f docker-compose.services.yml up -d

# Setup database
cd backend
python manage.py migrate
python manage.py setup_vector_collections

# Restart application
sudo systemctl restart gunicorn celery-worker celery-beat
sudo systemctl reload nginx

# Verify
curl http://13.49.245.174/api/v1/vectors/health/
```

---

## Final Verification Checklist

After deployment, verify:

- [ ] Site still accessible: http://13.49.245.174/
- [ ] Admin still works: http://13.49.245.174/admin/
- [ ] API docs accessible: http://13.49.245.174/api/docs/
- [ ] Qdrant running: `curl http://localhost:6333/health`
- [ ] Typesense running: `curl http://localhost:8108/health`
- [ ] Search API works: `curl "http://13.49.245.174/api/v1/search/jobs/?q=test"`
- [ ] Vector API works: `curl http://13.49.245.174/api/v1/vectors/health/`
- [ ] Celery worker running: `sudo systemctl status celery-worker`
- [ ] Celery beat running: `sudo systemctl status celery-beat`
- [ ] No errors in logs: `sudo journalctl -u gunicorn --since "10 minutes ago"`

---

## Post-Deployment Tasks

1. **Import ESCO Data** (when dataset available)
   ```bash
   python manage.py import_esco --skills /path/to/skills.csv --occupations /path/to/occupations.csv
   ```

2. **Setup AGE Graph** (after ESCO import)
   ```bash
   python manage.py setup_age_graph
   ```

3. **Generate Arabic Translations**
   ```bash
   python manage.py generate_arabic_translations --limit 500
   ```

4. **Embed Existing Jobs** (requires AWS Bedrock)
   ```bash
   python manage.py embed_jobs
   ```

5. **Setup Monitoring**
   - Configure CloudWatch or equivalent for logs
   - Setup alerts for service downtime
   - Monitor Qdrant/Typesense disk usage

---

## Rollback Plan (If Something Goes Wrong)

```bash
# Stop services
cd /var/www/usam
docker-compose -f docker-compose.services.yml down

# Restore code
cd /var/www/usam/backend
git reset --hard HEAD~1  # Go back one commit
# OR restore from backup
sudo rm -rf /var/www/usam/backend
sudo cp -r /var/www/usam/backend.backup.* /var/www/usam/backend

# Restore database (if needed)
sudo -u postgres psql usam_db < /path/to/backup.sql

# Restart application
sudo systemctl restart gunicorn celery-worker celery-beat
```

---

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u gunicorn -f`
2. Check service status: `sudo systemctl status gunicorn`
3. Verify environment variables: `cat /var/www/usam/backend/.env`
4. Test individual components: Run health check commands above

**Phase 1 deployment complete!** 🎉

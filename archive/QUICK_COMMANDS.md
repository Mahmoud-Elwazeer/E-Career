> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# 🚀 Quick Commands Reference

## 🐳 Docker Commands

### Start/Stop Services
```bash
cd "m:\job already web for jobs\E-Career"

# Start all services
docker-compose up -d

# Stop all services (keeps data)
docker-compose down

# Stop + delete all data
docker-compose down -v

# Restart all
docker-compose restart

# Restart one service
docker-compose restart backend
```

### View Status & Logs
```bash
# Check status
docker-compose ps

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Rebuild
```bash
# Rebuild backend (after code changes)
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache backend

# Rebuild and restart
docker-compose up -d --build
```

---

## 🎯 Django Commands

### Database
```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create migrations
docker-compose exec backend python manage.py makemigrations

# Reset database
docker-compose exec backend python manage.py flush

# Database shell
docker-compose exec backend python manage.py dbshell
```

### User Management
```bash
# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Change user password
docker-compose exec backend python manage.py changepassword admin
```

### Development
```bash
# Django shell
docker-compose exec backend python manage.py shell

# Run dev server (already running in container)
docker-compose exec backend python manage.py runserver 0.0.0.0:8000

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

---

## 📦 Scraping Commands

### Import Companies
```bash
# Import 100 test companies
docker-compose exec backend python manage.py import_companies --limit 100

# Import all 12,000+ companies (takes 5-10 min)
docker-compose exec backend python manage.py import_companies

# Import with filtering
docker-compose exec backend python manage.py import_companies --limit 500
```

### Scrape Jobs
```bash
# Scrape all active sources
docker-compose exec backend python manage.py scrape_jobs

# Scrape specific company (by slug)
docker-compose exec backend python manage.py scrape_jobs --source stripe --limit 10

# Run as async Celery task
docker-compose exec backend python manage.py scrape_jobs --async
```

### Maintenance
```bash
# Verify job URLs are still live
docker-compose exec backend python manage.py verify_apply_urls

# Remove old jobs (90+ days)
docker-compose exec backend python manage.py expire_old_jobs
```

---

## 🗄️ PostgreSQL Commands

### Connect to Database
```bash
# Connect to psql
docker-compose exec postgres psql -U postgres ecareer_dev
```

### Inside psql:
```sql
-- List all tables
\dt

-- Describe table structure
\d jobs_job
\d jobs_company

-- Count records
SELECT COUNT(*) FROM jobs_company;
SELECT COUNT(*) FROM jobs_job;

-- View recent jobs
SELECT title, company_name, location, posted_date 
FROM jobs_job 
ORDER BY posted_date DESC 
LIMIT 10;

-- View companies by ATS
SELECT name, ats_system 
FROM jobs_company 
WHERE ats_system IS NOT NULL 
LIMIT 20;

-- Exit
\q
```

### Database Backup/Restore
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ecareer_dev > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20260629.sql | docker-compose exec -T postgres psql -U postgres ecareer_dev
```

---

## 🔴 Redis Commands

### Connect to Redis
```bash
# Connect to redis-cli
docker-compose exec redis redis-cli
```

### Inside redis-cli:
```bash
# Test connection
PING

# List all keys
KEYS *

# Get server info
INFO

# Monitor commands in real-time
MONITOR

# Check memory usage
INFO memory

# Clear all data (careful!)
FLUSHALL

# Exit
exit
```

---

## 🔧 Celery Commands

### Worker Management
```bash
# View worker logs
docker-compose logs -f celery_worker

# Restart worker
docker-compose restart celery_worker

# Check worker status
docker-compose exec celery_worker celery -A config inspect active

# Check registered tasks
docker-compose exec celery_worker celery -A config inspect registered
```

### Beat Scheduler
```bash
# View beat logs
docker-compose logs -f celery_beat

# Restart beat
docker-compose restart celery_beat

# Check scheduled tasks
docker-compose exec backend python manage.py shell
```

Inside shell:
```python
from django_celery_beat.models import PeriodicTask
for task in PeriodicTask.objects.all():
    print(f"{task.name}: {task.crontab} - Enabled: {task.enabled}")
```

---

## 🧪 Testing & Debugging

### Run Tests
```bash
# Run all tests
docker-compose exec backend python manage.py test

# Run specific app tests
docker-compose exec backend python manage.py test apps.jobs

# Run with coverage
docker-compose exec backend coverage run --source='.' manage.py test
docker-compose exec backend coverage report
```

### Debug
```bash
# Check Django settings
docker-compose exec backend python manage.py diffsettings

# Check for problems
docker-compose exec backend python manage.py check

# Show migrations
docker-compose exec backend python manage.py showmigrations
```

### Health Checks
```bash
# Test health endpoint
curl http://localhost:8000/health/

# Expected response:
# {"status":"healthy","database":"connected","cache":"connected"}
```

---

## 📊 Data Queries

### Quick Stats
```bash
# Get all stats at once
docker-compose exec postgres psql -U postgres ecareer_dev << EOF
SELECT 'Companies' AS type, COUNT(*) AS count FROM jobs_company
UNION ALL
SELECT 'Jobs' AS type, COUNT(*) AS count FROM jobs_job
UNION ALL
SELECT 'Active Jobs' AS type, COUNT(*) AS count FROM jobs_job WHERE is_active = true
UNION ALL
SELECT 'Users' AS type, COUNT(*) AS count FROM auth_user;
EOF
```

### Job Stats by Source
```bash
docker-compose exec postgres psql -U postgres ecareer_dev -c "
SELECT source_name, COUNT(*) as job_count 
FROM jobs_job 
GROUP BY source_name 
ORDER BY job_count DESC;
"
```

### Recent Scraping Activity
```bash
docker-compose exec postgres psql -U postgres ecareer_dev -c "
SELECT DATE(created_at) as date, COUNT(*) as jobs_added 
FROM jobs_job 
WHERE created_at > NOW() - INTERVAL '7 days' 
GROUP BY DATE(created_at) 
ORDER BY date DESC;
"
```

---

## 🔒 Security

### Reset Admin Password
```bash
docker-compose exec backend python manage.py changepassword admin
```

### Generate New Secret Key
```bash
docker-compose exec backend python -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
"
```

### Generate Encryption Key
```bash
docker-compose exec backend python -c "
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
"
```

---

## 🧹 Cleanup

### Remove Old Data
```bash
# Remove jobs older than 90 days
docker-compose exec backend python manage.py expire_old_jobs

# Clear all jobs (keep companies)
docker-compose exec postgres psql -U postgres ecareer_dev -c "TRUNCATE TABLE jobs_job CASCADE;"

# Clear all data (dangerous!)
docker-compose exec backend python manage.py flush
```

### Docker Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything (nuclear option)
docker system prune -a --volumes
```

---

## 📱 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Django Admin** | http://localhost:8000/admin | Use superuser |
| **API Docs** | http://localhost:8000/api/schema/swagger-ui/ | - |
| **Health Check** | http://localhost:8000/health/ | - |
| **PostgreSQL** | localhost:5432 | postgres / ecareer@@WWQ2 |
| **Redis** | localhost:6379 | (no password) |

---

## 🚨 Emergency Commands

### Services Won't Start
```bash
# Check Docker is running
docker ps

# View error logs
docker-compose logs

# Restart Docker Desktop
# (From Windows: Restart Docker Desktop app)

# Force recreate containers
docker-compose up -d --force-recreate
```

### Database Connection Failed
```bash
# Check PostgreSQL health
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Wait then restart backend
sleep 10
docker-compose restart backend
```

### Out of Disk Space
```bash
# Check Docker disk usage
docker system df

# Clean up
docker system prune -a --volumes

# Restart services
docker-compose up -d
```

---

**Keep this file handy for quick reference!** 📝

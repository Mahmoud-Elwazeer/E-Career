> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# 🐳 Docker Quick Start - E-Career Platform

**Everything in one command!**

---

## ✅ Prerequisites

1. **Docker Desktop** installed
   - Download: https://www.docker.com/products/docker-desktop/
   - Make sure Docker is running (whale icon in taskbar)

2. **That's it!** No PostgreSQL, Redis, or Python setup needed.

---

## 🚀 Start All Services

### **Option 1: Full Stack (Recommended)**

```bash
cd "m:\job already web for jobs\E-Career"
docker-compose up -d
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Django Backend (port 8000)
- ✅ Celery Worker (background tasks)
- ✅ Celery Beat (scheduled jobs)

### **Option 2: Watch Logs (Debug Mode)**

```bash
docker-compose up
```

This shows live logs from all services.

---

## 📊 Check Status

```bash
# See all running containers
docker-compose ps

# Expected output:
# ecareer_postgres        Up (healthy)   5432/tcp
# ecareer_redis           Up (healthy)   6379/tcp
# ecareer_backend         Up             0.0.0.0:8000->8000/tcp
# ecareer_celery_worker   Up
# ecareer_celery_beat     Up
```

---

## 🔧 First-Time Setup

### **1. Create Superuser**

```bash
docker-compose exec backend python manage.py createsuperuser
```

Follow prompts:
- Username: `admin`
- Email: `admin@usamif.com`
- Password: (your choice)

### **2. Import Companies**

```bash
# Import 100 test companies
docker-compose exec backend python manage.py import_companies --limit 100

# Import all 12,000+ companies (takes 5-10 minutes)
docker-compose exec backend python manage.py import_companies
```

### **3. Test Scraping**

```bash
# Test scraping from Stripe (Greenhouse ATS)
docker-compose exec backend python manage.py scrape_jobs --source stripe --limit 10
```

---

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Django Admin** | http://localhost:8000/admin | Use superuser you created |
| **API Documentation** | http://localhost:8000/api/schema/swagger-ui/ | - |
| **PostgreSQL** | `localhost:5432` | postgres / ecareer@@WWQ2 |
| **Redis** | `localhost:6379` | (no password) |

---

## 📝 Common Commands

### **Logs**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### **Restart Services**

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart celery_worker
```

### **Stop Services**

```bash
# Stop all (keeps data)
docker-compose down

# Stop all + delete data
docker-compose down -v
```

### **Django Commands**

```bash
# Migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Shell
docker-compose exec backend python manage.py shell

# Database shell
docker-compose exec backend python manage.py dbshell

# Create app
docker-compose exec backend python manage.py startapp myapp
```

### **Database Commands**

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d ecareer_dev

# SQL queries inside psql:
\dt              # List tables
\d jobs_job      # Describe job table
SELECT COUNT(*) FROM jobs_job;
\q               # Quit
```

### **Redis Commands**

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Redis commands:
PING             # Test connection
KEYS *           # List all keys
INFO             # Server info
FLUSHALL         # Clear all data (careful!)
```

---

## 🧪 Test Workflow

### **Complete Test Run**

```bash
# 1. Start services
docker-compose up -d

# 2. Wait for health checks (30 seconds)
sleep 30

# 3. Create superuser
docker-compose exec backend python manage.py createsuperuser

# 4. Import test companies
docker-compose exec backend python manage.py import_companies --limit 20

# 5. Scrape jobs from multiple sources
docker-compose exec backend python manage.py scrape_jobs --source stripe --limit 10
docker-compose exec backend python manage.py scrape_jobs --source gitlab --limit 10

# 6. Check results
docker-compose exec postgres psql -U postgres -d ecareer_dev -c "SELECT COUNT(*) FROM jobs_company;"
docker-compose exec postgres psql -U postgres -d ecareer_dev -c "SELECT COUNT(*) FROM jobs_job;"

# 7. Visit admin
# Open: http://localhost:8000/admin
```

---

## 🐛 Troubleshooting

### **Problem: Port already in use**

```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5432
netstat -ano | findstr :6379

# Stop the process or change port in docker-compose.yml
```

### **Problem: Container won't start**

```bash
# View logs
docker-compose logs backend

# Rebuild image
docker-compose build backend
docker-compose up -d backend
```

### **Problem: Database connection failed**

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait 10 seconds, then restart backend
sleep 10
docker-compose restart backend
```

### **Problem: Celery not picking up tasks**

```bash
# Check worker is running
docker-compose ps celery_worker

# View worker logs
docker-compose logs -f celery_worker

# Restart worker
docker-compose restart celery_worker
```

---

## 🔄 Update Code

When you change code:

```bash
# Option 1: Hot reload (Django auto-detects)
# Just save your file - Django will reload automatically

# Option 2: Restart container (if needed)
docker-compose restart backend

# Option 3: Rebuild (if you changed Dockerfile/requirements.txt)
docker-compose build backend
docker-compose up -d backend
```

---

## 📦 Volume Management

### **Backup Database**

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres ecareer_dev > backup.sql

# Restore backup
cat backup.sql | docker-compose exec -T postgres psql -U postgres ecareer_dev
```

### **Clear Data**

```bash
# Stop and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d

# Re-run migrations
docker-compose exec backend python manage.py migrate
```

---

## 🚀 Production Considerations

For production deployment, update `docker-compose.yml`:

1. **Change to production settings**:
   ```yaml
   environment:
     - DJANGO_SETTINGS_MODULE=config.settings.production
   ```

2. **Add Nginx reverse proxy**:
   ```yaml
   nginx:
     image: nginx:alpine
     ports:
       - "80:80"
       - "443:443"
   ```

3. **Use environment secrets**:
   ```yaml
   env_file:
     - .env.production
   ```

4. **Set resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

---

## ✅ Success Checklist

After running `docker-compose up -d`:

- [ ] All 5 containers running: `docker-compose ps`
- [ ] PostgreSQL healthy (10 seconds)
- [ ] Redis healthy (5 seconds)
- [ ] Backend accessible: http://localhost:8000/admin
- [ ] Superuser created
- [ ] Companies imported
- [ ] Jobs scraped successfully
- [ ] Celery worker processing tasks
- [ ] Celery beat scheduling tasks

---

## 🎯 Next Steps

1. ✅ **Start services**: `docker-compose up -d`
2. ✅ **Create superuser**: See above
3. ✅ **Import companies**: See above
4. ✅ **Test scraping**: See above
5. 📄 **Continue to Phase 1C**: Job Pages Enhancement

---

**Docker Status**: 🟢 ALL SERVICES READY!  
**Access Admin**: http://localhost:8000/admin  
**View Logs**: `docker-compose logs -f`

🐳 **Docker makes everything easy!**

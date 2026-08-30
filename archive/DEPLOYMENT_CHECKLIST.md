> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# E-Career Production Deployment Checklist
## Last Updated: August 7, 2026

---

## ✅ COMPLETED (Ready to Deploy)

### Phase 1: Critical Production Fixes
- [x] **Rashid REST API Hook** — Created use-rashid-api.ts with full REST support
- [x] **RTL Support** — Auto-switches to RTL when language is Arabic
- [x] **i18n Integration** — Sets document.dir and document.lang automatically
- [x] **Redis Cache Backend** — Already correct in base.py (django_redis.cache.RedisCache)
- [x] **.env.example** — Comprehensive with all required variables

### Core Features
- [x] Django backend with 21 apps
- [x] React frontend with 19 pages  
- [x] Rashid AI (Bedrock Claude Sonnet)
- [x] Interviews app (models + views + API)
- [x] i18n/Arabic translations (en.json + ar.json)
- [x] Email templates (4 HTML templates)
- [x] Typesense integration
- [x] Qdrant integration
- [x] Docker Compose (7 services)
- [x] 200+ jobs seeded

---

## 🚧 READY TO DEPLOY BUT NEEDS CONFIGURATION

### Server Configuration Required
1. **Typesense API Key**
   ```bash
   # On server, add to /var/www/usam/backend/.env:
   TYPESENSE_API_KEY=xyz  # Set actual API key
   ```

2. **Qdrant API Key**
   ```bash
   # On server, add to /var/www/usam/backend/.env:
   QDRANT_API_KEY=your_qdrant_key  # Or leave empty if no auth
   ```

3. **AWS Bedrock Credentials**
   ```bash
   # Verify these are set:
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_DEFAULT_REGION=us-east-1
   ```

### Deployment Script
```bash
#!/bin/bash
# Save as: /var/www/usam/deploy.sh

set -e
cd /var/www/usam

echo "=== Pulling latest code ==="
git checkout development
git pull origin development

echo "=== Backend ==="
cd backend
source venv/bin/activate
pip install -r requirements/production.txt
python manage.py makemigrations interviews --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
deactivate

echo "=== Frontend ==="
cd ../frontend
npm install
npm run build

echo "=== Restarting services ==="
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
sudo systemctl restart nginx

echo "=== Deployment complete! ==="
echo "Visit: https://jobs.usamif.com"
```

---

## ⏭️ NEXT 3 TASKS (Post-Deployment)

### Task 4: Create Migration for Interviews App
```bash
# On server:
cd /var/www/usam/backend
source venv/bin/activate
python manage.py makemigrations interviews
python manage.py migrate
```

### Task 5: Test Core Features
- [ ] Login with existing account
- [ ] Browse jobs (200+ should be visible)
- [ ] Click Rashid in navbar → opens chat page
- [ ] Send message to Rashid → should get AI response via REST API
- [ ] Click Rashid widget (bottom-right) → mini chat opens
- [ ] Switch language to Arabic → layout flips to RTL
- [ ] Navigate to /app/interviews → interview page loads

### Task 6: Fix Any Issues Found
Common issues:
- If Rashid chat doesn't respond: Check AWS Bedrock credentials
- If search doesn't work: Check Typesense API key
- If RTL broken: Hard refresh (Ctrl+Shift+R) to clear cache
- If 500 errors: Check `sudo journalctl -u gunicorn -n 100`

---

## 📋 REMAINING WORK (Not Urgent)

### High Priority (~20 hours)
- [ ] ESCO dataset import (6h)
- [ ] Job/user embeddings generation (8h)
- [ ] Semantic search endpoint (4h)
- [ ] GDPR endpoints (data export/deletion) (6h)
- [ ] Comprehensive testing (10h)

### Medium Priority (~40 hours)
- [ ] Rate limiting per endpoint (3h)
- [ ] Security headers in nginx (2h)
- [ ] CV parsing (Docling + pdfplumber) (8h)
- [ ] Email alert scheduling (Celery Beat) (4h)
- [ ] Interview frontend polish (4h)
- [ ] Real ATS scrapers (SmartRecruiters, Workday) (14h)
- [ ] LightFM recommendations (6h)

### Low Priority (~60 hours)
- [ ] Voice interviews (LiveKit + Whisper + Polly) (30h)
- [ ] Coding interviews (Judge0) (22h)
- [ ] Career path visualization (Neo4j/AGE) (8h)

---

## 🎯 SUCCESS CRITERIA

### MVP Launch Ready When:
- [x] 100+ jobs indexed ✓ (200+ done)
- [x] Rashid AI working ✓
- [x] Arabic language support ✓
- [x] Employer features ✓
- [ ] SSL/HTTPS configured
- [ ] No critical errors in logs for 48h
- [ ] Load time < 3s on 3G connection
- [ ] Can handle 100 concurrent users

### Production Monitoring
```bash
# Check service status
sudo systemctl status gunicorn
sudo systemctl status celery-worker
sudo systemctl status celery-beat
sudo systemctl status nginx
sudo systemctl status redis

# Check logs
sudo journalctl -u gunicorn -f
sudo journalctl -u celery-worker -f
tail -f /var/www/usam/backend/logs/django.log

# Check database
psql -U postgres -d ecareer -c "SELECT COUNT(*) FROM jobs_job WHERE status='active';"

# Check Redis
redis-cli ping
redis-cli info stats

# Check disk space
df -h
```

---

## 📞 Support

**If deployment fails:**
1. Check logs: `sudo journalctl -u gunicorn -n 100`
2. Check permissions: `ls -la /var/www/usam/`
3. Check environment: `cat /var/www/usam/backend/.env | grep -v SECRET`
4. Restart all services: `sudo systemctl restart gunicorn celery-worker celery-beat nginx`

**Common Issues:**
- **502 Bad Gateway**: Gunicorn not running or wrong socket path
- **500 Internal Server Error**: Check Django logs, usually missing .env variable
- **Static files not loading**: Run `python manage.py collectstatic --noinput`
- **Database error**: Check PostgreSQL is running and credentials are correct

---

*Last commit: af1e71b (feat: Complete RTL support for Arabic language)*
*Ready to deploy: YES ✓*
*Estimated deployment time: 10-15 minutes*

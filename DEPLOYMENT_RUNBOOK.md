# Deployment Runbook

This runbook provides step-by-step instructions for deploying the USAM Career Compass application.

## Table of Contents

1. [Pre-deployment Checklist](#pre-deployment-checklist)
2. [Deployment Steps](#deployment-steps)
3. [Post-deployment Verification](#post-deployment-verification)
4. [Rollback Procedure](#rollback-procedure)
5. [Troubleshooting](#troubleshooting)

---

## Pre-deployment Checklist

### Environment Variables

Ensure the following environment variables are set in `.env`:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,localhost

# Database
DATABASE_URL=postgres://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# Qdrant
QDRANT_URL=http://host:6333

# AWS Bedrock
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Email
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True

# Frontend
REACT_APP_API_URL=https://your-domain.com/api/v1
```

### Database Migrations

```bash
# Run migrations
cd E-Career/backend
python manage.py migrate

# Create superuser (if needed)
python manage.py createsuperuser
```

### Static Files

```bash
# Collect static files
python manage.py collectstatic --noinput
```

---

## Deployment Steps

### Docker Deployment

1. **Build the Docker images**

```bash
cd E-Career
docker-compose build
```

2. **Start the services**

```bash
docker-compose up -d
```

3. **Verify services are running**

```bash
docker-compose ps
```

### Manual Deployment

1. **Install dependencies**

```bash
cd E-Career/backend
pip install -r requirements/base.txt

cd ../frontend
npm install
```

2. **Run database migrations**

```bash
cd E-Career/backend
python manage.py migrate
```

3. **Collect static files**

```bash
python manage.py collectstatic --noinput
```

4. **Start the application**

```bash
# Backend
cd E-Career/backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Frontend (production build)
cd E-Career/frontend
npm run build
npx serve -s dist
```

---

## Post-deployment Verification

### Health Check

```bash
# Check API health
curl https://your-domain.com/api/v1/core/health/

# Check database connection
curl https://your-domain.com/api/v1/core/db-status/
```

### Log Verification

```bash
# Check backend logs
docker-compose logs -f backend

# Check frontend logs
docker-compose logs -f frontend
```

### Test Endpoints

```bash
# Test talent score endpoint
curl -H "Authorization: Token your-token" \
  https://your-domain.com/api/v1/career/talent-score/

# Test job listing
curl https://your-domain.com/api/v1/jobs/jobs/
```

---

## Rollback Procedure

### Docker Rollback

1. **Stop current deployment**

```bash
docker-compose down
```

2. **Restore previous images**

```bash
docker-compose pull
docker-compose up -d
```

### Manual Rollback

1. **Stop the application**

```bash
# Stop gunicorn
pkill -f gunicorn

# Stop frontend
pkill -f serve
```

2. **Restore previous code**

```bash
cd E-Career
git checkout previous-commit-hash
```

3. **Restart the application**

```bash
# Start backend
cd E-Career/backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Start frontend
cd E-Career/frontend
npx serve -s dist
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms:** `Connection refused` error

**Solution:**
```bash
# Check database service
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify database URL in .env
grep DATABASE_URL .env
```

#### 2. Redis Connection Failed

**Symptoms:** `Connection refused` error for Redis

**Solution:**
```bash
# Check Redis service
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Verify Redis URL in .env
grep REDIS_URL .env
```

#### 3. Static Files Not Loading

**Symptoms:** CSS/JS files return 404

**Solution:**
```bash
# Collect static files
cd E-Career/backend
python manage.py collectstatic --noinput

# Check static files directory
ls -la staticfiles/
```

#### 4. Migration Errors

**Symptoms:** `Table already exists` or similar errors

**Solution:**
```bash
# Check migration status
cd E-Career/backend
python manage.py showmigrations

# Create new migration if needed
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Getting Help

If you encounter issues not covered in this runbook:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose exec backend env`
3. Test database connectivity: `docker-compose exec backend python manage.py shell`
4. Contact the development team

---

## Maintenance Tasks

### Daily

- [ ] Check application logs for errors
- [ ] Verify database backup completed
- [ ] Check disk space usage

### Weekly

- [ ] Review cost reports
- [ ] Check for security updates
- [ ] Review performance metrics

### Monthly

- [ ] Review and update dependencies
- [ ] Check database size and optimize if needed
- [ ] Review and update SSL certificates
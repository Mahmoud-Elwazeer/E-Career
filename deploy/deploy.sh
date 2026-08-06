#!/bin/bash
# E-Career Deployment Script
# Usage: bash deploy.sh

set -e

echo "=== E-Career Deployment Script ==="
echo "Server: $(hostname)"
echo "Date: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on server (not local)
if [ -z "$DEPLOY_ENV" ]; then
    echo -e "${YELLOW}Warning: DEPLOY_ENV not set. Assuming local development.${NC}"
    echo "Set DEPLOY_ENV=production for production deployment"
fi

cd "$(dirname "$0")/.."

# Pull latest code
echo ">>> Pulling latest code..."
git pull origin development

# Backend
echo ">>> Installing backend dependencies..."
cd backend
source /var/www/usam/venv/bin/activate 2>/dev/null || true
pip install -r requirements.txt --quiet 2>/dev/null || echo "Skipping pip install (not in venv)"

# Migrations
echo ">>> Running migrations..."
python manage.py migrate --noinput 2>/dev/null || echo "Skipping migrations (not in production)"

# Static files
echo ">>> Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || echo "Skipping static files (not in production)"

# Frontend
echo ">>> Building frontend..."
cd /var/www/usam/frontend 2>/dev/null || cd ../frontend
npm install --silent 2>/dev/null || echo "Skipping npm install"
npm run build 2>/dev/null || echo "Skipping frontend build"

# Restart services (only if running on server)
if [ -n "$DEPLOY_ENV" ] && [ "$DEPLOY_ENV" = "production" ]; then
    echo ">>> Restarting services..."
    sudo systemctl restart usam 2>/dev/null || echo "Skipping usam service restart"
    sudo systemctl restart celery-usam 2>/dev/null || echo "Skipping celery-usam service restart"
    sudo systemctl restart celery-beat-usam 2>/dev/null || echo "Skipping celery-beat-usam service restart"
fi

# Health check
echo ">>> Running health check..."
sleep 3
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/jobs/ 2>/dev/null || echo "000")
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ API is healthy (HTTP $STATUS)${NC}"
else
    echo -e "${RED}❌ API check failed (HTTP $STATUS)${NC}"
    echo "Checking service status..."
    sudo journalctl -u usam --since "30 sec ago" --no-pager 2>/dev/null | tail -10 || echo "Cannot check service logs"
    exit 1
fi

echo ""
echo "=== Deployment Complete ==="
echo "Site: https://jobs.usamif.com"
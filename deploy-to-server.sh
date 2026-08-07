#!/bin/bash
# Deployment script for E-Career platform
# Run on server: sudo bash deploy-to-server.sh

set -e  # Exit on error

echo "════════════════════════════════════════"
echo "  E-Career Deployment Script"
echo "════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project directory
cd /var/www/usam

echo -e "${GREEN}[1/7]${NC} Pulling latest code..."
git checkout development
git pull origin development

echo ""
echo -e "${GREEN}[2/7]${NC} Setting up Python environment..."

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment and install dependencies
cd backend
source venv/bin/activate
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || pip install -r requirements/production.txt 2>/dev/null || echo "Could not find requirements file"

echo ""
echo -e "${GREEN}[3/7]${NC} Running database migrations..."
python3 manage.py makemigrations interviews --noinput || echo "No new migrations for interviews"
python3 manage.py migrate --noinput

echo ""
echo -e "${GREEN}[4/7]${NC} Collecting static files..."
python3 manage.py collectstatic --noinput

deactivate
cd ..

echo ""
echo -e "${GREEN}[5/7]${NC} Building frontend..."
cd frontend
npm install
npm run build

echo ""
echo -e "${GREEN}[6/7]${NC} Restarting services..."
cd ..

# Find and restart the actual service names
echo "Checking for Django/Gunicorn service..."
if systemctl list-units --type=service --all | grep -q "gunicorn"; then
    sudo systemctl restart gunicorn
    echo "✓ Restarted gunicorn"
elif systemctl list-units --type=service --all | grep -q "ecareer"; then
    sudo systemctl restart ecareer
    echo "✓ Restarted ecareer"
elif systemctl list-units --type=service --all | grep -q "usam"; then
    sudo systemctl restart usam
    echo "✓ Restarted usam"
else
    echo -e "${YELLOW}⚠ Could not find Django service${NC}"
    echo "Please restart manually: sudo systemctl restart <your-django-service>"
fi

echo ""
echo "Checking for Celery worker service..."
if systemctl list-units --type=service --all | grep -q "celery-worker"; then
    sudo systemctl restart celery-worker
    echo "✓ Restarted celery-worker"
elif systemctl list-units --type=service --all | grep -q "celery"; then
    sudo systemctl restart celery
    echo "✓ Restarted celery"
else
    echo -e "${YELLOW}⚠ Could not find Celery worker service${NC}"
fi

echo ""
echo "Checking for Celery beat service..."
if systemctl list-units --type=service --all | grep -q "celery-beat"; then
    sudo systemctl restart celery-beat
    echo "✓ Restarted celery-beat"
elif systemctl list-units --type=service --all | grep -q "celerybeat"; then
    sudo systemctl restart celerybeat
    echo "✓ Restarted celerybeat"
else
    echo -e "${YELLOW}⚠ Could not find Celery beat service${NC}"
fi

echo ""
echo "Checking for Nginx service..."
if systemctl list-units --type=service --all | grep -q "nginx"; then
    sudo systemctl restart nginx
    echo "✓ Restarted nginx"
else
    echo -e "${YELLOW}⚠ Nginx not found${NC}"
fi

echo ""
echo -e "${GREEN}[7/7]${NC} Checking service status..."
echo ""
echo "════════ Service Status ════════"
systemctl is-active nginx 2>/dev/null && echo "✓ Nginx: Running" || echo "✗ Nginx: Not running"
systemctl is-active gunicorn 2>/dev/null && echo "✓ Gunicorn: Running" || echo "⚠ Gunicorn: Check service name"
systemctl is-active celery-worker 2>/dev/null && echo "✓ Celery Worker: Running" || echo "⚠ Celery Worker: Check service name"
systemctl is-active redis 2>/dev/null && echo "✓ Redis: Running" || echo "⚠ Redis: Check if running"

echo ""
echo "════════════════════════════════════════"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Check logs: sudo journalctl -u gunicorn -n 50"
echo "2. Test site: curl -I https://jobs.usamif.com"
echo "3. Monitor: sudo journalctl -f"
echo ""
echo "New features deployed:"
echo "  • Rashid REST API (production-ready)"
echo "  • RTL support for Arabic"
echo "  • Interviews system"
echo "  • Email templates"
echo "  • i18n translations"
echo ""

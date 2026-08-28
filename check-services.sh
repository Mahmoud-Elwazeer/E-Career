#!/bin/bash
# Quick diagnostic script to find service names
# Run on server: bash check-services.sh

echo "════════════════════════════════════════"
echo "  Service Discovery Tool"
echo "════════════════════════════════════════"
echo ""

echo "[1] Checking for Django/Gunicorn services..."
systemctl list-units --type=service --all | grep -E "gunicorn|django|usam|ecareer" || echo "  None found"

echo ""
echo "[2] Checking for Celery services..."
systemctl list-units --type=service --all | grep -E "celery" || echo "  None found"

echo ""
echo "[3] Checking for Nginx..."
systemctl list-units --type=service --all | grep nginx || echo "  None found"

echo ""
echo "[4] Checking for Redis..."
systemctl list-units --type=service --all | grep redis || echo "  None found"

echo ""
echo "[5] Checking Python processes..."
ps aux | grep -E "python|gunicorn|celery" | grep -v grep | head -10 || echo "  None found"

echo ""
echo "[6] Checking virtual environment..."
if [ -d "/var/www/usam/backend/venv" ]; then
    echo "  ✓ Virtual environment exists at /var/www/usam/backend/venv"
    /var/www/usam/backend/venv/bin/python --version
else
    echo "  ✗ No virtual environment found"
    echo "  Create with: cd /var/www/usam/backend && python3 -m venv venv"
fi

echo ""
echo "[7] Checking installed packages..."
if [ -f "/var/www/usam/backend/venv/bin/pip" ]; then
    /var/www/usam/backend/venv/bin/pip list | grep -E "Django|celery|gunicorn" || echo "  Django packages not installed"
fi

echo ""
echo "[8] Checking migrations..."
if [ -d "/var/www/usam/backend/apps/interviews" ]; then
    echo "  ✓ Interviews app exists"
    if [ -d "/var/www/usam/backend/apps/interviews/migrations" ]; then
        echo "  ✓ Migrations directory exists"
        ls /var/www/usam/backend/apps/interviews/migrations/
    else
        echo "  ✗ No migrations directory"
    fi
else
    echo "  ✗ Interviews app not found"
fi

echo ""
echo "[9] Checking .env file..."
if [ -f "/var/www/usam/backend/.env" ]; then
    echo "  ✓ .env file exists"
    echo "  Configuration:"
    cat /var/www/usam/backend/.env | grep -E "TYPESENSE_API_KEY|AWS_ACCESS_KEY_ID" | sed 's/=.*/=***/' || echo "  (No API keys set)"
else
    echo "  ✗ .env file not found"
fi

echo ""
echo "[10] Checking frontend build..."
if [ -f "/var/www/usam/frontend/dist/index.html" ]; then
    echo "  ✓ Frontend built successfully"
    ls -lh /var/www/usam/frontend/dist/index.html
else
    echo "  ✗ Frontend not built"
fi

echo ""
echo "════════════════════════════════════════"
echo "Diagnostic complete!"
echo ""
echo "To fix common issues:"
echo "  1. Create venv: cd /var/www/usam/backend && python3 -m venv venv"
echo "  2. Install deps: source venv/bin/activate && pip install -r requirements.txt"
echo "  3. Run migrations: python3 manage.py migrate"
echo "  4. Find services: systemctl list-units | grep -E 'gunicorn|celery'"
echo ""

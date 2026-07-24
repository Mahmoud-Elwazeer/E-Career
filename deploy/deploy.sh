#!/bin/bash
# ============================================================
# USAM Career Compass — One-Command Deploy
# Pulls latest code, migrates, collects static, restarts
# Usage: bash deploy.sh [branch]
# ============================================================
set -euo pipefail

PROJECT_DIR="/var/www/usam"
BRANCH="${1:-develop}"
VENV="${PROJECT_DIR}/venv/bin"

echo "================================================================"
echo " USAM Career Compass — Deploying branch: ${BRANCH}"
echo "================================================================"

cd ${PROJECT_DIR}

# ── 1. Pull latest code ───────────────────────────────────────────────
echo "→ Pulling latest code from ${BRANCH}..."
git fetch origin
git checkout ${BRANCH}
git pull origin ${BRANCH}

# ── 2. Install/update Python dependencies ────────────────────────────
echo "→ Installing Python dependencies..."
${VENV}/pip install --upgrade pip
${VENV}/pip install -r backend/requirements/base.txt
${VENV}/pip install gunicorn

# ── 3. Django migrations ──────────────────────────────────────────────
echo "→ Running database migrations..."
cd backend
${VENV}/python manage.py migrate --noinput

# ── 4. Collect static files ───────────────────────────────────────────
echo "→ Collecting static files..."
${VENV}/python manage.py collectstatic --noinput --clear

# ── 5. Build React frontend ───────────────────────────────────────────
echo "→ Building React frontend..."
cd ${PROJECT_DIR}/frontend
if command -v npm &>/dev/null; then
  npm ci --prefer-offline
  npm run build
  # Copy build output to nginx-served dir
  rm -rf ${PROJECT_DIR}/frontend/dist_prev 2>/dev/null || true
  echo "→ Frontend built successfully."
fi

# ── 6. Restart Gunicorn ───────────────────────────────────────────────
echo "→ Restarting Gunicorn..."
systemctl restart gunicorn-usam

# Give Gunicorn a moment to start
sleep 3
systemctl is-active --quiet gunicorn-usam && echo "✓ Gunicorn is running" || echo "✗ Gunicorn failed to start — check logs"

# ── 7. Reload Nginx ───────────────────────────────────────────────────
echo "→ Testing and reloading Nginx..."
nginx -t && systemctl reload nginx && echo "✓ Nginx reloaded"

# ── 8. Health check ───────────────────────────────────────────────────
echo "→ Running health check..."
sleep 2
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health/ || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
  echo "✓ Health check passed (HTTP 200)"
else
  echo "✗ Health check returned HTTP ${HTTP_STATUS} — check logs:"
  echo "  journalctl -u gunicorn-usam -n 50 --no-pager"
fi

echo ""
echo "================================================================"
echo " ✅ Deploy complete — $(date)"
echo "================================================================"

#!/bin/bash
# ============================================================
# USAM Career Compass — One-Command Rollback
# Reverts to a specific git commit and restarts services
# Usage: bash rollback.sh [commit-hash]
#        bash rollback.sh           → shows last 10 commits to pick from
# ============================================================
set -euo pipefail

PROJECT_DIR="/var/www/usam"
VENV="${PROJECT_DIR}/venv/bin"
TARGET_COMMIT="${1:-}"

cd ${PROJECT_DIR}

if [ -z "$TARGET_COMMIT" ]; then
  echo "Recent commits (pick one to roll back to):"
  echo "--------------------------------------------"
  git log --oneline -10
  echo "--------------------------------------------"
  echo ""
  echo "Usage: bash rollback.sh <commit-hash>"
  exit 0
fi

echo "================================================================"
echo " USAM Career Compass — Rolling back to: ${TARGET_COMMIT}"
echo "================================================================"

# Confirm
read -rp "Roll back to ${TARGET_COMMIT}? This will restart Gunicorn. [y/N] " CONFIRM
if [[ "${CONFIRM:-n}" != "y" && "${CONFIRM:-n}" != "Y" ]]; then
  echo "Rollback cancelled."
  exit 0
fi

# ── 1. Checkout target commit ─────────────────────────────────────────
echo "→ Checking out ${TARGET_COMMIT}..."
git checkout "${TARGET_COMMIT}"

# ── 2. Re-install dependencies for that commit ───────────────────────
echo "→ Installing dependencies..."
${VENV}/pip install -r backend/requirements/production.txt --quiet

# ── 3. Run migrations (rollback migrations if needed separately) ─────
echo "→ Running migrations..."
cd backend
export DJANGO_SETTINGS_MODULE=config.settings.production
${VENV}/python manage.py migrate --noinput

# ── 4. Collect static ─────────────────────────────────────────────────
echo "→ Collecting static files..."
${VENV}/python manage.py collectstatic --noinput

# ── 5. Restart Gunicorn ───────────────────────────────────────────────
echo "→ Restarting Gunicorn..."
systemctl restart gunicorn-usam
sleep 2
systemctl is-active --quiet gunicorn-usam && echo "✓ Gunicorn running" || echo "✗ Gunicorn failed"

# ── 6. Reload Nginx ───────────────────────────────────────────────────
nginx -t && systemctl reload nginx && echo "✓ Nginx reloaded"

echo ""
echo "================================================================"
echo " ✅ Rollback to ${TARGET_COMMIT} complete — $(date)"
echo " To return to latest: git checkout main && bash deploy.sh"
echo "================================================================"

#!/bin/bash
# ============================================================
# USAM Career Compass — EC2 Server Bootstrap
# Ubuntu 22.04 LTS  |  Run once on a fresh instance
# Usage: bash ec2-setup.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="/var/www/usam"
REPO_URL="https://github.com/YOUR_GITHUB_USERNAME/usam-career-compass.git"
PYTHON_VERSION="3.12"
DB_NAME="usam_db"
DB_USER="usam_user"
DB_PASS="$(openssl rand -base64 24)"

echo "================================================================"
echo " USAM Career Compass — Server Bootstrap"
echo "================================================================"

# ── 1. System update ─────────────────────────────────────────────────
echo "→ Updating system packages..."
apt-get update -y && apt-get upgrade -y
apt-get install -y \
  curl wget git unzip \
  build-essential libssl-dev libffi-dev libpq-dev \
  python3.12 python3.12-venv python3.12-dev python3-pip \
  nginx postgresql postgresql-contrib \
  certbot python3-certbot-nginx \
  ufw fail2ban

# ── 2. Firewall ────────────────────────────────────────────────────────
echo "→ Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo "UFW rules active."

# ── 3. PostgreSQL ─────────────────────────────────────────────────────
echo "→ Setting up PostgreSQL database..."
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -c "
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='${DB_USER}') THEN
    CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
  END IF;
END
\$\$;" 2>/dev/null || true

sudo -u postgres psql -c "
SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='${DB_NAME}')
\gexec" 2>/dev/null || true

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" 2>/dev/null || true

echo "PostgreSQL configured. DB: ${DB_NAME}, User: ${DB_USER}"
echo "DB Password (save this!): ${DB_PASS}"

# ── 4. Project directory ──────────────────────────────────────────────
echo "→ Setting up project directory..."
mkdir -p ${PROJECT_DIR}/{media,staticfiles,logs}
useradd -r -s /bin/false www-usam 2>/dev/null || true
chown -R www-usam:www-data ${PROJECT_DIR}
chmod -R 755 ${PROJECT_DIR}

# ── 5. Clone repo ─────────────────────────────────────────────────────
echo "→ Cloning repository..."
if [ -d "${PROJECT_DIR}/.git" ]; then
  cd ${PROJECT_DIR} && git pull origin main
else
  git clone ${REPO_URL} ${PROJECT_DIR}
fi

# ── 6. Python virtualenv ──────────────────────────────────────────────
echo "→ Creating Python virtual environment..."
python3.12 -m venv ${PROJECT_DIR}/venv
${PROJECT_DIR}/venv/bin/pip install --upgrade pip
${PROJECT_DIR}/venv/bin/pip install -r ${PROJECT_DIR}/backend/requirements/production.txt

# ── 7. Environment file ───────────────────────────────────────────────
if [ ! -f "${PROJECT_DIR}/backend/.env" ]; then
  echo "→ Creating .env from example..."
  cp ${PROJECT_DIR}/backend/.env.example ${PROJECT_DIR}/backend/.env
  # Auto-fill database URL and secret key
  SECRET=$(python3.12 -c "import secrets; print(secrets.token_urlsafe(50))")
  sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgres://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}|" ${PROJECT_DIR}/backend/.env
  sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET}|" ${PROJECT_DIR}/backend/.env
  echo "⚠  .env created. Edit ${PROJECT_DIR}/backend/.env to fill remaining values."
fi

# ── 8. Django setup ───────────────────────────────────────────────────
echo "→ Running Django migrations and collectstatic..."
cd ${PROJECT_DIR}/backend
export DJANGO_SETTINGS_MODULE=config.settings.production
${PROJECT_DIR}/venv/bin/python manage.py migrate --noinput
${PROJECT_DIR}/venv/bin/python manage.py collectstatic --noinput
${PROJECT_DIR}/venv/bin/python manage.py seed_data

# ── 9. Gunicorn service ───────────────────────────────────────────────
echo "→ Installing Gunicorn systemd service..."
cp /home/ubuntu/usam-career-compass/deploy/gunicorn.service /etc/systemd/system/gunicorn-usam.service
systemctl daemon-reload
systemctl enable gunicorn-usam
systemctl restart gunicorn-usam

# ── 10. Nginx ─────────────────────────────────────────────────────────
echo "→ Installing Nginx config..."
cp /home/ubuntu/usam-career-compass/deploy/nginx.conf /etc/nginx/sites-available/usam
ln -sf /etc/nginx/sites-available/usam /etc/nginx/sites-enabled/usam
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "================================================================"
echo " ✅ Server bootstrap complete!"
echo "================================================================"
echo " Project:   ${PROJECT_DIR}"
echo " DB:        ${DB_NAME} / ${DB_USER} / ${DB_PASS}"
echo " Next steps:"
echo "   1. Edit ${PROJECT_DIR}/backend/.env"
echo "   2. Point your domain DNS → this server's IP"
echo "   3. Run: bash /home/ubuntu/usam-career-compass/deploy/ssl-setup.sh"
echo "================================================================"

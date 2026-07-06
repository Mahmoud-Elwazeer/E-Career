#!/bin/bash
set -e

echo "🚀 Deploying E-Career..."

PROJECT_DIR="/home/ubuntu/.openclaw/workspace-architect/E-Career"

cd $PROJECT_DIR
git pull origin develop 2>/dev/null || git pull origin main

# Backend
echo "📦 Backend: installing deps..."
cd $PROJECT_DIR/backend
source .venv/bin/activate
uv pip install -r requirements/base.txt -r requirements/production.txt -q

echo "🔄 Running migrations..."
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate --noinput

echo "📁 Collecting static..."
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py collectstatic --noinput 2>/dev/null

echo "🔄 Restarting backend..."
sudo systemctl restart ecareer-backend

# Frontend
echo "🏗️  Building frontend..."
cd $PROJECT_DIR/frontend
npm ci --silent
VITE_API_URL= npm run build

echo "📂 Deploying to nginx..."
sudo rm -rf /var/www/ecareer/*
sudo cp -r dist/* /var/www/ecareer/
sudo chown -R www-data:www-data /var/www/ecareer

echo "🔄 Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "✅ Deployed! Site: https://jobs.usamif.com"

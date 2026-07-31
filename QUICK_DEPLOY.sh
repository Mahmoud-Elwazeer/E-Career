#!/bin/bash
# Quick Phase 1 Deployment Script
# Run this on production server: ubuntu@13.49.245.174

set -e  # Exit on error

echo "======================================"
echo "Phase 1 Deployment to Production"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/usam/backend"
VENV_DIR="$PROJECT_DIR/venv"
DOCKER_COMPOSE_FILE="/var/www/usam/docker-compose.services.yml"

echo -e "${YELLOW}Step 1: Backup current state${NC}"
BACKUP_DIR="/var/www/usam/backend.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp -r "$PROJECT_DIR" "$BACKUP_DIR"
echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"

echo -e "${YELLOW}Step 2: Pull latest code${NC}"
cd "$PROJECT_DIR"
git stash || true
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"

echo -e "${YELLOW}Step 3: Activate virtual environment${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo -e "${YELLOW}Step 4: Install dependencies${NC}"
pip install -r requirements/base.txt
pip list | grep -E "qdrant|typesense|apache-age|playwright|docling"
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${YELLOW}Step 5: Install Playwright browsers${NC}"
playwright install chromium || echo "Playwright install skipped (already installed)"
echo -e "${GREEN}✓ Playwright ready${NC}"

echo -e "${YELLOW}Step 6: Setup PostgreSQL extensions${NC}"
sudo -u postgres psql -d usam_db << EOF
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
ALTER DATABASE usam_db SET search_path = ag_catalog, "\$user", public;
SELECT extname, extversion FROM pg_extension WHERE extname = 'age';
EOF
echo -e "${GREEN}✓ PostgreSQL extensions ready${NC}"

echo -e "${YELLOW}Step 7: Start Qdrant and Typesense${NC}"
cd /var/www/usam
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    cat > "$DOCKER_COMPOSE_FILE" << 'DOCKEREOF'
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.11.3
    container_name: usam_qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__SERVICE__API_KEY: usam_qdrant_key_2024
      QDRANT__SERVICE__ENABLE_CORS: "true"

  typesense:
    image: typesense/typesense:27.1
    container_name: usam_typesense
    restart: unless-stopped
    ports:
      - "8108:8108"
    volumes:
      - typesense_data:/data
    environment:
      TYPESENSE_DATA_DIR: /data
      TYPESENSE_API_KEY: usam_typesense_key_2024
      TYPESENSE_ENABLE_CORS: "true"
    command: '--data-dir /data --api-key=usam_typesense_key_2024 --enable-cors'

volumes:
  qdrant_data:
  typesense_data:
DOCKEREOF
fi

docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
sleep 5
echo -e "${GREEN}✓ Qdrant and Typesense started${NC}"

echo -e "${YELLOW}Step 8: Update environment variables${NC}"
cd "$PROJECT_DIR"
if ! grep -q "TYPESENSE_HOST" .env; then
    cat >> .env << 'ENVEOF'

# ── Phase 1 Configuration ────────────────────────────────────────
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http
TYPESENSE_API_KEY=usam_typesense_key_2024
SEARCH_TRUST_SCORE_THRESHOLD=0.4

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=usam_qdrant_key_2024

# AWS Bedrock (Add your credentials)
AWS_ACCESS_KEY_ID=your-aws-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-here
AWS_DEFAULT_REGION=us-east-1

AI_USER_DAILY_TOKEN_LIMIT=50000
ENVEOF
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env to add AWS credentials!${NC}"
fi
echo -e "${GREEN}✓ Environment variables updated${NC}"

echo -e "${YELLOW}Step 9: Run database migrations${NC}"
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
python manage.py migrate
echo -e "${GREEN}✓ Migrations complete${NC}"

echo -e "${YELLOW}Step 10: Setup vector collections${NC}"
python manage.py setup_vector_collections
echo -e "${GREEN}✓ Vector collections created${NC}"

echo -e "${YELLOW}Step 11: Collect static files${NC}"
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data "$PROJECT_DIR/staticfiles"
echo -e "${GREEN}✓ Static files collected${NC}"

echo -e "${YELLOW}Step 12: Setup Celery services${NC}"
if [ ! -f /etc/systemd/system/celery-worker.service ]; then
    sudo tee /etc/systemd/system/celery-worker.service > /dev/null << 'CELERYEOF'
[Unit]
Description=Celery Worker for USAM
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
EnvironmentFile=/var/www/usam/backend/.env
WorkingDirectory=/var/www/usam/backend
ExecStart=/var/www/usam/backend/venv/bin/celery -A config worker -l info
Restart=on-failure

[Install]
WantedBy=multi-user.target
CELERYEOF

    sudo tee /etc/systemd/system/celery-beat.service > /dev/null << 'BEATEOF'
[Unit]
Description=Celery Beat for USAM
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
EnvironmentFile=/var/www/usam/backend/.env
WorkingDirectory=/var/www/usam/backend
ExecStart=/var/www/usam/backend/venv/bin/celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=on-failure

[Install]
WantedBy=multi-user.target
BEATEOF

    sudo systemctl daemon-reload
    sudo systemctl enable celery-worker celery-beat
fi
echo -e "${GREEN}✓ Celery services configured${NC}"

echo -e "${YELLOW}Step 13: Restart all services${NC}"
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
sudo systemctl reload nginx
echo -e "${GREEN}✓ All services restarted${NC}"

echo -e "${YELLOW}Step 14: Verification${NC}"
sleep 3

# Health checks
echo "Testing endpoints..."
curl -s http://localhost:8000/health/ | grep -q "healthy" && echo -e "${GREEN}✓ Django health OK${NC}" || echo -e "${RED}✗ Django health failed${NC}"
curl -s http://localhost:6333/health | grep -q "title" && echo -e "${GREEN}✓ Qdrant health OK${NC}" || echo -e "${RED}✗ Qdrant health failed${NC}"
curl -s http://localhost:8108/health | grep -q "ok" && echo -e "${GREEN}✓ Typesense health OK${NC}" || echo -e "${RED}✗ Typesense health failed${NC}"
curl -s http://localhost:8000/api/v1/vectors/health/ | grep -q "success" && echo -e "${GREEN}✓ Vector API OK${NC}" || echo -e "${RED}✗ Vector API failed${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}Phase 1 Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "Access your site:"
echo "  • Website: http://13.49.245.174/"
echo "  • Admin: http://13.49.245.174/admin/"
echo "  • API Docs: http://13.49.245.174/api/docs/"
echo ""
echo "Next steps:"
echo "  1. Edit .env to add AWS Bedrock credentials"
echo "  2. Import ESCO data: python manage.py import_esco --skills /path/to/esco/skills.csv"
echo "  3. Embed jobs: python manage.py embed_jobs"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}⚠ Remember to add AWS credentials in .env for AI features!${NC}"

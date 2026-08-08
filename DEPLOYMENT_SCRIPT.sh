#!/bin/bash
# E-Career Production Deployment Script
# Deploy ESCO data and generate embeddings

set -e  # Exit on error

SERVER="ubuntu@13.49.245.174"
PROJECT_DIR="/var/www/usam"

echo "======================================"
echo "E-CAREER PRODUCTION DEPLOYMENT"
echo "======================================"
echo ""

# Step 1: Upload ESCO sample data
echo "[1/3] Uploading ESCO sample data..."
scp backend/data/esco/skills_sample.csv $SERVER:$PROJECT_DIR/backend/data/esco/
scp backend/data/esco/occupations_sample.csv $SERVER:$PROJECT_DIR/backend/data/esco/
scp backend/data/esco/mappings_sample.csv $SERVER:$PROJECT_DIR/backend/data/esco/
echo "✓ ESCO data uploaded"
echo ""

# Step 2: Import ESCO data on server
echo "[2/3] Importing ESCO data on production..."
ssh $SERVER << 'ENDSSH'
cd /var/www/usam/backend
source ../venv/bin/activate

echo "Importing ESCO skills, occupations, and mappings..."
python3 manage.py import_esco \
  --skills data/esco/skills_sample.csv \
  --occupations data/esco/occupations_sample.csv \
  --mappings data/esco/mappings_sample.csv

echo "Verifying import..."
python3 manage.py shell -c "
from apps.skills.models import Skill, Occupation
print(f'✓ Skills: {Skill.objects.count()}')
print(f'✓ Occupations: {Occupation.objects.count()}')
"

ENDSSH
echo "✓ ESCO data imported"
echo ""

# Step 3: Generate embeddings for all jobs
echo "[3/3] Generating embeddings for all jobs..."
ssh $SERVER << 'ENDSSH'
cd /var/www/usam/backend
source ../venv/bin/activate

echo "Generating embeddings (this may take 5-10 minutes for 221 jobs)..."
python3 manage.py embed_jobs --batch-size 50

echo ""
echo "Verifying embeddings..."
python3 manage.py shell -c "
from apps.jobs.models import Job
total = Job.objects.filter(status='active').count()
embedded = Job.objects.filter(status='active', embedding__isnull=False).count()
print(f'✓ Total active jobs: {total}')
print(f'✓ Jobs with embeddings: {embedded}')
print(f'✓ Coverage: {embedded/total*100:.1f}%' if total > 0 else '✓ No jobs found')
"

ENDSSH
echo "✓ Embeddings generated"
echo ""

echo "======================================"
echo "✓ DEPLOYMENT COMPLETE"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Test semantic search at https://jobs.usamif.com"
echo "  2. Verify ESCO skills are available in Career Brain"
echo "  3. Check Proactive Rashid recommendations"
echo ""

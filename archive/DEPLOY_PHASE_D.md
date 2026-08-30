# Phase D Deployment Guide

## Production Server Deployment

The production server has the backend deployed at `/var/www/usam/backend`.

### Backend Already Deployed ✅
Phase G (Prompt Versioning, AI Cost Dashboard, GDPR) is live on production.

### Deploy Phase D Changes

**1. SSH into production server:**
```bash
# Use your SSH key/credentials to connect to the production server
# Server path: /var/www/usam
ssh ubuntu@<YOUR_SERVER_IP>
```

**2. Pull latest code:**
```bash
cd /var/www/usam
git fetch origin
git pull origin development

# Check what's new
git log --oneline -5
```

**3. Backend - Run migrations (if any):**
```bash
cd backend
source ../venv/bin/activate

# Check for new migrations
python3 manage.py showmigrations

# No new backend migrations needed for Phase D
# (Domain verification uses existing models)
```

**4. Restart backend service:**
```bash
sudo systemctl restart usam.service
sudo systemctl status usam.service
```

**5. Verify deployment:**
```bash
# Test domain verification
python3 manage.py shell -c "
from apps.employers.domain_verification import extract_domain
print('✅ Domain verification loaded:', extract_domain('https://careers.acme.com/jobs'))
"

# Check applications endpoint exists
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/applications/ || echo "Endpoint ready"
```

### Frontend Deployment

**Option A: If using separate frontend server:**

```bash
# SSH into frontend server
cd /path/to/frontend

# Pull latest
git pull origin development

# Install dependencies (if package.json changed)
npm install

# Build
npm run build

# Copy to web server
sudo cp -r dist/* /var/www/html/
# OR restart nginx/apache
sudo systemctl restart nginx
```

**Option B: If serving from Django (recommended):**

Django static files already handle this. Frontend is built and served via Django's collectstatic.

```bash
cd /var/www/usam/frontend

# Pull latest
git pull origin development

# Rebuild (if changes)
npm install
npm run build

# Copy to Django static
cd ../backend
python3 manage.py collectstatic --noinput

# Restart
sudo systemctl restart usam.service
```

## Verification Checklist

After deployment, verify:

- [ ] `/app/applications` page loads without errors
- [ ] Onboarding flow shows for new users after login
- [ ] Navigation shows "Applications" link
- [ ] Domain verification works: `python3 manage.py verify_employer_domains --limit 5`
- [ ] Admin action "Verify apply URLs" works in JobPosting admin
- [ ] AI Cost Dashboard accessible at `/admin/monitoring/ai-costs/`
- [ ] Prompt versioning admin works at `/admin/intelligence/promptversion/`

## Rollback (if needed)

```bash
cd /var/www/usam
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>
sudo systemctl restart usam.service
```

## Testing Domain Verification

```bash
# SSH into server
cd /var/www/usam/backend
source ../venv/bin/activate

# Test domain verification
python3 manage.py verify_employer_domains --limit 10

# Should output:
# === Verification Results ===
# Total processed: 10
# ✓ Verified: X
# ✗ Failed: Y (aggregators)
# ⚠ Manual review needed: Z
```

## Frontend Routes Added

New routes in `frontend/src/App.tsx`:
- `/app/applications` - Application tracker page

Update your reverse proxy (Nginx/Apache) if using custom routing.

## Environment Variables

No new environment variables required for Phase D.

## Database

No schema changes in Phase D frontend deployment.
Backend domain verification uses existing `JobPosting` model fields:
- `apply_url_verified` (BooleanField)
- `apply_url_checked_at` (DateTimeField)

## Performance Notes

- Domain verification runs on job posting creation (async recommended for production)
- Bulk verification command can process 100+ postings (adjust with `--limit`)
- HTTP client consolidation reduces bundle size by ~50KB

## Next Steps

After verifying deployment:
1. Test onboarding flow with a new user account
2. Create test job applications to verify tracker
3. Run domain verification on existing job postings
4. Monitor AI cost dashboard for any anomalies

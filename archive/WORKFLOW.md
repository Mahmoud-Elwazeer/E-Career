# Development Workflow Guide

## Quick Reference

### Local Development
```bash
# Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

### Deploy to Production
```bash
# 1. Commit locally
git add .
git commit -m "Description"
git push origin development:main

# 2. Deploy on server
ssh ubuntu@13.49.245.174
cd /var/www/usam/backend
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart usam

# 3. Build frontend (if changed)
cd /var/www/usam/frontend
npm install
npm run build
sudo systemctl reload nginx
```

---

## Branch Strategy

- **local `development`** → all local work happens here
- **remote `main`** → production branch (pulled by server)
- Push: `git push origin development:main`

---

## Adding a New Feature

### 1. Create Django App
```bash
cd backend
python manage.py startapp apps/myapp
```

### 2. Register in INSTALLED_APPS
Edit `backend/config/settings/base.py`:
```python
INSTALLED_APPS = [
    # ...
    "apps.myapp",
]
```

### 3. Create Models
Edit `apps/myapp/models.py`:
```python
from apps.core.models import UUIDModel

class MyModel(UUIDModel):
    name = models.CharField(max_length=255)
```

### 4. Make Migrations
```bash
python manage.py makemigrations myapp
python manage.py migrate
```

### 5. Create Views & URLs
`apps/myapp/views.py`:
```python
from rest_framework.views import APIView
from rest_framework.response import Response

class MyView(APIView):
    def get(self, request):
        return Response({"message": "Hello"})
```

`apps/myapp/urls.py`:
```python
from django.urls import path
from .views import MyView

urlpatterns = [
    path('', MyView.as_view()),
]
```

### 6. Include in Main URLs
Edit `backend/config/urls.py`:
```python
urlpatterns = [
    # ...
    path("myapp/", include("apps.myapp.urls")),
]
```

### 7. Test Locally
```bash
curl http://localhost:8000/api/myapp/
```

### 8. Deploy
```bash
git add apps/myapp
git commit -m "Add myapp feature"
git push origin development:main
# Then run deploy commands on server
```

---

## Common Tasks

### Update Dependencies
```bash
# Backend
pip install package-name
pip freeze > requirements/base.txt

# Frontend
npm install package-name
```

### Database Operations
```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Rollback migration
python manage.py migrate appname 0001

# Create superuser
python manage.py createsuperuser
```

### Celery Tasks
```bash
# Run worker
celery -A config worker -l info

# Run beat scheduler
celery -A config beat -l info
```

### Docker Services
```bash
# Start Typesense + Qdrant
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f typesense
```

---

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
sudo journalctl -u usam -n 50

# Test manually
cd /var/www/usam/backend
source /var/www/usam/venv/bin/activate
python manage.py check
python manage.py runserver 0:8000
```

### Frontend Build Fails
```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build
```

### Database Issues
```bash
# Connect to database
sudo -u postgres psql -d eusam_db

# Check migrations
python manage.py showmigrations
```

### Import Errors (AppRegistryNotReady)
- Never import models at module level in `__init__.py`
- Use lazy imports inside functions
- Check for circular imports

---

## File Naming Conventions

- Models: `PascalCase` (e.g., `class TalentScore`)
- Views: `PascalCase` for classes, `snake_case` for functions
- URLs: `kebab-case` (e.g., `/api/talent-score/`)
- Files: `snake_case.py`
- Components: `PascalCase.tsx`

---

## Code Style

### Python
- Follow PEP 8
- Use type hints where possible
- Docstrings for complex functions
- Keep views thin, logic in services

### TypeScript/React
- Use functional components
- Custom hooks for logic
- Services for API calls
- Keep components small

---

## Testing

### Backend
```bash
# Run tests
python manage.py test

# Run specific app
python manage.py test apps.career

# Coverage
coverage run manage.py test
coverage report
```

### Frontend
```bash
# Run tests
npm test

# Watch mode
npm run test:watch
```

---

## Environment Variables

### Never commit:
- `.env` files
- API keys
- Database passwords
- AWS credentials

### Always use:
- `.env.example` as template
- Environment variables in code
- `python-decouple` for Django
- `import.meta.env` for Vite

---

## Before Pushing

1. ✅ Code works locally
2. ✅ No `console.log` or `print()` debug statements
3. ✅ Migrations created (`makemigrations`)
4. ✅ Tests pass
5. ✅ No sensitive data in code
6. ✅ Commit message is descriptive

---

## After Deploying

1. ✅ Server restarts without errors
2. ✅ Health check returns 200: `curl https://jobs.usamif.com/health/`
3. ✅ Frontend loads correctly
4. ✅ Check logs for errors: `sudo journalctl -u usam -n 20`
5. ✅ Test the new feature in browser

---

## Emergency Rollback

```bash
# On server
cd /var/www/usam/backend
git log --oneline -5
git reset --hard <previous-commit-hash>
sudo systemctl restart usam
```

---

## Useful Commands Cheatsheet

```bash
# Django
python manage.py shell
python manage.py dbshell
python manage.py createsuperuser
python manage.py collectstatic --noinput

# Git
git status
git log --oneline -10
git diff
git stash
git stash pop

# System
sudo systemctl status usam
sudo systemctl restart usam
sudo systemctl reload nginx
sudo tail -f /var/log/nginx/error.log

# Database
sudo -u postgres psql -d eusam_db
\dt  # list tables
\d+ tablename  # describe table
```

---

**Remember**: Test locally before deploying. Small, frequent commits are better than large, infrequent ones.

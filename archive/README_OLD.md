# USAM Career Compass

A full-stack job aggregation platform for the MENA region — built with Django 5, DRF, and React.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 5, Django REST Framework |
| Auth | JWT (simplejwt) + Google OAuth (allauth) |
| Database | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Admin UI | django-unfold |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Deploy | EC2 + Nginx + Gunicorn + Let's Encrypt |

---

## Quick Start (Local Development)

1. `git clone https://github.com/YOUR_USERNAME/usam-career-compass.git`
2. `cd project/backend && cp .env.example .env` — fill in values
3. `pip install -r requirements/development.txt`
4. `python manage.py migrate`
5. `python manage.py seed_data`
6. `python manage.py runserver`
7. `cd ../frontend && npm install && npm run dev`
8. Open http://localhost:5173

**API Docs:** http://localhost:8000/api/docs/
**Admin:** http://localhost:8000/admin/

---

## Local Development Setup

### Backend

```bash
# 1. Clone and enter project
git clone https://github.com/YOUR_USERNAME/usam-career-compass.git
cd usam-career-compass

# 2. Create virtualenv
cd backend
python3.12 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements/development.txt

# 4. Create environment file
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and DATABASE_URL
# For SQLite in dev, leave DATABASE_URL blank

# 5. Run migrations
python manage.py migrate

# 6. Seed demo data (creates admin + demo user + 20 jobs)
python manage.py seed_data

# 7. Start dev server
python manage.py runserver
```

The backend runs at `http://localhost:8000`

**Default accounts after seeding:**

| Role | Email | Password | Notes |
|---|---|---|---|
| Super Admin | superadmin@gmail.com | SuperAdmin@2025! | Full Django admin access |
| Admin | admin@gmail.com | Admin@2025! | Staff access, admin API |
| User | user@gmail.com | User@2025! | Regular user, browse jobs |

**Key URLs:**
- API: `http://localhost:8000/api/v1/`
- Swagger docs: `http://localhost:8000/api/docs/`
- Admin panel: `http://localhost:8000/admin/`
- Health check: `http://localhost:8000/health/`

### Frontend

```bash
cd frontend

# Create env file
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend runs at `http://localhost:8080`

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in all values.

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) | Yes |
| `DEBUG` | `True` for dev, `False` for prod | Yes |
| `ALLOWED_HOSTS` | Comma-separated hostnames | Yes |
| `ADMIN_URL` | Secret admin path (e.g. `my-secret-admin/`) | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes (prod) |
| `FRONTEND_URL` | Frontend base URL for email links | Yes |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth app client ID | For OAuth |
| `GOOGLE_CLIENT_SECRET` | Google OAuth app secret | For OAuth |
| `EMAIL_HOST_USER` | Gmail address for sending emails | For email |
| `EMAIL_HOST_PASSWORD` | Gmail app password | For email |

### Frontend env

| Variable | Description |
|---|---|
| `VITE_API_URL` | Django API base URL (e.g. `https://yourdomain.com/api/v1`) |

---

## Running Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run a specific test file
pytest tests/integration/test_auth.py -v
```

---

## API Reference

Full interactive API documentation is available at `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc).

### Auth Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | Register new user | No |
| POST | `/api/v1/auth/login/` | Login, receive JWT | No |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token | Yes |
| POST | `/api/v1/auth/token/refresh/` | Get new access token | No |
| POST | `/api/v1/auth/password/reset/` | Request password reset email | No |
| POST | `/api/v1/auth/password/reset/confirm/` | Confirm password reset | No |

### User Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| GET/PATCH/DELETE | `/api/v1/users/me/` | Current user profile | Yes |
| POST | `/api/v1/users/me/avatar/` | Upload avatar | Yes |
| POST | `/api/v1/users/me/change-password/` | Change password | Yes |
| GET/POST | `/api/v1/users/me/saved-jobs/` | Saved jobs list/save | Yes |
| DELETE | `/api/v1/users/me/saved-jobs/<id>/` | Unsave a job | Yes |
| GET/POST | `/api/v1/users/me/alerts/` | Alerts list/create | Yes |
| GET/PATCH/DELETE | `/api/v1/users/me/alerts/<uuid>/` | Alert detail | Yes |
| GET | `/api/v1/users/me/notifications/` | Notifications | Yes |
| PATCH | `/api/v1/users/me/notifications/<uuid>/` | Mark read | Yes |
| POST | `/api/v1/users/me/notifications/mark-all-read/` | Mark all read | Yes |

### Jobs Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/jobs/` | List jobs (filterable) | No |
| POST | `/api/v1/jobs/` | Create job | Admin |
| GET | `/api/v1/jobs/<slug>/` | Job detail | No |
| PATCH | `/api/v1/jobs/<slug>/` | Update job | Admin |
| DELETE | `/api/v1/jobs/<slug>/` | Archive job | Admin |
| POST | `/api/v1/jobs/<slug>/apply/` | Track apply click | No |
| GET | `/api/v1/jobs/<slug>/similar/` | Similar jobs | No |
| GET | `/api/v1/jobs/companies/` | List companies | No |
| GET | `/api/v1/jobs/sources/` | List sources | No |
| GET | `/api/v1/jobs/tags/` | List tags | No |

**Job filters:** `q`, `work_mode`, `industry`, `seniority`, `location`, `company`, `tag`, `salary_min`, `salary_max`

**Ordering:** `posted_at`, `salary_min`, `salary_max`, `title` (prefix `-` for descending)

### Analytics Endpoints (Admin only)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/analytics/stats/` | Dashboard stats |
| GET | `/api/v1/analytics/charts/` | Jobs by industry/source |
| GET | `/api/v1/analytics/clicks/` | Apply-click analytics |
| GET | `/api/v1/analytics/searches/` | Search query analytics |
| GET | `/api/v1/analytics/conversion/` | View-to-click conversion |
| GET | `/api/v1/analytics/activity-logs/` | Admin activity log |

---

## AWS Deployment

### Prerequisites
- EC2 instance: Ubuntu 22.04 LTS, t2.micro or larger
- Domain name with DNS A record pointing to EC2 IP
- GitHub repository with your code

### Step-by-step

```bash
# 1. SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 2. Upload deploy scripts
scp -i your-key.pem deploy/*.sh ubuntu@YOUR_EC2_IP:~/

# 3. Run server bootstrap (installs everything)
sudo bash ec2-setup.sh

# 4. Fill in environment variables
sudo nano /var/www/usam/backend/.env

# 5. Deploy the application
sudo bash deploy.sh

# 6. Set up SSL (requires DNS already pointing to this IP)
sudo bash ssl-setup.sh yourdomain.com

# 7. Visit your live site
curl https://yourdomain.com/health/
```

### Rolling Back

```bash
# See recent commits
sudo bash rollback.sh

# Roll back to a specific commit
sudo bash rollback.sh abc1234
```

### Logs

```bash
# Gunicorn logs
journalctl -u gunicorn-usam -f

# Nginx logs
tail -f /var/log/nginx/usam_error.log
tail -f /var/log/nginx/usam_access.log

# Django application logs
tail -f /var/www/usam/logs/django.log
```

---

## Project Structure

```
usam-career-compass/
├── backend/
│   ├── apps/
│   │   ├── accounts/     # Auth, User model
│   │   ├── core/         # Shared utilities, FeatureFlags, Media
│   │   ├── jobs/         # Companies, Sources, Tags, Jobs
│   │   ├── users/        # SavedJobs, Alerts, Notifications
│   │   └── analytics/    # JobView, JobClick, SearchLog
│   ├── config/
│   │   ├── settings/     # base / development / production / test
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── templates/emails/ # Welcome + password reset emails
│   ├── tests/            # pytest + factory_boy
│   ├── manage.py
│   └── requirements/
├── frontend/
│   ├── src/
│   │   ├── pages/        # All page components
│   │   ├── components/   # UI + admin components
│   │   ├── hooks/        # Auth, saved jobs, alerts, etc.
│   │   ├── services/     # API client (client.ts, auth.ts, jobs.ts, etc.)
│   │   └── lib/          # Utilities, shims
│   └── vite.config.ts
└── deploy/
    ├── ec2-setup.sh      # Full server bootstrap
    ├── nginx.conf        # Reverse proxy + SSL
    ├── gunicorn.service  # Systemd unit
    ├── ssl-setup.sh      # Let's Encrypt
    ├── deploy.sh         # One-command deploy
    └── rollback.sh       # One-command rollback
```

---

## Post-MVP Roadmap

- Replace local media storage with **AWS S3** (`django-storages` — structure is ready, one config change)
- Replace SMTP email with **AWS SES** — one backend swap
- Add **Celery + Redis** for async tasks (alert emails, scraper jobs)
- Add more **OAuth providers** via allauth (LinkedIn, GitHub)
- Add **salary filter** (feature flag `salary_filter` already exists)
- Add **job scraper** service to auto-import from sources
- Add **Elasticsearch** for full-text search at scale

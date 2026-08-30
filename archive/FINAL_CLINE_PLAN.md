> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# FINAL Cline Implementation Plan - All Remaining Work
## E-Career Platform - Complete Audit & Phases
## Date: August 7, 2026

---

## AUDIT RESULTS: What's Done vs What's Missing

### DONE (Deployed & Working)
- [x] Django backend with 21 apps (accounts, jobs, rashid, employers, verification, skills, intelligence, career, search, vectors, analytics, assessment, emails, events, monitoring, salary, scraper, users, core, profiles)
- [x] React frontend with 18+ pages
- [x] Rashid AI character system (floating widget, 7 poses, navbar link, onboarding)
- [x] Rashid backend with Bedrock Claude Sonnet integration
- [x] Employer features (dashboard, register, job posting form)
- [x] Verification engine structure (engine.py, stages/, tasks.py)
- [x] Skills app with ESCO models, extraction, graph system
- [x] Career app with scoring engine, 808-line models
- [x] Search service with Typesense plugin
- [x] Vectors service with Qdrant + pgvector + Cohere plugins
- [x] Events system (emitter, consumers)
- [x] Intelligence app (Bedrock plugin, circuit breaker, LLM plugin)
- [x] Docker Compose (postgres, redis, typesense, backend+daphne, celery worker, celery beat)
- [x] 200+ jobs seeded in database
- [x] Production deployed at jobs.usamif.com
- [x] Assessment app (models exist)
- [x] Salary app (models exist)
- [x] Monitoring app (models exist)

### MISSING (Not Implemented)
- [ ] **Interviews app** — Does NOT exist (`backend/apps/interviews/` missing)
- [ ] **i18n / Arabic translations** — No translation files exist
- [ ] **RTL layout support** — Not implemented
- [ ] **REST API fallback for Rashid chat** — Frontend still uses WebSocket (won't work in prod with Gunicorn)
- [ ] **CV parsing pipeline** — Docling/pdfplumber/EasyOCR not integrated
- [ ] **GitHub OAuth integration** — Not implemented
- [ ] **GDPR data export/deletion** — gdpr_service.py exists but endpoints missing
- [ ] **Email templates** — HTML email templates not built
- [ ] **Push notifications / PWA** — Not implemented
- [ ] **Resume builder** — Not implemented
- [ ] **Natural language search** — Not implemented
- [ ] **A/B testing framework** — Not implemented
- [ ] **Proper test suite** — No meaningful tests
- [ ] **Rate limiting configuration** — Not configured per endpoint
- [ ] **SSL/HTTPS on production** — May not be configured
- [ ] **ESCO/O*NET data import commands** — Commands may not be complete
- [ ] **Typesense API key on production** — Getting 401 errors
- [ ] **Qdrant API key on production** — Getting 401 errors
- [ ] **ATS scrapers beyond seed data** — No real scraping active

---

## PHASE 1: Critical Production Fixes (Must Do Now)
**Time: 2-3 hours | Priority: CRITICAL**

### Cline Prompt:

```
## Task: Fix Rashid Chat to work in production (REST API mode)

### Context:
- Production runs Gunicorn (HTTP only), NOT Daphne/WebSocket
- The Rashid chat page and mini-chat widget use WebSocket which fails silently
- Backend already has REST endpoints at /api/v1/rashid/conversations/ 
- Need to make the frontend work via REST API

### Requirements:

#### 1. Create a REST API hook for Rashid chat
File: `frontend/src/hooks/use-rashid-api.ts`

Create a React hook that provides:
- `createConversation(mode: string)` → POST /api/v1/rashid/conversations/
- `sendMessage(conversationId: string, content: string)` → POST /api/v1/rashid/conversations/{id}/send_message/
- `getMessages(conversationId: string)` → GET /api/v1/rashid/conversations/{id}/messages/
- Use the existing auth token from localStorage ('accessToken')
- Base URL: `import.meta.env.VITE_API_URL || '/api/v1'`

#### 2. Update RashidMiniChat.tsx to use REST API
File: `frontend/src/components/rashid/RashidMiniChat.tsx`

Replace any WebSocket usage with the REST hook:
- On open: create conversation if none exists
- On send: call sendMessage, show typing indicator, display response
- Load previous messages on mount if conversationId exists

#### 3. Update RashidChat.tsx page to use REST API
File: `frontend/src/pages/RashidChat.tsx`

Same approach - replace WebSocket with REST calls.
Show a proper chat interface with:
- Message history
- Input field
- Typing indicator during AI response
- Tool results display (CV review, cover letter, etc.)

#### 4. Verify backend send_message endpoint
File: `backend/apps/rashid/views.py`

Ensure the `send_message` action on the ConversationViewSet:
- Accepts POST with `{ "content": "..." }`
- Creates user message
- Calls RashidService.get_response()
- Creates assistant message
- Returns both messages in response

If there are import errors or missing methods, fix them.
Do NOT change the WebSocket code (keep it for future Daphne deployment).
```

---

## PHASE 2: Interviews App (New Feature)
**Time: 3-4 hours | Priority: HIGH**

### Cline Prompt:

```
## Task: Create the interviews Django app for AI mock interviews

### Context:
- The career app exists at backend/apps/career/ with scoring
- The Rashid service exists at backend/apps/rashid/service.py with Bedrock integration
- The skills app has ESCO taxonomy
- Frontend needs a new page for interview practice

### Requirements:

#### 1. Create Django app
Run: `cd backend && python manage.py startapp interviews apps/interviews`

#### 2. Create models
File: `backend/apps/interviews/models.py`

```python
from django.db import models
from django.conf import settings

class InterviewSession(models.Model):
    INTERVIEW_TYPES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('coding', 'Coding'),
        ('system_design', 'System Design'),
        ('case_study', 'Case Study'),
    ]
    MODES = [('text', 'Text'), ('voice', 'Voice')]
    STATUS = [('in_progress', 'In Progress'), ('completed', 'Completed'), ('abandoned', 'Abandoned')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_sessions')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    target_role = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=10, choices=[('easy','Easy'),('medium','Medium'),('hard','Hard')], default='medium')
    mode = models.CharField(max_length=10, choices=MODES, default='text')
    status = models.CharField(max_length=20, choices=STATUS, default='in_progress')
    
    overall_score = models.FloatField(null=True, blank=True)
    score_breakdown = models.JSONField(null=True, blank=True)
    feedback_summary = models.TextField(blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']

class InterviewQuestion(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    question_index = models.IntegerField()
    question_text = models.TextField()
    answer_text = models.TextField(blank=True)
    
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    score_details = models.JSONField(null=True, blank=True)
    
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['question_index']
        unique_together = ('session', 'question_index')
```

#### 3. Create service
File: `backend/apps/interviews/service.py`

Build InterviewService class that:
- `generate_questions(interview_type, target_role, difficulty, user_context)` → uses Bedrock Haiku to generate 5 questions
- `evaluate_answer(question, answer, interview_type, target_role)` → uses Bedrock Sonnet to score answer on 6 dimensions (relevance, depth, structure, technical, communication, growth)
- `complete_session(session)` → aggregates scores, generates feedback summary

Use: `from apps.rashid.service import RashidService` or directly use `from ai.bedrock import bedrock_service`

#### 4. Create views
File: `backend/apps/interviews/views.py`

Endpoints:
- POST `/api/v1/interviews/start/` — create session, generate questions, return first question
- POST `/api/v1/interviews/{id}/answer/` — submit answer for current question, return score + next question
- POST `/api/v1/interviews/{id}/complete/` — finish session, return overall score
- GET `/api/v1/interviews/history/` — list user's past sessions with scores

#### 5. Create urls.py and register in config/urls.py
File: `backend/apps/interviews/urls.py`

#### 6. Add to INSTALLED_APPS
File: `backend/config/settings/base.py` — add `'apps.interviews'`

#### 7. Create migration
Run: `python manage.py makemigrations interviews`

#### 8. Create frontend page
File: `frontend/src/pages/InterviewPractice.tsx`

Build a page that:
- Step 1: Choose interview type (technical/behavioral/coding) + target role + difficulty
- Step 2: Q&A flow — show question, user types answer, submit, see score + feedback
- Step 3: Summary — overall score, strengths, weaknesses, suggestions
- Add radar chart for score dimensions using recharts

#### 9. Add route to App.tsx
Add: `<Route path="/app/interviews" element={<RequireAuth><InterviewPractice /></RequireAuth>} />`

#### 10. Add to Navbar
In navItems array add: `{ to: "/app/interviews", label: "Interview", labelAr: "مقابلة", icon: Mic }`
Import Mic from lucide-react.
```

---

## PHASE 3: Arabic i18n & RTL Support
**Time: 3-4 hours | Priority: HIGH**

### Cline Prompt:

```
## Task: Implement Arabic internationalization and RTL support

### Context:
- The app already has a `lang` state from `useTheme()` hook that returns 'ar' or 'en'
- The Navbar already shows Arabic labels (`labelAr` property)
- Need to add full translation system and RTL layout

### Requirements:

#### 1. Install react-i18next
Run in frontend/: `npm install react-i18next i18next i18next-browser-languagedetector`

#### 2. Create translation files
File: `frontend/src/i18n/en.json`
File: `frontend/src/i18n/ar.json`

Include translations for:
- Navigation items (Jobs, Companies, Profile, Rashid, About, Interviews)
- Common actions (Search, Apply, Save, Share, Login, Register, Submit)
- Job card fields (Location, Salary, Experience, Posted, Deadline, Remote, Hybrid, Onsite)
- Profile sections (Skills, Experience, Education, CV, Score)
- Rashid phrases (Ask Rashid, Career Advisor, Type a message)
- Interview page (Start Interview, Submit Answer, Next Question, Your Score)
- Employer page (Post Job, Applications, Candidates, Shortlist)
- Error messages (Not Found, Unauthorized, Server Error)
- Filters (All, Full Time, Part Time, Contract, Entry, Mid, Senior)

#### 3. Setup i18n config
File: `frontend/src/i18n/index.ts`

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import ar from './ar.json';

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, ar: { translation: ar } },
  lng: localStorage.getItem('lang') || 'ar',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
```

#### 4. Add RTL support
File: `frontend/src/App.tsx` — wrap BrowserRouter content with dir={lang === 'ar' ? 'rtl' : 'ltr'}

File: `frontend/tailwind.config.ts` — add RTL plugin:
```
plugins: [require('tailwindcss-rtl')],
```

Run: `npm install tailwindcss-rtl`

#### 5. Update key pages to use translations
Update these files to use `const { t } = useTranslation()`:
- Jobs.tsx (search placeholder, filters, job cards)
- Navbar.tsx (nav items)
- Profile.tsx (section headers)
- Index.tsx (hero text, CTAs)
- Login.tsx (form labels)

#### 6. Set document direction
In the ThemeProvider or App component, set `document.documentElement.dir` based on lang.
Also set `document.documentElement.lang` to 'ar' or 'en'.

#### 7. Fix RTL-specific issues
- Ensure icons don't flip (add `rtl:rotate-0` where needed)
- Ensure text alignment follows direction
- Margins/paddings use logical properties (ms-/me- instead of ml-/mr-)
- The Rashid widget should be bottom-LEFT in RTL mode
```

---

## PHASE 4: CV Parsing & Profile Enhancement
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Implement CV upload parsing and skill extraction

### Context:
- The career app has models for career profiles at backend/apps/career/models.py
- The skills app has extraction.py for skill extraction
- The intelligence app has bedrock_plugin.py for LLM calls
- Users can upload CVs but parsing doesn't extract structured data

### Requirements:

#### 1. Create CV parser service
File: `backend/apps/career/cv_parser.py`

```python
import pdfplumber
from docx import Document
from ai.bedrock import bedrock_service

class CVParser:
    def parse_file(self, file) -> dict:
        """Extract text from CV file (PDF or DOCX)"""
        if file.name.endswith('.pdf'):
            text = self._parse_pdf(file)
        elif file.name.endswith('.docx'):
            text = self._parse_docx(file)
        else:
            text = file.read().decode('utf-8', errors='ignore')
        return self._extract_structured(text)
    
    def _parse_pdf(self, file) -> str:
        with pdfplumber.open(file) as pdf:
            return '\n'.join(page.extract_text() or '' for page in pdf.pages)
    
    def _parse_docx(self, file) -> str:
        doc = Document(file)
        return '\n'.join(p.text for p in doc.paragraphs)
    
    def _extract_structured(self, text: str) -> dict:
        """Use Bedrock to extract structured data from CV text"""
        prompt = f"""Extract structured information from this CV/resume text. Return JSON with:
        - name (string)
        - email (string) 
        - phone (string)
        - location (string)
        - summary (string, 2-3 sentences)
        - experience (list of: title, company, start_date, end_date, description)
        - education (list of: degree, institution, year)
        - skills (list of strings)
        - certifications (list of strings)
        - languages (list of strings)
        
        CV Text:
        {text[:4000]}
        """
        response = bedrock_service.invoke(prompt, model='haiku')
        # Parse JSON from response
        import json
        try:
            return json.loads(response)
        except:
            return {'raw_text': text, 'parse_error': True}
```

#### 2. Add CV parsing endpoint
File: `backend/apps/career/views.py`

Add a view or action:
- POST `/api/v1/career/parse-cv/` — accepts file upload, parses it, returns structured data
- Also saves parsed data to the user's career profile (cv_parsed_data field)

#### 3. Add dependencies
File: `backend/requirements/base.txt`

Add: `pdfplumber>=0.10.0` and `python-docx>=1.0.0`

#### 4. Frontend CV upload component
File: `frontend/src/components/CVUpload.tsx`

Create a drag-and-drop CV upload component that:
- Accepts PDF/DOCX files
- Shows upload progress
- Calls the parse endpoint
- Displays extracted data (skills, experience, education)
- Allows user to confirm/edit extracted data

#### 5. Add to Profile page
File: `frontend/src/pages/Profile.tsx`

Add a "Upload CV" section that uses the CVUpload component.
After parsing, show extracted skills and let user add them to their profile.
```

---

## PHASE 5: Production Infrastructure Fixes
**Time: 1-2 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Fix production infrastructure issues

### Context:
- Server: 13.49.245.174 (Ubuntu 22.04, t3.small)
- Domain: jobs.usamif.com
- The redis cache backend fix is only applied via `sed` on server, not committed
- Typesense and Qdrant have 401 auth errors (no API keys configured)
- SSL/HTTPS status unknown
- The `seed_jobs` management command has been fixed locally but may not be committed

### Requirements:

#### 1. Fix Redis cache backend in committed code
File: `backend/config/settings/base.py`

Change the CACHES config:
```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
```
Make sure it's NOT using `django.core.cache.backends.redis.RedisCache`.

#### 2. Add Typesense env configuration
File: `backend/config/settings/base.py`

```python
TYPESENSE_CONFIG = {
    'api_key': os.environ.get('TYPESENSE_API_KEY', 'xyz'),
    'nodes': [{
        'host': os.environ.get('TYPESENSE_HOST', 'localhost'),
        'port': os.environ.get('TYPESENSE_PORT', '8108'),
        'protocol': 'http'
    }],
    'connection_timeout_seconds': 2
}
```

#### 3. Add Qdrant env configuration
File: `backend/config/settings/base.py`

```python
QDRANT_CONFIG = {
    'url': os.environ.get('QDRANT_URL', 'http://localhost:6333'),
    'api_key': os.environ.get('QDRANT_API_KEY', None),
}
```

#### 4. Create .env.example
File: `backend/.env.example`

Document all required environment variables:
```
# Database
DATABASE_URL=postgres://user:pass@localhost:5432/ecareer

# Redis
REDIS_URL=redis://localhost:6379/1

# Django
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=jobs.usamif.com,localhost

# AWS Bedrock
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Typesense
TYPESENSE_API_KEY=xyz
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Frontend URL
FRONTEND_URL=https://jobs.usamif.com
```

#### 5. Add SSL nginx config
File: `deploy/nginx-ssl.conf`

Create an nginx config with:
- Redirect HTTP to HTTPS
- SSL with Let's Encrypt paths
- Proxy to gunicorn on port 8000
- Static files from /var/www/usam/frontend/dist/
- WebSocket proxy for /ws/ (future)

#### 6. Create deployment script
File: `deploy/deploy.sh`

```bash
#!/bin/bash
set -e
cd /var/www/usam

# Pull latest code
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements/production.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Frontend
cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
sudo systemctl restart nginx

echo "Deployment complete!"
```
```

---

## PHASE 6: GDPR, Security & Rate Limiting
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Implement GDPR compliance, security headers, and rate limiting

### Context:
- backend/apps/core/gdpr_service.py exists but has import issues
- No rate limiting is configured
- No GDPR export/delete endpoints exist
- Security headers not configured

### Requirements:

#### 1. Fix and complete GDPR service
File: `backend/apps/core/gdpr_service.py`

Implement:
- `export_user_data(user)` → returns dict of ALL user data (profile, jobs saved, applications, conversations, scores, events)
- `delete_user_data(user)` → soft delete (set is_active=False, schedule hard delete in 30 days)
- `hard_delete_user_data(user)` → permanently remove all user data from all tables + S3 + vectors

#### 2. Create GDPR API endpoints
File: `backend/apps/accounts/views.py` (add to existing)

- POST `/api/v1/accounts/export-data/` → queues data export, emails download link
- POST `/api/v1/accounts/delete-account/` → soft delete with 30-day grace period
- POST `/api/v1/accounts/pause-account/` → stops AI processing, keeps data

#### 3. Add rate limiting
File: `backend/config/settings/base.py`

```python
REST_FRAMEWORK = {
    ...existing...,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        'ai': '20/minute',
        'auth': '10/minute',
    }
}
```

Create custom throttle class for AI endpoints:
File: `backend/apps/core/throttles.py`

```python
from rest_framework.throttling import UserRateThrottle

class AIThrottle(UserRateThrottle):
    rate = '20/minute'
    scope = 'ai'

class AuthThrottle(UserRateThrottle):
    rate = '10/minute'
    scope = 'auth'
```

Apply AIThrottle to: Rashid chat endpoints, interview endpoints
Apply AuthThrottle to: login, register, password reset

#### 4. Add security middleware
File: `backend/config/settings/base.py`

```python
MIDDLEWARE += [
    'django.middleware.security.SecurityMiddleware',
]

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

#### 5. Add CORS configuration
File: `backend/config/settings/base.py`

```python
CORS_ALLOWED_ORIGINS = [
    'https://jobs.usamif.com',
    'http://localhost:5173',  # Dev
]
CORS_ALLOW_CREDENTIALS = True
```
```

---

## PHASE 7: Email Notifications & Job Alerts
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Implement email notification system with job alerts

### Context:
- backend/apps/emails/ exists with models, service, tasks
- Users can set alert preferences (frequency, keywords)
- Celery Beat is running for scheduled tasks
- 200+ jobs exist in the database

### Requirements:

#### 1. Create HTML email templates
Directory: `backend/apps/emails/templates/emails/`

Create these templates:
- `job_alert.html` — Shows top 3-5 matching jobs with title, company, location, salary, match score. CTA button to view each job.
- `weekly_digest.html` — Summary: new jobs this week, profile views, score changes, suggestions
- `welcome.html` — Welcome email after registration with quick-start guide
- `password_reset.html` — Password reset link

Use inline CSS for email compatibility. Include the USAM logo.
Support both English and Arabic based on user preference.

#### 2. Build job matching for alerts
File: `backend/apps/emails/matching.py`

```python
def get_matching_jobs_for_user(user, since_hours=24):
    """Find jobs posted in last N hours that match user's alert criteria"""
    from apps.jobs.models import Job
    from django.utils import timezone
    from datetime import timedelta
    
    since = timezone.now() - timedelta(hours=since_hours)
    jobs = Job.objects.filter(status='active', posted_at__gte=since)
    
    # Filter by user's saved search criteria (keywords, location, salary)
    # Return top 5 by relevance
    return jobs[:5]
```

#### 3. Create Celery Beat schedule for alerts
File: `backend/apps/emails/tasks.py`

Add tasks:
- `send_daily_alerts()` — runs daily at 8 AM, sends job alerts to users with daily frequency
- `send_weekly_digest()` — runs every Monday at 8 AM
- `send_instant_alert(user_id, job_id)` — triggered when high-match job is found

Register in Celery Beat schedule in settings.

#### 4. Frontend alerts page
File: `frontend/src/pages/Alerts.tsx`

The page already exists but may need updating:
- Show alert preferences (keywords, locations, salary range, frequency)
- Toggle: instant / daily / weekly / off
- Show recent alert history (what was sent)
- Preview of current matching jobs
```

---

## PHASE 8: Testing & Quality
**Time: 3-4 hours | Priority: LOW (but important)**

### Cline Prompt:

```
## Task: Create comprehensive test suite

### Context:
- pytest is listed in requirements but no meaningful tests exist
- Need at minimum: API endpoint tests, model tests, service tests
- factory_boy for test data generation

### Requirements:

#### 1. Install test dependencies
File: `backend/requirements/test.txt`

```
pytest>=7.4
pytest-django>=4.5
factory-boy>=3.3
pytest-cov>=4.1
```

#### 2. Create pytest config
File: `backend/pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = --cov=apps --cov-report=term-missing
```

#### 3. Create test settings
File: `backend/config/settings/test.py`

```python
from .base import *
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
CELERY_TASK_ALWAYS_EAGER = True
```

#### 4. Create factories
File: `backend/tests/factories.py`

Create factories for: User, Company, Job, Tag, Source, CareerProfile, InterviewSession

#### 5. Create API tests
File: `backend/tests/test_jobs_api.py` — Test job list, detail, search, filters
File: `backend/tests/test_auth_api.py` — Test login, register, token refresh
File: `backend/tests/test_rashid_api.py` — Test conversation create, send message
File: `backend/tests/test_interviews_api.py` — Test start, answer, complete

#### 6. Create service tests  
File: `backend/tests/test_cv_parser.py` — Test PDF/DOCX parsing
File: `backend/tests/test_scoring.py` — Test talent score calculation

Target: 50+ tests covering critical paths.
```

---

## EXECUTION ORDER

| Phase | Priority | Time | Dependencies |
|-------|----------|------|-------------|
| **Phase 1** | CRITICAL | 2-3h | None — fixes broken Rashid chat in prod |
| **Phase 2** | HIGH | 3-4h | None — new feature |
| **Phase 3** | HIGH | 3-4h | None — i18n for Arabic users |
| **Phase 4** | MEDIUM | 2-3h | Phase 1 (Rashid working) |
| **Phase 5** | MEDIUM | 1-2h | None — infra fixes |
| **Phase 6** | MEDIUM | 2-3h | None — security |
| **Phase 7** | MEDIUM | 2-3h | None — notifications |
| **Phase 8** | LOW | 3-4h | Phases 1-2 done |

**Total: ~20-26 hours across 8 phases**

---

## WHAT IS NOT IN THIS PLAN (Phase 3-5 from IMPLEMENTATION_PLAN_PART1/PART2)

These are advanced features that require significant infrastructure and can be done later:

- Voice interviews (needs LiveKit, Faster-Whisper, AWS Polly, Pipecat) — Phase 3
- Coding interviews (needs Judge0 sandbox, Monaco editor) — Phase 3
- Apache AGE graph database — Phase 1 advanced
- Gorse recommendation engine — Phase 2 advanced
- LightFM / Metarank — Phase 2 advanced
- Common Crawl company discovery — Phase 1 advanced
- Real ATS scrapers (Greenhouse, Lever, Workday, etc.) — Phase 1 advanced
- Employer analytics (time-to-hire, funnel) — Phase 3
- Talent discovery for employers — Phase 3
- A/B testing framework — Phase 4
- Prometheus/Grafana monitoring — Phase 4
- Resume builder — Phase 5
- PWA / Push notifications — Phase 5
- Auto-scaling / Blue-green deploy — Phase 4
- Full ESCO/O*NET import with graph traversal — Phase 1 advanced

These will be planned in a PART 2 of this Cline plan after the 8 phases above are complete.

---

*Execute Phase 1 first. After each phase, commit and deploy to production.*

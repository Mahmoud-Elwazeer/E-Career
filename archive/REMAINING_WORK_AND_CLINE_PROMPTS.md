# E-Career: Remaining Work & Cline Implementation Prompts
## Deep Audit Results - August 6, 2026

---

## CURRENT STATUS: What's Actually Working on Production

| App | URL Registered | Models | Views | Status |
|-----|---------------|--------|-------|--------|
| **accounts** | `/api/v1/auth/` | User | 11 endpoints | WORKING |
| **jobs** | `/api/v1/jobs/` | Company, Source, Tag, Job, JobTag, JobAlsoOnSource | 12 endpoints | WORKING |
| **profiles** | `/api/v1/profile/` | (empty - uses users app) | 7 endpoints | WORKING |
| **rashid** | `/api/v1/rashid/` | RashidConfig, RashidProfile, RashidConversation, RashidMessage, RashidStoryBank, RashidUsage | 10+ endpoints | WORKING |
| **employers** | `/api/v1/employer/` | EmployerProfile, JobPosting, JobApplication, KnockoutQuestion, CandidateRanking, TalentDiscovery | 15+ endpoints | WORKING |
| **analytics** | `/api/v1/analytics/` | JobView, JobClick, SearchLog | 6 endpoints | WORKING |
| **search** | `/api/v1/search/` | (none - uses Typesense) | 7 endpoints | WORKING |
| **vectors** | `/api/v1/vectors/` | (none - uses Qdrant) | 4 endpoints | NEEDS QDRANT |
| **career** | `/api/v1/career/` | CareerProfile, CareerUserSkill, CareerLearning, TalentScore, InterviewSession, CareerBrain | 9 endpoints | WORKING |
| **salary** | `/api/v1/salary/` | SalaryData, MarketRate, SalaryBenchmark, SalaryInsight, SalaryAlert | 10 endpoints | WORKING (has URL duplicates) |
| **assessment** | `/api/v1/assessment/` | Assessment, AssessmentQuestion, AssessmentAttempt, SkillBadge, AssessmentTemplate, AssessmentResult | 7 endpoints | HAS BUGS |
| **core** | `/api/v1/core/` | Rule, FeatureFlag, GitHubConnection, PortfolioAnalysis, ActivityLog, Media, PlatformConfig, ProxyPool, PipelineHealth | 14 endpoints | WORKING (GDPR broken) |
| **emails** | `/emails/` | EmailAccount, EmailTemplate, EmailLog | 4 endpoints | WORKING |
| **events** | NOT registered | EventLog | 0 endpoints | DATA-ONLY (internal) |
| **skills** | NOT registered | Skill, SkillRelationship, Occupation, OccupationSkill, CareerPath, JobSkill | 0 public endpoints | DATA-ONLY |
| **monitoring** | NOT registered | HealthCheck, PerformanceMetric, ErrorLog, UptimeRecord | 8 endpoints ready | NOT WIRED |
| **verification** | NOT registered | VerificationResult | 0 endpoints | INTERNAL ONLY |
| **intelligence** | NOT registered | (none) | 0 endpoints | SERVICE LAYER |
| **scraper** | admin only | (none - uses jobs models) | 2 admin views | INTERNAL |

---

## CONFIRMED: Rashid AI is FULLY WORKING

Rashid is live at `/api/v1/rashid/` with:
- Conversations CRUD (create, list, retrieve, delete)
- Send messages with AI response (Bedrock/Anthropic)
- Active conversations management
- Profile management + onboarding flow
- STAR stories bank
- Token usage tracking
- Tool system (execute career tools)
- Encrypted messages (PII protection)

**No action needed on Rashid.**

---

## BUGS TO FIX (Small - Can Do Now)

### Bug 1: Assessment views.py missing `timezone` import
**File:** `backend/apps/assessment/views.py`
**Issue:** Uses `timezone.now()` but never imports it. Will crash on `start_assessment` and `submit_assessment`.
**Fix:** Add `from django.utils import timezone` to imports.

### Bug 2: Assessment & Salary duplicate URL paths
**File:** `backend/apps/assessment/urls.py`
**Issue:** Same path registered twice (function view + ViewSet). Last one wins, first is unreachable.
```
path('assessments/', get_user_assessments, ...)  # UNREACHABLE
path('assessments/', AssessmentViewSet.as_view(), ...)  # WINS
```
**Fix:** Remove ViewSet duplicates or namespace them differently.

**File:** `backend/apps/salary/urls.py`
**Same issue:** `market-rates/`, `insights/`, `alerts/` all duplicated.

### Bug 3: GDPR service broken imports
**File:** `backend/apps/core/gdpr_service.py`
**Issues:**
- `from apps.accounts.models import PasswordReset, EmailVerification` - NEITHER EXISTS
- `from apps.verification.models import VerificationRequest` - Should be `VerificationResult`
- References `app.cover_letter` and `app.resume` on JobApplication - fields don't exist

### Bug 4: Monitoring app not wired into URLs
**File:** `backend/config/urls.py`
**Issue:** `apps/monitoring/` has views and urls.py but is NOT included in the URL router.
**Fix:** Add `path("monitoring/", include("apps.monitoring.urls")),` to config/urls.py

### Bug 5: Skills app UUID vs int URL mismatch
**File:** `backend/apps/skills/urls.py`
**Issue:** URLs use `<int:id>` but Skill model uses UUID primary key.

### Bug 6: Career models missing timedelta import
**File:** `backend/apps/career/models.py`
**Issue:** `CareerBrain.update_from_profile()` uses `timedelta` without importing it.

---

## REMAINING WORK BY PRIORITY

### PHASE 1: Critical Fixes (30 min) - SMALL CODE FIXES

These are all small bugs that need code changes. Use the Cline prompt below.

### PHASE 2: Wire Missing Services (1 hour)

- Add monitoring app to URL router
- Add skills app public API to URL router (it has views but isn't registered)
- Configure Sentry DSN in .env
- Run scrapers to get more jobs (currently only 20)

### PHASE 3: Vector Search / Qdrant (2-3 hours)

- Deploy Qdrant (Docker on server)
- Configure QDRANT_URL in .env
- Index existing jobs
- Test semantic search endpoint

### PHASE 4: LightFM Recommendations (Deferred)

- Can't compile on 2-core server
- Options: pre-compile wheel, use a different ML library, or skip for MVP

### PHASE 5: Production Hardening (2-3 hours)

- Open redirect fix in emails TrackClickView
- Test coverage (currently ~5%)
- Sentry integration
- UptimeRobot setup

---

## CLINE PROMPTS

---

### PHASE 1 PROMPT: Fix All Critical Bugs

```
## Task: Fix critical bugs in E-Career Django backend

Fix these bugs one by one. After each fix, verify the file is syntactically correct.

### 1. Assessment views.py - Missing timezone import
File: `backend/apps/assessment/views.py`
Add `from django.utils import timezone` to the imports section (after line 6).

### 2. Assessment urls.py - Remove duplicate URL paths
File: `backend/apps/assessment/urls.py`
The file has duplicate paths: `assessments/`, `attempts/`, `badges/`, `templates/` appear twice (once as function view, once as ViewSet). Remove the ViewSet duplicates at the bottom (lines 40-44). Keep only the function-based view URLs (lines 25-37).

### 3. Salary urls.py - Remove duplicate URL paths  
File: `backend/apps/salary/urls.py`
Same issue. Lines 36-40 duplicate paths from lines 22-32. Remove lines 36-40 (the ViewSet duplicates for `market-rates/`, `insights/`, `alerts/`). Keep line 36 (`salary-data/`) and line 38 (`benchmarks/`) since those are unique paths.

### 4. GDPR service - Fix broken imports
File: `backend/apps/core/gdpr_service.py`
- Change `from apps.accounts.models import PasswordReset, EmailVerification` to be wrapped in try/except:
  ```python
  try:
      from apps.accounts.models import PasswordReset, EmailVerification
  except ImportError:
      PasswordReset = None
      EmailVerification = None
  ```
- Change `from apps.verification.models import VerificationRequest` to:
  ```python
  try:
      from apps.verification.models import VerificationResult as VerificationRequest
  except ImportError:
      VerificationRequest = None
  ```
- In the methods that use these models, add `if ModelName is not None:` guards before querying them.

### 5. Wire monitoring app into URL router
File: `backend/config/urls.py`
Add this line inside the `api/v1/` include block (after the assessment line, around line 49):
```python
        # Monitoring (Phase 4)
        path("monitoring/", include("apps.monitoring.urls")),
```

### 6. Career models - Missing timedelta import
File: `backend/apps/career/models.py`
Find where `timedelta` is used and ensure `from datetime import timedelta` is imported at the top of the file. If `datetime` is already imported, change it to `from datetime import datetime, timedelta`.

### 7. Skills URLs - Fix UUID vs int mismatch
File: `backend/apps/skills/urls.py`
Change all `<int:id>`, `<int:skill_id>`, `<int:occupation_id>` to `<uuid:id>`, `<uuid:skill_id>`, `<uuid:occupation_id>` since the Skill and Occupation models use UUID primary keys.

After all fixes, run:
```bash
cd backend && python manage.py check --deploy
```
```

---

### PHASE 2 PROMPT: Wire Skills API & Configure Services

```
## Task: Add skills public API to URL router and verify all apps load

### 1. Register skills URLs
File: `backend/config/urls.py`
Add inside the api/v1/ block:
```python
        # Skills taxonomy (Phase 2)
        path("skills/", include("apps.skills.urls")),
```

### 2. Verify all URL patterns load without error
Run: `python manage.py show_urls` or `python manage.py check`
Fix any import errors that come up.

### 3. Create a management command to run all scrapers
File: `backend/apps/scraper/management/commands/run_scrapers.py`
Create a Django management command that triggers the scraper orchestrator to fetch jobs from all configured sources. Look at `backend/apps/scraper/orchestrator.py` and `backend/apps/scraper/tasks.py` for the existing logic and call it.

### 4. Verify the following endpoints return 200:
- GET /api/v1/jobs/
- GET /api/v1/rashid/config/
- GET /api/v1/career/talent-score/
- GET /api/v1/salary/benchmark/
- GET /api/v1/assessment/templates/
- GET /api/v1/monitoring/health/
- GET /api/v1/skills/ (after wiring)
- GET /health/
```

---

### PHASE 3 PROMPT: Deploy Qdrant Vector Search

```
## Task: Deploy Qdrant and enable vector/semantic search

The app at `backend/apps/vectors/` already has fully implemented views for semantic search, hybrid search, and similar jobs. It needs Qdrant running and configured.

### 1. Check what the vectors app expects
Read `backend/apps/vectors/service.py` to understand:
- What collection name is used
- What vector dimensions are expected
- What embedding model/API is used (likely Cohere)

### 2. Create a Docker Compose file for Qdrant
File: `docker-compose.qdrant.yml` (at project root)
```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always

volumes:
  qdrant_data:
```

### 3. Add environment variables
Check what env vars the vectors service.py reads (likely QDRANT_URL, COHERE_API_KEY) and document them.

### 4. Create a management command to index all jobs
File: `backend/apps/vectors/management/commands/index_jobs.py`
Read the vectors service to understand the indexing format, then create a command that:
- Connects to Qdrant
- Creates the collection if it doesn't exist
- Fetches all active jobs from the database
- Generates embeddings (using whatever service is configured)
- Upserts vectors into Qdrant

### 5. Test the endpoints:
- GET /api/v1/vectors/health/
- GET /api/v1/vectors/search/semantic/?q=python+developer
```

---

### PHASE 4 PROMPT: Production Hardening & Security

```
## Task: Security fixes and production hardening

### 1. Fix open redirect vulnerability
File: `backend/apps/emails/views.py`
In `TrackClickView`, the `url` query parameter is used to redirect without validation. Fix:
- Add a whitelist of allowed domains (the app's own domain + employer domains)
- OR validate that the URL matches one stored in EmailLog
- At minimum, ensure the URL starts with `https://` and doesn't point to `javascript:` or `data:` schemes

### 2. Add Sentry integration
File: `backend/config/settings/base.py`
Add at the end:
```python
# Sentry Error Tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
```

### 3. Add rate limiting to sensitive endpoints
Verify these endpoints have throttle classes:
- POST /api/v1/auth/login/ (max 5/min)
- POST /api/v1/auth/register/ (max 3/min)
- POST /api/v1/auth/password-reset/ (max 3/min)
- POST /api/v1/rashid/conversations/*/send_message/ (max 20/min)

### 4. Add CORS origin validation
File: `backend/config/settings/base.py`
Verify CORS_ALLOWED_ORIGINS only includes `https://jobs.usamif.com` and development URLs.

### 5. Verify all sensitive views require authentication
Check that no admin/analytics/employer view is accessible without `IsAuthenticated` or `IsAdminUser` permission.
```

---

## WHAT'S NOT NEEDED (Don't Build)

These are internal service layers that work correctly as-is:
- **events/** - Internal event emitter, no public API needed
- **intelligence/** - Service layer for AI, used by rashid/career internally
- **verification/** - Internal verification pipeline, used by scraper
- **scraper/** - Background task, admin dashboard only

---

## DEPLOYMENT COMMANDS (After Fixes)

```bash
# On Windows: commit and push
cd "m:\job already web for jobs\E-Career"
git add -A
git commit -m "Fix assessment/salary URL duplicates, GDPR imports, wire monitoring"
git push origin development

# On Server:
cd /var/www/usam/backend
git pull origin development
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart usam celery-usam celery-beat-usam
```

---

## FINAL ARCHITECTURE SCORE

| Category | Score | Notes |
|----------|-------|-------|
| **Core Platform** | 9/10 | Auth, jobs, search, profiles all solid |
| **AI Features** | 9/10 | Rashid fully working, career scoring working |
| **Employer Portal** | 8/10 | Full ATS, needs more testing |
| **Assessment** | 6/10 | Has bugs (timezone, duplicate URLs) |
| **Salary** | 7/10 | Working but duplicate URLs, needs data |
| **Monitoring** | 5/10 | Built but not wired into URLs |
| **Vector Search** | 3/10 | Code exists but Qdrant not deployed |
| **Security** | 7/10 | Good basics, open redirect vulnerability |
| **Test Coverage** | 2/10 | ~5%, needs significant work |

**Overall: 73% complete for production launch**

---

## PRIORITY ORDER

1. **Phase 1** (30 min) - Fix bugs - DO FIRST
2. **Phase 2** (1 hr) - Wire services + run scrapers
3. **Phase 3** (2-3 hrs) - Qdrant deployment
4. **Phase 4** (2-3 hrs) - Security hardening
5. **Tests** (ongoing) - Add as you go

**Estimated total remaining: 8-10 hours of work**

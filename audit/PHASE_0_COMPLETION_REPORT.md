# Phase 0 Completion Report

**Date:** 2026-08-29  
**Commits:** d06aab6, f64b1a1, a169044, ac2b615  
**Test suite:** 107 passed, 2 skipped (core/verification/scraper/vectors/skills)

---

## Items Completed (Code Fixes)

### 0.1 — croniter + scrape_all_sources method
- **Status:** FIXED
- Added `croniter==2.0.1` to root `requirements.txt`
- Added `scrape_all_sources()` method to `ScraperOrchestrator` class (the management command called it but it didn't exist — would crash at runtime)

### 0.2 — remote_type → work_arrangement at scraper ingestion
- **Status:** FIXED
- Changed `remote_type=normalize_remote_type(...)` to `work_arrangement=...` in both `orchestrator.py:323` and `tasks.py:224`
- The Job model renamed this field; both call sites would raise TypeError

### 0.3 — VerificationEngine persists rejection
- **Status:** FIXED
- Added `"rejected"` to `Job.STATUS_CHOICES`
- Engine now writes `job.status = "rejected"` when verification fails
- Added `"status"` to `update_fields` in `job.save()`
- Previously: rejected jobs stayed `status="active"` and appeared in public listings

### 0.4 — Scraper integration test
- **Status:** ADDED
- Created `apps/scraper/tests/test_scraper_integration.py` with 4 tests:
  - Full pipeline creates job with correct fields
  - Blocked aggregator URL is filtered out
  - Duplicate job not re-added
  - `scrape_all_sources()` method exists and returns expected shape

### 0.5 — EmployerProfileViewSet.stats() field error
- **Status:** FIXED
- Changed `job__employer=employer` → `job__employer_posting__employer=employer`
- The Job model has no `employer` FK; the path goes through JobPosting

### 0.6 — Missing import in interviews/views.py
- **Status:** FIXED
- Added `from django.db import models` — `get_interview_stats()` uses `models.Avg`/`models.Count`

### 0.7 — HybridSearchView calls nonexistent search()
- **Status:** FIXED
- Changed `search_service.search(query=..., filters=..., page=..., page_size=...)` to `search_service.search_jobs(SearchQuery(q=query, filters=filters, page=1, per_page=limit))`
- Added `SearchQuery` import
- Updated corresponding test mock

### 0.8 — Stale fields in profiles/services.py
- **Status:** FIXED
- `Q(is_active=True)` → `Q(status='active')` (2 occurrences)
- `.order_by('-posted_date')` → `.order_by('-posted_at')` (2 occurrences)

### 0.9 — Stale fields across recommendation/matching/indexing
- **Status:** FIXED
- `recommendation_engine.py`: `job.remote_type` → `job.work_arrangement` (6 occurrences), `job.experience_required` → mapped from `job.experience_level` (2 occurrences), dict key `'remote_type'` → `'work_arrangement'`
- `job_matching.py`: `queryset.filter(remote_type=...)` → `work_arrangement=...`, `job.remote_type` → `job.work_arrangement`
- `marketing_intelligence.py`: `remote_type='remote'` → `work_arrangement='remote'`
- `analytics/tracking.py`: `remote_type='remote'` → `work_arrangement='remote'`
- `index_jobs.py`: `job.job_type` → `job.employment_type`, `job.is_remote` → `job.work_arrangement == 'remote'`

### 0.10 — Bedrock sonnet alias (inference-profile ARN)
- **Status:** FIXED (configurable)
- `MODEL_ALIASES` now reads from `settings.BEDROCK_MODEL_ALIASES` with plain model IDs as fallback defaults
- To use cross-region inference profiles, set `BEDROCK_MODEL_ALIASES` in Django settings with ARN values

### 0.13 — Employer registration sets User.role
- **Status:** FIXED
- `EmployerRegistrationView.perform_create()` now sets `self.request.user.role = 'employer'` and saves

### 0.14 — TalentDiscoveryViewSet consent gap
- **Status:** FIXED
- `perform_create()` now checks `CareerProfile.objects.filter(user=user, is_discoverable=True).exists()` before allowing discovery creation
- Raises `ValidationError` if user hasn't opted in

### 0.16 — monitoring/views_ai_costs.py field mismatches
- **Status:** FIXED
- `event.metadata` → `event.data` (EventLog model field is `data`)
- `u.input_tokens`/`u.output_tokens` → `u.tokens_used` (RashidUsage has single field)
- Cost formula uses blended rate since split isn't available

### 0.17 — JobPostingViewSet.perform_update no-op edit-lock
- **Status:** FIXED
- Replaced `return Response(...)` (which DRF ignores) with `raise ValidationError(...)`
- Used `serializer.instance` instead of redundant `self.get_object()` call

---

## Human Action Items (Cannot Be Fixed in Code)

### 0.11 — Voice interviews AWS IAM permissions
- **Status:** REQUIRES HUMAN ACTION
- Voice interview service needs `transcribe:StartStreamTranscription` and `polly:SynthesizeSpeech` IAM permissions on the AWS account
- Verify IAM policy attached to the service role

### 0.12 — Valid JUDGE0_API_KEY
- **Status:** REQUIRES HUMAN ACTION
- Code assessment grading requires a valid Judge0 CE API key
- Set `JUDGE0_API_KEY` in production `.env`

### 0.15 — AWS key rotation confirmation
- **Status:** REQUIRES HUMAN ACTION
- Confirm the exposed AWS key from the security incident has been rotated
- Verify no active credentials remain in any git-tracked file

---

## Additional Fixes (Discovered During Phase 0)

- **conftest.py**: Removed broken `_disable_throttling` fixture that used `settings` fixture from uninstalled `pytest-django`. Test settings already disable throttling.
- **pytest-django**: Installed (was in `requirements/test.txt` but not installed in the environment)

---

## Test Results

```
107 passed, 2 skipped (graph queries — SQLite limitation)
```

Suites passing: verification (31), core/comprehensive (59), scraper (4), vectors (11), skills (2 skipped as designed)

The `apps/career/tests/test_api.py` (23 tests) fails independently of these changes due to a pre-existing issue where test setUp doesn't create CareerProfile objects. These tests were never in the passing baseline.

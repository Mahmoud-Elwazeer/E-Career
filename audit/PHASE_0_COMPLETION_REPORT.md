# Phase 0 Completion Report

**Date:** 2026-08-30 (second pass — supplements the 2026-08-29 first pass)
**Branch:** `development`
**New commits this pass:** 6 (`4c673b7` through `5c3f223`)
**Prior first-pass commits:** `d06aab6`, `f64b1a1`, `a169044`, `ac2b615`

---

## Re-verification of all 17 items (second pass)

Most items were already fixed by the first pass on 2026-08-29. This second
pass re-verified every item against current code, found 7 items that were
either partially fixed or missed, and fixed them. Items marked "Already
fixed (first pass)" were confirmed correct by direct code reads.

---

## Items Fixed This Pass

### 0.3 — VerificationEngine.verify_job() persist rejection (partial fix)

**Status: TWO EARLY-RETURN PATHS WERE STILL MISSING PERSISTENCE**

The first pass fixed the main verification path (lines 168-191) but missed two
early-return paths that returned a `VerificationResult` without setting
`job.status = "rejected"`:
- Line 53: When `ats_result.platform == "BLOCKED_AGGREGATOR"`
- Line 76: When redirect resolves to a blocked aggregator

**Fix:** Added `job.status = "rejected"`, `job.quality_state = "rejected"`,
`job.last_verified_at = timezone.now()`, `job.save(update_fields=[...])` before
both early returns.

**File:** `backend/apps/verification/engine.py:54-58, 77-81`
**Commit:** `4c673b7`

### 0.4 — Scraper integration test (enhancement)

**Status: ENHANCED EXISTING TEST**

Test already existed from first pass. Added `VerificationResult` import and
assertion to `test_full_pipeline_creates_job` — now verifies a
`VerificationResult` row exists with valid status and non-negative trust score.

**File:** `backend/apps/scraper/tests/test_scraper_integration.py:12, 70-73`
**Commit:** `4c673b7`
**Verified:** 4/4 tests pass.

### 0.7 — HybridSearchView + JobSearchView method calls

**Status: FIXED**

- `JobSearchView.get()` called `search_service.search(query=..., filters=...)`
  with keyword args; the real method is `search_jobs(query: SearchQuery)`.
  Fixed to construct a `SearchQuery` and call `search_jobs()`, serialized
  via `SearchResponseSerializer`.
- `HybridSearchView` accessed `SearchResponse` via dict methods
  (`.get("hits", [])`) instead of attributes (`.hits`, `.id`, `.data`).
  Fixed all attribute accesses.

**Files:** `backend/apps/search/views.py:111-131`,
`backend/apps/vectors/views.py:267-329`
**Commit:** `64b4e26`

### 0.9 extras — Additional stale field references

**Status: FIXED (found references the first pass missed)**

- `ranking_service.py:179`: `job.remote_type` → `job.work_arrangement or job.location_type`
- `trend_detection.py:53,105`: `is_active=True` → `status='active'` on Job queries (2 occurrences)
- `tasks_gdpr.py:79`: `SavedJob.created_at` → `saved_at` (matches actual model field)
- `emails/tasks.py:220`: Fixed `select_related` path for employer through job posting

**Commit:** `ce2dd98`

### 0.10 — Bedrock inference profile IDs

**Status: FIXED**

Raw model IDs (`anthropic.claude-*`) fail with `ValidationException` in
Bedrock cross-region inference. Changed all IDs in both `MODEL_COSTS` and
`_DEFAULT_ALIASES` from `anthropic.*` to `us.anthropic.*`:
- `"haiku": "us.anthropic.claude-3-haiku-20240307-v1:0"`
- `"sonnet": "us.anthropic.claude-sonnet-4-20250514-v1:0"`

**File:** `backend/apps/intelligence/bedrock_plugin.py:23-32`
**Commit:** `c7a99f2`

### 0.14 — TalentDiscovery consent gap

**Status: FIXED**

`TalentDiscoveryViewSet.get_queryset()` returned all discoveries without
checking current consent status, leaking name/email of users who later
revoked `is_discoverable`. Added subquery filtering to only include
discoveries where the user's `CareerProfile.is_discoverable=True`.

**File:** `backend/apps/employers/views.py:640-649`
**Commit:** `01a935b`

### 0.16 — AI cost dashboard field references

**Status: FIXED**

`RashidUsage` has a `date` (DateField), not `created_at` (DateTimeField).
Fixed four filter calls:
- Line 60: `created_at__gte=today_start` → `date=today_start.date()`
- Line 61: `created_at__gte=week_start` → `date__gte=week_start.date()`
- Line 62: `created_at__gte=month_start` → `date__gte=month_start.date()`
- Line 122: `created_at__gte=day_start, created_at__lt=day_end` → `date=day_start.date()`

Note: `event.metadata` → `.data` was already correct in current code.

**File:** `backend/apps/monitoring/views_ai_costs.py:60-62, 122`
**Commit:** `5c3f223`

---

## Items Confirmed Already Fixed (First Pass or Prior Commits)

| # | Item | Confirmed how |
|---|---|---|
| 0.1 | croniter + run_scrapers | `croniter==2.0.1` in requirements.txt; `scrape_all_sources()` exists at orchestrator.py:353; installed in venv |
| 0.2 | remote_type → work_arrangement | Both call sites (tasks.py:224, orchestrator.py:324) already use `work_arrangement=` |
| 0.5 | EmployerProfileViewSet.stats() | views.py:174 queries `JobPosting.objects.filter(employer=employer)` directly (correct) |
| 0.6 | Missing models import | views.py:11 has `from django.db import models` |
| 0.8 | profiles/services.py stale fields | Uses `status='active'` and `posted_at` throughout; grep confirmed no stale refs |
| 0.9 main | recommendation/matching stale fields | search/recommendation_engine.py uses correct names; career/recommendation_engine.py and intelligence/job_matching.py don't exist (consolidated) |
| 0.13 | Employer role assignment | views.py:75-76 sets `user.role = 'employer'` and saves |
| 0.17 | perform_update edit-lock | views.py:271 raises `ValidationError` (not returning discarded `Response`) |

---

## Human Action Items (Unchanged)

### 0.11 — Voice interviews AWS IAM permissions

Requires:
1. IAM Console: Grant `polly:SynthesizeSpeech`,
   `transcribe:StartTranscriptionJob` + related actions,
   S3 read/write on the media bucket
2. Set `AWS_REGION` and `AWS_STORAGE_BUCKET_NAME` in `.env`

### 0.12 — JUDGE0_API_KEY

Set a valid RapidAPI key for Judge0 CE in `.env` (`JUDGE0_API_KEY`).

### 0.15 — AWS key rotation confirmation

Confirm the previously-leaked AWS access key (`AKIAYK...TGPY`) has been
rotated in the IAM Console. Create new key, update `.env`, deactivate old key.

---

## Test Results (This Pass)

- **Scraper integration tests:** 4/4 passed
- **Verification engine tests:** 42/42 passed
- **Django system check:** 0 errors (3 pre-existing allauth deprecation warnings)

---

## Summary Table

| # | Item | Status | Fixed by |
|---|---|---|---|
| 0.1 | croniter + run_scrapers | Fixed (first pass) | d06aab6 |
| 0.2 | remote_type → work_arrangement | Fixed (first pass) | d06aab6 |
| 0.3 | verify_job() persist rejection | Fixed (both passes) | ac2b615 + 4c673b7 |
| 0.4 | Scraper integration test | Fixed (both passes) | ac2b615 + 4c673b7 |
| 0.5 | stats() field error | Fixed (first pass) | d06aab6 |
| 0.6 | Missing models import | Fixed (first pass) | d06aab6 |
| 0.7 | HybridSearchView method | Fixed (second pass) | 64b4e26 |
| 0.8 | profiles/services.py stale fields | Fixed (first pass) | f64b1a1 |
| 0.9 | Stale fields across recs/matching | Fixed (both passes) | f64b1a1 + ce2dd98 |
| 0.10 | Bedrock inference profile | Fixed (second pass) | c7a99f2 |
| 0.11 | AWS IAM Polly/Transcribe/S3 | **HUMAN ACTION** | — |
| 0.12 | JUDGE0_API_KEY | **HUMAN ACTION** | — |
| 0.13 | Employer role assignment | Fixed (first pass) | a169044 |
| 0.14 | TalentDiscovery consent gap | Fixed (second pass) | 01a935b |
| 0.15 | AWS key rotation | **HUMAN ACTION** | — |
| 0.16 | AI cost dashboard fields | Fixed (second pass) | 5c3f223 |
| 0.17 | perform_update edit-lock | Fixed (first pass) | a169044 |

**Code fixes: 14/17** (all complete across both passes)
**Human action items: 3/17** (0.11, 0.12, 0.15)

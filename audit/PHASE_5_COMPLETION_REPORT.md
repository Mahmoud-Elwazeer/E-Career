# Phase 5 Completion Report: Jobright-Class Feature Adoption

**Date:** 2026-08-30
**Decision Record:** `audit/COMPETITIVE_ANALYSIS_JOBRIGHT.md`

---

## Summary

All 6 items from Phase 5 are implemented. The phase adds competitive features adopted from Jobright.ai and similar platforms, spanning match-score explainability, resume tailoring, quick-apply prep, browser extension auth, insider connections, and Rashid AI tool wiring.

---

## Item Status

| # | Feature | Backend | Frontend | Tests | Status |
|---|---------|---------|----------|-------|--------|
| 5.1 | Match Score UI with breakdown | Done | Done | 3 tests | **Complete** |
| 5.2 | Job-specific resume tailoring | Done | Done | 2 tests | **Complete** |
| 5.3 | Quick-Apply review screen | Done | Done | — | **Complete** |
| 5.4 | Browser extension autofill POC | Done | Done | 5 tests | **Complete** |
| 5.5 | Insider connections + referrals | Done | Done | — | **Complete** |
| 5.6 | Rashid agent tool wiring | Done | N/A | — | **Complete** |

---

## Detailed Changes

### 5.1 — Match Score UI with Explainable Breakdown

**Backend:**
- `apps/profiles/services.py`: Enhanced `_basic_match_breakdown()` — now computes real per-factor scores (skills via Jaccard similarity, experience level mapping, location preference matching, salary range comparison) instead of returning zeros.
- `apps/career/views.py`: Added `match_breakdown()` view — GET `/api/v1/career/jobs/{job_id}/match-breakdown/`.
- `apps/career/urls.py`: Registered the new endpoint.

**Frontend:**
- `src/components/MatchScoreCard.tsx` (NEW): Expandable card showing overall score + lazy-loaded breakdown via TanStack Query. Color-coded progress bars per factor, strengths/gaps lists, recommendation text.
- `src/pages/JobDetail.tsx`: Replaced inline `MatchBreakdownCard` with the new `MatchScoreCard` in the sidebar.

### 5.2 — Job-Specific Resume Tailoring

**Backend:**
- `apps/career/cv_tailor_service.py`: Complete rewrite fixing two bugs (`job.job_skills.all()` → `job.skills.all()`, `job.requirements` → `job.description`). Added `tailor_for_job(user, job)` method returning before/after ATS scores, suggestions, missing skills, and a tailored resume preview.
- `apps/career/views.py`: Added `job_tailor()` view — POST `/api/v1/career/jobs/{job_id}/tailor/`.
- `apps/career/urls.py`: Registered the new endpoint.

**Frontend:**
- `src/components/TailorResumePanel.tsx` (NEW): "Analyze My Resume" button → useMutation → displays before/after ATS scores with delta, missing skills as badges, and numbered suggestions.
- Wired into `JobDetail.tsx` sidebar.

### 5.3 — Quick-Apply for ATS Providers

**Backend:**
- `apps/employers/quick_apply_service.py` (NEW): `QuickApplyService` with `prepare_application(user, job)` (maps CareerProfile to ATS payload), `get_ats_provider_info(job)` (provider metadata, always `can_auto_submit: False`), `record_application(user, job)` (creates JobApplication via get_or_create).
- `apps/employers/views.py`: Added `quick_apply_prepare()` and `quick_apply_record()` views.
- `apps/employers/urls.py`: Registered both endpoints.

**Frontend:**
- `src/components/QuickApplyPanel.tsx` (NEW): Shows on jobs with `ats_platform`. "Prepare My Application" button → Dialog review screen showing all pre-filled fields with copy buttons → "Apply Now" opens external URL and records the application. Uses shadcn Dialog.

**Ethical constraint enforced:** `can_auto_submit` is always `False`. The user must click "Apply Now" to open the external ATS page and submit manually. No auto-submit bot.

### 5.4 — Browser Extension Autofill

**Backend:**
- `apps/accounts/extension_tokens.py` (NEW): `ExtensionToken` model (SHA-256 hashed, `eck_` prefix, scoped, revocable, 90-day expiry) + `ExtensionTokenAuthentication` (DRF `BaseAuthentication` using `ExtToken` header keyword).
- `apps/accounts/models.py`: Imported `ExtensionToken` for migration detection.
- `apps/accounts/migrations/0004_add_extension_token.py` (NEW): Migration for the ExtensionToken model.
- `apps/accounts/views.py`: Added `ExtensionTokenListCreateView` (list/create), `ExtensionTokenRevokeView` (soft-revoke), `ExtensionProfileView` (read-only profile for extension, uses ExtensionTokenAuthentication).
- `apps/accounts/urls.py`: Registered all 3 endpoints.

**Chrome Extension POC** (`browser-extension/`):
- `manifest.json`: Manifest V3, permissions for `storage` + `activeTab`, host permissions for Greenhouse/Lever/Ashby.
- `popup.html` + `popup.js`: Token-based login/disconnect UI. Validates token against the extension profile endpoint.
- `content-greenhouse.js`: Content script for `boards.greenhouse.io/*/jobs/*`. Fetches profile via extension token, pre-fills name/email/phone/LinkedIn fields. Shows "Review & submit manually" banner. Never auto-submits.

### 5.5 — Insider Connections & Referral Contacts

**Backend:**
- `apps/jobs/models.py`: Added `github_org` CharField to `Company` model.
- `apps/jobs/migrations/0006_add_github_org_to_company.py` (NEW): Migration.
- `apps/employers/connections_service.py` (NEW): `ConnectionsService.find_connections(company_id, requesting_user)` — finds E-Career users (`CareerProfile.is_discoverable=True`) matching the company via `current_company` or `cv_parsed_data.experience[]`, plus GitHub public org members.
- `apps/employers/views.py`: Added `insider_connections()` view — GET `/api/v1/employer/connections/{company_id}/`.
- `apps/employers/urls.py`: Registered the endpoint.

**Frontend:**
- `src/components/InsiderConnectionsCard.tsx` (NEW): Shows E-Career insider connections with role, current/former badges, and GitHub contributors with avatars + links. Hidden when no connections found.
- Wired into `JobDetail.tsx` sidebar (shows when `job.company?.id` is available).

**Ethical constraint enforced:** No LinkedIn scraping. Connections come only from (a) consenting E-Career users (`is_discoverable=True`) and (b) GitHub's public org members API.

### 5.6 — Rashid Agent Tool Wiring

- `apps/intelligence/agent.py`: Added 3 new tools to `_register_rashid_tools()`:
  - `get_match_score(job_id)` → calls `MatchingService().get_match_breakdown()`, formats breakdown with scores/strengths/gaps/recommendation.
  - `tailor_resume(job_id)` → calls `CVTailorService().tailor_for_job()`, formats before/after scores, missing skills, suggestions.
  - `find_referral_contacts(company_id)` → calls `ConnectionsService().find_connections()`, formats E-Career connections and GitHub contributors.

---

## API Service Layer

- `src/services/phase5.ts` (NEW): Frontend API functions for `tailorResume()`, `getInsiderConnections()`, `prepareQuickApply()`, `recordQuickApply()`.

---

## Test Results

| Suite | Result |
|-------|--------|
| `npx tsc --noEmit` | **Pass** (0 errors) |
| `npx vite build --mode production` | **Pass** (8.82s) |
| Existing backend tests (49) | **Pass** |
| New Phase 5 tests (10) | **Pass** |

### New Test Files
- `apps/accounts/tests/test_extension_tokens.py` — 5 tests: create, list (hides raw token), revoke, extension profile with token, unauthenticated rejection.
- `apps/career/tests/test_phase5_endpoints.py` — 5 tests: match breakdown (returns data, unauth, nonexistent job), tailor (returns scores, unauth).

---

## Files Changed/Created

### New Files (16)
- `backend/apps/employers/connections_service.py`
- `backend/apps/employers/quick_apply_service.py`
- `backend/apps/accounts/extension_tokens.py`
- `backend/apps/accounts/migrations/0004_add_extension_token.py`
- `backend/apps/jobs/migrations/0006_add_github_org_to_company.py`
- `backend/apps/accounts/tests/test_extension_tokens.py`
- `backend/apps/career/tests/test_phase5_endpoints.py`
- `frontend/src/services/phase5.ts`
- `frontend/src/components/MatchScoreCard.tsx`
- `frontend/src/components/TailorResumePanel.tsx`
- `frontend/src/components/InsiderConnectionsCard.tsx`
- `frontend/src/components/QuickApplyPanel.tsx`
- `browser-extension/manifest.json`
- `browser-extension/popup.html`
- `browser-extension/popup.js`
- `browser-extension/content-greenhouse.js`

### Modified Files (11)
- `backend/apps/profiles/services.py` — Enhanced `_basic_match_breakdown()`
- `backend/apps/career/cv_tailor_service.py` — Complete rewrite
- `backend/apps/career/views.py` — Added `match_breakdown`, `job_tailor` views
- `backend/apps/career/urls.py` — Added 2 URL patterns
- `backend/apps/employers/views.py` — Added `insider_connections`, `quick_apply_prepare`, `quick_apply_record`
- `backend/apps/employers/urls.py` — Added 3 URL patterns
- `backend/apps/jobs/models.py` — Added `github_org` to Company
- `backend/apps/accounts/models.py` — Imported ExtensionToken
- `backend/apps/accounts/views.py` — Added 3 extension views
- `backend/apps/accounts/urls.py` — Added 3 URL patterns
- `backend/apps/intelligence/agent.py` — Added 3 Rashid tools
- `frontend/src/pages/JobDetail.tsx` — Wired all new components

---

## Human Action Items

1. **Extension icons**: Create actual icon PNGs at `browser-extension/icons/` (16x16, 48x48, 128x128). Currently missing placeholder files.
2. **AWS Bedrock access**: AI-powered match breakdown and CV tailoring fall back to heuristic algorithms without valid Bedrock credentials. Verify in staging.
3. **GitHub API rate limiting**: The GitHub org members endpoint is rate-limited to 60 req/hour unauthenticated. For production, consider adding a `GITHUB_TOKEN` to increase the limit.
4. **Quick-Apply ATS integration**: Real ATS submission requires employer-specific board tokens. The current implementation prepares data + records click-throughs only. Full integration would require partner agreements with Greenhouse/Lever/Ashby.
5. **Chrome Web Store**: The extension POC is not packaged for distribution. Publish when ready.

---

## Ethical Constraints Verified

- **No auto-submit bots**: Quick-apply always sets `can_auto_submit: False`. Extension shows "Review & submit manually" banner.
- **No LinkedIn scraping**: Connections come from consenting E-Career users and GitHub's public API only.
- **No secrets touched**: `.env` never read, printed, logged, or committed.
- **No billing engine**: Out of scope per decision record.

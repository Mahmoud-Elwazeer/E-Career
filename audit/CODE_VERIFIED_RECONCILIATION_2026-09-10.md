# E-Career — Code-Verified Repository Reconciliation

**Audit date:** 2026-09-10  
**Local baseline:** `development` at `6aa73b9` (same commit as `origin/development`)  
**Scope:** Git topology and unmerged work, current Django/React implementation, documented feature plans, executable validation, and source-level frontend UX assessment.

> This report is the current code-verified reconciliation snapshot. It intentionally supersedes only claims in older plans/reports that conflict with the active source and validation results. It does **not** certify deployment, live third-party providers, production data quality, browser-rendered visual quality, or infrastructure credentials.

## Executive verdict

E-Career contains substantial backend implementation and a working backend test suite, but it is **not ready to be considered production-solid**. The primary risks are:

1. **Repository fragmentation:** the remote default branch, legacy `develop`, and active `development` are materially divergent. Merging them without an explicit reconciliation branch is high risk.
2. **Frontend release failure:** the SPA production bundle builds, but ESLint fails with 226 errors and Vitest fails in four of five test files (30 failing tests). CI also calls a nonexistent `format:check` script.
3. **Broken or misleading user journeys:** the resume builder uses an incorrect API prefix; settings contains persistent-looking but inert switches; employer dashboard links point to nonexistent routes; jobs turn API failure into an empty-results message.
4. **Fragmented platform implementation:** parallel API/client/feature paths exist for search, recommendations, Rasheed, notifications, onboarding, and layouts. Several complete backend capabilities have no confirmed frontend consumer.
5. **Inconsistent frontend experience:** a mature token system exists but is bypassed by legacy pages, creating multiple visual languages, uneven theme/RTL support, and disconnected navigation shells.

The appropriate next move is not another broad feature build. First stabilize the repository, fix trust-breaking flows and CI, then consolidate shells and API boundaries before expanding features.

## 1. GitHub vs local reconciliation

### Current refs after `git fetch origin --prune --tags`

| Ref comparison | Result | Risk / required action |
|---|---:|---|
| `development` vs `origin/development` | 0 local-only / 0 remote-only | Active local branch is synchronized at `6aa73b9`. |
| `main` vs `origin/main` | 0 local-only / 48 remote-only | Local `main` is stale. Remote `main` is the GitHub default branch at `03c8d2d`. |
| `development` vs `origin/main` | 251 local-only / 43 remote-only | Major divergence. Do **not** merge directly into a working branch. |
| `develop` vs `origin/develop` | 44 local-only / 44 remote-only | Same-named branches diverged after `04737ec`; this is not a simple fast-forward. |

There are no unmerged index paths and no `<<<<<<<`, `=======`, `>>>>>>>` conflict-marker triplets in active source. This means there is no active textual merge conflict, **not** that the branches are semantically compatible.

### Uncommitted and dangling work

The current working tree contains uncommitted changes in:

- `backend/apps/users/serializers.py`
- `backend/apps/users/urls.py`
- `backend/apps/users/views.py`

They add candidate application list/detail API endpoints (81 changed lines). `git diff --check` reports no whitespace issue, but no dedicated tests cover this new endpoint. Preserve and test this work before any branch switch/rebase.

`git fsck --no-reflogs --unreachable` found dangling commits that can be pruned by future garbage collection:

| Commit | Content | Action |
|---|---|---|
| `dce2b0f` | WIP on `development`, 235 changed lines across CV tailoring, Career URLs/views, Bedrock plugin, profile services and Rashid model | Preserve on a recovery branch, inspect/cherry-pick selectively. |
| `6f5633d` | Consent check for `TalentDiscovery` | Compare with current employer consent code, then preserve or discard intentionally. |
| `14d95cd` | Staged index state associated with `dce2b0f` | Preserve with the WIP analysis; do not rely on it remaining recoverable. |

**Safe branch-recovery procedure (human-approved change):** create a separate recovery branch from the dangling commit, run the full suite, then cherry-pick only reviewed changes into a dedicated integration branch. Do not rebase, reset, or merge the three divergent long-lived branches in place.

## 2. Validation results

| Check | Result | Evidence / implication |
|---|---|---|
| Django system check | Passed with 3 warnings | Deprecated django-allauth settings: `ACCOUNT_AUTHENTICATION_METHOD`, `ACCOUNT_EMAIL_REQUIRED`, `ACCOUNT_USERNAME_REQUIRED`. |
| Python compilation | Passed | `compileall` succeeded for `apps` and `config`. |
| Backend pytest | **Passed: 497**, skipped: 2 | Completed in 88.40 seconds using local `config.settings.test`. Warnings remain for Daphne’s Windows event-loop policy, naive `CareerUserSkill.created_at` datetimes, and drf-spectacular typing. |
| Backend formatting/lint/type checks | Not runnable | Local virtualenv lacks Black, isort, Flake8, and mypy even though CI expects them. |
| Frontend production build | Passed with warnings | Caniuse database is 15 months stale; entry bundle is 1,340.79 kB minified / 355.73 kB gzip. |
| Frontend lint | **Failed: 226 errors, 25 warnings** | Dominated by `no-explicit-any`; also empty catch blocks, hook dependencies, raw `require`, and non-const variables. |
| Frontend Vitest | **Failed: 4/5 files; 30 failed tests; 5 errors** | `use-auth.tsx:56` calls `.then` on an undefined mocked `getMe()` result, cascading into auth-hook and Login tests. |
| Docker/live integration | Not run | Docker Desktop daemon is not running; no Postgres/Redis/container or production-style E2E validation was possible. |

### CI defect

`.github/workflows/ci.yml` invokes `npm run format:check`, but `frontend/package.json` does not define that script. The frontend CI job cannot be treated as a reliable green gate until this mismatch is fixed and the lint/test failures are addressed.

## 3. Current feature and integration findings

### High-priority functional defects

| Priority | Finding | Verified evidence | Required outcome |
|---|---|---|---|
| P0 | Resume Builder sends requests to an unmounted API family. | `frontend/src/pages/ResumeBuilder.tsx` uses `/api/v1/resumes/...`; root backend routes mount the app below `/api/v1/resume/`, making the active family `/api/v1/resume/resumes/...`. | Correct paths, move requests to the shared authenticated client, and add CRUD/export contract tests. |
| P0 | Employer dashboard routes to pages that do not exist. | Dashboard links target `/app/employer/jobs` and `/app/employer/applications`; neither route is declared in `frontend/src/App.tsx`. | Implement routes/pages or remove/redirect links; add route navigation tests. |
| P0 | Settings presents stateful preference controls that do not persist. | Notification and public-profile `Switch` controls have no state, handler, preference load, or mutation. | Back them with a single preference API/form with loading, save, success, and retry state. |
| P0 | Job listing hides errors as “No jobs match.” | `Jobs.tsx` catch only clears `loading`; it has no error state. | Render a retryable API-error state and preserve prior results where appropriate. |
| P1 | Search requests are not debounced. | `searchTimeout` is declared in `Jobs.tsx` but never assigned; URL/filter mutation triggers fetch effect for each keystroke. | Debounce/cancel search updates, keep filter changes immediate, and test request count/error behavior. |
| P1 | Onboarding ownership is duplicated and completion is weak. | `Index.tsx` mounts `OnboardingFlow`; `App.tsx` also mounts an onboarding wrapper. The wrapper suppresses request errors and only records local completion. | One server-backed onboarding controller and one render point. |
| P1 | Profile has weak data-state handling. | `ProfilePage.tsx` bypasses shared shell, lacks a query error state, has mutations without user feedback, initializes edit state once from async data, and lacks advertised CV-size validation. | Use shared layout and typed mutations; add error/retry/success states and validate 10 MB client-side. |
| P1 | Employer API error may redirect the user to registration. | Employer dashboard handles any employer-profile query error as “profile missing.” | Only route to registration on a verified 404/no-profile response; render 401/403/5xx independently. |

### Platform fragmentation and capability gaps

- **Retrieval/matching:** browse (`/jobs/`), search (`/search/`), vectors (`/vectors/`), and career recommendations (`/career/`) coexist. The active user-facing job browser uses `/jobs/`; no frontend consumer was confirmed for semantic/vector search.
- **Assistant:** `RashidChat.tsx` calls `/rashid/...` directly, while `services/intelligence.ts` calls `/intelligence/rashid/chat/`. These are competing user-facing integration points with inconsistent authentication/error handling.
- **Notifications:** inbox is read from `/users/me/notifications/`, while preferences and additional notification operations live under `/notifications/`. This should be reconciled into a documented canonical contract after verifying writers/models.
- **API client:** `services/client.ts` centralizes versioned base URL, JWT refresh, envelope unwrapping, and error normalization, but ResumeBuilder, RashidChat, InterviewPractice, IntelligenceDashboard, and related hooks use direct `fetch` variants. This recreates past API inconsistency risks.
- **Backend-only capabilities:** skills taxonomy, vector/hybrid search, advanced notification administration, and much of the admin/billing control plane have mounted backend routes but no confirmed end-user frontend flow.

### Older-plan assertions that are no longer current-source findings

The master plan is valuable for locating systems but several headline assertions were invalidated by active code and should not be repeated as current facts:

- Employer registration now explicitly assigns the employer role.
- Employer stats uses the corrected employer-posting relationship.
- Scraper task persistence uses `work_arrangement`, not the removed `remote_type` field.
- Hybrid search calls `search_jobs()` rather than a nonexistent `.search()` method.
- Role-aware frontend guards now exist.
- Settings is not wholly static: account name, password, and deletion mutations are wired, although preference switches remain inert.
- Subscription plans and company subscription APIs now exist; payment-provider/customer-billing integration was **not** verified.

## 4. Frontend quality and redesign assessment

### Source-proven causes of an inconsistent experience

1. **Design-system drift:** `index.css` and `tailwind.config.ts` define semantic light/dark/night tokens, motion, focus, and RTL support. Profile, employer dashboard, TalentScore, SalaryInsights, Recommendations, and other legacy pages hard-code palettes and raw controls instead. They will not consistently inherit themes or visual hierarchy.
2. **Multiple application shells:** Some pages use `Layout`, some mount `AuthNavbar` directly, and Profile/Employer dashboard bypass both. Admin has a separate shell. Users experience different headers, landmarks, footers, transitions, and spacing depending on route.
3. **Information architecture inconsistency:** Candidate secondary destinations are hidden in desktop user dropdown but expanded in mobile navigation. Employer has a different partial nav. Admin tabs use ephemeral local state rather than URLs.
4. **Localization is not scalable:** i18next/RTL are initialized, but no source use of `useTranslation` or `t()` was found. Many pages manually branch English/Arabic; Profile, Employer and Admin remain English-heavy or English-only.
5. **Large eager frontend:** `App.tsx` imports all pages, including specialist/admin experiences. `AdminDashboard.tsx` is monolithic and local-tab based, limiting deep linking, testing, responsive refinement, and code splitting.
6. **Misleading data states:** multiple pages treat API errors as empty/zero/no-profile states. This removes user trust and makes operational issues invisible.

### Phased frontend remediation

**Phase A — trust and task completion (one sprint)**

- Fix the five P0 flows above: ResumeBuilder routing, employer dead links, settings persistence, Jobs error/retry, and frontend CI/test failures.
- Restore a green frontend quality gate: define `format:check`, reduce lint errors to zero or adopt a reviewed staged rule migration, and repair failing mocks/tests.
- Add route tests for employer links, settings persistence, job error state, onboarding gate, and resume API path.

**Phase B — one product shell (one to two sprints)**

- Define `PublicShell`, `CandidateShell`, `EmployerShell`, and `AdminShell` as route layouts.
- Standardize PageHeader, Card, Stat, Form, Table, Empty, Loading, and Error primitives using semantic tokens.
- Migrate Profile, Employer Dashboard, TalentScore, SalaryInsights, Recommendations, and specialist pages first.
- Make candidate/employer navigation priority and secondary destinations consistent on desktop and mobile.

**Phase C — canonical services and performance (two sprints)**

- Establish typed domain services built on `apiRequest`; retain explicit adapters only for streaming/WebSocket cases.
- Select canonical contracts for search/recommendations, Rasheed, notifications, onboarding, and applications; deprecate duplicate routes/clients deliberately.
- Split Admin and specialist pages using route-level lazy loading, nested routes, URL-backed admin tabs, skeletons, and route error boundaries.
- Set and enforce an initial entry-chunk performance budget below the current 1.34 MB minified bundle.

**Phase D — prove the visual and accessibility outcome**

Run browser-based visual regression and manual QA across EN/AR × light/dark/night × phone/tablet/desktop, plus keyboard, screen-reader, contrast, focus-management, offline/error, and real API-data journeys. The source review cannot validate actual contrast, clipping, responsive layout, focus traps, chart/table RTL, or provider-backed interactions.

## 5. Recommended repository recovery sequence

1. **Protect current work:** create recovery references for dangling commits and commit/stash the user’s application-endpoint work only after review.
2. **Choose the integration target:** document whether `origin/main` or `development` becomes the intended release lineage. Do not continue feature work on three competing trunks.
3. **Create a disposable reconciliation branch:** merge/cherry-pick in small, tested sets; use `git range-diff` and feature-level tests, not commit messages alone.
4. **Gate promotion:** require clean frontend lint/test/build, backend test/check, a working CI format script, and Docker-backed integration validation before merging into the chosen release branch.
5. **Archive branch decision:** once reconciliation is complete, protect one canonical default branch and retire/lock legacy branches so divergence cannot recur.

## 6. Limitations and follow-up checks

- No production deployment, database corpus, Celery scheduling, AWS Bedrock/Polly/Transcribe, payment, external ATS, or browser extension was exercised.
- Docker Desktop was unavailable, so service-to-service and Postgres/Redis behavior was not verified.
- Backend style/type tools were not installed in the local virtualenv; their status is unknown.
- The user’s uncommitted endpoint changes compiled and passed the broad backend suite but have no targeted endpoint tests.
- Browser visual quality, accessibility and mobile behavior require an environment with frontend + API data and a device/browser test pass.

## Appendix: audited evidence paths

- Repository guidance: `AGENTS.md`
- Master plan and historical audit corpus: `MASTER_IMPLEMENTATION_PLAN.md`, `audit/D1_*` through `audit/D10_*`
- CI: `.github/workflows/ci.yml`
- Routing: `backend/config/urls.py`, `frontend/src/App.tsx`
- API client: `frontend/src/services/client.ts`
- User journey examples: `frontend/src/pages/ResumeBuilder.tsx`, `Settings.tsx`, `Jobs.tsx`, `ProfilePage.tsx`, `pages/employer/EmployerDashboard.tsx`
- Design foundation: `frontend/src/index.css`, `frontend/tailwind.config.ts`, `frontend/src/components/Layout.tsx`, `frontend/src/components/AuthNavbar.tsx`

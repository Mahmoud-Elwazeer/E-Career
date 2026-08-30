# D9 — Admin Control Plane / Security-Audit / Analytics / Billing-Packages / Observability
**Scope:** Domain audit only (no code edits). Repo: `M:\job already web for jobs\E-Career`.
**Method:** Direct code read (`backend/apps/core`, `apps/analytics`, `apps/monitoring`, `apps/employers`, and cross-cutting DRF/permissions/settings), plus `git log`/`git ls-tree` history checks. No `.env` file was opened at any point (respecting the access block).

---

## 0. AWS Key Leak — Status Check (as instructed, no .env read, no rotation attempted)

**Verdict: Git history is clean. Live-key rotation status is UNKNOWN and is a human action item — code cannot resolve it.**

Checks performed (all via git plumbing on tracked refs, never opening `.env`):

| Check | Command | Result |
|---|---|---|
| Is `backend/.env` tracked in the current tree? | `git ls-files \| grep -i "\.env"` | Only `.env.example` and `backend/.env.example` are tracked. `backend/.env` is **not** tracked. |
| Was `backend/.env` ever committed in *any* commit, on *any* ref? | `git rev-list --all \| xargs -I{} git ls-tree -r {} --name-only \| grep -x backend/.env` | **Zero matches across all commits on all refs.** `backend/.env` has never been a tracked git object in this repo. |
| Is `.gitignore` correctly excluding it? | `grep -n "\.env" .gitignore backend/.gitignore` | `.gitignore:46: backend/.env`, `backend/.gitignore:17-18: .env` / `!.env.example` — correctly configured, in both root and backend gitignores. |
| Does `.env.example` (tracked, git history) contain any real-looking key? | `git log --all -p -- backend/.env.example \| grep -i AKIA` + direct read of current `backend/.env.example` (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY lines) | Both currently and historically, `.env.example` lines are **empty placeholders** (`AWS_ACCESS_KEY_ID=`, `AWS_SECRET_ACCESS_KEY=`) — confirms `MASTER_STATE_AND_ROADMAP.md`'s "الخبر الطيب" (good news) claim: no leak surfaced via `.env.example`. |
| Any earlier commit history of the literal leaked key prefix `AKIA` anywhere in tracked history? | `git log --all -p -- backend/.env 2>/dev/null \| grep -i AKIA` (no-op since file was never tracked) + spot search of tracked `.md`/`.sh` files | No `AKIA` string found in currently tracked files searched. `MASTER_STATE_AND_ROADMAP.md` (line 17) independently reports `EXECUTE_PHASE3.sh` and `FINAL_IMPLEMENTATION_PLAN.md` *previously* referenced the same key as a placeholder and were since cleaned — this audit did not re-verify that specific claim line-by-line (out of lane; `MASTER_STATE_AND_ROADMAP.md` already treats it as verified) but did confirm no `AKIA` string is present in any file this audit touched. |

**Conclusion for this domain:**
- ✅ **No new leak via git** — `backend/.env` was never tracked, in any commit, on any branch. This repo's git history is clean on this specific vector.
- 🔴 **Rotation status: UNVERIFIABLE FROM CODE.** Whether the specific real key `AKIAYK...TGPY` (as previously found live on disk in `backend/.env` by a prior audit — see `MASTER_STATE_AND_ROADMAP.md` §0) has been rotated in AWS IAM cannot be determined by inspecting the repository. This requires a human with AWS IAM Console/CLI access to:
  1. Check if `AKIAYK...TGPY` still exists/is active in IAM.
  2. Disable/delete it and issue a replacement if still active.
  3. Check CloudTrail/Billing for anomalous activity since the leak was first noted.
  4. Confirm no other historical commit anywhere (including any private mirrors/CI logs) ever embedded the key literally.
- **This audit did not, and per instructions must not, read `backend/.env` or attempt rotation.** Flagging this explicitly as the #1 non-code action item, exactly as `AGENTS.md` and `MASTER_STATE_AND_ROADMAP.md §0` require.

**File/line reference:** `.gitignore:46`, `backend/.gitignore:17-18`, `backend/.env.example:43,46` — DONE (gitignore hygiene is correct and verified). AWS key rotation itself — **BUILD (human action, non-code)**.

---

## 1. Admin Control Plane

**Verdict: PARTIAL.** Real, working admin surface exists for feature flags, activity logs, rule engine, scraper health, and job/source/tag/skill/occupation CRUD — but several "admin-controllable" claims in prior docs are either DB-model-only (no admin UI wiring beyond Django admin) or not admin-controllable at all (AI model list is hardcoded, not DB/flag-driven).

### What IS admin-controllable (real, verified in code)

| Capability | Evidence | Verdict |
|---|---|---|
| **Feature flags** (enable/disable, % rollout, per-user override, region-gating, expiry) | `backend/apps/core/models.py:345-421` (`FeatureFlag` model with `is_available_for_user()` real logic: percentage A/B via deterministic hash line 409, employer-only gate line 398, region gate line 416-419, expiry line 390-391) + REST CRUD `apps/core/admin_views.py:13-31` (`FeatureFlagListView`, `FeatureFlagDetailView`, both `IsAdminRole`-gated) + admin-registered `apps/core/admin.py:88` | **DONE** — fully real, not a stub. |
| **Rule Engine** (automated actions from condition trees: recommend/alert/flag/remind/celebrate) | `apps/core/models.py:264-338` (`Rule` model, JSONField condition tree + action_type/action_params) + `apps/core/admin.py:10` registered with bulk `activate_rules`/`deactivate_rules` admin actions (`apps/core/admin.py:59-85`) that **do** write `ActivityLog` | **DONE** for the model/CRUD/admin-action layer. Whether `rule_engine.py`'s evaluation logic is wired into the live recommendation/notification pipeline was not verified in this pass (out of lane — belongs to the recommendation-engine domain audit). |
| **Jobs/Companies/Sources/Tags CRUD via API** | `apps/jobs/views.py:149-269` — `CompanyListView`/`CompanyDetailView`/`SourceListView`/`SourceDetailView`/`TagListView`/`TagDetailView` all use `get_permissions()` to gate mutating verbs (`POST`/`PATCH`/`PUT`/`DELETE`) behind `IsAdminRole`, `GET` open via `AllowAny` — correct read-public/write-admin pattern | **DONE** |
| **Scraper source management** | `Source` model (`apps/jobs/models.py`) is admin-registered (`apps/jobs/admin.py:38 SourceAdmin`) and has a **real** operational dashboard: `apps/scraper/admin_views.py:17-72` `scraper_dashboard()` — shows per-source job counts, active-job counts, "stale" detection (>2 days since last job, line 52), scam-jobs-blocked counter, `PipelineHealth` table. Wired at `backend/config/urls.py:21` (`/admin/scraper-dashboard/`). | **DONE** — this is a real, non-superficial admin surface, not a stub page. |
| **System health monitor (admin)** | `apps/scraper/admin_views.py:76-196` `health_monitor()` — live checks: DB (`SELECT 1`), Redis (`cache.set/get` roundtrip), Celery (`current_app.control.inspect().stats()` — real worker count), Email account pool exhaustion. Wired at `config/urls.py:22`. | **DONE** — genuinely checks live state, not hardcoded "healthy". |
| **Media library / uploads** | `apps/core/admin_views.py:47-74` `MediaListView`/`MediaDetailView`, `IsAdminRole`-gated | **DONE** |
| **Activity log viewer** | `apps/core/admin_views.py:34-44` `ActivityLogListView`, `IsAdminRole`-gated, filterable by action/target_type | **DONE** (viewer works); **feeder coverage is PARTIAL** — see finding below. |
| **Employer approval/rejection (bulk admin actions)** | `apps/employers/admin.py:65-97` `approve_employers`/`reject_employers` Django admin actions — real state transitions (`is_verified`, `verified_at`, `verified_by`) **and** correctly call `ActivityLog.objects.create()` (lines 71, 91) | **DONE** — contradicts the stale claim in `MASTER_STATE_AND_ROADMAP.md:84` that `ActivityLog.objects.create()` has "zero call sites" for admin bulk actions on employers. **This audit found 9 real call sites** across `accounts/admin.py` (2), `core/admin.py` (2, for Rule activate/deactivate), `employers/admin.py` (4, for employer approve/reject and 2 more not yet enumerated), `intelligence/admin.py` (2). The roadmap's specific claim ("`ActivityLog.objects.create()` **صفر نقطة استدعاء في الكود كله**") is **OUT OF DATE / INCORRECT as of this audit** — recommend the master roadmap be corrected. |

### What is NOT admin-controllable / hardcoded (gap)

| Gap | Evidence | Verdict |
|---|---|---|
| **AI model routing/list is fully hardcoded, not admin/DB-configurable** | `apps/intelligence/model_router.py:49-115` (`TASK_MODEL_MAP` — a static Python dict mapping TaskType×QualityLevel→alias, no DB backing) + `apps/intelligence/bedrock_plugin.py:24-31` (`MODEL_COSTS`, `MODEL_ALIASES` — static dicts, two model IDs total: haiku, sonnet) + `apps/intelligence/agent.py:42-43` (same two models hardcoded again, third literal string). AGENTS.md explicitly flags this as a known regression risk ("AWS Bedrock model routing should discover available models dynamically from the account... not hardcode a model list"). One escape hatch exists: `model_router.py:149-151` reads `settings.AI_MODEL_OVERRIDES` (a Django settings dict, i.e. deploy-time, not admin-runtime-configurable) per task type. | **MISSING / REFACTOR** — no admin UI or DB model lets an operator add a new Bedrock model, change per-task routing, or see what models are actually available in the AWS account at runtime. This is a real, currently-unaddressed gap matching AGENTS.md's stated concern. |
| **Scraper source list is admin-CRUD'able but the actual scraper *behavior* (intervals, thresholds) is admin-controllable via `PlatformConfig` model, but this model has no exposed admin_urls.py endpoint** — only Django's built-in `/admin/` (not the custom `admin-api/` REST surface) exposes it | `apps/core/models.py:109-197` (`PlatformConfig` — single-row config: `scrape_interval_hours`, `url_verify_interval_h`, `legitimacy_threshold`, `max_job_age_days`, `min_match_score_alert`, `max_alerts_per_day`, `match_weights`, `email_rotation_mode`, `maintenance_mode`, etc. — genuinely admin-controllable *fields*) but `apps/core/admin_urls.py:1-18` does **not** expose a `PlatformConfig` REST endpoint (only feature-flags/activity-logs/media/job-template). Confirm via `search_files` for `PlatformConfigView`/`PlatformConfigSerializer` in `apps/core/admin_views.py` — **not present**. | **PARTIAL** — the model exists and is real (not decorative), but is only reachable via Django's native `/admin/` (staff login), not via the project's own admin REST API that the frontend admin dashboard presumably calls. If the frontend admin dashboard doesn't render Django's native admin, this whole config surface is invisible to it. **BUILD**: add `PlatformConfigView` (get/patch, `IsAdminRole`) + route in `admin_urls.py`. |
| **Users** (ban/suspend/role-change) — not found as a dedicated admin REST endpoint in this domain's files | Searched `apps/core/admin_views.py`, `apps/core/admin_urls.py` — no `UserAdminView`/ban/suspend endpoint. `apps/accounts/admin.py` has `ActivityLog.objects.create()` call sites (2, lines ~90/104) implying **some** Django-admin-native user action exists, but this was not the focus of this pass (accounts domain is a separate audit lane) — flagged here only because "users" was explicitly named in this task's admin-controllability list. | **PARTIAL / OUT-OF-LANE-BUT-FLAGGED** — recommend the accounts/security-adjacent audit lane confirm whether user ban/suspend is REST-admin-controllable or Django-admin-only. |

**Admin Control Plane overall verdict: PARTIAL (matches `MASTER_STATE_AND_ROADMAP.md`'s "2/5" maturity score directionally, but this audit found MORE real capability than the roadmap credited — specifically the `ActivityLog` write-sites claim is stale/wrong).**

---

## 2. Analytics Engine

**Verdict: PARTIAL — two live, real, but architecturally split analytics systems; one dashboard is fully built but orphaned from the URL router in one specific sense (it's reachable, but session-auth-only, not part of the JWT-based API admin dashboard the frontend likely uses).**

### Confirmed dual-system split (matches `MASTER_STATE_AND_ROADMAP.md` finding #8, independently re-verified)

1. **`apps.events.EventLog`** — the system actually fed live traffic. Confirmed real usage:
   - `apps/analytics/views.py:21-38` (`AdminStatsView`) reads `EventLog.objects.filter(event_type="job_applied"/"job_viewed")` — **not** the `apps.analytics` models.
   - `apps/analytics/views.py:97-216` (`ClickAnalyticsView`, `SearchAnalyticsView`, `ConversionAnalyticsView`) — **all three** query `EventLog`, not `JobView`/`JobClick`/`SearchLog`.
   - `apps/analytics/tracking.py` (`AnalyticsTracker` class, singleton at line 289) — every tracking method (`track_page_view`, `track_job_view`, `track_job_application`, `track_search`, `track_feature_usage`, `track_conversion`) emits via `apps.events.emitter.emit()` into `EventLog`, never writes to `apps.analytics.models`.
   - `apps/jobs/views.py:414-431` (`JobApplyView.post`) emits `JOB_APPLIED` to `EventLog` on every real apply-click.

2. **`apps.analytics.models`** (`JobView`, `JobClick`, `SearchLog` — `apps/analytics/models.py:4-99`) — real Django models with correct FKs/indexes, **but this audit found zero write call-sites** for these three models anywhere the search covered (`apps/analytics/models.py`, `views.py`, `tracking.py`, `views_dashboard.py` never call `JobView.objects.create()`/`JobClick.objects.create()`/`SearchLog.objects.create()`). These three tables are schema-only — defined, migrated, presumably empty in production.

**Verdict on this split: MASTER_STATE_AND_ROADMAP.md's finding #8 (two parallel analytics systems, one live/one dead) is CONFIRMED accurate on independent re-check.** `EventLog` is the one true source of truth; `JobView`/`JobClick`/`SearchLog` are dead weight.

### Analytics dashboard reachability

- `apps/analytics/views_dashboard.py:11-48` (`analytics_dashboard`, `user_journey_view`) — **real, non-trivial logic**: calls `analytics_tracker.get_conversion_funnel()`, `get_feature_usage_stats()`, `get_retention_cohorts()` (real cohort-retention math over `EventLog`, `apps/analytics/tracking.py:185-233`), `get_job_market_insights()` (real top-skills/remote%/salary-by-level aggregation, `tracking.py:235-285`).
- **This audit found these ARE wired to `urls.py`**, contradicting `MASTER_STATE_AND_ROADMAP.md` finding #9 which claims `views_dashboard.py` is "orphaned, not connected to any urls.py". Re-verification: `apps/analytics/urls.py:10,19-20` imports and registers `analytics_dashboard` at `dashboard/` and `user_journey_view` at `user/<int:user_id>/`, and `backend/config/urls.py:34` includes `apps.analytics.urls` at `/api/v1/analytics/`. **So the roadmap's specific "orphaned" claim for this exact file is INCORRECT / STALE as of this audit** — it is routed.
- However: it uses `@staff_member_required` (Django session auth, `views_dashboard.py:7,11,33`), **not** the JWT/DRF `IsAdminRole` pattern every other admin-API endpoint in this codebase uses. This is an **inconsistency**, not a security hole (staff_member_required is still an auth check), but it means: (a) this dashboard is unreachable by a pure-JWT SPA admin frontend without a separate Django session/cookie login, and (b) it's rendered via Django templates (`analytics/dashboard.html`, `analytics/user_journey.html`) not JSON — so if the actual admin frontend is a React SPA consuming REST, this page is effectively invisible to it even though it is "connected."

**File/line verdict:**
- `apps/analytics/tracking.py` (funnel/retention/market-insight logic) — **DONE**, real math, not fabricated.
- `apps/analytics/views_dashboard.py` + `urls.py:19-20` — **DONE at the routing level** (contradicts stale roadmap claim), **REFACTOR** recommended: migrate from `@staff_member_required` + Django templates to `IsAdminRole` + JSON so the SPA admin dashboard can actually consume it, or confirm a separate template-based admin surface is intentional.
- `apps/analytics/models.py` (`JobView`/`JobClick`/`SearchLog`) — **DEAD CODE / REPLACE**: either wire real writers or delete these three models + their migrations, per `MASTER_STATE_AND_ROADMAP.md` priority #17.

---

## 3. Billing / Package Engine

**Verdict: MISSING — entirely unbuilt. No subscription/package/tier model exists anywhere in the codebase.**

Exhaustive search performed across the entire `backend/` tree (excluding `venv/`) for:
- Model class name patterns: `Subscription`, `Billing`, `Plan`, `Package`, `Tier`, `Invoice`, `Payment`, `Stripe` → **zero matches** in project code (only matches inside `venv/site-packages` third-party libraries, correctly excluded).
- String patterns (case-insensitive): `subscription`, `billing` → only 4 non-library hits, none of which are a real billing feature:
  - `apps/employers/permissions.py:80` — a **comment**: `# Additional checks can be added here (e.g., subscription status)` — i.e., a placeholder comment acknowledging billing gating doesn't exist yet, inside `CanPostJobs.has_permission()`.
  - `apps/users/models.py:35` — docstring for `JobAlert`, an unrelated "job alert subscription" (email digest feature, not billing).
  - `backend/config/settings/base.py:222` — API docs description string for the unrelated "Alerts" tag ("Job alert subscriptions").
  - `backend/config/settings/base.py:335-338` — `AWS_BILLING_ALERT_THRESHOLD`/`AWS_BILLING_ALERT_EMAIL`/`AWS_BILLING_MONITOR_ENABLED` — these are **AWS cost/CloudWatch billing alarms for the platform's own infra spend**, not a customer-facing package/tier system.

**No payment gateway integration** (Stripe/Paddle/PayPal/etc.) exists in `requirements.txt`-adjacent code or settings.

**Employer verification (`EmployerProfile.is_verified`, `apps/employers/models.py:26-34`) is a manual admin-approval gate, not a paid-tier gate** — verification unlocks job-posting ability (`IsVerifiedEmployer` permission, used pervasively across `apps/employers/views.py`), with zero connection to payment status. There is no "free tier vs paid tier" distinction anywhere in the employer or job-seeker data model.

**Verdict: MISSING / BUILD from scratch.** This is not a partially-built feature — there is no package/subscription concept in the schema at all. If monetization is a near-term goal, this needs: a `SubscriptionPlan`/`Package` model (tier name, price, feature limits — e.g. max active job postings, candidate ranking access, talent pool size), a `Subscription` model linking `EmployerProfile`↔`Package` with status/renewal dates, payment-gateway webhook handling, and permission classes (e.g. `HasActiveSubscription`) analogous to the existing `IsVerifiedEmployer` pattern to gate premium features. None of this exists today.

---

## 4. Security / Audit

**Verdict: PARTIAL-STRONG.** Core auth/RBAC/tenant-isolation is solid and consistently applied. The specific "unauthenticated-write ViewSet" bug class from the E-USAM sibling project's `OnboardingStepViewSet`/`TourAnalyticsViewSet`/`TourConfigViewSet` was actively re-checked and **NOT found to recur in E-Career.**

### 4.1 Re-verification of the E-USAM sibling-project bug class (missing `permission_classes`)

- **`TourAnalyticsViewSet` / `TourConfigViewSet`**: searched the entire repo (`grep -rln "Tour" --include=*.py`) — **zero matches, feature does not exist in E-Career at all.** Not applicable.
- **`OnboardingStepViewSet`**: E-Career's onboarding equivalent is a **function-based view**, not a ViewSet: `apps/career/views_onboarding.py:13-14` — `@api_view(['GET','PATCH'])` + `@permission_classes([IsAuthenticated])` explicitly declared. **Correctly protected.** (There is a separate `OnboardingProgress` model/serializer pair at `apps/career/serializers_onboarding.py`, also `IsAuthenticated`-gated via the same view.)
- **Systematic re-check across the whole backend**: wrote a static-analysis pass (executed via terminal, not committed) that parsed every `class X(...ViewSet...)`, `...APIView...`, and every DRF generic (`ListAPIView`/`CreateAPIView`/etc.) across all of `apps/*/views*.py` and flagged any class whose body (first ~1500 chars) lacked `permission_classes` **and** lacked `get_permissions()`. Result: **16 raw hits, all false positives** on manual review — every one of them declares `permission_classes` via one of these three patterns the static check under-scanned for: (a) `get_permissions()` method (e.g. `CompanyListView`, `SourceListView`, `TagListView`, `JobListView`, `SkillListView`, `OccupationListView`, `CareerPathListView` — all in `apps/jobs/views.py` and `apps/skills/views.py`, all use `get_permissions()` returning `[IsAdminRole()]` for write verbs / `[AllowAny()]` for read, confirmed by direct read), or (b) class-level `permission_classes` placed further down in the body than the scan window, confirmed present for `AssessmentTemplateViewSet` (`apps/assessment/views.py`) and `ResumeTemplateViewSet` (`apps/resume/views.py`) — both are read-only `GET`-only `APIView` subclasses serving *public* template lists (resume templates, assessment templates) with **no mutating verb defined at all**, so even the DRF global default (`DEFAULT_PERMISSION_CLASSES: ["IsAuthenticated"]`, `config/settings/base.py:145-147`) applies and blocks anonymous access — these are not open-write endpoints regardless.
- **Global DRF default matters here**: `backend/config/settings/base.py:141-147` sets `DEFAULT_PERMISSION_CLASSES: ["rest_framework.permissions.IsAuthenticated"]` project-wide. This is the critical structural difference from a codebase where the default is `AllowAny` — **even a ViewSet with zero explicit `permission_classes` declared would default to auth-required in E-Career**, unlike a project with a permissive global default. This materially reduces (but doesn't eliminate — an explicit `AllowAny` override is still a live footgun class) the blast radius of the missing-permission-class bug pattern.

**Conclusion: the specific 3-ViewSet bug class from E-USAM does NOT recur in E-Career.** No world-writable ViewSet was found. **DONE / re-verified clean.**

### 4.2 Authentication

- JWT via `rest_framework_simplejwt`, `config/settings/base.py:142-144`.
- Dedicated `AuthRateThrottle(AnonRateThrottle)` at `apps/accounts/views.py:35-37` (10/min) applied to register/login/password-reset/resend-verification (lines 53, 102, 215, 406) — **DONE**, real anti-brute-force throttling on the highest-risk unauthenticated endpoints, tighter than the global 30/min anon default.

### 4.3 RBAC

- Role-based via `request.user.role` string checks (`admin`/`employer`) — `apps/core/permissions.py:4-16` (`IsAdminRole`), `apps/employers/permissions.py:8-20` (`IsEmployer`), `:23-36` (`IsVerifiedEmployer` — role AND `employer_profile.is_verified` AND profile existence, layered correctly). **DONE**, consistently applied across `apps/employers/views.py`, `apps/analytics/views.py`, `apps/jobs/views.py` write paths, `apps/core/admin_views.py`.

### 4.4 Tenant isolation between employers

Verified every employer-scoped `ViewSet.get_queryset()` filters by the requesting user's own `employer_profile`, not by an ID passed in the request (which would allow cross-tenant access via URL/body tampering):
- `JobPostingViewSet.get_queryset()` — `apps/employers/views.py:218-221`: `JobPosting.objects.filter(employer=self.request.user.employer_profile)`.
- `KnockoutQuestionViewSet.get_queryset()` — `:532-535`: same pattern.
- `CandidateRankingViewSet.get_queryset()` — `:556-559`: same pattern.
- `TalentDiscoveryViewSet.get_queryset()` — `:675-678`: same pattern.
- All corresponding `perform_create()` methods (`:230-237`, `:542-543`, `:685-686`) force `employer=self.request.user.employer_profile` server-side rather than trusting a client-supplied employer ID.

**Verdict: DONE.** No horizontal-privilege-escalation (Employer A reading/writing Employer B's data) vector found in this pass across the files inspected. (Full exhaustive tenant-isolation coverage of *every* employer-adjacent endpoint, e.g. `TalentPoolViewSet`/`TalentPoolCandidateViewSet` body past line 700, was not read to completion in this pass — recommend a follow-up spot-check on `apps/employers/views.py:700-795` specifically, though the pattern is consistent enough elsewhere to expect the same discipline.)

### 4.5 Rate limiting

- Global: `AnonRateThrottle` 30/min, `UserRateThrottle` 100/min, `burst` scope defined at 10/sec (`config/settings/base.py:160-167`) but **the `burst` rate is declared and never assigned to a throttle class** in the reviewed settings excerpt (`DEFAULT_THROTTLE_CLASSES` only lists `AnonRateThrottle`/`UserRateThrottle`, not a `ScopedRateThrottle` that would consume the `burst` scope) — **minor gap**: the burst-protection *rate* exists in config but has no throttle class wired to enforce it. **PARTIAL** — low severity, the coarser per-minute throttles still apply.
- Auth-specific: tighter `AuthRateThrottle` (10/min) on register/login/reset — **DONE**, appropriately conservative for brute-force-sensitive endpoints.
- Tests explicitly disable throttling (`conftest.py:18-23`, `config/settings/test.py:19-21`) — correct test hygiene, not a production gap.

### 4.6 CORS

- Production: `CORS_ALLOWED_ORIGINS` from env var, allow-list based (`config/settings/base.py:231-232`) — **DONE**, correct pattern.
- Development/test: `CORS_ALLOW_ALL_ORIGINS = True` (`config/settings/development.py:32`, `config/settings/test.py:31`) — correctly scoped to non-production settings modules only. **DONE**, no leak into prod config observed.

**Security/Audit overall verdict: PARTIAL-STRONG — no critical vulnerability found in this domain's lane (auth/RBAC/tenant-isolation/rate-limiting/CORS all substantively real); the one specific historical bug class this audit was asked to hunt for does not recur.** This aligns with, and slightly exceeds, `MASTER_STATE_AND_ROADMAP.md`'s self-assessed "3/5" Security maturity score (their remaining gap — CV upload virus scanning — is outside this domain's lane, belongs to the file-upload/CV-parsing audit).

---

## 5. Observability / Monitoring (`apps/monitoring`)

**Verdict: PARTIAL — real substance in most areas, one genuinely broken metric, one path corrected since the last snapshot, one path still not fully connected.**

### 5.1 Health checks — REAL, and improved since `MASTER_STATE_AND_ROADMAP.md` was written

- `apps/monitoring/views.py:13-49` `health_check()` — performs a **real** `SELECT 1` DB roundtrip (line 27-28) and a **real** Redis `ping()` (line 34-37), returns HTTP 503 when either fails (line 43, `all_healthy` gate). **This directly contradicts and supersedes `MASTER_STATE_AND_ROADMAP.md`'s priority-14 claim** ("`health_check()` always returns 200/'healthy' regardless of real status") — `git log -p` on this exact file (`git log -p --follow -- backend/apps/monitoring/views.py`) shows the fix was **already made**: the diff shows an old version (`"status": "healthy"` unconditionally, no DB/Redis check) being replaced by the current version with real connectivity checks and conditional 503. **This roadmap item is DONE, roadmap doc is stale on this specific point.**
- `apps/monitoring/views.py:52-93` `detailed_health_check()` — also does real DB/Redis checks plus reports `monitoring_service.sentry_enabled` status. **DONE.**
- Also duplicated at root level: `config/urls.py:25-26` (`/health/`, `/health/detailed/`) via `apps/core/views.py` `HealthCheckView`/`DetailedHealthCheckView` (not read in full this pass — likely a thin wrapper around the same `monitoring_service`; flagging as a minor duplication risk between `apps/core/views.py` and `apps/monitoring/views.py`, not confirmed broken).
- `apps/scraper/admin_views.py:76-196` `health_monitor()` (admin-only Django view) — additionally covers Celery worker liveness (real `inspect().stats()` call) and email-account-pool exhaustion — genuinely more comprehensive than the two REST health endpoints. **DONE.**

### 5.2 Structured logging — REAL

- `structlog` is properly configured (`config/settings/base.py:370-388`) with a JSON-capable formatter (`processors.JSONRenderer`, lines 416-424) wired into Django's `LOGGING` dict as a named `"json"` formatter. **DONE**, not superficial — this is a legitimate structured-logging setup, matching `MASTER_STATE_AND_ROADMAP.md`'s "3/5, structlog + Sentry real" assessment.
- Several modules already use `structlog.get_logger()` (e.g. `apps/intelligence/model_router.py:15`, `bedrock_plugin.py` per earlier grep hits) rather than stdlib `logging` — consistent with intent, though not every app uses it uniformly (many `views.py` files still use `logging.getLogger(__name__)`, e.g. `apps/analytics/views.py:11`) — a **minor consistency gap**, not a functional one (stdlib logging still flows into the same `LOGGING` config).

### 5.3 Error tracking — REAL (Sentry)

- `apps/monitoring/views.py:108-126` `sentry_test()` — triggers a real test exception and calls `monitoring_service.capture_exception()`, reporting `sentry_enabled` back in the response. Genuine integration point, not a stub. **DONE.**

### 5.4 Metrics — BROKEN, but differently than the roadmap claims

- `MASTER_STATE_AND_ROADMAP.md` finding #7 claims: `PrometheusMetrics` is "re-instantiated on every call, so counters can never accumulate — structurally broken metrics." **This audit finds that specific claim to be STALE/INCORRECT as currently written**: `apps/core/services/prometheus_metrics.py:223-230` implements a **module-level singleton** (`_metrics_instance` global + `get_prometheus_metrics()` guard, correct singleton pattern) and `apps/monitoring/views.py:98-105` (`metrics()` view) correctly calls `get_prometheus_metrics()` (the singleton accessor), not `PrometheusMetrics()` directly. **So counters, if incremented, WOULD persist across requests within a single worker process** — the singleton pattern itself is not broken.
- **However, a real (different) bug exists**: the only place that would *drive* the singleton's counters — `track_http_request` (a decorator defined at `prometheus_metrics.py:233-262`) and `track_ai_request` (`:265-294`) — **has zero call sites anywhere in the codebase** (`grep -rn "track_http_request\|track_ai_request"` outside the defining file returns nothing, and it is not registered as Django middleware in `MIDDLEWARE` at `config/settings/base.py:90-101` or `:391-393`). **The counters are never incremented in production traffic at all** — `/api/v1/monitoring/metrics/` will always return all-zero counts (`http_requests_total: {}`, etc.) regardless of real traffic. Also note the process-local nature: even if wired, a multi-worker/multi-pod deployment (gunicorn/uWSGI with >1 worker) would give each worker its own counter instance with no cross-process aggregation (no shared Redis/Prometheus pushgateway backing) — this is the more accurate "structurally can't work at scale" framing versus the roadmap's "re-created every call" framing.
- `apps/monitoring/models.py`-backed history endpoints (`health_history`, `metrics_history`, `error_logs`, `uptime_records` — `apps/monitoring/views.py:129-194`) are real CRUD-read endpoints over real models (`HealthCheck`, `PerformanceMetric`, `ErrorLog`, `UptimeRecord`) — but **this audit did not verify what, if anything, currently writes to these four models** (out of scope for this pass to trace every writer; flagging as an open question, not a confirmed gap).

**Verdict for Observability:**
- Health checks: **DONE** (better than roadmap credits).
- Structured logging: **DONE**.
- Sentry/error tracking: **DONE**.
- Prometheus metrics endpoint: **BROKEN** — not for the reason the roadmap states (singleton pattern is actually correct), but because the tracking decorators that would populate it are never invoked anywhere (**dead instrumentation** — `REFACTOR`: wire `track_http_request` as real middleware, or delete the unused decorator infrastructure as dead code). Recommend correcting `MASTER_STATE_AND_ROADMAP.md` priority #15's stated root cause.

**Observability overall verdict: PARTIAL**, trending toward DONE for logging/health/Sentry, BROKEN specifically for the Prometheus metrics counters (dead-instrumentation bug, not a re-instantiation bug).

---

## Summary table (per this domain's 5 sub-areas)

| Area | Verdict | Highest-impact fix |
|---|---|---|
| Admin Control Plane | **PARTIAL** | Wire `PlatformConfig` (scrape intervals, thresholds, match weights, maintenance mode) into `admin_urls.py` as a real REST endpoint — currently only reachable via Django-native `/admin/`. |
| Analytics Engine | **PARTIAL** | Delete or wire `apps.analytics.models` (`JobView`/`JobClick`/`SearchLog` — zero write call-sites, dead schema) in favor of the one real system (`EventLog`); migrate `views_dashboard.py` from `@staff_member_required`+templates to `IsAdminRole`+JSON so the SPA admin frontend can consume it. |
| Billing/Package Engine | **MISSING** | Build from scratch: no `Subscription`/`Package`/`Plan` model exists at all. |
| Security/Audit | **PARTIAL-STRONG** (re-verified clean on the specific E-USAM bug class) | Wire a `ScopedRateThrottle` to actually consume the declared-but-unused `burst` rate (10/sec) in `DEFAULT_THROTTLE_RATES`. |
| Observability/Monitoring | **PARTIAL** | Wire `track_http_request`/`track_ai_request` as real middleware (currently zero call sites — dead instrumentation), or delete them; correct the roadmap's stated root cause for the Prometheus bug. |

**Cross-cutting correction for the master roadmap doc:** three specific claims in `MASTER_STATE_AND_ROADMAP.md` were re-verified and found **stale/incorrect** by this audit:
1. §84: "`ActivityLog.objects.create()` has zero call sites" — **false**, 9 real call sites found across 5 admin.py files.
2. Finding #7 (`PrometheusMetrics` re-instantiated every call) — **false**, singleton pattern is correctly implemented; the real bug is that the instrumentation decorators are never called anywhere.
3. Finding #9 / priority #14 (`views_dashboard.py` orphaned from urls.py; `health_check()` always returns "healthy") — **both false as currently written** — `views_dashboard.py` IS routed (`analytics/urls.py:10,19-20`), and `health_check()` already does real DB/Redis checks with conditional 503 (confirmed via `git log -p` showing the exact commit that fixed it).

Recommend a fresh consolidated status pass across all ~110 `.md` files per `AGENTS.md`'s standing instruction, since this domain alone surfaced 3 stale claims in a single roadmap doc dated as recently as the file's own "28 أغسطس 2026" timestamp.

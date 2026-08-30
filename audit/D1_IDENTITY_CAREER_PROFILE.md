# D1 — Identity / Auth / User Profile / Career Identity / Onboarding Audit

**Scope:** Auth Engine, User Profile Engine, Career Identity Engine, Onboarding flow.
**Method:** Direct code inspection only (backend/apps/{accounts,users,profiles,career,employers}, frontend/src/{pages,services,components,hooks}). No live server run. Per repo convention (`AGENTS.md`), no `.md` status doc was trusted without code verification.
**Date:** 2026-08-29

---

## 0. Executive summary

| Engine | Verdict |
|---|---|
| Auth Engine (register/login/JWT/roles) | **PARTIAL** — core JWT auth is real and solid; role assignment for employers is **BROKEN** |
| User Profile Engine | **PARTIAL / REFACTOR** — real but split across 2 live model families (`CareerProfile` canonical + deprecated-but-still-live `users.UserProfile`), reconciled only by a one-time migration + a fragile Python alias, not a DB constraint |
| Career Identity Engine ("single source of truth") | **BROKEN / MISSING as claimed** — a real `CareerBrain` model exists that is architecturally exactly what's wanted, but its only sync method (`update_from_profile`) is **never called anywhere in the codebase** (confirmed 0 call sites). Career data instead lives fragmented across **6 separate, uncoordinated models** (`CareerProfile`, `CareerUserSkill`, `CareerLearning`, `TalentScore`, `InterviewSession` (×2, duplicated in `career` and `interviews` apps), `CareerGoal`) with no aggregation job keeping `CareerBrain` current. |
| Onboarding flow | **PARTIAL / FRAGMENTED** — **3 independent, non-communicating onboarding implementations** exist simultaneously (frontend-only landing overlay, Rashid chatbot-style overlay, and a real backend `OnboardingProgress` model+API that neither frontend flow calls). None does account-type (jobseeker/employer) detection. |

This directly confirms the repo's documented pattern (`AGENTS.md` lines 9-12, `MASTER_STATE_AND_ROADMAP.md` "Profile Consolidation" section) of career data fragmenting into disconnected per-feature models instead of one Career Graph — this audit found it is **worse** than the previous consolidation report described, because the intended consolidation target (`CareerBrain`) itself turned out to be a dead/orphaned model.

---

## 1. Current State — Auth Engine

**Files:** `backend/apps/accounts/{models.py, views.py, serializers.py, urls.py, permissions.py, signals.py}`

- **User model** — `backend/apps/accounts/models.py:12-73`. Custom `AbstractUser` subclass, email as `USERNAME_FIELD` (line 49), UUID (line 33), `role` field with choices `jobseeker/employer/admin/user(legacy)` (lines 18-23), `status` (active/inactive/banned, lines 25-28), soft-delete (`is_deleted`, `deleted_at`, lines 42-43, `soft_delete()` method lines 68-73). This is real, not a stub.
- **Registration** — `RegisterView` (`views.py:49-94`) → `RegisterSerializer` (`serializers.py:8-33`). Creates user via `User.objects.create_user(...)` (line 28-33), returns JWT tokens immediately (`get_tokens_for_user`, `views.py:40-45`). Fields accepted: `email, first_name, last_name, password, password_confirm` only — **`role` is NOT an accepted registration field** (`serializers.py:14`). Every new user is created with the model default `Role.JOBSEEKER` (`models.py:20,38`) regardless of stated intent (jobseeker vs employer) at signup time.
- **Login** — `LoginView` (`views.py:98-134`) → `LoginSerializer` (`serializers.py:36-53`), uses Django `authenticate()` with email; checks `is_active`, `is_deleted`, `status == banned`. Real, functional.
- **JWT** — `rest_framework_simplejwt` with blacklist app installed (`config/settings/base.py:34-35`); `LogoutView` blacklists refresh token (`views.py:138-174`); `TokenRefreshView` real (`views.py:178-207`). **DONE.**
- **Password reset** — real email-based flow using Django's token generator (`views.py:211-289`), always-200 anti-enumeration pattern correctly implemented (line 225).
- **Email verification / Google OAuth** — wired to `django-allauth` (`views.py:379-464`); `GoogleAuthView`/`GoogleCallbackView` are effectively stub redirect responses (lines 429-464) — real allauth URLs are used elsewhere (`config/urls.py:75`) but these two DRF views add nothing beyond returning a static redirect string. **PARTIAL** (usable via allauth's own URLs, but the DRF wrapper views are decorative).
- **Roles: jobseeker/employer/admin** — enum exists and is enforced in permission classes (`accounts/permissions.py:7-52`: `IsJobSeeker`, `IsEmployer`, `IsAdmin`, `IsJobSeekerOrEmployer`) and again independently in `apps/employers/permissions.py:8-102` (`IsEmployer`, `IsVerifiedEmployer`, `CanPostJobs`, `CanViewApplicants` — **duplicate/parallel role-gating logic**, not shared with `accounts.permissions`).
  - **CRITICAL BROKEN FINDING:** There is **no code path anywhere in the backend that sets `user.role = "employer"`** (confirmed via repo-wide search — zero matches for `user.role = ` assignments and zero matches for `role=... Role.EMPLOYER`). `EmployerRegistrationView` (`apps/employers/views.py:53-94`) creates an `EmployerProfile` row (line 66) but **never touches `User.role`**. Since `IsEmployer`/`IsVerifiedEmployer` (`apps/employers/permissions.py:15-20, 30-36`) require `request.user.role == "employer"` (or `in ['employer','admin']`), **a user who completes employer registration is immediately locked out of every employer-gated endpoint** (`EmployerProfileViewSet`, `JobPostingViewSet`, ranking, talent pool) because their `role` is still the default `jobseeker`. This is only recoverable via manual admin role edit. This is a **BROKEN** integration between the Auth Engine and the Employer onboarding path.
  - Frontend confirms this: `EmployerRegister.tsx` (`frontend/src/pages/employer/EmployerRegister.tsx:32-38, 60-69`) POSTs to `/employer/register/` and on success just `navigate('/app/employer/dashboard')` (line 36) — no role refresh, no re-fetch of `/users/me/`, no UI indication the account is still jobseeker-scoped.
- **Account-type distinction at signup** — there is no "I am a jobseeker / I am an employer" choice anywhere in `Login.tsx` (register mode, lines 129-141 only collect first/last name + email/password) or `RegisterSerializer`. Employer status is only reachable by a *second*, separate flow (`/app/employer/register`) after already being logged in as a jobseeker. **No account-type detection at registration exists.**

**Auth Engine Verdict: PARTIAL.** Core auth mechanics (JWT, password reset, soft delete) are DONE. Role-based access for the employer path is BROKEN by omission.

---

## 2. Current State — User Profile Engine

**Files:** `backend/apps/profiles/{models.py, views.py, urls.py, serializers.py}`, `backend/apps/users/models.py`, `backend/apps/career/models.py`, `backend/apps/accounts/serializers.py` (`UserMeSerializer`)

- Two separate "user profile" concepts exist and are both live:
  1. **Account identity profile** — `accounts.User` fields exposed via `UserMeSerializer` (`accounts/serializers.py:65-77`): name, avatar, role, status. Served at `GET/PATCH /api/v1/users/me/` and `/api/v1/auth/me/` (two URL names for the same `MeView`, `accounts/urls.py:39,43-44`).
  2. **Career/CV profile** — `CareerProfile` (`backend/apps/career/models.py:21-294`), the actual "user profile" job seekers fill in: CV file/parsed data, skills (flat JSON, line 111-114), education, languages, certifications, target roles/locations/salary, GitHub/portfolio, completeness score (`update_completeness()`, lines 216-256).
- **Deprecated model still fully alive:** `apps/users/models.py:112-183` defines a full second `UserProfile` model (own DB table, own migrations `0001_initial.py`, `0002_userprofile_jobmatchscore.py`, `0004_convert_min_match_score_to_float.py`) with the **same fields** as `CareerProfile` (skills, education, desired_roles, min_match_score, etc.). It is not deleted, its table still exists, and `apps.users` is still an installed app (`config/settings/base.py:50`).
- **The "consolidation" is a Python alias, not a schema-level guarantee:** `backend/apps/profiles/models.py:10-19` does `from apps.career.models import CareerProfile` then `UserProfile = CareerProfile` (line 14) — pure name aliasing at import time inside the `profiles` app, which is a THIRD app in the mix that owns no models of its own. Any code that still imports `apps.users.models.UserProfile` directly (not through the alias) reaches the real deprecated table, not `CareerProfile`. This is exactly the risk flagged in `MASTER_STATE_AND_ROADMAP.md` line 50 ("مضمون بالعادة (convention) فقط, مش ببنية تمنع الانحراف مستقبلًا" — guaranteed by convention only, not by structure that prevents future drift) — **confirmed true by this audit.**
- **One-time migration, not an ongoing sync:** `apps/career/migrations/0004_migrate_userprofile_data.py:11-114` copies data from `users.UserProfile` → `career.CareerProfile` **once**, at migration-apply time, with a fill-if-empty policy (line 21 `if up.cv_file and not cp.cv_file`). It does not delete the old rows, does not deprecate the old table, and — per `MASTER_STATE_AND_ROADMAP.md` — `min_match_score` was explicitly **not** migrated (confirmed: migration `0004` copies `cv_file`, `skills`, `education`, `languages`, `certifications`, `experience_years`, `current_role`, `portfolio_url`, `target_roles`, `target_locations`, salary, `open_to_remote`, `alert_frequency`, `email_alerts`, `preferred_type` — no `min_match_score` line anywhere in the file). Old users' custom alert thresholds are silently lost.
- **API surface is real and works against `CareerProfile`:** `apps/profiles/views.py:31-256` (`ProfileViewSet`) correctly imports `from apps.career.models import CareerProfile` (line 14, bypassing the alias entirely and using the canonical model directly) and exposes `upload_cv`, `completion`, `skills`, `preferences`, `matches`, `calculate_matches` actions — all functional against real DB fields, not mocked.
- **Frontend has TWO parallel Profile pages, only one routed:** `App.tsx:16,59` routes `/app/profile` → `ProfilePage.tsx` (real: calls `profileApi.getProfile()`/`getCompletion()`/`uploadCV()` against `/profile/` endpoints — `frontend/src/pages/ProfilePage.tsx:13-36`, `frontend/src/services/profile.ts:117-149`). No second competing `Profile.tsx` file was found in the current `pages/` listing (unlike the stale claim in `MASTER_STATE_AND_ROADMAP.md` about `Profile.tsx` vs `ProfilePage.tsx` — that appears to have already been resolved by the time of this audit; only `ProfilePage.tsx` exists now). This is a case where the roadmap doc is stale — flagging per `AGENTS.md`'s own instruction to verify against real code.
- **JobMatchScore split:** `JobMatchScore` remains permanently in `apps/users/models.py:186-217` (never migrated to `career`), imported directly by `apps/profiles/views.py:15` and `apps/profiles/models.py:16-19` (try/except import). This is an intentional, documented split (per model docstring, `career/models.py` header) but it means match data lives in yet another app boundary from the profile it's matching against.

**User Profile Engine Verdict: PARTIAL / REFACTOR needed.** Functionally works end-to-end (upload CV → parse → completeness → matches), but the "single canonical model" claim is enforced by an import alias and a one-time migration, not a schema-level source of truth — a live, queryable deprecated duplicate table (`users.UserProfile`) still exists on disk with the risk of future writes going to the wrong table if any code imports it directly.

---

## 3. Current State — Career Identity Engine (evolving single-source-of-truth profile)

**Files:** `backend/apps/career/models.py` (1277 lines total)

The task asks specifically whether a real evolving "Career Identity" single-source-of-truth model exists, or whether career data is fragmented. **Verified finding: fragmented, and the would-be consolidator is itself dead code.**

### 3a. The intended consolidator: `CareerBrain`
- `career/models.py:599-905`. This model is **exactly** the requested "Career Identity Engine" shape: `identity` (JSON: professional_title, career_stage, self_perception — line 627-630), `skills` (JSON with level/verified/years — line 633-636), `goals` (line 639-642), `preferences` (line 645-648), `learning` (line 651-654), `history_summary` (AI-generated text, line 657-660), `ai_observations` (strengths/growth_areas, line 663-666), `confidence_score` (line 669-672).
- Has real, well-written logic: `to_prompt_context()` (lines 685-772, confidence-gated prompt serialization for Bedrock), `update_from_profile()` (lines 774-830, aggregates `CareerProfile` + `CareerUserSkill` + `CareerLearning` into itself), `_calculate_confidence()` (lines 870-905, weighted completeness formula).
- **CRITICAL FINDING — orphaned sync method:** `update_from_profile()` (line 774) is **the only code path that would populate `CareerBrain` from the rest of the system**, and a repo-wide search confirms **zero call sites** for `update_from_profile` anywhere else in `backend/` (checked `apps/career/tasks.py` — the Celery task module that would be the natural home for this — it has no reference to `CareerBrain` or `update_from_profile` at all; checked `apps/rashid/proactive_service.py`, the one place that imports `CareerBrain` (`proactive_service.py:15`) — it only *reads* `CareerBrain`/`CareerGoal`, never calls `.update_from_profile()` on them).
- **Consequence:** `CareerBrainView` (`career/views.py:406-437`) does `CareerBrain.objects.get_or_create(user=request.user)` (line 423) and serves it directly — for any user, this returns an **empty-shell `CareerBrain`** (all JSONFields default to `{}`/`[]`, `confidence_score` default `0.0`, line 669-671) unless something calls `.save(identity=..., skills=..., ...)` on it via the `POST` endpoint (`CareerBrainView.post`, lines 427-437) — which itself is a raw partial-update passthrough with no aggregation logic, i.e. it would only reflect whatever the frontend explicitly PATCHes in, not an automatically evolving synthesis of the user's real activity. **No frontend service file calls `/career/career-brain/` at all** (confirmed: `career-brain` appears nowhere in `frontend/src/services/*.ts` — only in `career/urls.py:52` and `career/views.py`). So `CareerBrain` is dead on both the write side (no automatic aggregation job) and the read side (no frontend consumer). It is a fully built, fully orphaned model.

### 3b. Where career data actually lives (the fragmentation)
Confirmed live, separately-queried, uncoordinated models, each with its own lifecycle and no shared aggregation layer:

| Model | File:Line | Data it owns |
|---|---|---|
| `CareerProfile` | `career/models.py:21-294` | CV parse, flat skills list, experience, target roles/locations/salary, GitHub/portfolio, completeness score |
| `CareerUserSkill` | `career/models.py:297-372` | Structured skill↔proficiency↔verification↔source (the "real" skills model, separate from `CareerProfile.skills` flat JSON — **two skill representations for the same user, not reconciled at write time**: `CareerProfile.skills` (flat list) is written by CV parsing (`cv_parser.py`) while `CareerUserSkill` (structured, verified) is written separately and read by `skill_gap_analysis.py:44-51` and `completeness_calculator.py:217-247`. Nothing keeps them in sync.) |
| `CareerLearning` | `career/models.py:375-433` | Course/certification history — read by `CareerBrain.update_from_profile()` (dead path) and nowhere else confirmed |
| `TalentScore` | `career/models.py:436-504` | 8-dimension composite score, separately calculated by `ScoringEngine` (`career/views.py:19,33-78`) |
| `InterviewSession` (career) | `career/models.py:507-596` | Interview Q&A/scoring — **duplicated model name** with `apps/interviews/models.py:8` (`InterviewSession`, a completely separate table/app used by the actual interview feature per `interviews/views.py`, `interviews/serializers.py`). Two different "interview history" tables exist under the same class name in two apps; `career.InterviewSession` appears to be legacy/unused by the live interview feature (the live interview UI, `InterviewPractice.tsx`, talks to `apps.interviews`, not `apps.career`). This is application-history/interview-history fragmentation exactly as flagged in the task brief. |
| `CareerGoal` / `CareerGoalAction` | `career/models.py:913-1054+` | Goals/milestones — has its own dedicated API (`goal_api.py`, `career/urls.py:27-36,55-62`) fully separate from `CareerBrain.goals` |
| `OnboardingProgress` | `career/models.py:1123+` | Career-stage/primary-interest onboarding answers — see §4 |
| `JobMatchScore` | `users/models.py:186-217` | Match scores — separate app (`apps.users`), separate from `TalentScore` (`apps.career`) — **two different "scoring" concepts split across two apps** |
| Application history | `employers/models.py:166-217` (`JobApplication`) | Applications — lives in `apps.employers`, not surfaced anywhere in `CareerBrain` or `CareerProfile` |

**No single query, view, or serializer in the codebase joins these into one "Career Identity" object for AI/matching consumption other than the dead `CareerBrain.update_from_profile()`.** Rashid AI context-building (`proactive_service.py`) reads `CareerBrain` directly assuming it's populated, but nothing populates it — meaning Rashid's "career context" for personalization is silently empty/stale for every real user, an invisible functional failure the task explicitly wanted flagged.

**Career Identity Engine Verdict: BROKEN.** The single-source-of-truth model (`CareerBrain`) exists in code, has good design, but its aggregation logic is 100% dead code (confirmed zero call sites for its only update method). Actual career data is fragmented across 9 disconnected models spanning 4 different Django apps (`career`, `users`, `interviews`, `employers`), with at least one direct duplication (two `InterviewSession` models) and one unreconciled dual-representation (flat `CareerProfile.skills` vs structured `CareerUserSkill`).

---

## 4. Current State — Onboarding flow

**Files:** `frontend/src/components/landing/OnboardingFlow.tsx`, `frontend/src/components/rashid/RashidOnboarding.tsx`, `frontend/src/App.tsx`, `backend/apps/career/{views_onboarding.py, serializers_onboarding.py, migrations/0005_onboardingprogress_coverletter.py}`

Three completely separate, non-communicating onboarding implementations were found:

1. **`OnboardingFlow.tsx`** (`frontend/src/components/landing/OnboardingFlow.tsx:132-432`) — a 3-step modal (career track → work mode → location) gated by a plain `localStorage` flag `usam_onboarding_complete` (line 7, checked line 143). On completion, `App.tsx:110-114` (`OnboardingWrapper.handleOnboardingComplete`) does: `console.log("User preferences:", preferences); // TODO: Send preferences to backend API` (literal TODO comment, `App.tsx:111-112`) — **the collected data is discarded, never sent to any backend endpoint.** This is a functional dead-end.
2. **`RashidOnboarding.tsx`** (`frontend/src/components/rashid/RashidOnboarding.tsx:47-241`) — a separate 3-question modal (career level → field → goal) gated by a **different** localStorage flag `rashid_onboarded` (line 53). It DOES POST to a backend endpoint: `fetch('/api/v1/rashid/profile/complete_onboarding/', ...)` (line 93) — but **on fetch failure it marks onboarding complete anyway** (lines 108-115), and even on success there is no evidence this endpoint feeds `CareerProfile`, `CareerBrain`, or `OnboardingProgress` (the URL path `rashid/profile/complete_onboarding/` was not found among the confirmed `apps.career` onboarding endpoints — it's a third, separate onboarding store inside `apps.rashid`, not cross-checked further as `apps.rashid` internals are out of this domain's lane per task scope, but its existence itself confirms the fragmentation).
3. **Real backend `OnboardingProgress` model + API** (`career/models.py:1123` class, `career/migrations/0005_onboardingprogress_coverletter.py:18-97`, `career/views_onboarding.py:13-48`, `career/serializers_onboarding.py`) — this is architecturally the correct piece: tracks `steps_completed` (JSON list), `career_stage` (student/junior/mid/senior/exec/career_change — migration lines 44-58), `primary_interest` (find_job/explore/improve_skills/prepare_interviews — lines 59-71), `completed_at`. Exposed at `GET/PATCH /api/v1/career/onboarding/` (`career/urls.py:77`, `career/views_onboarding.py:15-21`). **Confirmed via repo-wide search: no frontend file calls `/career/onboarding/` or imports `onboarding_progress`.** This real, well-designed backend feature is completely unused by any frontend code — it is orphaned in the opposite direction from `CareerBrain` (built, wired, never called).

- **Account-type detection at onboarding:** none of the three onboarding flows ask "are you a jobseeker or employer" — `OnboardingFlow.tsx` assumes jobseeker context throughout (career track/work mode/location are all jobseeker-framed). Employer account creation is a fully separate, later, manually-navigated flow (`/app/employer/register`, §1 above) with its own 2-step wizard (`EmployerRegister.tsx:71-256`) that has no relationship to any of the onboarding components. **There is no unified onboarding entry point that branches by account type.**
- **Progressive structured data collection:** exists in spirit (3 separate step-based UIs) but none of them write to the model (`CareerProfile`/`CareerUserSkill`/`OnboardingProgress`) that the rest of the platform (completeness score, skill gap analysis, matching) actually reads. The `career_stage`/`primary_interest` choices in the real `OnboardingProgress` model would be valuable signal for `CareerBrain.identity` or `CareerProfile.target_roles` — none of that wiring exists.

**Onboarding Verdict: PARTIAL / REFACTOR.** Real UI polish exists (2 different animated modal flows), a real backend model+API exists — none of the three pieces talk to each other, and the two frontend flows both use localStorage-only gating that a backend session/account state cannot see, meaning onboarding "completion" is a browser-local illusion, not an account-level fact.

---

## 5. Gaps (consolidated)

1. **Employer role never granted programmatically** — `EmployerRegistrationView` creates `EmployerProfile` but never sets `User.role = "employer"`; all employer-gated permission classes require exactly that role. Employer self-service registration is functionally broken without a manual admin fix. *(Auth Engine)*
2. **No account-type selection at registration** — `RegisterSerializer` has no `role`/`account_type` field; role defaults to jobseeker for 100% of self-registered users. *(Auth Engine / Onboarding)*
3. **Deprecated `users.UserProfile` table still live** on disk, still an installed app, still imported directly in places (`apps/profiles/models.py` alias, `apps/profiles/views.py` bypasses it correctly but nothing prevents future code from importing the wrong one) — consolidation is convention-only. *(User Profile Engine)*
4. **`min_match_score` permanently lost for pre-consolidation users** — confirmed absent from the `0004` migration's field list. *(User Profile Engine)*
5. **`CareerBrain.update_from_profile()` has zero call sites** — the one method that would make `CareerBrain` an evolving single source of truth is never invoked. No Celery task, no signal, no view calls it. *(Career Identity Engine — most severe finding)*
6. **No frontend consumer of `CareerBrain`** — `/career/career-brain/` endpoint is unused by any `frontend/src/services/*.ts` file. *(Career Identity Engine)*
7. **Two `InterviewSession` models** (`apps.career.InterviewSession` and `apps.interviews.InterviewSession`) with the live interview feature using only the latter — the former appears to be dead/legacy, contributing directly to the "interview history" fragmentation named in the task. *(Career Identity Engine)*
8. **Dual skill representation unreconciled**: `CareerProfile.skills` (flat list, written by CV parser) vs `CareerUserSkill` (structured, verified, written separately) — no sync job between them. *(Career Identity Engine)*
9. **`JobMatchScore` (apps.users) vs `TalentScore` (apps.career)** — two separately-calculated "how good is this user" scoring systems in two different apps, no shared model. *(Career Identity Engine)*
10. **Application history lives outside any career-identity model** — `JobApplication` (apps.employers) is never referenced by `CareerBrain`, `CareerProfile`, or any completeness/skill-gap calculation. Task explicitly asked whether application history is part of the evolving profile — confirmed it is not. *(Career Identity Engine)*
11. **Three disconnected onboarding implementations**, two of which (`OnboardingFlow.tsx`, `RashidOnboarding.tsx`) never write to the one backend model (`OnboardingProgress`) actually designed for this, and the third (`OnboardingProgress`/`views_onboarding.py`) is itself never called by any frontend code — fully orphaned in both directions. *(Onboarding)*
12. **Onboarding "complete" state is `localStorage`-only** for both live frontend flows — not tied to the authenticated account, so it resets per-browser and can't be used server-side to gate features or trigger backend personalization. *(Onboarding)*
13. **No account-type branching in onboarding UI** — all onboarding copy/steps assume a jobseeker; employer onboarding is a separate, unrelated, manually-discovered flow. *(Onboarding)*

---

## 6. Verdict table

| # | Subsystem | Verdict | Primary evidence |
|---|---|---|---|
| 1 | Auth — registration/login/JWT core | **DONE** | `accounts/views.py:49-207`, `accounts/serializers.py:8-53` |
| 2 | Auth — password reset / email verify | **DONE** | `accounts/views.py:211-289, 379-426` |
| 3 | Auth — role model (enum + permission classes) | **PARTIAL** | `accounts/models.py:18-23`, `accounts/permissions.py:7-52` |
| 4 | Auth — employer role assignment | **BROKEN** | `employers/views.py:53-94` never sets `role`; `employers/permissions.py:15-20` requires it |
| 5 | Auth — account-type selection at signup | **MISSING** | `accounts/serializers.py:8-14` (no role field) |
| 6 | User Profile — CRUD/CV/completeness API | **DONE** | `profiles/views.py:31-256` |
| 7 | User Profile — single canonical model guarantee | **REFACTOR** | `profiles/models.py:10-19` (alias, not schema-enforced); deprecated `users/models.py:112-183` still live |
| 8 | User Profile — historical data migration completeness | **PARTIAL** | `career/migrations/0004_migrate_userprofile_data.py` (missing `min_match_score`) |
| 9 | Career Identity — `CareerBrain` model design | **DONE** (as a model) | `career/models.py:599-905` |
| 10 | Career Identity — `CareerBrain` aggregation/sync | **BROKEN** | zero call sites for `update_from_profile()` repo-wide |
| 11 | Career Identity — single-source-of-truth in practice | **BROKEN / REPLACE** | 9 fragmented models across 4 apps, §3b table |
| 12 | Career Identity — skills consolidation | **BROKEN** | `CareerProfile.skills` (flat) vs `CareerUserSkill` (structured) unreconciled |
| 13 | Career Identity — interview history unification | **BROKEN** | duplicate `InterviewSession` in `career` and `interviews` apps |
| 14 | Career Identity — application history integration | **MISSING** | `JobApplication` (employers app) not referenced by any career-identity model |
| 15 | Career Identity — scoring unification | **BROKEN** | `JobMatchScore` (users) vs `TalentScore` (career), no shared model |
| 16 | Onboarding — backend model/API | **DONE** (built) / **INTEGRATE** (unused) | `career/views_onboarding.py:13-48`, zero frontend callers |
| 17 | Onboarding — frontend flows | **PARTIAL / REFACTOR** | `OnboardingFlow.tsx` discards data (`App.tsx:111-112` TODO); `RashidOnboarding.tsx` posts to an unverified separate endpoint |
| 18 | Onboarding — account-type detection | **MISSING** | no code path asks jobseeker vs employer during onboarding |
| 19 | Onboarding — progressive data collection wired to profile | **BROKEN** | none of the 3 onboarding flows write to `CareerProfile`/`CareerUserSkill`/`CareerBrain` |

**Overall recommendation for a follow-up build task (out of scope for this audit):** Retire `CareerBrain` as currently defined or make it real by (a) wiring `update_from_profile()` into a Celery signal/task fired on `CareerProfile`/`CareerUserSkill`/`CareerLearning`/`JobApplication`/`InterviewSession` writes, and (b) folding `JobApplication` and the `interviews.InterviewSession` history into its `learning`/`ai_observations` fields so it can actually serve as the "structured evolving profile" the product spec describes. Separately, fix the employer role-assignment gap before any employer-facing feature work is trusted as "working."

# D10 — Frontend Navigation/UX Journeys + Cross-Cutting Production-Readiness Spot-Check

**Date:** 2026-08-29 | **Scope:** Domain 10 of 10 parallel audits. Read-only, no code edits.
**Baseline read first:** `AGENTS.md`, `M:\job already web for jobs\MASTER_STATE_AND_ROADMAP.md` (2026-08-28),
`BACKEND_ARCHITECT_REVIEW_2026-08.md` (2026-08-29, same day as this audit). This report **does not
re-litigate** items those two already settled (Recommendations 404 root cause, `CareerDashboard`→`TalentScore`
swap, `Profile`→`ProfilePage` swap, `Notifications.tsx` mock claim, AI-shim migration) — it re-verifies the
frontend nav/routing state as of right now and adds new findings. Live repo is being actively edited by other
agents in parallel; line numbers pinned to the state read during this session.

---

## 1. Actual navigation/routes wired per role

### 1.1 Route table (from `frontend/src/App.tsx`, current, lines 50–90)

| Path | Component | Auth gate | Role gate |
|---|---|---|---|
| `/`, `/about`, `/login`, `/reset-password` | Index/About/Login/ResetPassword | none | none |
| `/app/jobs`, `/app/jobs/:id`, `/app/companies/:id` | Jobs/JobDetail/CompanyProfile | `RequireAuth` | **none** |
| `/app/profile`, `/profile` | `ProfilePage` | `RequireAuth` | none |
| `/app/career`, `/app/talent-score` | `TalentScore` | `RequireAuth` | none |
| `/app/saved`, `/saved` | `SavedJobs` | `RequireAuth` | none |
| `/app/alerts`, `/alerts` | `Alerts` | `RequireAuth` | none |
| `/app/recommendations` | `Recommendations` | `RequireAuth` | none |
| `/app/rashid` | `RashidChat` | `RequireAuth` | none |
| `/app/interviews` | `InterviewPractice` | `RequireAuth` | none |
| `/app/resume` | `ResumeBuilder` | `RequireAuth` | none |
| `/app/notification-preferences`, `/app/notifications` | Notification pages | `RequireAuth` | none |
| `/app/settings` | `Settings` | `RequireAuth` | none |
| `/app/applications` | `Applications` | `RequireAuth` | none |
| `/admin` | `AdminDashboard` | `RequireAuth` | **none** (see 1.3) |
| `/admin/intelligence` | `IntelligenceDashboard` | `RequireAuth` | **none** (see 1.3) |
| `/api-docs` | `ApiDocs` | none | none |
| `/app/employer/dashboard`, `/register`, `/post-job`, `/talent-search` | Employer pages | `RequireAuth` | **none** (see 1.2) |

**`RequireAuth`** (`frontend/src/components/RequireAuth.tsx:4-15`) checks only `isAuthenticated` — it has **zero
role awareness**. There is no `RequireRole`/`RequireAdmin`/`RequireEmployer` wrapper anywhere in `frontend/src`
(`search_files` for `RequireAdmin|RequireRole|IsAdmin` in frontend → 0 hits). Backend does enforce role via
`IsAdminRole` (`backend/apps/core/permissions.py:4-16`) and `IsEmployer`/`IsJobSeeker`
(`backend/apps/accounts/permissions.py:7-52`) on the actual API endpoints, so a jobseeker hitting `/admin` or
`/app/employer/dashboard` will get a working shell UI that then 403s/404s on every data call rather than being
redirected away up front. **Verdict: MISSING** — a client-side role gate for `/admin*` and `/app/employer/*` is
architecturally absent. Not a data-integrity bug (backend is the real gate) but a UX/security-posture gap:
non-admin/non-employer users can navigate into these shells and see broken UI instead of a clean "not
authorized" redirect.

### 1.2 Employer navigation — re-verified, MASTER_STATE's claim #5 (`/employer/register` missing `/app` prefix) is now STALE/FALSE

Re-checked every `navigate()`/`<Link>` inside `frontend/src/pages/employer/*.tsx`:
- `EmployerDashboard.tsx:44` → `<Navigate to="/app/employer/register" />` — has `/app` prefix.
- `EmployerDashboard.tsx:81,88` → `to="/app/employer/talent-search"`, `to="/app/employer/post-job"` — correct.
- `EmployerRegister.tsx:36` → `navigate('/app/employer/dashboard')` — correct.
- `JobPostingForm.tsx:63,72,80` → `navigate('/app/employer/dashboard')` — correct.
- `TalentSearch.tsx:194` → `to="/app/employer/dashboard"` — correct.

All five employer-portal internal links already carry the `/app` prefix that matches the routes registered in
`App.tsx:77-80`. **This item is DONE, not the bug MASTER_STATE_AND_ROADMAP.md flagged on 2026-08-28** — same
drift pattern as the other stale items `BACKEND_ARCHITECT_REVIEW_2026-08.md` caught. Re-verify before acting on
the older report's action item #12.

**New finding — no discoverable employer entry point for a normal user.** Grepped the whole `frontend/src` tree
for any public-facing link to `/app/employer/register` or an "Employer"/"Post a Job"/"For Employers" CTA outside
the employer pages themselves (`Footer.tsx`, `Navbar.tsx`, `AuthNavbar.tsx`, `Index.tsx` — 0 hits). A user who
signs up as a jobseeker has **no in-app way to discover or switch into the employer flow** — the only way to
reach `/app/employer/register` is to type the URL directly, because `role` is fixed at registration
(`backend/apps/accounts/models.py:18-23`, `Role.JOBSEEKER` default) and no UI exposes a role-switch/upgrade
path. **Verdict: MISSING** (product gap, not a bug) — employer acquisition funnel has no navigational surface.

### 1.3 Admin navigation — reachable at `/admin` but unlisted anywhere in the nav; verified role gate is backend-only

`AdminDashboard.tsx` and `IntelligenceDashboard.tsx` are routed (`App.tsx:72-73`) but **no `<Link>` to `/admin`
exists anywhere in `Navbar.tsx`, `AuthNavbar.tsx`, `UserMenu.tsx`, or `Footer.tsx`** — confirmed via grep across
`frontend/src`. This is presumably intentional (admin panel not meant to be in a normal user's nav), but combined
with §1.1's missing client role-gate, this means: (a) admins have to know/bookmark the `/admin` URL — there is no
UI affordance for an admin user to get there after login, and (b) any authenticated non-admin who guesses/finds
the URL gets a rendered shell before individual API calls (backed by real `IsAdminRole`, verified at
`backend/apps/analytics/views.py:18,52,100,134,182` and `backend/apps/core/permissions.py:15`) start failing.
**Verdict:** backend security = DONE (real role check on every admin data endpoint); frontend UX = MISSING
(no admin nav entry point, no client-side redirect for the unauthorized case).

### 1.4 Two navbars, two different nav item sets — confirmed still both in use, not obviously wrong but worth flagging

`components/Navbar.tsx` (used by `AppLayout`, e.g. `Settings.tsx`, `Applications.tsx`, `Notifications.tsx`) shows
`Jobs / Applications / Career`. `components/AuthNavbar.tsx` (used by `Layout`, e.g. `Index.tsx`, `Jobs.tsx`,
`Alerts.tsx`, `SavedJobs.tsx`, `CompanyProfile.tsx`, `About.tsx`, `Recommendations.tsx`, `RashidChat.tsx`) shows
a different, smaller set: `Jobs / Profile / About`. Since routing between `Layout`-wrapped and `AppLayout`-wrapped
pages happens constantly in the same user session (e.g. Jobs→Applications, or Alerts→Settings), the **primary
nav bar visibly changes shape depending on which page you're on** — no `Applications`/`Alerts`/`Saved`/`Career`
link is visible from `Layout`-wrapped pages, and no `About` link from `AppLayout`-wrapped pages. This is the same
architectural-duplication pattern already flagged for `services/client.ts` vs `services/api.ts` and
`CareerDashboard.tsx` vs `TalentScore.tsx` in the prior reports — it is now confirmed to also exist **one layer up**
in the layout/nav components themselves, not just the API-client layer. **Verdict: REFACTOR** — collapse to one
`Navbar`/`Layout` pair with one canonical nav-item list; low risk, no backend dependency.

---

## 2. Production-readiness spot-check — 5 sampled pages/features (file:line, frontend call → backend view)

Sampled: Employer Dashboard, Company Profile, Settings, Saved Jobs, Alerts (as suggested), swapping in
Job-Posting-Form's custom-form-fields path in place of a second admin duplicate since D-admin/security domain
already owns Admin Dashboard proper.

### 2.1 Employer Dashboard — DONE (real data), one dead-end + one real TS type bug found

- Frontend: `frontend/src/pages/employer/EmployerDashboard.tsx:15,21,29` call
  `getEmployerProfile()`/`getEmployerStats()`/`getJobPostings()` from `frontend/src/services/employer.ts:106-108,
  129-131,139-141`, all via `apiRequest` (the canonical, correct client — `services/client.ts`).
- Backend: `backend/apps/employers/views.py:97-166` `EmployerProfileViewSet` (`profile/`, `profile/stats/`),
  `JobPostingViewSet` (`jobs/`) — real querysets filtered by `request.user`, real DB aggregates
  (`Job Posting.objects... .aggregate(Count(...))` at `views.py:169-184`). **Real, DB-backed, not mock.**
- **New bug found — dead "View All" / "Review New Applications" affordances**: `EmployerDashboard.tsx:160-162`
  and `:220-234` render a `<span title="Coming soon" className="cursor-not-allowed">` instead of a working link
  for "View All" jobs and "Review New Applications" — these are inert placeholders shipped in the DOM, not real
  navigation. Minor UX debt, not a data-integrity bug. **Verdict: PARTIAL** (data path DONE; two UI actions
  BUILD-pending / placeholder-only, honestly labeled "Coming soon" in the UI itself).
- **New TypeScript bug found**: `frontend/src/pages/employer/JobPostingForm.tsx:37-41` passes an `onSuccess`
  callback to `useQuery(...)` — this option was **removed in TanStack React Query v5**
  (`package.json:44` confirms `@tanstack/react-query: ^5.83.0` is installed) and only survives on
  `useMutation`. Confirmed via `npx tsc --noEmit -p tsconfig.app.json` → `JobPostingForm.tsx(41,5): error
  TS2769: No overload matches this call.` — this is a genuine, currently-live type error (not caught by the
  passing `vite build` reported in `BACKEND_ARCHITECT_REVIEW_2026-08.md` because Vite's esbuild transform does
  not type-check). **Practical effect**: when editing an existing job posting (`jobId` present), the form's
  `useQuery` fetches the job but the `onSuccess` handler that's supposed to populate `formData` from the fetched
  job **silently never runs** in React Query v5 (the callback is simply not invoked — v5 dropped it entirely,
  it is not a compile-only issue). Editing an existing job posting is very likely broken (form stays empty on
  load) even though creating a new one works. **Verdict: BROKEN** (edit-job pre-fill path) —
  `frontend/src/pages/employer/JobPostingForm.tsx:37-56`, needs `useEffect` on the query's `data` instead of
  `onSuccess`.

### 2.2 Company Profile — DONE, real data, minor client-side join

- Frontend: `frontend/src/pages/CompanyProfile.tsx:37-38` calls `fetchCompanyBySlug(id)` and `fetchJobs({
  page_size: 20 })` from `frontend/src/services/jobs.ts:160-162,130-135`, both via `apiRequest`.
- Backend: `backend/apps/jobs/urls.py:16` → `CompanyDetailView` (`backend/apps/jobs/views.py:170-179`,
  `RetrieveUpdateDestroyAPIView` on real `Company` queryset). Job list is real too
  (`backend/apps/jobs/views.py` `JobListSerializer`/pagination).
- **Note (not a bug, an inefficiency)**: `CompanyProfile.tsx:38-43` fetches only the first 20 jobs platform-wide
  and filters client-side by `j.company_slug === comp.slug` rather than calling a company-scoped jobs endpoint
  or query param — a company with >20 total jobs across the platform, or one whose jobs aren't in the first page,
  will show an incomplete/empty "Jobs" tab even though matching jobs exist. **Verdict: PARTIAL** — real backend,
  but the frontend query construction (`fetchJobs({ page_size: 20 })` with no `company` filter) is a
  correctness bug for any company beyond the first page of results. Fix: add a `company` filter param to
  `fetchJobs`/`JobListView` and use it here instead of client-side filtering.

### 2.3 Settings — MOSTLY STATIC MOCK UI, only theme toggle is real

- `frontend/src/pages/Settings.tsx` (149 lines) renders four cards (Account, Notifications, Privacy & Security,
  Danger Zone). **Every input is uncontrolled and every button has no `onClick`**: `Settings.tsx:42,46` — plain
  `<Input>` with no `value`/`onChange`; `:48` — `<Button>{...Save Changes}</Button>` with **no handler at all**;
  `:71,81,91` — three `<Switch defaultChecked>`/`<Switch>` with no `onCheckedChange`, state is never read or
  persisted; `:115` — public-profile `<Switch defaultChecked>`, same; `:120` — "Update Password" button, no
  handler; `:141` — "Delete" button, no handler. Zero `apiRequest`/service imports for any of these actions
  (only import in the file besides UI primitives is `useTheme` for language, `Settings.tsx:8`). Grepped
  `backend/apps` for a `/settings/` or `/users/me/preferences/` endpoint matching this page's fields — none
  found beyond the already-known `changePassword`/`deleteAccount`/`updateMe` in `services/auth.ts:87-110`
  (real backend endpoints — `MeView`, `ChangePasswordView` per `backend/apps/users/urls.py:2,11-13` — that
  this page simply never calls). **Verdict: MOCK / BUILD** — the backend capability partially exists
  (`changePassword`, `deleteAccount`, `updateMe` are real, wired, and unused elsewhere in the codebase this page
  could call) but `Settings.tsx` itself is 100% presentational scaffolding with no data binding in either
  direction. This is a "built-the-UI-shell-only" pattern distinct from the other domains' "mock data displayed"
  pattern — here there's no data displayed OR submitted at all.

### 2.4 Saved Jobs — DONE, real backend, real data

- Frontend: `frontend/src/pages/SavedJobs.tsx:8` → `useSavedJobs()` (`frontend/src/hooks/use-saved-jobs.ts:20`
  → `fetchSavedJobs()`, `:41` → `saveJob()`, `:51` → `unsaveJob()`, all in
  `frontend/src/services/userdata.ts:12-30`, via `apiRequest`.
- Backend: `backend/apps/users/urls.py:15-16` → `SavedJobListView`/`SavedJobDetailView`
  (`backend/apps/users/views.py:17-67`) — real `SavedJob` model (`backend/apps/users/models.py:6-31`), real
  `unique_together`, real `select_related`/`prefetch_related` queryset. **Verdict: DONE**, end-to-end real,
  contradicts nothing in the prior reports (SavedJobs was flagged there only as "orphaned"/unrouted at the time
  of the 2026-08-28 snapshot — it is now routed at both `/app/saved` and `/saved`, `App.tsx:62,87`, and fully
  functional).

### 2.5 Alerts — DONE, real backend, real data

- Frontend: `frontend/src/pages/Alerts.tsx:16` → `useAlerts()` (`frontend/src/hooks/use-alerts.ts:21,36,49,57`
  → `fetchAlerts`/`createAlert`/`updateAlert`/`deleteAlert`, `frontend/src/services/userdata.ts:46-77`, via
  `apiRequest`.
- Backend: `backend/apps/users/urls.py:18-19` → `AlertListView`/`AlertDetailView`
  (`backend/apps/users/views.py:73-117`) — real `Alert` model (`backend/apps/users/models.py:34-72`), scoped to
  `request.user`, real CRUD. **Verdict: DONE**, fully wired, matches the model MASTER_STATE_AND_ROADMAP.md
  didn't flag as broken for this specific page.
- **Caveat carried over from the roadmap (not re-litigated, just noted for context)**: creating an alert here
  writes to `apps.users.Alert`, which is a *different* model from `apps.profiles`'s `min_match_score` /
  `UserProfile.alert_frequency` fields the roadmap flagged as having a stalled migration — these are two
  parallel alert-preference stores. This page's alerts are real and functional on their own terms, but whether
  they're actually *acted on* by a delivery mechanism is governed by the Notifications-delivery gap the roadmap
  already flagged (§"Notifications" row) — zero send mechanism exists, so an Alert record here is inert data
  with no cron/Celery consumer confirmed to read it. Not re-verified in this pass (belongs to
  notifications/automation domain); flagging the cross-reference only.

### Spot-check summary table

| Page | Frontend call site | Backend view | Verdict |
|---|---|---|---|
| Employer Dashboard | `EmployerDashboard.tsx:15,21,29` → `services/employer.ts:106,129,139` | `apps/employers/views.py:97-184` | PARTIAL (data real; 2 dead UI stubs; edit-job prefill BROKEN via `JobPostingForm.tsx:37-56` React Query v5 `onSuccess`) |
| Company Profile | `CompanyProfile.tsx:37-38` → `services/jobs.ts:160,130` | `apps/jobs/views.py:170-179` + job list | PARTIAL (real data, but jobs-tab filter is client-side over first page only — incomplete for companies w/ >20 platform-wide jobs) |
| Settings | `Settings.tsx` (whole file) | `apps/users/urls.py:11-13` (unused by this page) | MOCK/BUILD (zero data binding either direction; real backend capability exists but isn't called) |
| Saved Jobs | `SavedJobs.tsx:8` → `use-saved-jobs.ts` → `services/userdata.ts:12-30` | `apps/users/views.py:17-67` | DONE |
| Alerts | `Alerts.tsx:16` → `use-alerts.ts` → `services/userdata.ts:46-77` | `apps/users/views.py:73-117` | DONE |

---

## 3. Dynamic Application Forms — re-verify, correction to MASTER_STATE_AND_ROADMAP.md's "not connected anywhere" claim

MASTER_STATE_AND_ROADMAP.md (§"Not-fixed", "Dynamic Application Forms") states: *"`DynamicFormFields.tsx` is
completely dead code — not imported anywhere, not in the applicant's apply page, not in `JobPostingForm.tsx` for
the employer."* **This is now false on the applicant side, confirmed stale:**

- `frontend/src/pages/JobDetail.tsx:24` imports `DynamicFormFields` and `validateDynamicFields`; it is rendered
  at `JobDetail.tsx:597-612` inside the apply modal, bound to `job.custom_form_fields` (typed field, populated by
  the real backend serializer method `get_custom_form_fields` at `backend/apps/jobs/serializers.py:236-242`),
  with live `values`/`onChange`/`errors` wiring back to `applicationValues`/`applicationErrors` state.
- On submit, `frontend/src/services/jobs.ts:207-232` `submitApplication()` posts to
  `/jobs/<slug>/submit-application/`, which is real: `backend/apps/jobs/urls.py` routes to
  `JobSubmitApplicationView` (`backend/apps/jobs/views.py:483-599`) — real validation of required fields
  (`views.py:522-530`), real knockout-question evaluation (`views.py:541-`), and a real
  `JobApplication.objects.create(...)` (`views.py:579-585`) with `custom_form_responses` persisted.
- On the employer side, `JobPostingForm.tsx:401-529` builds a `custom_form_fields` array (add/remove/edit field
  type, label, options, knockout value) and submits it as part of `CreateJobPostingData` via
  `createJobPosting`/`updateJobPosting` (`services/employer.ts:177-183`) → real backend `JobPosting` model field.

**Corrected verdict: DONE, not dead code.** The MASTER_STATE_AND_ROADMAP.md claim was accurate as of its
2026-08-28 snapshot (per that doc's own caveat about rapid drift) but has since been resolved — likely in the
same wave of fixes as the `services/api.ts` deletion commit `35f797b` documented in
`BACKEND_ARCHITECT_REVIEW_2026-08.md`. Only remaining gap noted there (form-builder library, e.g.
`react-formio`) is genuinely absent — but that was never required: the employer's own hand-rolled field editor
in `JobPostingForm.tsx` fully substitutes for it end-to-end. **No action item remains here beyond the roadmap
already being stale on this specific point** — flag for whoever owns doc consolidation.

---

## 4. Open-source repo evaluations (2 of the requested set — both are personal job-search CLI tools, not platforms)

### 4.1 `santifer/career-ops` — REJECT (wrong category; nothing portable to E-Career as a platform)

Career-ops is an **agentic Claude-Code skill pack for an individual job seeker**, not a job board / hiring
platform: it's a local CLI workflow (`/career-ops`, `/career-ops scan`, `/career-ops pdf`, etc.) that uses
Playwright to scan Greenhouse/Ashby/Lever/company career pages, scores postings A-F, tailors a personal CV per
JD, and tracks a personal application pipeline in a terminal dashboard — it runs on the *user's* machine against
*other companies'* job boards, not as a service E-Career would deploy for its own users. There is no server,
no multi-tenant data model, no REST API, no employer-side features — none of it maps onto E-Career's
Django/DRF + React architecture. Its portal-scanning approach (ATS-specific scrapers for Greenhouse/Ashby/Lever)
is conceptually adjacent to E-Career's own ingestion pipeline (already covered by the
web-intelligence/scraping-architect specialist per `AGENTS.md`), but the implementation is Claude-Code-skill
markdown + a Playwright script, not extractable backend code. **Verdict: REJECT** as a codebase to adopt/adapt;
at most, its "Block G posting-legitimacy check" *concept* (flagging scams/ghost jobs) is worth a product-idea
nod for the Job Quality Engine states already defined in `AGENTS.md`, but that's an idea, not code to reuse.

### 4.2 `MadsLorentzen/ai-job-search` — REJECT (same category as 4.1; template repo for one person's job hunt)

Same pattern: a **fork-and-personalize template** for an individual using Claude Code as a career advisor —
LaTeX CV/cover-letter templates, `.claude/skills/` workflow definitions, a personal application tracker, all
designed to be forked, filled with one person's name/CV/salary expectations, and run locally. No backend, no
database, no multi-user concerns, no API. Explicitly warns users to keep it in a private repo because `/setup`
writes personal data into tracked files — the opposite of a shared platform's data model. **Verdict: REJECT** —
nothing here is adoptable for E-Career's multi-tenant Django/React stack; it solves a different problem
(personal job-hunt tooling) than what E-Career is (a job aggregation + hiring platform for many users on both
sides).

**Overall repo-evaluation note for future domain owners:** both remaining unassessed repos in this pair are
personal-productivity CLI tools rather than platform codebases. If other domain audits were expecting
copy-paste-able backend/frontend code from this pair, recalibrate — the realistic yield from this pair is
product-idea inspiration (e.g. career-ops's A-F legitimacy scoring rubric) rather than code.

---

## 5. Priority action list (net-new from this audit; does not repeat MASTER_STATE_AND_ROADMAP.md/BACKEND_ARCHITECT_REVIEW items)

1. **`JobPostingForm.tsx:37-56`** — fix the React Query v5 `onSuccess`-on-`useQuery` bug (replace with a
   `useEffect` keyed on the query's `data`). Currently breaks pre-fill when editing an existing job posting.
   Confirmed via `tsc --noEmit`, not caught by `vite build` (type-checking gap worth closing in CI — `vite
   build` alone is not sufficient evidence of "green," as the prior architect review's own build-passed claim
   didn't catch this).
2. **`Settings.tsx`** — wire the existing, real `updateMe`/`changePassword`/`deleteAccount` endpoints
   (`services/auth.ts:87-110`) to this page's forms; currently 100% non-functional UI shell (no `onChange`, no
   `onClick` on any control).
3. **Add a client-side role gate** (`RequireRole`/`RequireAdmin`/`RequireEmployer` wrapping `RequireAuth`) for
   `/admin*` and `/app/employer/*` routes — currently any authenticated user (regardless of `role`) renders the
   full admin/employer shell before individual API calls 403; a redirect-on-mismatch is cheap and improves both
   UX and defense-in-depth.
4. **`CompanyProfile.tsx:37-43`** — replace the "fetch 20 jobs platform-wide, filter client-side by
   `company_slug`" pattern with a real `company`-scoped query param on `fetchJobs`/`JobListView`; currently
   silently drops jobs for any company whose postings aren't in the first 20 platform-wide results.
5. **Collapse `Navbar.tsx`/`AppLayout` vs `AuthNavbar.tsx`/`Layout`** into one canonical pair — the visible nav
   items currently change shape depending on which of the two layout wrappers a given page happens to use, with
   no functional reason for the split (same architectural-duplication pattern already flagged for the API
   clients and the dashboard-page duplicates).
6. **Employer acquisition funnel** — no public UI link to `/app/employer/register` exists anywhere in the nav,
   footer, or landing page; add a "For Employers" / "Post a Job" CTA if employer signups are meant to happen
   through the web app rather than a manual/offline process.
7. **Dead UI stubs in `EmployerDashboard.tsx:160-162,220-234`** — "View All" and "Review New Applications" are
   inert `<span title="Coming soon">` placeholders; either build the linked views or remove the visual affordance
   so they don't look like frozen buttons.

## 6. Corrections logged against prior reports (for the doc-consolidation pass)

- MASTER_STATE_AND_ROADMAP.md action item #12 ("fix employer `navigate()`/`<Link>` missing `/app` prefix") —
  **already fixed**, re-verified false-as-currently-stated in this pass (§1.2).
- MASTER_STATE_AND_ROADMAP.md "Dynamic Application Forms (Frontend)" row — **already fixed**, `DynamicFormFields`
  is wired on both applicant (`JobDetail.tsx`) and employer (`JobPostingForm.tsx`) sides with a real backend
  endpoint (§3).
- MASTER_STATE_AND_ROADMAP.md "Talent Pool (Frontend)" row ("search... rejected zero results") — **partially
  stale**: `frontend/src/pages/employer/TalentSearch.tsx` exists, is routed at `/app/employer/talent-search`
  (`App.tsx:80`), and does call real Talent Pool APIs (`listTalentPools`, `createTalentPool`, `rankCandidates`,
  `listRankings` — `services/employer.ts:287-314`, backed by real `TalentPoolViewSet`/`CandidateRankingViewSet`
  at `backend/apps/employers/views.py:546,689`). The original claim's search term was likely case/substring
  sensitive on "TalentPool" (one word) vs the actual file name "TalentSearch" — re-verify grep methodology in
  future passes; a bare-string grep for the exact model name is not sufficient to declare a feature area
  frontend-absent.

# PROMPT — E-Career Phase 3: Polish / Cleanup / Consistency

You are a senior backend/full-stack engineer working in the E-Career repo at
`M:\job already web for jobs\E-Career` (Django/DRF backend in `backend/`,
React/Vite frontend in `frontend/`).

## Prerequisite

Ideally Phase 0, 1, and 2 are complete (this phase is cleanup on top of
their work). Check `M:\job already web for jobs\E-Career\audit\` for
`PHASE_0_COMPLETION_REPORT.md`, `PHASE_1_COMPLETION_REPORT.md`,
`PHASE_2_COMPLETION_REPORT.md` — if any are missing, this phase can still
mostly proceed since these are low-risk/isolated items, but flag any item
below that turns out to depend on unfinished earlier-phase work instead of
guessing.

## Before touching anything

1. Read `AGENTS.md` in full.
2. Read `MASTER_IMPLEMENTATION_PLAN.md` — items below are 3.1–3.11 from its
   "Phase 3" table. These are all small, low-risk, isolated cleanups —
   each should be a small independent commit.
3. Never touch `.env` or secrets.

## Scope: these 11 items only

**3.1** — Delete confirmed-dead code:
- Pre-insert deduplication hash computation in the scraper pipeline
  (`apps/scraper/pipeline/deduplicator.py:10-32` — verify it's still dead
  post-Phase-1 before deleting; if Phase 1 wired dedup differently, adjust)
- `apps/core/services/cost_reporting.py` if still unwired after Phase 1/2
- Dead `NotificationCenter.tsx` frontend component (verify zero importers
  first with a repo-wide grep)
- Unused pieces of `apps/config/ai_config.py` if Phase 2 item 2.17 decided
  not to adopt it (check that report first)

For each deletion: grep the whole repo for any reference first, only
delete if genuinely zero live references remain.

**3.2** — Remove leftover debug `print()` statements in
`apps/vectors/plugins/pgvector_plugin.py:202-204`. Replace with proper
`logger.debug(...)` calls if the output is actually useful for
troubleshooting, or just remove if it's leftover noise.

**3.3** — Standardize interview app response envelopes to the project's
standard `{"success": ..., "data": ...}` shape. Currently
`apps/interviews/views.py` doesn't consistently follow this pattern, which
causes 14 of 15 of the app's own tests in
`apps/interviews/tests/test_api.py` to fail on response-shape assertions.
Fix the views to match the standard envelope (check how other apps like
`apps/accounts/views.py` do it for the canonical pattern), then re-run
`apps/interviews/tests/test_api.py` and confirm all 15 pass.

**3.4** — In `frontend/src/pages/employer/EmployerDashboard.tsx:160-162,220-234`,
either wire up the "Coming soon" dead UI stubs ("View All", "Review New
Applications" — check if the backend already supports what they'd need
after Phase 2's work) or remove them cleanly if they're not being built
this cycle. Don't leave dead "Coming soon" UI indefinitely if the backing
data is now available.

**3.5** — Wire a `ScopedRateThrottle` to actually consume the
declared-but-unused `burst` rate (10/sec) in
`config/settings/base.py:160-167`. Check DRF's throttle configuration
docs for `ScopedRateThrottle` usage; apply it to whichever
view(s)/action(s) were intended to have burst protection (check git
history/comments near the settings for intent, or ask the user which
endpoints need burst throttling).

**3.6** — Wire `track_http_request`/`track_ai_request` decorators
(`apps/core/services/prometheus_metrics.py:233-262`) as real middleware
that actually gets called on requests, OR delete the dead Prometheus
instrumentation entirely if metrics aren't being actively used/scraped
(check if there's a `/metrics` endpoint being polled by anything in
`docker-compose`/deployment config first — that tells you whether this
is genuinely wanted).

**3.7** — Fix a field-name inconsistency within
`apps/intelligence/trend_detection.py` itself, lines 45, 53, 97, 105 — the
"recent window" and "previous window" queries use different field names
for what should be the same filter (one presumably still has a
Phase-0-style stale reference). Make both windows use the same, correct
field consistently.

**3.8** — Delete or wire `apps.analytics.models`
(`JobView`/`JobClick`/`SearchLog`, `analytics/models.py:4-99`) — confirmed
zero writers anywhere in the codebase, dead schema. Since
`MASTER_IMPLEMENTATION_PLAN.md` notes `EventLog` is the real, live
analytics system, the recommended action is deletion (with a migration) —
but grep first for any reader (admin views, reports) that might depend on
these tables before removing them; migrate any real readers to `EventLog`
first if found.

**3.9** — Migrate the analytics dashboard
(`apps/analytics/views_dashboard.py`) from `@staff_member_required` +
Django server-rendered templates to `IsAdminRole` (DRF permission) + JSON
responses, so the JWT-based React admin dashboard can actually consume it
instead of it being a separate Django-template-only surface.

**3.10** — Fix `CourseAdvisorTool`
(`apps/rashid/tools.py:385-404`) — it has a hardcoded 14-course Arabic
string list despite a docstring claiming it "fetches from edu.usamif.com".
EITHER build the real integration with edu.usamif.com's course API (check
if E-USAM, the sibling platform, exposes a public API for this — see
E-USAM's own repo/AGENTS.md if accessible), OR fix the docstring to
accurately describe the current hardcoded-list behavior so it stops
misleading future readers. Prefer the real integration if edu.usamif.com's
API is accessible from this environment.

**3.11** — Fix `frontend/src/pages/NotificationPreferences.tsx:50,59` — it
uses a bare `fetch()` call with no auth header, instead of the app's
standard `apiRequest()` client (from `services/client.ts`) that every other
authenticated page uses. This will 401 on the auth-required endpoint it's
calling. Replace with `apiRequest()`.

## When done

Write a completion report to
`M:\job already web for jobs\E-Career\audit\PHASE_3_COMPLETION_REPORT.md`
covering all 11 items: status, what changed, verification.

## After Phase 3 is complete

All 4 phases (0-3) covering the full `MASTER_IMPLEMENTATION_PLAN.md` will
be done. As a final step, read all 4 completion reports together and
produce one consolidated `M:\job already web for jobs\E-Career\audit\ALL_PHASES_FINAL_STATUS.md`
summarizing what was fixed, what was deferred/flagged for human decision,
and any NEW issues discovered during implementation that weren't in the
original 10 domain audits (there often are some — implementing a fix
sometimes surfaces an adjacent bug). Do not let this final report become
yet another disconnected planning doc — it should say "MASTER_IMPLEMENTATION_PLAN.md
is now fully executed as of [date]; see this file for final delta only."

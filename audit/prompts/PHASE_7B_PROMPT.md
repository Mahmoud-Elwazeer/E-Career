# PROMPT — E-Career Phase 7b: Admin AI Copilot, Packages/Entitlements, AI Cost Fixes, Global Search, Celery Beat Viewer

Phase 7a is reviewed and approved (commits `45d80de` through `362550e`
on `development`). Read `audit/PHASE_7A_COMPLETION_REPORT.md` in full
first — it lists the exact 13 new endpoints, 39 tests, and 8 deferred
items this prompt now picks up. Read `AGENTS.md` and `CLAUDE.md` too.

## Scope — the 5 items explicitly deferred from 7a, in priority order

**7b.1 — Admin AI Copilot**

Build a NEW, admin-scoped `pydantic-ai` agent — separate instance from
the user-facing Rashid agent in `apps/intelligence/agent.py` (privilege
separation: do not add admin tools to the user-facing agent's tool
list, and do not let a user-facing conversation invoke admin tools).
Put it in a new file, e.g. `apps/intelligence/admin_agent.py`.

Tools (each must call a REAL existing service/endpoint — reuse the
Phase 7a `admin_api_views.py` views' underlying logic directly, don't
re-implement queries):
- `get_scraper_health()` → wraps `ScraperDashboardView`'s query logic.
- `get_ai_cost_breakdown(period)` → wraps `AICostDashboardView`.
- `find_verification_anomalies()` → e.g. jobs with `admin_override=True`
  in the last N days, or a spike in a specific verification stage's
  failure rate — use `VerificationResult` data.
- `get_talent_pool_stats()` → wraps `TalentPoolAdminView`.
- `get_system_health()` → wraps `SystemHealthView`.

Any tool that would perform a DESTRUCTIVE or state-changing action
(pausing a source, overriding a verification result) must NOT execute
directly from a single chat turn — implement a propose→confirm pattern:
the tool returns a proposed action description + a confirmation token;
a SEPARATE explicit "confirm" endpoint (or a second, clearly-labeled
tool call with the token) actually executes it, and every execution
writes an `ActivityLog` entry (reuse the same pattern
`VerificationOverrideView`/`SourceControlView` already established in
7a — don't invent a new audit mechanism).

New DRF endpoint: `POST /api/v1/admin-api/copilot/chat/` (or similar),
`IsAdminRole`-gated, wrapping the new agent. Frontend: a simple chat UI
in the AdminDashboard's a chosen tab (e.g. add it to "Overview" or a new
"Copilot" section under Administration) — reuse the existing user-facing
Rashid chat UI's component patterns if any are reusable, but keep the
admin chat visually/structurally distinct so there's no confusion about
which agent a screen is talking to.

**7b.2 — Packages/Entitlements model (NO payment/billing — confirmed
scope per the owner's Phase 7 review response)**

Build `SubscriptionPlan` (name, description, feature_flags: M2M or
JSONField list of `FeatureFlag` keys it unlocks, job_posting_limit,
talent_pool_access_tier, candidate_search_limit, ai_features_enabled:
bool or list) and `CompanySubscription` (company FK, plan FK, status:
`trial`/`active`/`suspended`/`cancelled`, started_at, notes). NO Stripe
fields, NO payment fields, NO webhook handlers — this is pure
entitlement bookkeeping. Wire entitlement CHECKS into at least 2 real
gated actions (pick 2 from: job posting count limit, talent pool search
result count limit, AI-powered candidate ranking availability) so the
model has a real effect, not just data sitting unused (same "must have
a real effect" principle from the original governance mandate §24).
Admin CRUD for both models via a new DRF view + a "Packages" tab (the
7a nav placeholder already has a slot ready per the completion report's
nav structure — check if "Packages" needs adding to the 20-section nav,
since it wasn't in the 7a list of 20; if missing, add it as the 21st
item or fold it into "Administration").

**7b.3 — AI cost tracking blind spots (4 gaps identified in 7a, not yet
fixed)**

Per `PHASE_7A_COMPLETION_REPORT.md`'s task 7a.4 note: "4 tracking blind
spots (double-counting, missing operation labels, pydantic-ai
untracked, no per-user)". Fix each:
1. **Double-counting**: find where the same AI call's cost is recorded
   twice (likely two separate logging call sites for one logical
   operation) — trace it in `apps/intelligence/bedrock_plugin.py` and
   wherever `RashidUsage` (or equivalent cost-log model) is written, and
   dedupe to a single write point per call.
2. **Missing operation labels**: cost log entries that don't tag WHICH
   feature/task type triggered them (making `AICostDashboardView`'s
   "by feature" breakdown incomplete) — ensure every AI call site passes
   a `task_type`/`feature` label through to the cost-log write, ideally
   using the `TaskType` enum from `apps/intelligence/model_router.py` as
   the canonical label set (don't invent a second label taxonomy).
3. **pydantic-ai untracked**: the Rashid agent's `pydantic-ai`-based
   tool-calling calls (including the 3 Phase 5 tools and any Phase 7b.1
   admin copilot calls) may bypass the cost-tracking wrapper entirely if
   they call the model through a different code path than
   `BedrockLLMPlugin`. Confirm and instrument this path so agent calls
   are tracked identically to direct `BedrockLLMPlugin` calls.
4. **No per-user**: cost log entries missing a `user_id` (or company_id
   for employer-side AI features) field, making per-user cost analysis
   (needed for future entitlement enforcement in 7b.2, and for detecting
   abuse) impossible. Add the field, backfill is not required for
   historical rows but new rows must have it.

After fixing, extend `AICostDashboardView` to expose per-user/per-company
cost breakdowns (not just per-feature) now that the data supports it.

**7b.4 — Admin global search**

One new DRF endpoint (e.g. `GET /api/v1/admin-api/search/?q=...`) that
searches across Users, Companies, Jobs by a few obvious fields (email/
name for users, name/domain for companies, title/company-name for jobs)
and returns a small, ranked, mixed-type result list with enough info to
link to each result's detail view (reusing whichever detail views 7a
already built — `AdminCompanyDetailView`, the future per-job detail view
if built, etc.). Frontend: a search box in the admin nav header,
`Cmd/Ctrl+K`-style quick-open is a nice-to-have but a plain search bar +
results dropdown is sufficient for this pass — don't over-engineer.

**7b.5 — Celery Beat schedule viewer**

Wrap `django_celery_beat`'s existing `PeriodicTask`/`IntervalSchedule`/
`CrontabSchedule` models (already real, already DB-backed — confirmed in
the Phase 7 audit) in a new read-only DRF list view + a "Automation" tab
in the admin nav (the 7a nav already has an "Automation" placeholder per
the completion report — wire it to this new endpoint). Show: task name,
schedule (human-readable), enabled/disabled, last run, total run count.
Add an enable/disable toggle (PATCH on `PeriodicTask.enabled`) with an
`ActivityLog` entry — this is the one write action in this otherwise
read-only viewer.

## Rules (unchanged from 7a)

- Local commits only, do not push.
- `IsAdminRole` on every new endpoint — no exceptions.
- Do not weaken `is_discoverable` consent enforcement anywhere.
- No payment/billing code (7b.2 is entitlements only, per the confirmed
  decision).
- Real test coverage for every new endpoint with side effects — same
  standard as 7a's 39 tests; do not ship an untested destructive action
  (this repo has a documented history of exactly that mistake in Phase
  5/6, do not repeat it a third time).
- Run full backend test suite + `npx tsc --noEmit` + `npx vite build
  --mode production` before considering 7b complete.

## When done

Write `audit/PHASE_7B_COMPLETION_REPORT.md` with the same structure as
`PHASE_7A_COMPLETION_REPORT.md` (task checklist, endpoint inventory, test
results, deferred items if any). Do not proceed to Phase 7c
(analytics/decision-support polish) without this checkpoint — report
back for review first, same pattern as every prior phase.

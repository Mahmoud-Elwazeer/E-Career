# PROMPT — E-Career Phase 7b/7c: Admin Control Plane Implementation (run AFTER Phase 7's audit is reviewed)

**⚠️ PREREQUISITE: `audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT.md` must already
exist** (the output of `PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md`) **and
the platform owner must have reviewed its classification table and
implementation order.** If that file doesn't exist yet, STOP and run
`PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md` first — this prompt is Phase
7's execution half, not a replacement for its audit half.

---

You are a senior full-stack engineer working on E-Career at
`M:\job already web for jobs\E-Career`. Read `AGENTS.md`, `CLAUDE.md`,
and `audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT.md` (the actual audit output,
not the prompt that generated it) in full before writing any code — its
classification table (DONE/PARTIAL/BROKEN/MISSING/REFACTOR/INTEGRATE/
REPLACE/BUILD) and implementation order (Phase 7a/7b/7c split) are your
exact scope and sequence. Do not deviate from its decisions without
flagging the deviation explicitly in your completion report.

## Execution order (matches the audit's own Phase 7a/7b/7c split)

**Phase 7a — Consolidation (do this first, lowest risk, highest
leverage):**
1. Unify the 3-layer admin surface (Django admin / Django-template
   staff views / React SPA) into ONE authenticated path — the React SPA
   backed exclusively by `IsAdminRole`-gated DRF views. For each
   Django-template view identified in the audit (`scraper_dashboard`,
   `health_monitor`, etc.), build an equivalent DRF endpoint + React SPA
   tab, reusing the underlying query logic (do not rewrite the actual
   data-fetching, just move it behind a proper DRF view and JWT auth).
   Do NOT delete the old Django-template views outright until their DRF
   replacements are confirmed working — deprecate, then remove in a
   follow-up commit once verified.
2. Extend the existing `PlatformConfig` model (do not create a parallel
   config table) to hold: AI model routing overrides (cost limits per
   task type, enabled/disabled models, fallback model), automation
   toggles (which Celery Beat tasks are admin-pausable), and any other
   owner-level settings identified in the audit.
3. Extend the existing `ActivityLog` model's usage to cover every new
   admin action this phase introduces (model override, scraper
   pause/resume, entitlement override, etc.) — every action must be
   logged with who/what/when/why.
4. Surface the verification engine's existing per-job audit trail
   (confirm/build a `VerificationResult` read endpoint if the audit found
   one missing) in a new "Jobs" or "Verification" admin tab — for a given
   job, show which of the 6 verification stages passed/failed and why.
5. Surface django-celery-beat's existing `PeriodicTask`/`TaskResult` data
   (if the audit recommended this over building a new workflow engine)
   via a new DRF wrapper + React tab, giving the owner pause/resume/run-
   now/view-history controls over existing scheduled tasks without
   building a net-new workflow engine.

**Phase 7b — Genuine new builds (only the items the audit classified as
BUILD, not anything it classified as already DONE/PARTIAL):**
1. **Admin AI Copilot**: a new, admin-scoped `pydantic-ai` agent instance
   (separate from the user-facing Rashid agent — privilege separation) in
   `apps/intelligence/admin_agent.py` or similar, with tools like
   `get_scraper_health()`, `get_ai_cost_breakdown(period)`,
   `find_verification_anomalies()`, `get_talent_pool_stats()` — each tool
   calls REAL existing services/models, never fabricates numbers. Gate
   the chat endpoint with `IsAdminRole`. For any tool that would perform
   a destructive/high-risk action (pausing a scraper, disabling a
   feature flag), the agent must PROPOSE the action and require a
   separate explicit confirmation call before executing — never execute
   directly from a single chat turn for destructive actions.
2. **Packages/Entitlements model** (feature-flag-driven, NOT payment
   processing — that's Phase 8, only run if/when the owner decides to
   monetize): `SubscriptionPlan` linking to existing `FeatureFlag`
   records (which flags a plan unlocks) and job-posting/candidate-search
   limits. `CompanySubscription` linking a company to a plan with a
   status field (`trial`/`active`/`suspended`/`cancelled`) — no Stripe,
   no payment fields yet, just the entitlement structure. Admin can
   assign/change a company's plan manually via the admin SPA.
3. **AI Control Center cost-limit/model-health layer**: extend
   `apps/intelligence/model_router.py`'s existing `TASK_MODEL_MAP` with
   an admin-editable override stored in `PlatformConfig` (per Phase 7a
   item 2), plus a per-task-type cost-limit check (if a task type's daily
   spend exceeds an admin-set threshold, fall back to a cheaper model or
   block the call and log it) and a simple model-health check (track
   consecutive failures per model ID; if a model fails repeatedly,
   automatically fail over to the configured fallback and surface this in
   the admin AI dashboard).

**Phase 7c — Polish (do last):**
1. Analytics dashboards per the audit's §19 requirements (user funnel,
   job pipeline health, company funnel, talent pool health, AI
   usage/cost, business metrics) — build ONLY the ones the audit found
   genuinely missing; many analytics primitives already exist
   (`apps/analytics/`, the existing `AnalyticsTab` in `AdminDashboard.tsx`)
   — extend, don't duplicate.
2. Decision-support alerts per the audit's §22 — surface proactive
   warnings (scraper failing, AI cost spike, recommendation quality
   drop, queue backlog) on the admin Overview tab. Start with the
   cheapest-to-implement, highest-value alerts (scraper health is
   already tracked per Phase 7a item 4/5 — wire a simple threshold alert
   on top of data that already exists before building anything new).

## Explicit checklist — the 9 items flagged in the audit prompt as likely MISSING (verify against the actual audit output; build whichever it confirmed as MISSING/BUILD, skip whichever it found already DONE/PARTIAL)

These map 1:1 to the "Explicit checklist" section in
`PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md` — the audit should have
already told you DONE/PARTIAL/MISSING for each; this is the build
checklist so none of them get silently dropped between audit and
execution:

1. **Scraping Control Center — operational controls**: per-`Source`
   start/stop/pause/resume/enable/disable/run-now/reschedule actions (DRF
   views + React admin tab), not just the existing read-only stats
   dashboard. Wire each action through Celery (e.g. revoke a scheduled
   task, trigger an immediate one-off task) with an `ActivityLog` entry
   per action.
2. **AI-assisted scraping (optional, evaluate cost/benefit first)**: if
   the audit recommends it, start with the lowest-risk assist (anomaly/
   failure diagnosis — an AI tool that reads recent scraper error logs
   and summarizes likely causes) before source-discovery or parser-
   adaptation automation, which are higher-risk. Any AI action that would
   change a live parser/source config MUST go through the
   propose→approve→execute→audit flow — never auto-apply.
3. **Talent Quality framework**: only build if the audit found
   `TalentScore`/`ScoreBreakdown` insufficient — if those already
   implement an explainable, evidence-based score, this item is
   INTEGRATE (surface it better in admin), not BUILD.
4. **Recommendation Control (admin view)**: a new admin-only endpoint +
   React tab that, given a recommendation event ID (or user+job pair),
   shows the full breakdown (reuse `MatchingService.get_match_breakdown`
   from Phase 5 — call it from the admin side too, don't duplicate the
   scoring logic) plus admin-configurable ranking weight overrides stored
   in `PlatformConfig`.
5. **Per-job admin detail page**: one new React page
   (`AdminJobDetail.tsx` or similar) + one new DRF view aggregating
   `Job` + its `VerificationResult` history + duplicate relationships +
   quality_state + matching stats. Link to it from the existing
   `AdminJobsTable.tsx` (add a "view details" action per row).
6. **User Lifecycle Timeline**: one new React component rendering a
   per-user timeline from `ActivityLog` + any other event sources
   identified in the audit (onboarding steps, CV upload/analysis events,
   application/interview status changes). Backend: one aggregating DRF
   view, not N separate calls per timeline stage.
7. **Company Lifecycle Timeline**: same pattern as item 6, for companies.
8. **Employer/Recruiter admin control**: extend the existing
   `EmployerTeamMember` model's admin visibility — a new admin tab
   listing all hiring-team members across all companies, with a
   suspend/restrict action (soft-disable, not hard delete) and
   `ActivityLog` entry.
9. **Notification admin control + data retention/consent tooling**:
   (a) admin-configurable notification digest/frequency defaults via
   `PlatformConfig`; (b) a genuine per-user data export (JSON dump of
   their profile/CV/applications/interview data) and a delete/anonymize
   action with a confirmation step and `ActivityLog` entry — this is a
   real GDPR-style requirement, treat it with the same care as any other
   irreversible action (require typed confirmation, e.g. re-entering the
   user's email, before executing deletion).

## Rules

- Follow every constraint from `PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md`
  verbatim (no weakening the `is_discoverable` consent gate, no payment
  processing in this phase, no fine-grained admin RBAC unless the audit
  explicitly recommended it, no rebuilding the verification engine/model
  router/feature flags/activity log — extend them).
- Real tests for every new endpoint with side effects (same standard as
  Phase 6's B3 finding — do not repeat the "shipped with zero tests"
  mistake).
- Local commits only, do not push.
- Run `npx tsc --noEmit`, `npx vite build --mode production`, and the
  full backend test suite before considering any sub-phase (7a/7b/7c)
  complete.

## When done (per sub-phase, not just at the very end)

Write `audit/PHASE_7A_COMPLETION_REPORT.md`,
`audit/PHASE_7B_COMPLETION_REPORT.md`, `audit/PHASE_7C_COMPLETION_REPORT.md`
separately as each sub-phase finishes (don't wait until all three are
done to report — this lets the owner review and course-correct between
sub-phases, same pattern as the original Phase 0-3 execution).

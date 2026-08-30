# PROMPT — E-Career Phase 7: Admin Control Plane + Platform Governance Audit

You are a senior full-stack engineer + platform architect working on
E-Career at `M:\job already web for jobs\E-Career` (Django/DRF backend in
`backend/`, React/Vite frontend in `frontend/`). Read `AGENTS.md` and
`CLAUDE.md` first, then read every file in `audit/` — especially
`MASTER_IMPLEMENTATION_PLAN.md` and every `PHASE_*_COMPLETION_REPORT.md`
— before touching anything. **This codebase has changed substantially
since those documents were written. Treat every claim in them as a
hypothesis to re-verify against current code, not a fact.**

## The owner's mandate (verbatim intent, do not water this down)

The platform owner wants the existing Admin Dashboard turned into the
**central control plane** for the entire platform — not rebuilt from
scratch, not a new set of disconnected pages, but the single place they
can see, understand, and safely control every major engine (users,
companies, talent pool, jobs, scraping, verification, matching,
recommendations, Rashid AI, AI model routing/costs, interviews, voice,
notifications, automation/workflows, packages/entitlements, analytics,
security, system health). Every control must be real (operates on the
actual database/services, not a mock), authorized, validated, and
audited. Destructive or high-risk actions require explicit approval, not
silent automation. This is a governance and observability project, not a
feature-count project — do not add pages/tables just because a checklist
item exists; add them where they close a real gap between what the owner
needs to see/control and what currently exists.

## What ALREADY EXISTS — verified against current code, do not rebuild these

This section was produced by directly inspecting the current repo (not
from old planning docs) immediately before writing this prompt. Confirm
each still holds, then build ONLY the gaps — treat re-litigating any of
these as wasted effort unless your verification finds it's actually
broken.

1. **Admin surface today** is split across three layers that don't share
   one navigation:
   - Django admin classes: `apps/{accounts,analytics,assessment,career,
     core,emails,employers,events,intelligence,jobs,monitoring,
     notifications,profiles,rashid,resume,salary,skills,users,
     verification}/admin.py` — standard Django admin registrations, staff-
     only via Django's own auth, not role-gated through `IsAdminRole`.
   - Django-template-based custom admin views (`@staff_member_required`,
     NOT DRF, NOT JWT): `apps/scraper/admin_views.py` (scraper_dashboard,
     health_monitor — 196 lines), `apps/jobs/import_export_admin.py`,
     `apps/jobs/templates/admin/`. These require Django session auth
     (login via `/admin/login/`), which is why the live-verification pass
     found them returning 302 when hit with a JWT — that's correct
     behavior, not a bug, but it means these pages are NOT part of the
     React admin SPA's auth flow.
   - A React admin SPA: `frontend/src/pages/AdminDashboard.tsx` (553
     lines, tabs: overview/jobs/sources/media/settings/logs/analytics/
     import), backed by `apps/core/admin_views.py` (89 lines — DRF views,
     properly gated by `IsAdminRole` permission class, covering
     FeatureFlag, ActivityLog, Media, PlatformConfig only) plus
     `apps/scraper/admin_views.py`'s data being read separately.
   **This 3-layer split (Django admin / Django-template staff views / React
   DRF-backed SPA) is itself the #1 architectural finding — the "control
   plane" the owner wants requires consolidating what's controllable into
   ONE authenticated surface (the React SPA + `IsAdminRole`-gated DRF
   API), not three.**

2. **RBAC**: `apps/accounts/models.py` has `User.Role` (`jobseeker`,
   `employer`, `admin`, legacy `user`) and `apps/core/permissions.py` has
   `IsAdminRole` (checks `role == 'admin'`). This is real but coarse —
   there is no finer-grained admin permission tier (e.g. "can view AI
   costs" vs "can disable a scraper" vs "can delete a user") — everything
   with `IsAdminRole` is all-or-nothing.

3. **AI Model Router**: `apps/intelligence/model_router.py` (165 lines)
   is real and already does task-based routing — `TaskType` enum (13
   task types: chat, cv_parsing, job_matching, interview_prep,
   cover_letter, skill_analysis, content_generation, research,
   classification, extraction, ranking, summary, translation),
   `QualityLevel` enum (fast/balanced/high), `TASK_MODEL_MAP` mapping
   task+quality to a model alias, resolved via
   `apps/intelligence/bedrock_plugin.py`'s `MODEL_ALIASES`
   (`BEDROCK_MODEL_ALIASES` setting, defaulting to `{"haiku": ...,
   "sonnet": ...}`). This is the right shape (task→quality→model, not
   hardcoded) — **the gap is that none of this is exposed or editable
   from the Admin Dashboard**, and there's no cost-limit/rate-limit/model-
   health/fallback-model layer on top of the alias map yet.

4. **AI Cost Tracking**: `apps/rashid/models.py` has `RashidUsage` (per
   the Phase 0 fix history, `event.data` not `event.metadata`).
   `apps/monitoring/views_ai_costs.py` (147 lines) exists and was fixed in
   Phase 0 item 0.16. Verify it's still correct and check whether it
   covers cost tracking for AI calls OUTSIDE Rashid (CV parsing, job
   matching's `career_ai_service`, cv_tailor_service's AI calls added in
   Phase 5) — if those don't write to the same usage/cost table, the
   "AI Control Center" the owner wants will have blind spots.

5. **Direct-Apply Verification Engine**: `apps/verification/` is a real,
   substantial 6-stage engine (`ats_fingerprint.py`,
   `deduplicator.py`, `domain_verifier.py`, `freshness_checker.py`,
   `legitimacy_scorer.py`, `redirect_resolver.py`, orchestrated by
   `engine.py`), with a DB-backed `BlockedDomain` model (unified in Phase
   1 item 1.7). This is NOT a stub — it's real and reasonably
   sophisticated. The gap per the owner's request (§13) is admin
   VISIBILITY into it: is there a UI where an admin can see, for one job,
   which of the 6 stages passed/failed and why? Check
   `apps/verification/models.py` for a `VerificationResult` audit trail
   model, and confirm whether the React admin SPA surfaces it per-job (it
   currently doesn't, per `AdminDashboard.tsx`'s tab list above).

6. **Job Quality States**: `apps/jobs/models.py` has a real
   `quality_state` field with a `QUALITY_STATE_CHOICES` list (confirmed:
   includes at least `active`, `probably_active`, `direct_verified`,
   `needs_verification` — read the full choices list yourself, there may
   be more per the 9-state design in `MASTER_IMPLEMENTATION_PLAN.md`) and
   a queryset manager filtering on it. This is real, not aspirational —
   confirm the full state list and whether admin can see/override it.

7. **Consent/Privacy gate for Talent Pool**: `CareerProfile.is_discoverable`
   (from `apps/career/models.py`) is real and enforced at multiple call
   sites in `apps/employers/views.py` (`TalentDiscoveryViewSet`,
   `TalentPoolViewSet`, candidate ranking) — this was a security fix from
   an earlier audit pass and Phase 5's `connections_service.py` also
   respects it. **Do not weaken or bypass this anywhere in this phase.**

8. **Feature Flags**: `apps/core/models.py`'s `FeatureFlag` model +
   `apps/core/admin_views.py`'s `FeatureFlagListView`/`FeatureFlagDetailView`
   (both `IsAdminRole`-gated) are real and wired to
   `frontend/src/hooks/use-feature-flags.ts`. This is a real, working
   feature-flag system — use it as the mechanism for §15's
   entitlements/packages work, don't build a second flag system.

9. **PlatformConfig**: a real singleton model + `IsAdminRole`-gated
   retrieve/update view already exists (`apps/core/admin_views.py`'s
   `PlatformConfigView`). This is the right place to add AI model
   routing config, cost limits, etc. — extend this model, don't create a
   parallel config table.

10. **ActivityLog**: a real audit-log model + list view already exists
    (`apps/core/models.py`'s `ActivityLog`, `apps/core/admin_views.py`'s
    `ActivityLogListView`, filterable by `action`/`target_type`). This is
    the existing audit trail mechanism — extend its usage to cover new
    admin actions in this phase, don't build a parallel logging system.

## What does NOT exist yet — confirmed via repo-wide search, real gaps

1. **No Packages/Subscription/Entitlement models anywhere** (confirmed:
   `grep -rln "class Package\|class Subscription\|class Entitlement\|class Plan\b"`
   across all of `apps/` returns nothing). §15's "centralized entitlement
   system" is a genuine BUILD item, not a consolidation — but per Phase 2
   item 2.22's decision (`audit/COMPETITIVE_ANALYSIS_JOBRIGHT.md` /
   `MASTER_IMPLEMENTATION_PLAN.md`), billing itself was explicitly
   deferred as premature while the core product doesn't yet deliver real
   jobs reliably. **Resolve this tension explicitly in your audit output**:
   the owner is now asking for entitlement/package CONTROL (§15) which is
   related to but distinct from BILLING (§22's earlier "Skip for now").
   You can build the entitlement/feature-flag-driven package structure
   (which package unlocks which FeatureFlag-gated capabilities) WITHOUT
   building payment processing — flag this distinction clearly and ask
   the user to confirm this scoping before building Stripe/payment code.

2. **No unified Workflow Engine** (confirmed: no `class Workflow`,
   `WorkflowEngine`, or `class Automation` anywhere in `apps/`). What
   exists instead is Celery Beat's `CELERY_BEAT_SCHEDULER =
   'django_celery_beat.schedulers:DatabaseScheduler'` (real, DB-backed,
   admin-editable via Django admin's periodic task UI) plus Django
   signals scattered per-app (e.g. `apps/courses/signals.py`-style
   patterns referenced in other reports). §16/§17's "Platform Workflow
   Engine" / "Automation Center" is a real, large potential BUILD — but
   per the owner's own principle §16 ("do not build multiple disconnected
   workflow systems without a strong architectural reason"), evaluate
   whether django-celery-beat's existing admin UI (already real,
   already DB-backed, already has execution history via
   `django_celery_beat`/`django_celery_results` if installed) can be
   surfaced INSIDE the React admin SPA (via a new DRF wrapper around
   `PeriodicTask`/`TaskResult`) rather than building a net-new workflow
   engine from scratch. Research this tradeoff explicitly before
   proposing a build.

3. **No Admin AI Copilot** (confirmed: no `AdminCopilot`, `admin_chat`,
   or similar). This is a genuine BUILD (§21) — but it should be built as
   a thin, admin-scoped extension of the ALREADY-CONSOLIDATED Rashid
   agent pattern (`apps/intelligence/agent.py`'s `pydantic-ai` tool-
   calling agent, extended with 3 new tools in Phase 5) rather than a
   separate AI system. Register new admin-only tools (e.g.
   `get_scraper_health()`, `get_ai_cost_breakdown()`,
   `find_verification_anomalies()`) on a SEPARATE agent instance scoped
   to `IsAdminRole` users only — do not add admin capabilities to the
   user-facing Rashid agent's tool list (privilege separation).

4. **No fine-grained admin RBAC** beyond the single `admin` role (see
   "What already exists" #2 above) — if the owner wants tiered admin
   access (e.g. a support-tier admin who can view but not disable
   scrapers), this needs a real permission-tier model, not just
   `IsAdminRole`. Confirm with the owner whether single-tier admin is
   acceptable for now (platform is likely owner-only today) before
   building a multi-tier RBAC system that may be premature.

## Explicit checklist — confirm the classification covers ALL of these (do not silently skip any; each maps to a numbered section in the owner's original mandate)

Cross-checked against the owner's full 30-section request — these 9 items
are real, named requirements that are easy to under-scope if the audit
stays too abstract. Each MUST get its own row/subsection in your
classification table, with a DONE/PARTIAL/BROKEN/MISSING/BUILD verdict
grounded in actual code inspection (most of these will classify as
MISSING per the repo-wide searches already run, but verify yourself —
don't assume):

1. **Scraping Control Center — REAL per-source operational controls**
   (owner's §9/§10). `apps/scraper/admin_views.py`'s `scraper_dashboard`
   is READ-ONLY monitoring (confirmed: it only renders `Source`/`Job`
   aggregates, no start/stop/pause/resume/run-now/schedule-edit action
   views exist anywhere in `apps/scraper/`). This is almost certainly
   MISSING — confirm, and if so it's a genuine BUILD: an admin needs to
   individually start/stop/pause/resume/enable/disable/run-now/reschedule
   each `Source`, not just watch its stats. Also missing: differentiated
   workflows for NEW JOB DISCOVERY vs OLD JOB REVALIDATION vs EXPIRED JOB
   CLEANUP vs BROKEN LINK DETECTION vs DUPLICATE DETECTION (§10) — check
   whether these are even conceptually distinct in the current Celery
   task structure, or one undifferentiated "scrape" task.
2. **AI-assisted scraping operations** (§11) — source discovery, parser
   adaptation, anomaly/failure diagnosis via AI. Confirmed MISSING (no
   AI-assist code found in `apps/scraper/` in prior searches). If built,
   must follow the owner's explicit propose→validate→approve→execute→
   audit pattern for anything destructive — AI must never silently
   change a live parser or disable a source.
3. **Talent Quality / Qualification framework** (§5) — an explainable,
   evidence-based scoring system (profile completeness + CV quality +
   verified experience + skills + assessments + interview performance +
   career consistency), explicitly NOT an arbitrary AI "truth score."
   Check whether `TalentScore`/`ScoreBreakdown` (referenced in
   `apps/career/views.py`'s imports: `TalentScoreViewSet`,
   `ScoreBreakdownViewSet`, `ScoreTrendsViewSet`) already implements this
   — if so this may be PARTIAL/DONE, not MISSING; verify the actual
   scoring factors used before classifying.
4. **Recommendation Control — admin-facing explainability + config**
   (§6) — admin visibility into WHY a specific job was recommended to a
   specific user (or candidate to a company), with matching/ranking
   factors, confidence, missing info, negative signals, AND
   admin-configurable ranking weights/eligibility thresholds/frequency
   (via `PlatformConfig`, not hardcoded). Distinct from the USER-facing
   `MatchScoreCard` (Phase 5) — this is an ADMIN view into any
   recommendation event with full audit detail.
5. **Per-job full inspector** (§12) — one dedicated admin page per job
   showing: source, employer, ATS, original/canonical/application URLs,
   direct-apply verification result AND timestamp, status, expiration,
   duplicate relationships, quality score, matching stats, AI
   classification, full source/update history. Distinct from the
   existing `AdminJobsTable.tsx` list view — check if a per-job DETAIL
   view exists at all (likely missing).
6. **User Lifecycle Timeline** (§2) — a per-user admin view showing the
   REGISTERED→ONBOARDING→PROFILE→CV→CAREER IDENTITY→SKILLS→TALENT
   QUALIFIED→RECOMMENDATIONS→APPLICATIONS→INTERVIEWS→RESULTS journey as
   an actual timeline, backed by existing `ActivityLog`/event data where
   available. Confirmed MISSING as a dedicated admin UI (no such
   component found in `frontend/src/components/admin/`).
7. **Company Lifecycle Timeline** (§3) — same pattern for companies
   (REGISTERED→VERIFICATION→PROFILE→PACKAGE→JOBS→DISCOVERY→SCREENING→
   INTERVIEWS→HIRING→ANALYTICS). Confirmed MISSING.
8. **Employer/Recruiter account control** (§14) — admin visibility into
   hiring team members (uses the real `EmployerTeamMember` model from
   Phase 2 item 2.8), permission review, abuse flagging, and an actual
   suspend/restrict action (with `ActivityLog` entry) — not just viewing
   the company's own team-management self-service page. Check whether
   this exists from the ADMIN side specifically (the company's own
   self-service team UI existing is not the same thing).
9. **Notification admin control + data retention/consent tools** (§18,
   §20 partial) — admin-configurable notification templates/frequency/
   digest rules (extend the dual-notification-system fix from earlier
   phases, don't rebuild it), PLUS a genuine data retention/deletion tool
   (view/export/delete a user's data on request, consent history,
   right-to-be-forgotten execution with an audit trail) — GDPR-style
   tooling the owner explicitly asked for in §20 ("data retention, data
   deletion... consent management") that has not been addressed in any
   prior phase's scope. Confirmed MISSING.

## Task: produce the audit BEFORE writing implementation code

Per the owner's explicit instruction (§28: "Do not immediately rewrite
the platform. First produce a definitive Admin Control + Platform
Governance audit"), your FIRST deliverable is
`audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT.md`, not code. Structure it as:

1. **Section-by-section classification** (DONE / PARTIAL / BROKEN /
   MISSING / REFACTOR / INTEGRATE / REPLACE / BUILD) for every one of the
   owner's 30 numbered sections above (§1 Owner-Level Control through
   §30 Final Mandatory Thinking Pass) — grounded in the real code you
   verify, with file:line citations, same rigor as
   `MASTER_IMPLEMENTATION_PLAN.md`'s existing engine table. Do not accept
   my "what already exists" list above as final — re-verify it yourself
   (things may have changed again) and extend it; I did a fast pass, not
   an exhaustive one.
2. **The 3-layer admin surface consolidation plan** (see "what already
   exists" #1) — this is the single highest-leverage architectural
   decision in this whole phase; give it its own subsection with a
   concrete before/after navigation structure matching the owner's §23
   requested IA (Overview/Users/Companies/Talent/Jobs/Sources/Scraping/
   Verification/Matching/Recommendations/AI/Rashid/Interviews/
   Automations/Notifications/Analytics/Packages/Security/System
   Health/Settings), mapped to which EXISTING backend view/model each
   nav section will read from vs. which need a NEW DRF view.
3. **Open-source research** (§26) for the 2 genuinely-new subsystems
   identified above (Admin AI Copilot pattern, Workflow/Automation
   visibility) — search for prior art (e.g. admin-facing AI copilot
   patterns, django-celery-beat admin UI extensions, existing "operations
   command center" OSS dashboards) and give USE/ADAPT/REFERENCE/REJECT
   verdicts, same discipline as `COMPETITIVE_ANALYSIS_JOBRIGHT.md`.
4. **Cross-system trace** (§27) for at least these 3 critical paths, each
   traced FRONTEND → API → SERVICE → DATABASE → EVENT/QUEUE → WORKER →
   AI → RESULT → ADMIN VISIBILITY → USER/COMPANY RESULT, flagging every
   broken link found:
   - A job being scraped, verified, and published (or rejected) —
     does an admin currently have visibility into WHY a specific job
     was rejected by the verification engine?
   - A candidate being recommended to a company via Talent Pool — does
     an admin have visibility into why THIS candidate ranked where they
     did, and can they audit that the `is_discoverable` consent gate was
     actually honored for that specific recommendation?
   - An AI call (any of: CV parsing, match scoring, resume tailoring,
     Rashid chat) — does its cost/latency/model/success actually land in
     a place the admin AI-cost dashboard reads from, end to end?
5. **Answers to the §30 mandatory thinking-pass questions** — do not
   skip this section; the owner explicitly asked for it. Answer each
   question with a concrete statement about current behavior (from your
   verification) and what changes as a result.
6. **Implementation order** (§28) — phased, respecting "don't rebuild
   what works." Split into Phase 7a (consolidation: unify the 3 admin
   surfaces, extend existing models like `FeatureFlag`/`PlatformConfig`/
   `ActivityLog` rather than new ones, surface the verification engine's
   existing audit trail, surface django-celery-beat's existing schedule
   admin inside the SPA), Phase 7b (genuine new builds: Admin AI Copilot,
   Packages/Entitlements model, AI Control Center cost-limit/model-health
   layer on top of the existing model_router), Phase 7c (polish:
   analytics dashboards, decision-support alerts per §22).

## Rules

- Do NOT delete or rebuild the verification engine, model router,
  feature flag system, activity log, or `is_discoverable` consent gate —
  these are real and correct; INTEGRATE and extend, per the owner's own
  §25 instruction.
- Do NOT weaken the `is_discoverable` privacy gate anywhere for the sake
  of admin convenience — admin visibility into WHY a candidate is/isn't
  shown to a company is fine; admin ability to bypass consent and expose
  a non-consenting candidate's PII is not, unless the owner explicitly
  says otherwise in writing.
- Do NOT build a payment/billing engine in this phase — flag the
  packages/entitlements vs. billing distinction (see "what does NOT
  exist" #1) and get explicit confirmation before touching that boundary.
- Do NOT push to GitHub or run `git push` — this is an audit-first phase;
  even after Phase 7b/7c implementation (if the user approves proceeding
  past the audit), commit locally only. The user pushes via Claude Code
  in Visual Studio themselves.
- Local commits only for any code you DO write in this pass (the audit
  doc itself should be committed).

## When done with the audit

Present the classification table and implementation order to me for
review BEFORE writing any Phase 7b/7c implementation code — this mirrors
how the original 10-domain audit → `MASTER_IMPLEMENTATION_PLAN.md` →
phased execution worked earlier in this project. Do not skip straight to
building the Admin AI Copilot or Packages model without that checkpoint.

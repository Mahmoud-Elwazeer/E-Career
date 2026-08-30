# RESPONSE — Phase 7 Audit Review: 2 Corrections + Decisions + Go-Ahead

Read `audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT.md` (your own audit output,
commit `45d80de`) again alongside this message before proceeding — this
is a correction + decision response to that audit, not a fresh task.

## Corrections to the classification table (verified against actual code, not re-reading your own report)

Two items in your 30-section table are marked **DONE** but direct code
inspection shows they should be **PARTIAL**. Fix the table in
`audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT.md` before Phase 7a starts, so the
implementation prompt doesn't skip them as "already done":

### §16 Workflow Engine → PARTIAL, not DONE

`apps/intelligence/workflows.py` (165 lines) imports `from prefect import
flow, task` and `from prefect.task_runners import ConcurrentTaskRunner`,
and defines `@flow`-decorated pipelines (`cv_processing_pipeline`,
`company_enrichment_pipeline`). But:
- `prefect` is **not installed** in the venv (`pip show prefect` →
  "Package(s) not found").
- **No file anywhere in `apps/` imports from `apps.intelligence.workflows`**
  (confirmed via repo-wide grep — zero consumers).

This means the "Prefect" half of your DONE verdict is dead code that
would `ModuleNotFoundError` the instant anything tried to actually call
it. The Rule engine (`apps/core/models.py`'s `Rule` model) and Celery
Beat ARE real and DONE — keep that part of the verdict. But the combined
"Prefect + Rule engine + Celery Beat" DONE verdict overstates the actual
workflow-engine coverage. Reclassify as **PARTIAL**: Rule engine +
Celery Beat = real automation substrate (DONE); the Prefect-based
pipeline layer = dead/unreachable code (MISSING in practice, despite
existing on disk). Decide in Phase 7a whether to (a) actually install
`prefect` and wire these 2 pipelines in, or (b) delete
`workflows.py` as dead code and rely on Celery Beat + Rule engine alone
(recommended — avoids adding a whole new async-orchestration dependency
for 2 unused flows when Celery already does this job platform-wide).

### §20 Security/GDPR → PARTIAL, not DONE

`apps/accounts/models_gdpr.py` (111 lines) defines the
`DataExport`/`AccountDeletion`-style models — the DATA MODEL is real.
But confirmed via grep across `apps/accounts/views.py`,
`apps/accounts/urls.py`, and `apps/accounts/admin.py`: **there is no DRF
view, URL route, or admin action that actually invokes these models.**
A model existing with no endpoint or admin control that uses it is not
"done" by this audit's own stated standard (§24 of the original mandate:
"every control must have a real effect" / "avoid... hard-coded values,
frontend-only controls, fake toggles"). Reclassify as **PARTIAL** and
move the actual admin-usable GDPR export/delete flow into Phase 7c's
scope explicitly (it's currently implied but not named as a Phase 7c
task in your implementation order) — building the DRF view + admin
button + confirmation flow + `ActivityLog` entry for both export and
delete/anonymize.

## Decisions

**1. Packages scope — confirmed: entitlement/feature-flag bundles only,
NO payment/billing.** Build `SubscriptionPlan`/`CompanySubscription` (or
equivalent naming you prefer) as a feature-flag/limit bundle with no
Stripe/payment fields at all. This matches the Phase 2 item 2.22
decision and `COMPETITIVE_ANALYSIS_JOBRIGHT.md`'s reasoning — billing
stays fully out of scope until a separate, explicit decision to
monetize. (Reference: `audit/prompts/PHASE_8_BILLING_PROMPT.md` exists
and is explicitly marked "DO NOT RUN YET" for whenever that separate
decision is made — do not pull anything from it into Phase 7.)

**2. Proceed with Phase 7a implementation now** — apply the 2
corrections above to the audit doc first (5 minutes of edit), then start
Phase 7a per your own stated implementation order (12 tasks: unify auth,
wrap Django template views as DRF, build verification/job inspector,
source operational controls, expand nav to 20 sections, fix AI cost
tracking blind spots). Use `audit/prompts/PHASE_7B_ADMIN_IMPLEMENTATION_PROMPT.md`
as your execution reference for the 7a/7b/7c split and the 9-item
explicit checklist it contains (Scraping Control Center operational
controls, AI-assisted scraping, Talent Quality — already confirmed DONE
so skip, Recommendation Control admin view, per-job inspector, User/
Company lifecycle timelines, Employer/Recruiter admin control, and the
now-corrected GDPR export/delete tooling) — cross-check each against
your own audit's verdicts (most already covered by your table under
different names, e.g. your §12/§13 map to the checklist's per-job
inspector and verification admin items) so nothing is built twice under
two different names.

**3. §24 Admin Search (MISSING → BUILD)** — confirmed as a real gap, not
in the original checklist, good catch. Keep it in Phase 7b as you
scoped it.

## Rules (unchanged from the original Phase 7 prompt)

- Local commits only, do not push — you push via Claude Code in Visual
  Studio yourself.
- Do not weaken `is_discoverable` consent enforcement anywhere in this
  work.
- Do not build payment/billing code in this phase (see Decision 1).
- Real tests for every new endpoint with side effects — the
  quick_apply/insider_connections zero-test gap from Phase 6 must not
  repeat here.
- Run full backend test suite + `tsc --noEmit` + `vite build --mode
  production` before considering any sub-phase (7a/7b/7c) complete.

## When done with Phase 7a

Report back with the same format as before (completion report at
`audit/PHASE_7A_COMPLETION_REPORT.md`) before starting 7b — do not chain
straight through 7a→7b→7c without a checkpoint, same pattern as the
original Phase 0-3 execution.

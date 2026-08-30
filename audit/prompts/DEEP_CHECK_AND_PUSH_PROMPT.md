# PROMPT — E-Career: Final Deep-Check, Test, Commit & Push

You are a senior full-stack engineer + release manager for the E-Career
repo at `M:\job already web for jobs\E-Career` (Django/DRF backend in
`backend/`, React/Vite frontend in `frontend/`). All 4 implementation
phases (Phase 0-3, ~66 items across `MASTER_IMPLEMENTATION_PLAN.md`) have
been executed across ~50 local commits on the `development` branch. Your
job now: verify everything actually works, fix what doesn't, add missing
tests, then push to GitHub.

## Read first

1. `AGENTS.md`
2. `MASTER_IMPLEMENTATION_PLAN.md`
3. `audit/PHASE_0_COMPLETION_REPORT.md`, `PHASE_1_COMPLETION_REPORT.md`,
   `PHASE_2_COMPLETION_REPORT.md`, `PHASE_3_COMPLETION_REPORT.md`,
   `audit/ALL_PHASES_FINAL_STATUS.md` — these claim what was done. **Do
   not trust them at face value** — this repo has a documented history of
   completion claims being inaccurate (e.g. one prior report in this exact
   session claimed item 2.8 "has tests" when it in fact has zero — `python
   manage.py test apps.employers` returns "Found 0 test(s)"). Verify every
   claim against real command output before treating it as true.

## Known specific issue to fix first

**Item 2.8 (multi-seat employer / `EmployerTeamMember`)** was built twice
after being explicitly resolved as "Skip for now" in
`audit/prompts/PHASE_2_PROMPT.md`. On inspection the code itself is
additive and safe (existing single-seat permission checks are preserved,
new team-membership checks are OR'd in, not replacing anything;
`makemigrations --check` shows no drift). **Decision: keep it** — reverting
working, non-breaking code a third time has no value. But:

1. **Write real tests for it** — `backend/apps/employers/tests.py` is
   currently 3 lines (`# Create your tests here.`), completely empty.
   Add proper test coverage for `EmployerTeamMember`: model creation,
   the 5 updated permission classes (`IsEmployer`, `IsVerifiedEmployer`,
   `IsOwnerEmployer`, `CanPostJobs`, `CanViewApplicants`) with team-member
   scenarios AND regular single-seat-owner scenarios (to prove the
   original behavior still works unchanged), and the
   `EmployerTeamViewSet` invite/accept/update-role/deactivate endpoints.
2. Verify no other test file in the repo was broken by the permission
   class changes — run the full test suite (see "Test execution" below)
   and confirm.

## Deep-check scope — verify these specific claims from the source audits

The user's own words, verbatim, on what to re-verify hardest: **"scraper
dead code" (D3), "matching/recommendations معطوبين" (D4), "AI backbone
معطّل" (D6/D7), and "all dead code."** For each:

### Scraper (was: entirely dead code, croniter missing, remote_type crash)
- Confirm `croniter` is actually installed in `backend/venv` (not just
  listed in requirements.txt — `pip show croniter` inside the venv).
- Run the scraper's own test suite:
  `python manage.py test apps.scraper` — must pass, not just "not error."
- Actually invoke `python manage.py run_scrapers --dry-run` (or whatever
  the real management command + safe flag is) and confirm it doesn't
  crash on import or on the first real call.
- Confirm `VerificationEngine.verify_job()` writes `job.status`/
  `job.quality_state` on ALL code paths, not just the main one — re-grep
  every `return` in that method.

### Matching/Recommendations (was: both engines broken, stale fields, dead job_matching.py)
- Run `python manage.py test apps.career apps.search` — confirm the
  recommendation-engine tests (if any exist; if not, note that as a gap)
  actually pass.
- Grep the ENTIRE `backend/apps/` tree one more time for
  `is_active=True` and `remote_type` used against `Job`/`CareerProfile`
  querysets — the bug class recurred 3+ times already across different
  files; do one final exhaustive pass, not a spot check.
- Confirm `apps/intelligence/job_matching.py` was actually deleted (per
  Phase 1 item 1.5) or, if kept, is genuinely wired to a real URL now —
  check `git log` for whether it still exists on disk at all.
- If a local dev server can be started safely (sqlite fallback + LocMemCache
  override for Redis, same pattern used earlier in this session — do NOT
  touch `.env`, override via env vars only), hit
  `/api/v1/career/recommendations/` with a real authenticated request and
  confirm 200, not 500.

### AI backbone (was: Bedrock alias broken, every AI feature silently degraded)
- Confirm the `us.anthropic.*` inference-profile fix in
  `apps/intelligence/bedrock_plugin.py` is syntactically and semantically
  correct — if AWS credentials are available in this environment, make
  one real Bedrock `invoke_model` call through the app's own service
  layer and confirm it returns a genuine model response, not a fallback
  string. If credentials aren't available, say so explicitly rather than
  assuming the fix works.
- Re-check whether any OTHER file in `apps/intelligence/`,
  `apps/rashid/`, `apps/career/`, `apps/interviews/` still hardcodes a raw
  (non-cross-region) Bedrock model ID bypassing the router — grep for
  `anthropic.claude` patterns NOT prefixed with `us.`/`eu.`/`apac.`.

### Dead code (general)
- Grep for every module/function/class flagged as "dead" or "zero callers"
  across all 10 `audit/D*.md` reports and all 4 `PHASE_*_COMPLETION_REPORT.md`
  files. For each: confirm it was actually deleted, OR wired in, OR is a
  deliberate exception with a documented reason. Do not accept "should be
  handled" from a prior report without checking the current file exists/
  doesn't exist.

## Test execution (must actually run, not just claimed)

From `backend/`, with the venv activated:
```
export DJANGO_SETTINGS_MODULE=config.settings.test
python manage.py test apps
```
If Redis/Celery connection errors block this (a known local-environment
issue, not a code bug), that's fine to note as an environment limitation —
but run whatever subset of the suite CAN run cleanly and report the exact
pass/fail counts, not a vague "tests pass" claim. If you fix the
Redis-dependency-in-tests issue itself (e.g. proper mocking/settings
override), that's a welcome bonus but not required.

From `frontend/`:
```
npx tsc --noEmit
npx vite build --mode production
```
Both must exit 0. If they don't, fix what's broken before proceeding to
commit/push — do not push a build that doesn't compile.

## Commit discipline

- Commit any new fixes/tests you make in this pass with clear, scoped
  messages (same discipline as the 4 phases — don't squash unrelated
  changes together).
- Do NOT rewrite or squash the existing ~50 commits from Phase 0-3 — they
  are a legitimate history, leave them as-is.

## Push to GitHub

Once the deep-check above is complete and either (a) everything passes, or
(b) you've fixed what you found broken and re-verified:

```
git -C "M:\job already web for jobs\E-Career" status --short
git -C "M:\job already web for jobs\E-Career" log --oneline origin/development..HEAD | wc -l
git -C "M:\job already web for jobs\E-Career" push origin development
```

Before pushing, print the full list of commits about to be pushed
(`git log --oneline origin/development..HEAD`) so there's a clear record
of exactly what's going up. After pushing, confirm success by running
`git -C "M:\job already web for jobs\E-Career" log origin/development -1`
and checking it matches your local HEAD.

## Final deliverable

Write `M:\job already web for jobs\E-Career\audit\DEEP_CHECK_AND_PUSH_REPORT.md`
covering: what you re-verified and how (exact commands + output, not
prose claims), what you found wrong and fixed, the final test pass/fail
counts, the frontend build status, and confirmation of the push (commit
count pushed + final remote HEAD SHA).

## Hard rules (same as before)

- Never read, print, log, or commit `backend/.env` or any secret.
- Do not build the billing/subscription engine (item 2.22) — still
  explicitly out of scope.
- If you disagree with a past decision (like keeping 2.8), you may fix
  code quality issues (like adding the missing tests) but do not silently
  re-revert or re-build previously-resolved product decisions without
  saying so explicitly in your final report.

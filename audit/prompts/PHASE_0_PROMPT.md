# PROMPT — E-Career Phase 0: Critical Bugs, Security, Compliance

You are a senior backend/full-stack engineer working in the E-Career repo at
`M:\job already web for jobs\E-Career` (Django/DRF backend in `backend/`,
React/Vite frontend in `frontend/`). This project's production domain is
jobs.usamif.com.

## Before touching anything

1. Read `M:\job already web for jobs\E-Career\AGENTS.md` in full — it has
   mandatory project conventions and known pitfalls.
2. Read `M:\job already web for jobs\E-Career\MASTER_IMPLEMENTATION_PLAN.md`
   in full — it is the authoritative synthesis of 10 independent domain
   audits performed 2026-08-29. Every task below is item 0.1–0.17 from its
   "Phase 0" table.
3. **Do not trust any status doc at face value, including this one.** The
   repo has a documented history of status docs drifting from code within
   days. Before fixing each item, re-verify the claim against the CURRENT
   code (`grep`/read the exact file:line cited) — if it's already fixed or
   the code has moved, say so and skip it, don't re-break working code.
4. Never read, print, or commit `backend/.env` or any secret. It's
   access-blocked by design in some tools — respect that; don't try to
   bypass it.
5. Run the relevant tests/build after each fix. Commit each logical group
   separately with a clear message (don't squash all 17 into one commit).

## Scope: these 17 items only (do not expand scope — Phase 1/2/3 are separate)

**0.1** — Add `croniter` to `backend/requirements.txt` (or the correct
requirements file — check `requirements/base.txt` vs `requirements.txt`) and
install it. Then fix `apps/scraper/management/commands/run_scrapers.py:87`,
which calls `orchestrator.scrape_all_sources()` — a method that doesn't
exist on the class; find the correct method name or add it.
Evidence: `scraper/orchestrator.py:14` (`ModuleNotFoundError: No module
named 'croniter'` reproduced live by the audit).

**0.2** — Fix `Job.objects.create(remote_type=...)` at BOTH ingestion call
sites — `remote_type` was removed by a migration months ago (replaced by
`work_arrangement`). Change to the correct field.
Evidence: `scraper/tasks.py:224`, `scraper/orchestrator.py:323`.

**0.3** — Make `VerificationEngine.verify_job()` actually persist its
rejection decision — currently it computes a verdict but never writes
`Job.status` (or whichever field the public job list actually filters on),
so rejected/aggregator-sourced jobs stay publicly visible. Fix it to write
the field the public list query (`jobs/views.py:289-295`) actually checks.
Evidence: `verification/engine.py:156-170` vs `jobs/views.py:289-295`.

**0.4** — Add an end-to-end scraper integration test: a fixture ATS
response → goes through the pipeline → produces a real `Job` DB row → has a
real `VerificationResult`. This is a regression guard so items 0.1-0.3
can't silently break again. Put it wherever the repo's existing scraper
tests live (check `apps/scraper/tests/` first).

**0.5** — Fix `EmployerProfileViewSet.stats()` — it filters on
`job__employer=employer`, but `Job` has no `employer` field (the real
relation is through `employer_posting`, per audit note — verify the exact
correct path against the current `Job` and `EmployerJobPosting`-equivalent
model before writing the fix). This 500s on every real call.
Evidence: `employers/views.py:176-178` (live `FieldError` reproduced).

**0.6** — Add the missing `from django.db import models` import in
`apps/interviews/views.py` — its absence causes `GET /api/v1/interviews/stats/`
to 500 with a `NameError` on every call.
Evidence: `interviews/views.py:404-433`, specifically around line 417.

**0.7** — Fix `HybridSearchView` (`apps/vectors/views.py:266-271`) — it
calls `search_service.search()`, but `SearchService` only has
`search_jobs()`. Either call the correct method with correctly-shaped
arguments, or add a thin `.search()` compatibility method on `SearchService`
that delegates to `search_jobs()`. Verify with a live request after the fix
(200, not 500).

**0.8** — Fix stale field references in `apps/profiles/services.py` at
lines 85, 115, 136, 152 — `Q(is_active=True)` (should be `status='active'`,
per the same field that was already fixed elsewhere in commit `3a92ce0` on
2026-08-29 — this file was missed by that commit) and
`.order_by('-posted_date')` (verify the real field name on `Job`, likely
`posted_at` or `created_at` — check `apps/jobs/models.py`). Grep the WHOLE
`apps/profiles/` directory for any other `is_active`/`posted_date` on `Job`
you find while you're in there — the pattern has already recurred twice.

**0.9** — Fix stale field references across the job-matching/recommendation
code: `job.remote_type`, `job.experience_required`, `profile.saved_jobs`,
`job.job_type`, `job.is_remote` — none of these exist on the current models.
Locations: `apps/search/recommendation_engine.py` (5 sites — grep for all of
them), `apps/career/recommendation_engine.py:252-255`,
`apps/vectors/management/commands/index_jobs.py:93,97`. For each, find the
actual correct field name on the current `Job`/`CareerProfile` model and fix
it. Also fix `apps/intelligence/job_matching.py:10` — it imports
`from apps.vectors.services import vector_service`, a wrong module/symbol —
find the real import path, and fix the 2 more stale-field bugs in the same
file at lines 113, 148-149, 184, 346 (verify each against current models).

**0.10** — **Highest-leverage single fix in the whole platform.** The AWS
Bedrock model alias used for `sonnet` is a raw model ID that actually needs
an inference-profile ARN (Bedrock cross-region inference requirement).
Location: `apps/intelligence/bedrock_plugin.py:31`. Every AI-powered feature
across Assessment, Interviews, CV parsing, CareerBrain, and all 5 Rashid
tools currently silently degrades to generic fallback content because of
this. Get the correct inference-profile ARN for the account's Bedrock
Claude Sonnet access (check AWS Bedrock console → model access → inference
profiles, or `aws bedrock list-inference-profiles`) and fix the alias/config
so real model calls succeed. Verify live: make one real AI call end-to-end
(e.g. hit an endpoint that calls `bedrock_plugin`) and confirm it returns a
real (not fallback) response.

**0.11** — Voice interviews are non-functional because the AWS IAM user
configured for this app has zero Polly/Transcribe/S3 permissions, and
`AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` aren't set. This requires: (a) IAM
console changes granting `polly:SynthesizeSpeech`, `transcribe:StartTranscriptionJob`
+ related Transcribe actions, and S3 read/write on the relevant bucket to
whichever IAM user/role the app assumes; (b) setting `AWS_REGION` and
`AWS_STORAGE_BUCKET_NAME` env vars (in `.env`, not `.env.example` — do not
read/print `.env`, just note in your final report that these need setting
and let the human do it if you can't safely edit `.env` yourself). Verify
by reproducing the `AccessDeniedException` before your fix and confirming
it's resolved after (if you have AWS credentials available in this
environment; otherwise document exactly what's needed and mark it human
action item).
Evidence: `apps/interviews/voice_service.py`.

**0.12** — Set a valid `JUDGE0_API_KEY` (coding-assessment grading is
currently non-functional, live-reproduced HTTP 401). This is likely a
`.env` value — do not read/print `.env`; if you have access to the correct
key, set it; otherwise document as human action item.
Evidence: `apps/core/code_execution.py:19`.

**0.13** — Fix employer self-registration: `EmployerRegistrationView` /
whatever view handles employer signup never sets `User.role = "employer"`,
so newly-registered employers are immediately locked out of every
employer-gated endpoint. Find the exact registration view/serializer and
add the role assignment.
Evidence: `apps/employers/views.py:53-94`; permission check at
`apps/employers/permissions.py:15-20`.

**0.14** — Close a real privacy gap: `TalentDiscoveryViewSet` (whatever its
exact class/view is — grep for it in `apps/employers/`) leaks a candidate's
name/email without honoring the `is_discoverable` consent flag, unlike its
sibling `TalentPoolViewSet.add_candidate` and `CandidateRankingViewSet.rank()`
which correctly check it. Add the same `is_discoverable` check.
Evidence: `apps/employers/views.py:666-686`.

**0.15** — Human action item, not code: confirm whether the previously
leaked AWS access key (format `AKIAYK...TGPY`) has been rotated in the AWS
IAM console. You cannot read `.env` to check this — just note in your final
report that this must be confirmed by a human with AWS console access if
not already done, and do not attempt to read/rotate credentials yourself.

**0.16** — Fix `apps/monitoring/views_ai_costs.py` — the only admin AI-cost
dashboard throws `AttributeError` on load because it references
`event.metadata` (real field is `.data`) and wrong `RashidUsage` field names
for tokens/timestamp. Fix at lines 33, 40-41, 64-75 — find the actual
correct field names on the relevant models first.

**0.17** — Fix `JobPostingViewSet.perform_update`'s draft/rejected-only
edit-lock — it currently returns a `Response` object from a DRF hook that
silently discards it, so the lock is a no-op and published jobs remain
editable when they shouldn't be. Change it to raise `rest_framework.exceptions.ValidationError`
(or equivalent) instead of returning a `Response`.
Evidence: `apps/employers/views.py:263-271`.

## When done

Write a completion report to
`M:\job already web for jobs\E-Career\audit\PHASE_0_COMPLETION_REPORT.md`
listing, for each of the 17 items: what you found (still broken as
described / already fixed / different than described), what you changed
(file:line), and how you verified it (test run, live request, etc.). Flag
anything you could not fix (missing credentials, needs human AWS console
access, etc.) explicitly rather than silently skipping it.

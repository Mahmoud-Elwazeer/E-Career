# PROMPT — E-Career: Final Deep Audit, GitHub-vs-Local Reconciliation, Remaining Work

You are a senior full-stack engineer + release auditor working on E-Career
at `M:\job already web for jobs\E-Career` (Django/DRF backend in
`backend/`, React/Vite frontend in `frontend/`, a Chrome extension POC in
`browser-extension/`). Read `AGENTS.md` and `CLAUDE.md` first.

## Context — how this repo got here

Phases 0-3 (66 items: critical fixes, architecture consolidation, feature
completion, polish) were executed and committed. A deep-check pass fixed
critical import bugs and pushed 62 commits to `origin/development`. A
live end-to-end verification pass (real HTTP requests against a local
dev server) found and fixed 5 more bugs. A competitive analysis of
Jobright.ai produced `audit/COMPETITIVE_ANALYSIS_JOBRIGHT.md`, and Phase 5
(6 items: match score breakdown, resume tailoring, quick-apply, browser
extension autofill, insider connections, 3 new Rashid AI tools) was then
implemented on top. **As of the last commit, this work exists ONLY in
local git history — it has NOT been pushed to GitHub yet.** Read every
completion report in `audit/` (`PHASE_0_COMPLETION_REPORT.md` through
`PHASE_5_COMPLETION_REPORT.md`, `DEEP_CHECK_AND_PUSH_REPORT.md`,
`LIVE_VERIFICATION_REPORT.md`) and `MASTER_IMPLEMENTATION_PLAN.md` before
touching anything — do not repeat work already done, and do not trust any
of these reports at face value without spot-checking 2-3 claims per
report against the actual current code first (this repo has a documented
history of status docs being wrong).

## Part A — GitHub vs local reconciliation (do this FIRST)

1. Run `git status`, `git log --oneline -20`, and `git fetch origin &&
   git log --oneline origin/development..HEAD` and `git log --oneline
   HEAD..origin/development`. Report exactly what's local-only,
   remote-only, and confirm there's no divergence/conflict.
2. If local is ahead of remote (expected state per this prompt's
   context), do NOT push yet — first complete Part B below, then push
   everything together at the end with the user's explicit go-ahead
   (they said they will commit/push themselves via Claude Code in Visual
   Studio — respect that; finish the work and leave it committed locally,
   report the exact commit range that needs pushing, but let the human
   do the actual `git push`).
3. Confirm the working tree is clean of scratch files (`audit/*.json`
   temp outputs, `db.sqlite3`, any `qa_local_verify.py` settings file) —
   delete any that exist and are not meant to be tracked.

## Part B — Real bugs already found in this session, confirm and fix

These were found via live testing/direct inspection just before this
prompt was written — verify each still reproduces, then fix:

**B1. UUID/int URL converter mismatch (confirmed via `django.urls.reverse`
test — this is a real, reproduced bug, not a hypothesis):**
`Job` extends `UUIDModel` (see `apps/jobs/models.py:194`,
`class Job(UUIDModel)`), so `job.id` is a UUID. But
`apps/career/urls.py` registers:
```python
path('jobs/<int:job_id>/match-breakdown/', match_breakdown, name='match-breakdown'),
path('jobs/<int:job_id>/tailor/', job_tailor, name='job-tailor'),
```
using the `int` converter. Any real job UUID will 404 on both endpoints
in production. Fix: change both to `<uuid:job_id>`. **Then check why the
existing tests in `apps/career/tests/test_phase5_endpoints.py` didn't
catch this** — they call `reverse("career:match-breakdown", kwargs={"job_id": job.id})`
which will fail to reverse against a UUID with the `int` converter
(reproduce this yourself first: `python manage.py shell` and try
`reverse('career:match-breakdown', kwargs={'job_id': uuid.uuid4()})` —
it will raise `NoReverseMatch`). Figure out how the existing tests were
passing (likely a stale cached URL config, or the test job fixture had
an integer PK from a different model, or `--reuse-db` served a stale
schema) and fix the root cause, not just the symptom — after fixing the
url pattern, re-run `apps/career/tests/test_phase5_endpoints.py` and
confirm it still passes with the corrected converter.

**B2. Missing Chrome extension icon files:**
`browser-extension/manifest.json` references
`icons/icon16.png`, `icons/icon48.png`, `icons/icon128.png` in both the
top-level `icons` key and `action.default_icon`, but
`browser-extension/icons/` is an empty directory. The extension will fail
to load in Chrome (`chrome://extensions` will show a manifest error).
Generate 3 simple placeholder PNG icons (16x16, 48x48, 128x128 — a plain
E-Career logo/monogram is fine, doesn't need to be polished, but must be
valid PNGs at the referenced paths) so the extension actually loads for
testing. Flag if real branded icons should replace these later.

**B3. Zero test coverage on 2 new Phase 5 endpoints with real side
effects:**
`apps/employers/quick_apply_service.py` (creates `JobApplication` rows via
`record_application`) and `apps/employers/connections_service.py` (queries
across users, makes an external GitHub API call) have **no test file** —
confirmed via `find . -iname "*test*quick_apply*" -o -iname
"*test*connections*"` returning nothing. Write real tests:
- `quick_apply_prepare` returns mapped fields correctly from a real
  `CareerProfile`; `quick_apply_record` creates exactly one
  `JobApplication` (not a duplicate on repeat calls — verify the
  `get_or_create` semantics actually hold under a second call).
- `insider_connections`: (a) a consenting user (`is_discoverable=True`)
  with a matching `current_company` IS returned; (b) a non-consenting
  user (`is_discoverable=False`) is NOT returned even with a matching
  company — this is the privacy-critical case, test it explicitly; (c)
  the GitHub API call path (mock `urllib.request.urlopen` — do not make
  a real network call in tests) returns contributors when `github_org` is
  set and an empty list when it's blank or the request fails.

**B4. Missing optional Python dependencies (Phase 2 item 2.10 claimed
"done" but the deps were never actually installed):**
`requirements.txt` lists `easyocr==1.7.2`, `pdf2image==1.17.0`,
`xhtml2pdf==0.2.16` (confirmed present in the file), but `pip show
easyocr pdf2image xhtml2pdf` in the actual venv returns "Package(s) not
found" for all three. Run `pip install -r requirements.txt` in the venv
and confirm all three actually install (check for native-dependency
issues — `easyocr` needs a working PyTorch install, `pdf2image` needs
poppler on the system PATH, `xhtml2pdf` is pure-Python). If any fails to
install cleanly on this Windows dev machine, document the exact error and
the platform-specific fix (e.g. poppler install instructions for
Windows) rather than silently leaving it broken.

**B5. GitHub API rate limiting (flagged as a known gap in
`PHASE_5_COMPLETION_REPORT.md` item 3, but not yet actioned):**
`apps/employers/connections_service.py`'s `_find_github_contributors`
makes unauthenticated GitHub API calls (60 req/hour limit). Add support
for an optional `GITHUB_TOKEN` setting (via `django-environ`/`decouple`
config pattern already used elsewhere in `config/settings/base.py`) that,
if set, is sent as an `Authorization: Bearer <token>` header to raise the
rate limit to 5000 req/hour. Must work with the token unset (current
behavior preserved) — this is additive, not required.

## Part C — Full repo grep for remaining TODOs/FIXMEs (do NOT assume Part B is the complete list)

1. Run `grep -rn "TODO\|FIXME\|XXX\|HACK" --include="*.py" backend/apps/`
   (excluding migrations and test files) and evaluate each hit — some are
   None found. Two are already confirmed and require this Phase 6.7 to
   handle. Confirmed so far, evaluate whether still relevant:
   - `apps/core/views.py:221` — `# TODO: Implement GitHub OAuth flow`
   - `apps/core/views.py:269` — `# TODO: Implement portfolio analysis`
   - `apps/employers/views.py:303` — `# TODO: Send notification to admin`
   - `apps/jobs/models.py:339` — `# TODO: Remove these after migration is
     complete` (on `salary_min_new`/`salary_max_new`/`salary_currency_new`
     — check if the migration IS actually complete now; if the old
     `salary_min`/`salary_max` fields are no longer read anywhere, this
     migration cleanup is safe to finish: drop the old fields via a new
     migration, rename `_new` fields to the canonical names, update all
     call sites).
   For each: either fix it now (if small/self-contained) or add it as an
   explicit item to your final report with a reason it's deferred (e.g.
   "requires product decision" or "requires external OAuth app
   registration you don't have credentials for").
2. Run the same grep across `frontend/src/` for `TODO`/`FIXME` and
   `// Coming soon` placeholder text — `MASTER_IMPLEMENTATION_PLAN.md`
   Phase 3 item 3.4 already flagged "Coming soon" stubs in
   `EmployerDashboard.tsx`; confirm whether that was actually fixed (Phase
   3 report claims yes) — spot check it live in the running dev server,
   don't just trust the report.

## Part D — Re-run full verification (do not trust old numbers, they're now stale by 5 commits)

1. Backend: `cd backend && source venv/Scripts/activate && export
   DJANGO_SETTINGS_MODULE=config.settings.test && python -m pytest -q`
   — record the exact pass/fail/skip count. The last known-good number
   was 418 passed, 0 failed, 2 skipped — if this run shows fewer passing
   or any new failures, that's a regression from Part B's fixes; find and
   fix it before proceeding.
2. Frontend: `cd frontend && npx tsc --noEmit && npx vite build --mode
   production` — both must be clean.
3. Live E2E spot-check (not the full 11-engine sweep again — just the 2
   corrected endpoints from B1): stand up the local dev server the same
   way prior sessions did (`config/settings/qa_local_verify.py` scratch
   override for LocMemCache, sqlite, real JWT login), hit
   `/api/v1/career/jobs/{real-uuid}/match-breakdown/` and
   `/api/v1/career/jobs/{real-uuid}/tailor/` with an actual job UUID (not
   an int) and confirm 200, not 404. Clean up the scratch settings file
   and sqlite db afterward, same as every prior pass.

## Part E — Production readiness checklist (report status, most of these are human/infra action items you cannot complete yourself)

For each, either confirm truly done, or write the exact remaining action
needed (do not mark anything "done" without having just verified it in
Part B-D above):

1. AWS Bedrock: model ID fixed to `claude-sonnet-4-5-20250929-v1:0` in
   code — but confirm the actual AWS Bedrock model access has been
   requested/granted for this specific model ID in the target AWS
   account (this needs the human to check the AWS Bedrock console model
   access page — you cannot grant it yourself). Note the exact console
   navigation path in your report.
2. AWS IAM permissions for Polly/Transcribe/S3 (voice interview feature,
   items 0.11) — still pending per every prior report; re-confirm.
3. `JUDGE0_API_KEY` (code execution grading, item 0.12) — still pending;
   re-confirm.
4. AWS key rotation (the originally-flagged `AKIAYK...TGPY` key) — ask
   explicitly in your final report whether the human has done this; do
   not assume yes or no.
5. Redis + ClamAV — must be provisioned in the actual deployment target
   (not just noted as "unavailable in QA, tests worked around it"). List
   exactly what Redis is used for (Celery broker, DRF throttle cache,
   django-redis cache backend) and what ClamAV is used for (CV upload
   malware scan, fail-closed by design) so deployment ops has a clear
   checklist.
6. Chrome extension: after B2's icon fix, is it loadable in
   `chrome://extensions` (developer mode, "Load unpacked")? Actually load
   it if you have a way to verify (or clearly state you could not verify
   this in a headless environment and it needs human verification).

## When done

Write `audit/PHASE_6_FINAL_AUDIT_REPORT.md` covering every part above:
what was found, what was fixed (with commit SHAs), what's still a human
action item (with the EXACT thing the human needs to do, not a vague
restatement), and the final test/build numbers. Do NOT push — the user
will review and push via Claude Code in Visual Studio themselves. Commit
your fixes locally in logical groups as usual.

At the very end of your report, answer this directly: **"Is E-Career
now feature-complete and production-ready, or does gap X/Y/Z remain?"**
— give a real yes/no-with-exceptions answer, not a hedge.

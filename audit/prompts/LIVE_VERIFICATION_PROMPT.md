# PROMPT — E-Career: Full-Platform Live End-to-End Verification & Completion

You are a senior full-stack engineer + QA lead doing the FINAL completion
pass on E-Career at `M:\job already web for jobs\E-Career` (Django/DRF
backend in `backend/`, React/Vite frontend in `frontend/`). Read
`AGENTS.md` and `CLAUDE.md` first.

## Context — what's already done

`MASTER_IMPLEMENTATION_PLAN.md` (10-domain audit synthesis) + 4 phase
completion reports + `audit/DEEP_CHECK_AND_PUSH_REPORT.md` document ~66
items fixed across Phase 0-3, all pushed to `origin/development` at
commit `e0cbb27` (or later, if Phase 4's test-fix prompt already ran —
check `git log` for `PHASE_4_TEST_SUITE_FIX_REPORT.md`/commits first and
treat that as done too if present).

**Everything up to now has been fixed by reading and patching code.**
This pass is different: **you must actually RUN the platform and exercise
every engine with real requests**, not just confirm the code looks
correct. Static correctness ≠ working software — this repo's own history
(`AGENTS.md`) documents multiple cases where code that "looked right" 500'd
the moment someone actually hit it. Do not repeat that pattern here.

## Setup: get a local dev environment running

```
cd backend
source venv/Scripts/activate
export DJANGO_SETTINGS_MODULE=config.settings.development
export DATABASE_URL=""   # forces sqlite fallback per config/settings/development.py
```

Redis is likely unavailable locally — DRF throttling middleware needs a
working cache. Create a temporary settings override (do NOT edit
`.env` or committed settings):
```
# backend/config/settings/qa_local_verify.py (create if it doesn't exist,
# delete it again before you finish — it's a scratch file, never commit it)
from config.settings.development import *
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
```
Then `export DJANGO_SETTINGS_MODULE=config.settings.qa_local_verify` and
run migrations + start the server:
```
python manage.py migrate --no-input
python manage.py runserver 127.0.0.1:8123 --noreload
```
(Run the server as a background process so you can keep issuing curl
requests against it in the same session.)

Create one real test user via `python manage.py shell` (see prior
session pattern: `User.objects.get_or_create(email=..., ...)`,
`set_password(...)`), then get a JWT via
`POST /api/v1/auth/login/`.

**Delete `qa_local_verify.py`, drop `db.sqlite3`, and kill the server
before you finish this task** — none of this is meant to survive as
repo state.

## What to actually exercise, per engine (live requests, not code reads)

For EACH of the following, make a REAL authenticated HTTP request (via
`curl` against the local server above) and report the exact status code
+ a snippet of the response body. If something 500s, read the traceback
from the server's stdout, fix the root cause in code, restart the server,
and re-test until it's a genuine 200 (or an expected 4xx like 401/403 for
an intentionally-gated case — not an accidental 500 disguised as
progress).

1. **Auth**: register a new user, register a new employer (confirm
   `role="employer"` actually gets set — this was Phase 0 item 0.13),
   login, refresh token, logout.
2. **Career/Profile**: `GET/PATCH` on the profile endpoint, CV upload
   (use a real small PDF/text fixture — construct one if none exists in
   `backend/apps/*/tests/fixtures/`), confirm parsed skills come back.
3. **Jobs**: list jobs, get job detail, job search (`apps/search` —
   keyword), hybrid search (`apps/vectors` — the one that was 500ing
   before Phase 0's fix).
4. **Recommendations**: `GET /api/v1/career/recommendations/` — this
   specific endpoint was the original 500 that started this whole audit
   chain (nonexistent `is_active` field). Confirm 200 with a real,
   sensible response shape (even if `count: 0` on an empty dev DB, that's
   fine — the shape and status code are what matter).
5. **Employer**: `EmployerProfileViewSet.stats()` (previously 500'd via
   `job__employer` FieldError), job posting create/edit (confirm the
   `perform_update` edit-lock from item 0.17 actually blocks editing a
   published job with a 4xx, not silently allowing it), employer team
   member invite (item 2.8's new endpoints).
6. **Talent Pool**: `TalentDiscoveryViewSet` — confirm the `is_discoverable`
   consent filter from item 0.14 actually excludes a non-consenting
   user's data from the response (set up two test users, one with
   `is_discoverable=False`, confirm they don't appear).
7. **Assessment/Interviews**: start an interview session, submit an
   answer, `GET /api/v1/interviews/stats/` (previously 500'd via missing
   import — item 0.6).
8. **Rashid AI**: send a chat message through the real chat endpoint —
   if AWS Bedrock credentials ARE available in this environment, confirm
   you get a real model response (not a generic fallback string — check
   for signs of a canned/fallback response vs genuine model output). If
   credentials are NOT available, say so explicitly and note this item
   is UNVERIFIABLE in this environment, do not guess.
9. **Notifications**: trigger an action that should create a notification
   (e.g. submit a job application), then `GET` the in-app notifications
   list and confirm the notification you just triggered actually appears
   (this closes the loop on Phase 1 item 1.12 — frontend reading the
   model that real events actually write to).
10. **Admin/Monitoring**: `GET /health/`, `GET /health/detailed/`, the
    AI-cost admin dashboard endpoint (previously 500'd via wrong field
    names — item 0.16).
11. **Scraper** (if safely runnable without hitting real external sites —
    check for a `--dry-run`/test-fixture mode; do NOT scrape real
    LinkedIn/Indeed/company sites from this environment): confirm the
    management command at least imports and starts cleanly, per the
    fixes in items 0.1/0.2. If a full live scrape isn't safely
    testable here, say so and rely on the existing integration test
    (`apps/scraper/tests/test_scraper_integration.py`) instead — but
    actually run that test and report its result, don't assume.

## Frontend verification

Start the frontend dev server (`npm run dev` from `frontend/`, or serve
the production build) pointed at your local backend
(`VITE_API_URL=http://127.0.0.1:8123` or whatever env var the frontend
actually uses — check `frontend/.env.example`). You don't have a browser
in this environment, so instead:
- Run `npx tsc --noEmit` and `npx vite build --mode production` — both
  must be clean (should already be, per the last report, but re-confirm).
- For each of the 10 pages/routes the original D10 audit flagged as
  "spot-checked" (`Employer Dashboard`, `Company Profile`, `Settings`,
  `Saved Jobs`, `Alerts`, plus any others you can identify from
  `App.tsx`'s route list), grep the component's actual API call sites and
  cross-reference against the backend endpoint you just live-tested above
  — confirm the frontend is calling the URL that actually exists and
  returns the shape the component expects (TypeScript types should make
  mismatches obvious — check the interface definitions in
  `frontend/src/services/*.ts` against what the live backend response
  actually contained in your curl tests above).

## Fix-as-you-go

Any REAL bug you find during this live-verification pass (not
speculative, actually reproduced via a live request) — fix it
immediately, verify the fix with another live request, commit it with a
clear message referencing what you found. This is expected: static
analysis catches a lot but not everything; live exercising typically
surfaces a few more genuine issues (the previous 4 phases already found
several this way — e.g. the `JobSave`/`JobSearch` import bug was only
caught by actually running tests, not by reading code).

## Explicitly out of scope (still)

- Do NOT build the billing/subscription engine (item 2.22).
- Do NOT touch `.env`, rotate credentials, or attempt AWS IAM changes —
  those remain human action items (0.11, 0.12, 0.15).
- Do NOT do a live scrape against real external job sites/ATSs.

## When done

1. Kill the local dev server, delete `backend/config/settings/qa_local_verify.py`
   and `backend/db.sqlite3` if created — leave no scratch state.
2. Commit any real fixes found during this pass (local commits, do not
   push yet).
3. Write `audit/LIVE_VERIFICATION_REPORT.md`: for every one of the 11
   engine checks above, the exact command/curl issued, the exact status
   code + response snippet received, and PASS/FAIL/UNVERIFIABLE (with
   reason) for each. Include the frontend build confirmation and the
   list of any new bugs found+fixed with file:line + commit SHA.
4. End the report with a single-paragraph honest verdict: is the
   platform's core loop (user registers → builds profile → searches/gets
   recommended jobs → applies; employer registers → posts a job →
   discovers candidates → hires) now genuinely functional end-to-end on a
   local dev environment, or does something in that chain still break?
   Do not round up — if one link in the chain is still broken, say
   exactly which one.

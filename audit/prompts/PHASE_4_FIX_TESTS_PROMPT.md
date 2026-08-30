# PROMPT — E-Career: Fix All 67 Pre-Existing Test Failures (Response Envelope Standardization)

You are a senior Django/DRF backend engineer working on E-Career at
`M:\job already web for jobs\E-Career` (backend in `backend/`, venv at
`backend/venv/`). Read `AGENTS.md` and `CLAUDE.md` first.

## Context

The last deep-check pass (`audit/DEEP_CHECK_AND_PUSH_REPORT.md`, already
pushed to `origin/development` at commit `e0cbb27`) ran the full backend
test suite and found:

```
67 failed, 212 passed, 2 skipped
```

All 67 are **pre-existing** (not caused by Phase 0-3 work) and share one
root cause: **response envelope inconsistency**. Some views return the
project's standard `{"success": bool, "data": ..., "message": ..., "errors": ...}`
envelope (used by `apps/accounts/views.py` and others — this is the
correct, canonical pattern per `AGENTS.md`), while others return raw DRF
`Response(serializer.data)` with no envelope. The 67 failing tests assert
the envelope shape and correctly fail against views that don't produce it.

Failure breakdown from the last report:
| File | Failures | 
|------|----------|
| `career/tests/test_api.py` | 23 |
| `rashid/tests/test_api.py` | 15 |
| `jobs/tests/test_api.py` | 12 |
| `tests/test_integration.py` | 9 |
| `accounts/tests/test_auth.py` | 8 |

## Your task

For EACH of the 5 files above:

1. Run the specific failing tests first to see the exact assertion
   failures:
   ```
   cd backend && source venv/Scripts/activate
   export DJANGO_SETTINGS_MODULE=config.settings.test
   python manage.py test apps.career.tests.test_api -v 2
   python manage.py test apps.rashid.tests.test_api -v 2
   python manage.py test apps.jobs.tests.test_api -v 2
   python manage.py test apps.tests.test_integration -v 2
   python manage.py test apps.accounts.tests.test_auth -v 2
   ```
2. For each failure, determine the correct fix direction:
   - **If the VIEW is wrong** (returns raw DRF response when the rest of
     the app's convention is the `{"success","data",...}` envelope):
     wrap it correctly. Look at `apps/accounts/views.py` for the
     canonical pattern (or wherever the project's actual envelope
     helper/mixin lives — check for a shared `api_response()` helper or
     similar before hand-rolling one per view).
   - **If the TEST is wrong** (asserts an envelope that was never the
     real intended contract for that specific endpoint — some endpoints
     may legitimately be envelope-free, e.g. if they're consumed by a
     third party or match a different established convention): fix the
     test assertion instead, but only if you can justify why that
     endpoint should NOT be enveloped (e.g. it's a public API consumed
     externally, or matches a REST convention the rest of the codebase
     already uses elsewhere for the same resource type).
   - **Do not fix by weakening the assertion generically** (e.g. don't
     change `assertEqual` to a vague truthy check just to make it pass).
3. Fix each file's failures as a batch (all `career` failures together,
   then `rashid`, etc.) with one commit per file/app, clear message.
4. After each app's fixes, re-run that app's tests and confirm 0 failures
   before moving to the next.
5. At the end, run the FULL suite again:
   ```
   python manage.py test apps
   ```
   and confirm the failure count dropped from 67 to 0 (or document
   precisely why any remaining failures are genuinely out of scope —
   e.g. require external services unavailable in this environment, not
   an envelope issue).

## Rules

- Local commits only, do NOT push (the human pushes after review).
- Never touch `.env`.
- Do not change response envelopes for endpoints outside the 5 failing
  test files without checking their own tests still pass after — a
  shared envelope helper change can ripple; re-run the FULL suite, not
  just the 5 files, after any shared-code change.
- If fixing a view's envelope requires a matching frontend change
  (unlikely for a pure format fix, but check), note it in your report —
  do not silently break a frontend call site. Grep
  `frontend/src/services/` for the affected endpoint paths before
  changing a view's response shape, to confirm the frontend already
  expects (or doesn't care about) the enveloped format.

## When done

Write `audit/PHASE_4_TEST_SUITE_FIX_REPORT.md`: which files needed view
fixes vs test fixes and why, final full-suite pass/fail count, and
confirmation the frontend build (`npx tsc --noEmit && npx vite build
--mode production` from `frontend/`) still passes after any envelope
changes.

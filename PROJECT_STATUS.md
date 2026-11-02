# E-Career (USAM Jobs) — Project Status

**Last updated:** 2026-09-21 (end of session)
**Last verified commit:** `6a7347f` on branch `development` (pushed, matches `origin/development`)
**Author of this document:** AI coding agent (Kiro), summarizing a multi-session hardening pass on the Legal/Privacy/Payments/Consent subsystem.

> **How to use this file:** This is the authoritative entry point for
> resuming work. It is written to be read on its own, without the chat
> history that produced it. Where a claim is backed by a specific test run
> or file, that evidence is cited. Where something is unverified, it is
> labeled `UNVERIFIED` rather than assumed. Per `AGENTS.md` (read that file
> next — it is the project's standing operating guide and takes precedence
> over any older planning doc), **do not trust any other root-level
> `*_SUMMARY.md`/`*_REPORT.md`/`*_PLAN.md` file at face value** — this repo
> has ~100 such files that have historically contradicted each other and
> the real code. This file and `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md`
> are the two documents this session treated as ground truth, and both are
> code/test-verified as of the dates stated in them.

---

## 1. Project overview

E-Career (production domain: `jobs.usamif.com`) is a career + hiring
platform, not just a job board. Stack:

- **Backend:** Django + DRF (`backend/`), Postgres + pgvector, Typesense,
  Qdrant, Celery, Django Channels, AWS Bedrock model routing.
- **Frontend:** React + Vite + TypeScript (`frontend/`), Tailwind, shadcn/ui,
  react-router-dom v7.
- **Core workflow graph (per `AGENTS.md`):** User → Profile → CV → Skills →
  Jobs → Matching → Applications → Interviews → Career Growth → Talent
  Pool → Employer → Hiring → Outcomes → Learning/Recommendations. One
  shared "Career Graph" intelligence layer is the intended architecture —
  avoid re-fragmenting it into disconnected per-feature schemas.

**Backend apps** (`backend/apps/`): `accounts`, `analytics`, `assessment`,
`career`, `core`, `emails`, `employers`, `events`, `intelligence`,
`interviews`, `jobs`, `legal`, `matching`, `monitoring`, `notifications`,
`outreach`, `payments`, `profiles`, `rashid`, `resume`, `salary`,
`scraper`, `search`, `skills`, `users`, `vectors`, `verification`.

**Frontend structure** (`frontend/src/`): `pages/`, `components/`,
`hooks/`, `services/`, `i18n/`, `lib/`, `integrations/`.

**This session's scope was narrow and specific**: the Legal/Privacy/
Payments-disclosure/Consent subsystem (`backend/apps/legal`,
`frontend/src/pages/legal`, `frontend/src/components/legal`,
`CookieConsentBanner`, signup consent, Privacy Center) plus two
cross-cutting bugs found while browser-testing it (employer onboarding
403, Arabic/RTL language toggle). **No other subsystem (matching,
interviews, Rashid/AI, scraper/ATS ingestion, career graph, payments core)
was reviewed, changed, or re-verified this session.** Their status should
be read from the most recent dated audit file under `audit/` that covers
them, not assumed from this document.

---

## 2. Completed this session (code-verified, pushed)

All of the following is merged into `development` and pushed to
`origin/development` as of commit `6a7347f`. Full narrative + evidence is
in `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §9C — this section is a
condensed index, not a replacement for it.

### 2.1 Three real bugs found (via real-browser testing, not assumed) and fixed

| Bug | Root cause | Fix | Files |
|---|---|---|---|
| Arabic language toggle did nothing | `LangToggle`'s actual `<Button>` had been commented out since the component's creation commit — never a working feature | Uncommented the button; the underlying `useTheme()` locale state (`lang`/`dir`/`toggleLang`, localStorage-persisted) was already correct | `frontend/src/components/ThemeToggle.tsx` |
| Mobile hamburger menu detached/broke when switching language while open | `AuthNavbar`'s `Sheet` sets `side={isAr ? "left" : "right"}` — toggling language while the Sheet is open flips its slide side mid-animation | `LangToggle` now accepts an `onToggled` callback; the mobile Sheet instance closes itself as part of the same click, so the side never flips while open | `frontend/src/components/ThemeToggle.tsx`, `frontend/src/components/AuthNavbar.tsx` |
| Public legal pages (`/legal/privacy`, `/legal/security`, etc.) intermittently failed to load ("This document couldn't be loaded") | Shared 30/min anonymous DRF throttle, pooled across ALL anonymous traffic on a page, was exhausted by normal browsing | New dedicated `legal_public` throttle scope (120/min), applied only to 9 read-only public legal endpoints; mutation endpoints (consent POST, DSR, auth) keep the normal budget | `backend/apps/legal/views.py`, `backend/config/settings/base.py` |
| Brand-new employer signups got an opaque 403 instead of the intended 404→onboarding-redirect | `EmployerProfileViewSet`'s class-wide `IsEmployer` permission requires an `employer_profile` a first-time employer doesn't have yet; DRF rejected before the view's own "no profile → 404" logic ran | `get_permissions()` override: only `list` uses `IsAuthenticated` alone (still scoped to `request.user`); every other action keeps `IsAuthenticated`+`IsEmployer` | `backend/apps/employers/views.py` |

### 2.2 Real-browser E2E test suite added (Playwright, devDependency only — never installed in production)

Location: `frontend/e2e/`. Config: `frontend/playwright.config.ts` (two
projects: `chromium-desktop`, `chromium-mobile` using `devices["Pixel 7"]`).
Driven via system-installed Chrome (`channel: "chrome"`) because this dev
sandbox has no outbound access to the Playwright Chromium CDN — **on a
machine/CI with normal internet access, switch back to
`npx playwright install chromium`** and drop the `channel` override if
preferred (not required — either works).

| Suite | Tests | Result (last run) |
|---|---|---|
| `legal-public-pages.spec.ts` | 19 | 19 passed |
| `signup-consent.spec.ts` | 2 | 2 passed |
| `authenticated-journeys.spec.ts` | 3 | 3 passed |
| `mobile-and-rtl.spec.ts` | 10 | 10 passed |
| **Total** | **34** | **34 passed, 0 failed** |

Run it yourself with: `cd frontend && npx playwright test` (requires the
backend running under `config.settings.e2e` on port 8000 and Vite dev
server on port 5173 — see `frontend/playwright.config.ts` for the expected
`baseURL`).

### 2.3 Regression tests added (backend, pytest)

- `backend/apps/employers/tests_new_employer_onboarding.py` — 3 tests.
- `backend/apps/legal/tests/test_public_read_throttle.py` — 4 tests.

### 2.4 Supporting infrastructure added

- `backend/config/settings/e2e.py` — throwaway SQLite settings module for
  local E2E runs only (points at the existing dev Redis container's
  host-mapped port, `CELERY_ALWAYS_EAGER=True`). **Does not touch the
  shared dev Postgres container.** Not used in production.
- `backend/.gitignore` — added `db_e2e.sqlite3` / `db_e2e.sqlite3-journal`.
- `frontend/.gitignore` — added Playwright's local artifacts
  (`test-results/`, `playwright-report/`, `e2e-results.json`, `*.log`).
- `frontend/package.json` — added `@playwright/test` devDependency and a
  `test:e2e` script (`playwright test`).

### 2.5 Documentation updated this session

- `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` — new **§9C** records the
  full real-browser E2E pass, all 3 bugs, and the product-surface
  inventory (§2.6 below). §10/§11 checklists updated to reflect it.
- `audit/LEGAL_POLICY_COVERAGE_MATRIX.md` — added a note superseding its
  own `E2E_TEST: NOT_DONE` / `RTL_STATUS: CODE_PRESENT_NOT_VISUALLY_VERIFIED`
  claims for the 7 documents now directly browser-verified.
- `audit/LEGAL_LINK_VERIFICATION.md` — added a note that the "runtime 404
  check: NOT PERFORMED" gap it flagged is now closed by the Playwright
  suite, including the specific throttle-429 bug that check would have
  caught.

### 2.6 Product-surface inventory (confirms no hidden legal-coverage gap)

Checked whether Education, Freelancing, Kids/minors, Government/B2G, or
Corporate/Enterprise exist as **distinct, separately-wired** product
verticals (as opposed to a label on existing models). Result: **all five
are NOT_PRESENT as distinct surfaces** — see `audit/
LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §9C for the file-level evidence per
item. This means the 13-document legal matrix is not missing a vertical
that would need its own policy page.

---

## 3. What remains unresolved — explicitly NOT done, NOT invented

These are real, open gaps. Do **not** treat any of them as closed without
new evidence (a legal sign-off, an admin-entered config value, or a
dedicated implementation pass).

### 3.1 Legal/compliance (requires a human, not code)

- **Every one of the 13 seeded policy documents is still `DRAFT`.** None
  is publicly live. Promoting one to `ACTIVE` requires an admin to review
  the actual rendered text and act through the Admin Legal Control Plane
  (`/admin/legal`) — this was deliberately never automated.
- **All Arabic content is `is_machine_translated=True`, unreviewed.** RTL
  now rendering correctly in a real browser (§2.1/§2.2) is an engineering
  fact only — it does not make any Arabic text legally approved.
- **Minors'/guardian-consent age threshold** (Egypt + Saudi Arabia) is
  unset — no single source gave a definitive number for this platform's
  context; `JurisdictionPolicyProfile.minor_age_threshold` is deliberately
  blank.
- **DPA (data processing agreement) status** for all 5 registered
  processors is unconfirmed (`dpa_signed=NULL`).
- **Refund window** (`LegalEntityConfig.default_refund_window_days`) is
  unset.
- **Retention periods** for 4 of 6 retention categories are unconfirmed —
  enforcement for those stays disabled by design until confirmed.
- **Legal entity identity** (name, address, privacy contact) is not
  configured in `LegalEntityConfig`.
- Running `python manage.py legal_readiness` against any environment will
  correctly report `OVERALL: BLOCKED` until the above are resolved. This
  is expected, not a bug — see `backend/apps/legal/management/commands/
  legal_readiness.py` and `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §7
  for the full list with sources.

### 3.2 Engineering (previously flagged, not touched this session)

- No `Content-Security-Policy` enforcing mode (Report-Only only) —
  flagged in `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §5, not escalated
  this session.
- `CareerProfile.cv_file`/`JobApplication.cv_snapshot` are served from a
  predictable `/media/...` URL with no signed-URL/authorization check —
  disclosed in the Security Overview policy page, not fixed.
- Two parallel `InterviewSession` models exist (`apps/career/models.py`
  and `apps/interviews/models.py`) — a pre-existing fragmentation risk,
  unchanged.
- Subscription cancellation semantics (`CompanySubscription`/
  `UserSubscription`) have no "immediate vs period-end" distinction —
  flagged, not modeled.
- `Job.salary_currency` (jobs app) vs. the employer-posting model's
  `salary_currency` have/had different defaults — resolved in an earlier
  pass per `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §9.6; **not
  re-verified this session**.

### 3.3 Deployment (cannot be determined from the repo alone)

- Production server state (deployed commit, venv path, running service
  names, Docker Compose state, ClamAV daemon reachability) is
  **UNVERIFIED** — this sandbox has no access to the production host.
  Before any deployment of this session's changes, someone with server
  access needs to confirm: which commit is currently live, how the
  backend process is managed (systemd/pm2/Docker), whether
  `config.settings.production` is in use, and whether new migrations
  from prior passes (`legal`, `accounts`, `jobs`, `payments` apps) have
  already been applied in production.
- No deployment was performed or attempted this session.

### 3.4 Everything outside the Legal/Privacy/Consent subsystem

Matching/recommendations, Rasheed (AI), interview voice coaching, the
scraper/ATS ingestion pipeline, the Career Graph schema, admin
governance, and billing/payments core logic were **not reviewed this
session**. Their last-known status is whatever the most recent dated file
under `audit/` says (e.g. `audit/D1_IDENTITY_CAREER_PROFILE.md` through
`audit/D10_FRONTEND_NAV_PRODUCTION_READINESS.md`, or
`audit/MASTER_PLATFORM_AUDIT_2026-08-31.md` and its corrections report) —
treat those as **unverified by this session**, consistent with `AGENTS.md`'s
instruction not to trust status docs without re-checking the real code.

---

## 4. Important decisions made this session (and why)

- **Fixed the Sheet/RTL race in the app, not the test.** The test failed
  three different ways across three attempted test-side fixes (timeout
  increase, force-click, stability-wait) before the root cause was traced
  to `AuthNavbar.tsx` tying the mobile Sheet's `side` prop to the live
  language. The fix is a small `onToggled` callback on `LangToggle`, not a
  test workaround — this is the generally correct approach when a test
  keeps failing in different ways: treat it as a signal of a real bug,
  not flaky infrastructure.
- **Playwright drives system Chrome via `channel: "chrome"`**, not a
  downloaded Chromium, because this sandbox cannot reach the Playwright
  CDN. This is a sandbox-specific workaround, documented in
  `playwright.config.ts` and here — not a project-wide policy. A
  developer/CI with normal internet access can use
  `npx playwright install chromium` and drop the channel override.
- **A dedicated SQLite settings module** (`config.settings.e2e`) was
  created for local E2E runs instead of reusing the dev Postgres
  container, specifically to avoid any risk to shared dev data.
- **The public-legal throttle fix is scoped to exactly 9 read-only GET
  endpoints**, deliberately excluding every mutation endpoint (cookie
  consent POST, policy accept, DSR creation, auth) — a blanket throttle
  relaxation was explicitly rejected as a security regression.
- **No legal/Arabic content was reworded, approved, or activated.** This
  was a hard constraint throughout — engineering fixes to RTL rendering,
  throttling, and permissions were kept strictly separate from legal
  content decisions.

---

## 5. Exact last completed step

The last action taken was pushing commit `6a7347f` (`docs(legal): record
real-browser E2E acceptance evidence (section 9C)`) to
`origin/development`, confirmed via `git fetch` + `git log origin/
development` showing `6a7347f` as the tip. `git status` is clean. No
background processes (dev servers, test runs) were left running — all
were explicitly stopped at session end.

---

## 6. Next steps (recommended starting point for the next session)

In priority order:

1. **If continuing the Legal/Privacy/Consent subsystem:** read
   `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §3.1 ("REQUIRES LEGAL
   REVIEW" items) and §9/§10/§11 for the full open-items list, then either:
   - Obtain real legal/configuration answers for §3.1 above and enter
     them via the Admin Legal Control Plane, or
   - Extend E2E coverage to the 6 policy documents not yet directly
     browser-click-tested for RTL (`security`, `ai-disclosure`,
     `acceptable-use`, `data-rights`, `subprocessors`,
     `international-transfers` — see `audit/LEGAL_POLICY_COVERAGE_MATRIX.md`'s
     "Real browser E2E update" note).
2. **If preparing for production deployment of this session's work:**
   get real server-discovery output first (current deployed commit,
   process manager, settings module in use, pending-migration state) —
   do not guess. See §3.3 above.
3. **If starting work on a different subsystem** (matching, Rasheed,
   interviews, scraper/ATS, admin/billing): do **not** assume its audit
   doc under `audit/` is current. Re-verify against the real code first,
   per `AGENTS.md`'s standing instruction — dispatch a context-gathering
   pass before trusting any completeness claim.
4. In all cases: `git pull` on `development` first to confirm you're
   starting from `6a7347f` (or later, if someone else has pushed since).

---

## 7. Quick reference — how to verify this document's claims yourself

```powershell
# Confirm commit / branch state
git log --oneline -6
git status

# Backend tests (from backend/)
./venv/Scripts/python.exe -m pytest apps/legal apps/accounts apps/payments apps/jobs apps/employers apps/career apps/interviews apps/core apps/emails apps/scraper/ats apps/scraper/pipeline apps/scraper/tests --no-cov -q

# Frontend typecheck / unit tests / build (from frontend/)
npx tsc --noEmit -p tsconfig.app.json
npx vitest run
npm run build

# Real-browser E2E (from frontend/; requires backend on :8000 under config.settings.e2e and Vite on :5173)
npx playwright test

# Legal readiness / link audit (from backend/)
./venv/Scripts/python.exe manage.py legal_readiness --settings=config.settings.e2e
./venv/Scripts/python.exe manage.py legal_link_audit --settings=config.settings.e2e
```

All of the above were run and passed/matched expectations as of commit
`6a7347f` (results summarized in §2 above; full output recorded in
`audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §9C).

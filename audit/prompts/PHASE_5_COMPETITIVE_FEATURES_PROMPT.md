# PROMPT — E-Career Phase 5: Jobright-Class Feature Adoption (Match Score, Tailoring, Autofill, Referrals, Rashid tools)

You are a senior full-stack engineer working on E-Career at
`M:\job already web for jobs\E-Career` (Django/DRF backend in `backend/`,
React/Vite frontend in `frontend/`). Read `AGENTS.md` and `CLAUDE.md`
first, then read `audit/COMPETITIVE_ANALYSIS_JOBRIGHT.md` in full — it is
the authoritative decision record for this phase; every item below
implements one of its numbered decisions. Do not deviate from its
USE/ADAPT/REJECT calls without flagging it explicitly in your completion
report.

## Prerequisite

Phase 0-4 and the live-verification pass should already be done — check
`git log` for `PHASE_4_TEST_SUITE_FIX_REPORT.md` and
`audit/LIVE_VERIFICATION_REPORT.md`. If the core recommendation
engine/matching/AI backbone aren't confirmed working yet, this phase's
items 5.1 and 5.5 depend on them — fix or flag blockers before building on
top of broken foundations.

## Hard ethical/legal line (non-negotiable)

- **No auto-submit application bots.** Every apply flow must end with an
  explicit human click on a real "Submit" button. This is not a UX
  preference, it's the platform's core direct-apply-verification identity
  — see `AGENTS.md` and `COMPETITIVE_ANALYSIS_JOBRIGHT.md` §3.
- **No LinkedIn (or any ToS-restricted platform) scraping for the
  referral/connections feature.** Use only first-party E-Career user data
  (consent-gated via `is_discoverable`) and public APIs (e.g. GitHub's
  public API) — see §4.

## Scope: 6 items

**5.1 — Match Score UI with explainable breakdown**

Backend: confirm the consolidated recommendation/matching engine (Phase 1
item 1.6) returns a structured breakdown, not just a bare score — shape
should be `{overall_score, breakdown: {skills: {score, reasoning}, experience: {...}, location: {...}, salary: {...}}, strengths: [...], gaps: [...]}`.
If the current engine only returns a bare number, extend it to compute
and return the per-factor breakdown (the design for this already existed
in the old `job_matching.py` per `MASTER_IMPLEMENTATION_PLAN.md` — reuse
that scoring logic if it's sound, don't invent new formulas from
scratch).

Frontend: build a `MatchScoreCard` component (job list + job detail pages)
showing the overall score prominently plus an expandable breakdown (bar or
list per factor with the reasoning text). Wire it to the real endpoint —
verify with a live request that the shape matches what the component
expects (TypeScript interface should catch mismatches).

**5.2 — Job-specific resume tailoring with before/after ATS score**

Backend: extend `apps/career/ats_scoring_service.py` (Phase 2 item 2.18)
to accept an optional `job_description` parameter and return a
job-specific compatibility score (keyword overlap with that specific
posting, not just generic ATS formatting checks). Wire
`apps/career/cv_tailor_service.py`'s tailoring output through this scorer
so the API can return `{original_score, tailored_score, score_delta,
tailored_resume_preview}`.

Frontend: on the job detail page, add a "Tailor My Resume for This Job"
action that calls this endpoint and shows the before/after score plus a
preview of the tailored content, with an explicit "Apply changes to my
resume" confirm step (never silently overwrite the user's saved resume).

**5.3 — Quick-Apply for API-capable ATS providers (Greenhouse/Lever/Ashby)**

For jobs where `direct_apply_url` was verified (Phase 0/1 work) AND the
ATS is one with a documented public application-submission API
(Greenhouse Job Board API, Lever Postings API, Ashby Job Board API — check
each provider's current public API docs for whether posting applications
is actually supported without special partner access; if a provider only
supports read, not write, skip it for this item and note it), build:
- A backend service that maps E-Career's `CareerProfile`/resume data to
  that ATS's application-submission payload shape.
- A frontend "Quick Apply" button that shows a review screen (pre-filled
  from the mapping, editable) before the user clicks a final, explicit
  "Submit Application" button — the submission call only fires on that
  explicit click, never automatically.
- Track submitted applications in the existing `Application`/
  `JobApplication` model so they show up in the user's normal application
  history.

If none of the ATS providers actually expose a public submission API
without special partner agreements (this is common — verify via each
provider's current developer docs, don't assume), **document that finding
explicitly and skip this item's backend submission piece** — build only
the review-screen UI with a "Continue to [ATS name] to submit" handoff
link instead (still valuable: pre-fills nothing on the third-party page,
but at least tracks the click-through).

**5.4 — Browser-extension-style DOM autofill for non-API ATS providers**

For ATS providers without a submission API (Workday, iCIMS, Workable,
SmartRecruiters, Teamtailor, Recruitee, BambooHR, Personio, Jobvite):
build a lightweight browser extension (Chrome/Manifest V3) that:
- Reads the user's E-Career profile via an authenticated API call (a
  scoped, revocable token — do not reuse the main session JWT directly in
  an extension; add a dedicated "extension token" auth flow with its own
  revocation endpoint).
- Detects known ATS form structures per-provider (reference
  `github.com/andrewmillercode/Autofill-Jobs`'s approach of per-platform
  field-detection logic as an implementation pattern — do not copy its
  code verbatim, it only covers 2 platforms; build E-Career's own
  detection for the ATS list above).
- Fills the form fields, and STOPS — never auto-clicks submit. The
  extension's own README/UI must say this explicitly.
- Logs the "autofill used" event back to E-Career (for application
  tracking) only after the user has navigated away or the page shows a
  success state — don't assume submission happened without some signal.

This is a genuinely large new subsystem (its own repo/package,
`manifest.json`, content scripts, build tooling). If time/scope doesn't
allow full implementation in this pass, build the extension token
auth backend (a real, testable, secure piece) and a minimal
proof-of-concept content script for ONE ATS provider (pick the simplest,
e.g. Greenhouse's own hosted application form, even though Greenhouse
also has an API route from 5.3 — the extension path is useful as a
fallback when a candidate applies via a Greenhouse page E-Career didn't
originate). Document the remaining providers as follow-up scope rather
than half-building all of them.

**5.5 — First-party "people in your network" + referral-request drafting**

Backend: build an endpoint that, given a target company, returns other
E-Career users who (a) have `is_discoverable=True` (reuse the exact
consent gate from Phase 0 item 0.14 — do not build a new, weaker check)
and (b) list that company as a past/current employer in their
`CareerProfile`/work history. Also add a lightweight GitHub public-API
lookup (no auth needed for public data, or use a GitHub App/PAT if rate
limits require it) that, given a company's GitHub org handle (add an
optional `github_org` field to the `Company` model if it doesn't exist),
surfaces public contributors as a "technical people at this company"
signal for engineering-track jobs.

Frontend: on a job/company detail page, add an "Insider Connections"
section showing these two sources; for E-Career-user connections, add a
button that calls Rashid (via the tool described in 5.6) to draft a
referral-request message — reuse the message-scenario structure from
`peiyan0/referral-helper` (LinkedIn formal / casual DM / email / cold
outreach) as the set of message TYPES to offer, but generate the actual
text via the real AI agent, not a static template.

**5.6 — Wire 3 new Rashid tool calls**

Extend the consolidated `apps/intelligence/agent.py` tool registry
(Phase 1 item 1.13) with 3 new tools:
- `get_match_score(job_id)` → calls the service from 5.1.
- `tailor_resume(job_id)` → calls the service from 5.2.
- `find_referral_contacts(company_id)` → calls the service from 5.5.

Confirm via a real chat message (through the live chat path, which
Phase 1 already migrated onto this agent) that Rashid can actually invoke
these tools mid-conversation and return their real results — not just
that the tool functions exist in isolation.

## Rules

- Local commits only, do NOT push.
- Never touch `.env`.
- Every new frontend piece must pass `npx tsc --noEmit` and `npx vite
  build --mode production` before you consider it done.
- Every new backend piece needs at least basic test coverage (this repo
  has a documented history of shipping untested code that broke in
  production — item 2.8's missing-tests issue from the last pass is the
  most recent example; don't repeat it).
- If you discover during implementation that an ATS's "public API" claim
  in this prompt is wrong (e.g. it requires a paid partner agreement you
  don't have credentials for), document that and adjust scope — don't
  fake a working integration against an API you can't actually call.

## When done

Write `audit/PHASE_5_COMPLETION_REPORT.md`: per-item status (done/partial/
deferred with reason), what was built, test coverage added, and an
explicit confirmation that no auto-submit or LinkedIn-scraping code was
introduced anywhere (the two hard ethical lines from this prompt).

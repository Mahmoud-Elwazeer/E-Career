# Competitive Analysis — Jobright.ai + Alternatives → Decisions for E-Career

**Date:** 2026-08-30. Source: jobright.ai landing page + web research on
Simplify, Teal, Huntr, LazyApply/Tsenta, JobHire.AI, FrogHire.ai, plus
GitHub search for autofill/referral open-source projects.

This document is the ONE decision record for "what to adopt from
Jobright-style products" — every item below is USE/ADAPT/REFERENCE/REJECT,
same discipline as `MASTER_IMPLEMENTATION_PLAN.md` §5. Do not re-litigate
these decisions without new evidence; execute them via
`audit/prompts/PHASE_5_COMPETITIVE_FEATURES_PROMPT.md`.

---

## What Jobright.ai actually offers (verified via their own site + 5
independent review sources)

1. **AI Job Match with score** — ranks jobs against resume/preferences,
   claims "no fake listings," early-posting alerts.
2. **1-Click Application Autofill** (Chrome extension) — fills forms
   across Workday, Greenhouse, Lever, iCIMS, Ashby, Workable. Candidate
   still manually submits (per independent reviews — Jobright does NOT
   auto-submit, unlike LazyApply/Tsenta).
3. **Job-specific AI-tailored resume** — ATS-optimized, generated in
   ~6 seconds per job description.
4. **Insider Connections / Referrals** — finds alumni and hiring managers
   at target companies, message templates to request referrals.
5. **24/7 AI Career Copilot ("Orion")** — conversational assistant across
   matching, tracking, and interview prep. Independent reviews note this
   is narrower than marketed ("copilot," not full delegation).
6. **Volume claim**: 8M+ aggregated jobs, 400K new/day — this is a raw
   aggregation count, not verified-direct-apply count. Multiple
   independent reviews flag billing/complaint issues and don't
   independently verify listing freshness/legitimacy.

## Competitor landscape (for context, not adoption)

| Product | Model | Verdict for E-Career |
|---|---|---|
| Simplify | Free browser-extension autofill, candidate still submits manually | Same category as Jobright's autofill — legitimate pattern |
| Teal | Resume builder + tracker, no job discovery | Not competing with E-Career's core loop |
| Huntr | Application tracker only | Not competing |
| LazyApply / Tsenta / JobCopilot / Wobo / Sorce | **Cloud bots that auto-submit** hundreds of applications/day without human review | **Anti-pattern — explicitly reject this model** |
| Jobscan | ATS resume-keyword scoring only | E-Career already built the equivalent (`ats_scoring_service.py`, Phase 2 item 2.18) |
| FrogHire.ai | Autofill + "review before submit" | Same legitimate pattern as Simplify/Jobright |

**Universal pattern across every legitimate competitor**: autofill helps
with the FORM, the human still reviews and clicks submit. The
spray-and-pray auto-submit bots (LazyApply-class) are explicitly called
out by independent reviewers as producing low response rates and carrying
detection/ToS risk. **E-Career must follow the Simplify/Jobright pattern
(assist, human submits), never the LazyApply pattern (bot submits).**

---

## Decisions

### 1. AI Match Score with explainable breakdown — **USE (finish what's already started)**

Not a new concept for this repo — `MASTER_IMPLEMENTATION_PLAN.md` §D4
already documented that `apps/intelligence/job_matching.py` had the
*correct design* for this (`{overall_score, breakdown: {skills, experience,
location, salary}, recommendation}` — exactly Jobright's "92% match
because: skills 95%, experience 90%..." pattern) but was dead/broken code,
since consolidated in Phase 1. **Decision: this is not a new build, it's
finishing the frontend surface for the already-consolidated recommendation
engine** — add a real Match Score UI component showing the breakdown, not
just a bare percentage.

### 2. Job-specific AI resume tailoring — **USE (extend existing work)**

E-Career already has `apps/career/cv_tailor_service.py` (tailoring) and
the just-built `apps/career/ats_scoring_service.py` (Phase 2 item 2.18,
ATS-compatibility scoring). Jobright's specific value-add on top of this:
tailoring is **job-description-aware** (not just generic ATS scoring) and
produces a before/after score. **Decision: extend, don't rebuild** — wire
`ats_scoring_service` to accept a job description and produce a
job-specific score delta, surfaced next to the "Apply" button on a job
detail page.

### 3. 1-Click Autofill — **ADAPT, Simplify/Jobright pattern only, never LazyApply pattern**

**Hard rule: candidate reviews and clicks submit. No auto-submission,
ever.** This is both an ethical line and consistent with E-Career's
existing direct-apply-verification moat — a platform whose entire pitch is
"we verify real, direct employer links" cannot also ship a bot that
carpet-bombs those same employers with unreviewed submissions.

Two concrete, legitimate builds:
- **(a) First-party quick-apply for jobs with a direct apply URL E-Career
  already verified** — since the platform already resolves and verifies
  `direct_apply_url` (Phase 0/1 work), for ATS providers with a documented
  public application API (Greenhouse Job Board API, Lever Postings API,
  Ashby Job Board API all support public read + some support posting)
  build a native "apply with your E-Career profile" flow that pre-fills
  and submits ONLY when the candidate explicitly clicks final submit —
  this is safer and more integrated than a browser extension because it's
  API-based, not DOM-scraping a third party's page.
- **(b) Browser-extension-style autofill for ATS providers without a
  public submission API** (Workday, iCIMS, Workable, SmartRecruiters,
  Teamtailor, Recruitee, BambooHR, Personio, Jobvite) — reference
  `andrewmillercode/Autofill-Jobs` (github.com/andrewmillercode/Autofill-Jobs,
  MIT-style small OSS Chrome extension, Vue, supports Greenhouse+Lever
  form-field detection patterns) as an implementation-pattern REFERENCE
  only — its scope is narrow (2 ATSs) and unmaintained-feeling; don't
  fork it, but its DOM-selector detection approach per ATS is a useful
  starting reference for building E-Career's own, wider-coverage version.
  **REJECT** `AbhishekMandapmalvi/AutoApply` and any "auto-apply bot" repo
  outright — that's the LazyApply anti-pattern (auto-submits across
  6 platforms without review), which conflicts with the product's stated
  ethics.

### 4. Insider Connections / Alumni Finder — **ADAPT, first-party data only, no LinkedIn scraping**

Jobright's version depends on scraping/licensing LinkedIn alumni data —
this is against LinkedIn's Terms of Service and a real legal exposure
(LinkedIn has litigated scraping cases). **Reject building this the way
Jobright does it.**

Legitimate, lower-risk alternative using data E-Career already has or can
legitimately obtain:
- Surface **other E-Career users** who list the same target company or
  same alma mater in their `CareerProfile` (if they've opted into
  discoverability — reuse the exact `is_discoverable` consent gate from
  Phase 0 item 0.14) as "people in your network at [Company]." This is
  first-party data, consent-gated, zero scraping risk.
- For companies with public engineering blogs/GitHub orgs, surface public
  GitHub contributors at that company (GitHub's API is a legitimate public
  data source, unlike LinkedIn) as a lighter "who works there" signal for
  technical roles.
- REFERENCE `peiyan0/referral-helper` (github.com/peiyan0/referral-helper) —
  a small, 100%-client-side, MIT-style React/TS tool that generates
  Google search queries + templated outreach messages for requesting
  referrals. Zero backend, zero scraping — its "template generator"
  concept (structured referral-request message templates per scenario:
  LinkedIn formal / casual DM / email / cold outreach) is directly
  reusable as a frontend feature: once E-Career surfaces a real contact
  (from the first-party sources above), auto-draft a referral-request
  message using AI (Rashid), don't hand-roll static templates like the
  reference repo does — E-Career's AI layer can do this better.

### 5. 24/7 AI Career Copilot — **USE (this is Rashid, already in progress)**

This is not a new feature — it's Rashid, and Phase 1 item 1.13 already
began consolidating Rashid's tool-calling onto the real
`apps/intelligence/agent.py` implementation instead of raw prompt
concatenation. **Decision: extend that consolidated agent** with 3 new
tool calls surfacing the features above as conversational actions:
`get_match_score(job_id)`, `tailor_resume(job_id)`,
`find_referral_contacts(company_id)` — Rashid should be able to say "I
found 92% match for you, want me to tailor your resume for it?" and
actually call the real services, not describe them.

### 6. Volume/freshness marketing angle — **USE the differentiation, don't copy the metric**

Jobright's "8M jobs" is a raw aggregation count with no independent
freshness/legitimacy verification per multiple reviews. E-Career's
`MASTER_IMPLEMENTATION_PLAN.md` Job Quality Engine (9-state field, Phase 1
item 1.8) is a genuine advantage IF the scraper pipeline (Phase 0 items
0.1-0.4) is actually running in production. **Decision: once the scraper
is confirmed live (see the live-verification prompt already issued),
market "every job is verified direct-apply" as the differentiator instead
of chasing a raw volume number** — this is a positioning decision for
the landing page copy, not a new engineering build.

### 7. What NOT to build

- No auto-submit bot (see #3).
- No LinkedIn scraping (see #4).
- No "90% of your job search automated" marketing claim — multiple
  independent reviews call this kind of claim out as misleading even for
  Jobright itself. Keep E-Career's claims verifiable.

# PROMPT — E-Career Phase 2: Feature Completion

You are a senior backend/full-stack engineer working in the E-Career repo at
`M:\job already web for jobs\E-Career` (Django/DRF backend in `backend/`,
React/Vite frontend in `frontend/`).

## Prerequisite

Phase 0 and Phase 1 should be complete. Read
`M:\job already web for jobs\E-Career\audit\PHASE_0_COMPLETION_REPORT.md`
and `PHASE_1_COMPLETION_REPORT.md` first (same `audit/` directory) — if
either shows unresolved blocking items that this phase's work depends on
(e.g. item 2.2 depends on 1.1's CareerBrain decision), resolve the
dependency or flag it before proceeding.

## Before touching anything

1. Read `AGENTS.md` in full.
2. Read `MASTER_IMPLEMENTATION_PLAN.md` in full — items below are 2.1–2.22
   from its "Phase 2" table. Unlike Phase 0/1, several of these are BUILD
   items (genuinely new code, not fixes) — treat those with normal
   feature-development rigor (tests, migrations, frontend+backend
   together where applicable).
3. Never touch `.env` or secrets.
4. Commit logically-grouped items separately.

## Scope: these 22 items only

**2.1** — RESOLVED: Yes, schedule it. Wire
`ProactiveRashidService.check_user_triggers()`
(`apps/rashid/proactive_service.py`) into Celery beat with a sensible
cadence (daily). It's fully built, currently has zero callers and isn't in
the beat schedule — this is a zero-cost win, do it.

**2.2** — Wire `CareerBrainService.update_brain()`
(`apps/career/career_brain_service.py:154-199`) to fire automatically via
signal or beat task instead of only on an explicit `POST` request. This
depends on Phase 1 item 1.1's decision about `CareerBrain`'s fate — if 1.1
decided to retire CareerBrain, skip this item.

**2.3** — Fix `ResumeBuilder.tsx:24-32`'s localStorage key mismatch — it
reads `access_token` but the app's real auth flow stores the JWT under
`usam_access` (or whatever the actual current key is — check
`services/client.ts`/`hooks/use-auth.tsx` for the real key name). This
breaks the component's own local `apiFetch` calls silently.

**2.4** — Fix resume export: DOCX export (`apps/resume/views.py:250-278`)
currently returns `success: True` without producing a file — add the actual
`docx` branch (a Python library like `python-docx` should already be a
project dependency or needs adding). PDF export silently falls back to raw
HTML mislabeled as `.pdf` when `xhtml2pdf` is missing — add `xhtml2pdf` to
requirements (see 2.5) and verify the PDF branch actually produces a real
PDF, not an HTML fallback, after the dependency is installed.

**2.5** — Add missing dependencies to `requirements.txt`: `easyocr`,
`pdf2image`, `xhtml2pdf` (all currently imported in code but absent from
requirements, causing silent degradation). Then fix the CV-parser plugin
ordering bug in `apps/profiles/cv_parser.py:282-288` — the OCR fallback
plugin is currently unreachable for any PDF because a different plugin
(Docling) always matches first in the plugin chain, so scanned/image-only
PDFs get empty text instead of falling through to OCR. Fix the plugin
selection logic to actually try OCR when the primary extraction returns
empty/near-empty text.

**2.6** — Seed `ResumeTemplate` data. There's currently no fixture/seed
management command, so `GET /resume/templates/` returns empty on a fresh
database. Add a Django data migration or management command
(`manage.py seed_resume_templates` or similar, matching repo conventions)
that creates a reasonable starter set of templates.

**2.7** — RESOLVED: Deprecate `KnockoutQuestion`. Mark the model as
deprecated (docstring + comment, and if safe, a Django deprecation
warning on save), keep the already-working dynamic-form knockout
(`custom_form_fields[].knockout_value`, confirmed end-to-end functional and
security-hardened per `MASTER_IMPLEMENTATION_PLAN.md` §7 "What NOT to
Touch") as the sole canonical mechanism. Do not build new capture/eval
logic for the old model — that would recreate the exact "duplicated
parallel systems" anti-pattern this whole plan exists to eliminate. If
`KnockoutQuestion` has zero remaining callers after this, that's fine —
leave the model in place (don't drop the table) unless a follow-up
migration decision is made later.

**2.8** — RESOLVED: Skip for now. Multi-seat employer accounts are not a
near-term priority — the single-seat employer flow itself has open
correctness issues addressed in Phase 0/1 (employer role assignment,
stats endpoint, edit-lock). Do not build `EmployerTeamMember`/invitations
in this pass; leave `EmployerProfile.user`
(`apps/employers/models.py:11-15`) as a one-to-one for now. Revisit only
if the user explicitly requests it in a future phase.

**2.9** — Add `send_notification_digest`
(`apps/notifications/tasks.py:67-124`) and `send_weekly_career_digest`
(`apps/emails/tasks.py:351-417`) to `config/celery.py`'s `beat_schedule`.
Both are fully implemented already; neither is currently scheduled to run.
Pick sensible cadences (daily for notification digest, weekly for career
digest, matching their names) unless the code itself specifies a cadence.

**2.10** — `apps/interviews/coding_service.py`'s `coding_interview_service`
is built but not wired — the `coding-question`/`problem`/`solution` URLs in
`apps/interviews/urls.py:18-20` currently all alias the generic `start`
action instead of calling the real coding-specific service. EITHER wire
them to the real service, OR if coding-type interviews aren't a near-term
priority, delete the dead module and fix the misleading URL names so they
don't imply functionality that doesn't exist.

**2.11** — Build an Assessment Engine frontend. The backend
(`apps/assessment/views.py:118-236`) is real, live-verified working
(MCQ+Judge0 grading), but has zero UI — this is a new frontend feature:
assessment-taking flow, question display, submission, results view. Match
the existing frontend's design system/conventions.

**2.12** — Fix `frontend/src/pages/employer/JobPostingForm.tsx:37-56`'s
React Query v5 bug — it uses `onSuccess` as an option on `useQuery`, which
was removed in TanStack Query v5 (silently does nothing now). Replace with
a `useEffect` that runs when `data` changes. This currently means editing
an existing job posting never pre-fills the form.

**2.13** — Wire `frontend/src/pages/Settings.tsx` to the real,
already-existing backend endpoints (`updateMe`, `changePassword`,
`deleteAccount` — check `services/auth.ts:87-110` for exact names/shapes).
Currently the page has zero `onChange`/`onClick` handlers anywhere — it's a
100% non-functional shell despite working backend endpoints existing
unused. Build the actual form state + submit handlers.

**2.14** — Fix `CompanyProfile.tsx:37-43`'s company-scoped jobs query —
it currently fetches 20 jobs platform-wide and filters client-side, missing
any company jobs beyond page 1 of the platform-wide result. Fix it to query
jobs filtered by company server-side (check if the jobs API supports a
`company` or `employer` query param; add one if it doesn't).

**2.15** — Add an employer acquisition funnel entry point. Currently
there's zero discoverable link to `/app/employer/register` anywhere in the
main nav, footer, or landing page — a real acquisition gap, not just a UX
nit. Add a "For Employers" / "Post a Job" CTA in an appropriate, visible
location matching the site's existing design.

**2.16** — Add a REST endpoint for `PlatformConfig`
(`apps/core/models.py:109-197`) under `apps/core/admin_urls.py` or wherever
the SPA admin dashboard's API surface lives. The model is real and
admin-controllable in principle but currently only reachable via Django's
native `/admin/` (invisible to the React admin dashboard). Build the
serializer + viewset + URL registration.

**2.17** — Decide the fate of `apps/config/ai_config.py` (or wherever it
actually lives — check the exact path) — a fully dead, unwired
cost-optimization module claiming ~$112/mo savings via cheaper Llama
routing for certain tasks. EITHER wire it into the model router (from
Phase 1 item 1.11's consolidated router) as a real cost-optimization path,
OR delete it if the savings claim isn't worth the added complexity — flag
this as a decision point for the user rather than assuming.

**2.18** — Build ATS-compatibility scoring for CVs (keyword density,
formatting/parseability against common ATS parsing patterns) — this
currently doesn't exist at all anywhere in the repo. This is a genuine
BUILD item: design a scoring rubric, implement it (likely in
`apps/career/` alongside the existing tailoring service), expose it via API,
surface it in the CV/resume frontend UI.

**2.19** — Build a `LearningResource` catalog model so skill-gap
recommendations (`apps/career/skill_gap_analysis.py:223-269`) reference
real courses instead of hardcoded generic strings. Design the model
(title, provider, URL, skill tags, level), seed some real data (could
integrate with the sibling E-USAM platform's course catalog if
appropriate — check with the user), wire skill-gap recommendations to query
it instead of the current hardcoded strings.

**2.20** — Wire `VectorService.semantic_search`
(`apps/vectors/service.py`) into `apps/intelligence/research_engine.py`
and/or Rashid's `agent.py` tools. Real pgvector-based RAG infrastructure
exists but is currently unused by the one feature area (research/Rashid)
that would benefit most from it. Add the integration so research/Rashid
queries can retrieve semantically relevant internal content.

**2.21** — Configure GPT-Researcher's search-provider API key(s)
(check `.env.example` for the exact env var names expected) so real cited
source URLs actually get returned by `research_engine.py:148-242`, instead
of the current internal-data fallback that fabricates a confidence score
without real source URLs. If you can't set the actual API key (secrets
access), at minimum fix the fallback path to explicitly label its
confidence score as "not computed from external sources" rather than
presenting a fake-looking number.

**2.22** — RESOLVED: Skip for now. Monetization is not the near-term goal
— the platform's core value delivery is broken today (Phase 0/1: the
scraper never ingests a real job, both recommendation engines are broken,
the AI backbone is degraded). Charging employers for a product that isn't
reliably delivering yet is a trust/business risk, not just an engineering
one. Do NOT build `SubscriptionPlan`/`Package`/`Subscription` models or
any payment-gateway integration in this pass. Revisit only after Phase
0/1 are verified working end-to-end and the user explicitly requests
billing work.

## When done

Write a completion report to
`M:\job already web for jobs\E-Career\audit\PHASE_2_COMPLETION_REPORT.md`
covering all 22 items: status, what changed, verification, and explicitly
flag every item where you made a product/scope decision (2.1, 2.7, 2.8,
2.17, 2.21, 2.22 especially) so the user can review those calls.

# PROMPT — E-Career Phase 9: Master Platform Cross-Check + Career Coach + ATS Coverage Gaps

You are a senior full-stack engineer + platform architect working on
E-Career at `M:\job already web for jobs\E-Career`. Read `AGENTS.md`,
`CLAUDE.md`, `MASTER_IMPLEMENTATION_PLAN.md`, and
`audit/FINAL_PLATFORM_COMPLETION_REPORT.md` in full first — this repo has
already been through 9+ audit/implementation phases (Phase 0 through the
Final Platform Completion pass), and the owner's newest request (a
30-section "MASTER FULL PLATFORM" audit) asks to re-verify everything
against current code rather than trust any prior claim. **Most of what
that 30-section request asks for already exists and is more complete
than the request assumes** — this prompt is scoped to the REAL gaps found
by direct code inspection, not a restatement of the full 30 sections.

## What direct inspection just confirmed ALREADY EXISTS (do not rebuild)

1. **10 real ATS scraper connectors** — not 6-8 as commonly assumed:
   `apps/scraper/ats/{ashby,bamboohr,greenhouse,lever,smartrecruiters,
   teamtailor,workable,workday,icims,oracle,sap}.py`. This actually
   EXCEEDS the original scope (iCIMS, Oracle, SAP weren't even in the
   original ATS list) — Recruitee, Personio, Jobvite are the only 3 named
   ATS providers from the owner's list genuinely missing.
2. **7-dimension explainable Talent Score** — `apps/career/models.py`'s
   `TalentScore` model has `overall_score`, `skill_score`,
   `experience_score`, `education_score`, `portfolio_score`,
   `interview_score`, `growth_score`, `communication_score` — this is
   real, multi-signal, NOT a single opaque AI score, matching the owner's
   explicit requirement in §5/§O ("use multiple signals rather than one
   AI score"). This satisfies the "Talent Qualification" requirement
   already — do not build a parallel system.
3. **Hybrid search (Typesense + Postgres fallback)** — `apps/search/
   service.py` wraps `TypesenseSearchPlugin` with automatic fallback to
   `postgres_plugin` when Typesense is unavailable. This is a real,
   working search architecture decision already made — do not re-evaluate
   Elasticsearch/OpenSearch/Meilisearch/Qdrant from scratch; the decision
   is made and working.
4. **Cover Letter engine** — `apps/career/cover_letter_service.py` +
   `apps/career/views_cover_letter.py` are real, not a stub.
5. **Job normalization/deduplication** — THREE separate dedup
   implementations exist: `apps/scraper/pipeline/deduplicator.py`,
   `apps/verification/stages/deduplicator.py`,
   `apps/core/services/embedding_deduplication.py`. This is a real
   fragmentation finding worth investigating in this pass (see Task 3
   below) — not because dedup is missing, but because 3 separate
   implementations for one concept is the "disconnected engines"
   anti-pattern the owner explicitly warned against in §6/§16.
6. **Recommendation engine consolidation already done** — only ONE
   `recommendation_engine.py` remains (`apps/search/recommendation_engine.py`)
   — the historical fragmentation (career/recommendation_engine.py vs
   search/recommendation_engine.py) that earlier audits flagged has
   already been resolved via consolidation in an earlier phase. Confirm
   this is still true and do not re-fragment it.
7. **CareerGoal/CareerGoalAction models** — real, existing Career Coach
   data model (`apps/career/models.py`).
8. **AI Model Router with quality→cost routing** — `apps/intelligence/
   model_router.py` (confirmed in the Phase 7 audit), extended with
   admin-configurable overrides in Phase 7b.
9. **Rashid agent now genuinely wired to live chat** with 9 tools
   (confirmed fixed in Phase 7c — this was previously the single biggest
   "Rashed must call real services" gap the owner has repeatedly raised;
   it is now closed).
10. **Admin Control Plane** — 28+ DRF endpoints across system health, AI
    costs, scraper control, verification, talent pool, GDPR,
    entitlements, celery beat, global search, admin copilot (Phase
    7a/7b/7c). This substantially satisfies §Y/§AA/§AB/§AC of the
    owner's request already.

## Real gaps found — this is the actual scope of this phase

**9.1 — 3 missing ATS connectors: Recruitee, Personio, Jobvite**

Build 3 new files in `apps/scraper/ats/` following the exact pattern
already established by the 10 existing connectors (read
`apps/scraper/ats/base.py` for the shared interface, and
`apps/scraper/ats/greenhouse.py` or `apps/scraper/ats/lever.py` as the
closest reference implementations — Recruitee and Personio both have
documented public job-board APIs similar in shape to Greenhouse's).
Register each in whatever central registry `apps/scraper/orchestrator.py`
or the ATS `__init__.py` uses to dispatch by ATS type. Add basic tests
following the existing ATS connector test pattern (check
`apps/scraper/tests/` if one exists for an existing connector, mirror its
structure).

**9.2 — Deduplication fragmentation: consolidate or clearly delineate**

Investigate the 3 existing deduplicators:
- `apps/scraper/pipeline/deduplicator.py`
- `apps/verification/stages/deduplicator.py`
- `apps/core/services/embedding_deduplication.py`

Determine: are these 3 genuinely different concerns (e.g. scraper-time
exact-match dedup vs. verification-time cross-source dedup vs.
embedding-based semantic near-duplicate detection), in which case
DOCUMENT the distinction clearly (a short docstring/README explaining
why 3 exist and what each is for) so it doesn't look like accidental
fragmentation to the next person who reads this code — OR are 2+ of them
doing genuinely redundant work, in which case CONSOLIDATE them the same
way the recommendation engines were consolidated in an earlier phase.
Do not guess — read all 3 implementations fully before deciding.

**9.3 — Career Coach: verify it's a real continuous layer, not just data models**

`CareerGoal`/`CareerGoalAction` are real models, but the owner's §S
requirement is a Career Coach that "continuously recommends actions"
based on identity+skills+goals+applications+interviews+market trends —
this is a BEHAVIOR requirement, not just a data model. Check
`apps/rashid/proactive_service.py` (already confirmed real and wired to
some notification triggers in earlier phases) — does it actually
generate career-coach-style proactive recommendations tied to
`CareerGoal` progress, or only the narrower triggers already built
(trending skills, etc. from the Final Platform Completion pass)? If the
coaching logic is present but narrower than the full continuous loop the
owner describes, extend `proactive_service.py` with 1-2 new trigger
types (e.g. "goal stalled — no progress in 30 days, suggest 3 concrete
next actions using Rashid" or "market trend detected in target role —
notify with specific skill gap"). Do not build a second, parallel
"career coach service" — extend the existing proactive service.

**9.4 — Talent classification: confirm it avoids arbitrary labels (owner's explicit anti-requirement)**

The owner explicitly said: "DO NOT blindly use [Entry/Junior/Mid/Senior/
Expert] labels... Research evidence-based approaches... use multiple
signals rather than one AI score." The 7-dimension `TalentScore` already
satisfies "multiple signals." Confirm: is there any code path that
derives a single Entry/Junior/Mid/Senior/Expert LABEL from
`TalentScore`, and if so, is that derivation transparent/explainable
(e.g. documented thresholds per dimension) rather than an opaque
AI-generated label? If no such label-derivation exists yet and the admin
UI (Phase 7a's Talent Pool tab) needs a human-readable summary tier for
scanning a candidate list quickly, add ONE simple, documented,
threshold-based tier derivation (not a new AI call) — e.g. based on
`experience_score` + `overall_score` bands — and expose the exact
thresholds in the admin UI so it's auditable, never a black box.

**9.5 — Onboarding: confirm CV data isn't re-asked**

Owner's §B explicit requirement: "The user should not have to repeat
information already extracted from their CV... intelligently confirm or
enrich instead of asking again." Trace the actual onboarding flow
(`frontend/src/App.tsx`'s `OnboardingWrapper`, confirmed touched in the
Final Platform Completion pass for the onboarding-preferences fix) —
does it check for already-parsed CV data (`CareerProfile.cv_parsed_data`)
before presenting a question, or does it always ask every onboarding
question regardless of CV state? If it always asks, add the "skip/pre-fill
from CV data, let user confirm or edit" behavior for at least the fields
CV parsing already extracts (experience, education, skills) — this is a
real UX gap directly named by the owner, not speculative.

**9.6 — Open-source research: 2 targeted evaluations, not a blind adoption**

The owner named several repos in this request. Give each an explicit
verdict grounded in E-Career's actual current state (most of what these
repos offer, E-Career has already built better/more-integrated versions
of, per the "already exists" list above):
- `JOYCEQL/magic-resume`: **REJECT** — Apache 2.0 but with a strict
  commercial-use restriction requiring a paid commercial license for any
  SaaS/for-profit use (confirmed from the repo's own README). E-Career is
  a for-profit platform; using this would require a commercial license
  from the author. Also, E-Career already has CV upload/parsing/ATS
  scoring/tailoring built and more deeply integrated (Phase 2/5 work) —
  a standalone resume EDITOR isn't E-Career's gap.
- `MadsLorentzen/ai-job-search` / `santifer/career-ops`: **REJECT
  (unchanged from earlier audit)** — both are personal Claude-Code-CLI-
  driven individual job-hunt tools (run by a job seeker in their own
  terminal), not multi-tenant platform codebases; nothing ports directly
  to a Django/React SaaS. `career-ops`'s scale (69k stars) is notable as
  a signal of market interest in AI-assisted job search, worth knowing
  about for positioning/marketing, but not a code-integration candidate.
- `ngoanpv/DeepInterview`: **RE-EVALUATE, ADAPT is now more attractive
  than at the last review.** Its own README states (as of this repo
  snapshot) it now supports a **fully local, zero-API-key path**
  (Ollama + faster-whisper + Kokoro) verified end-to-end, in addition to
  cloud providers behind swappable adapters (`STT_PROVIDER`/
  `TTS_PROVIDER`/`LLM_PROVIDER` env vars, no code changes to swap
  vendors). Its prep/live/post multi-agent architecture (5 prep agents +
  3 live agents + 4 post agents, using a shared `InterviewContext`
  blackboard) is a more sophisticated pattern than a simple STT→LLM→TTS
  loop. E-Career's own voice interview system (`apps/interviews/
  voice_service.py`) is currently blocked purely on AWS IAM permissions
  (Part 2 human action item, not a code gap) — DeepInterview's
  provider-adapter pattern is worth referencing as a way to make
  E-Career's voice pipeline provider-agnostic too (reduce lock-in to
  AWS Polly/Transcribe specifically), but this is a nice-to-have
  architecture improvement, not a blocker. **Verdict: REFERENCE the
  provider-adapter pattern in a code comment/doc for future
  consideration; do NOT integrate the repo directly** (it's a full
  separate application with its own LiveKit/Supabase stack — pulling it
  in would violate the "no disconnected engines" principle far more than
  it would help, given E-Career's interview simulation is already real
  and working per Live Verification).
- `IliaLarchenko/Interviewer`: **REJECT (unchanged)** — single-file
  Gradio app, not a production platform component.

## Rules

- Do NOT rebuild anything confirmed already working in the "already
  exists" list above.
- Do NOT adopt `JOYCEQL/magic-resume`'s code given its commercial-use
  license restriction — this is a real legal constraint, not a stylistic
  preference.
- Local commits only, do not push.
- Real test coverage for the 3 new ATS connectors and any behavior
  change to onboarding/proactive service.
- Never present an AI-derived talent tier as an unexplainable black box
  — every threshold must be visible/documented per the owner's explicit
  anti-black-box requirement (§8/§O/§9 of their request).
- Run full backend test suite + `npx tsc --noEmit` + `npx vite build
  --mode production` before considering this phase complete.

## When done

Write `audit/PHASE_9_MASTER_CROSSCHECK_REPORT.md`: for each of the 6
tasks (9.1-9.6), what was found, what was built/fixed/documented, and
explicit confirmation of what was intentionally NOT changed because it
already satisfies the owner's requirement (cite the "already exists"
list above by number). End with a direct answer: **"Does any of the
owner's 30-section MASTER audit request point to a genuine, unaddressed
platform gap beyond what this phase and all prior phases have already
closed?"** — if yes, name it precisely; if no, say so plainly rather than
generating more busywork for its own sake.

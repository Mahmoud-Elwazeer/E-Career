# E-Career — MASTER IMPLEMENTATION PLAN

**Status: THE authoritative planning document for this repo, going forward.**
Supersedes all ~110 prior `*_SUMMARY.md` / `*_REPORT.md` / `*_PLAN.md` files at the repo
root, and the now-partially-stale `MASTER_STATE_AND_ROADMAP.md`. Do not create a new
parallel planning doc — patch this one.

**Source:** Synthesis of 10 independent, code-verified domain audits (`audit/D1`–`D10`,
2026-08-29) covering the entire Django/DRF backend + React/Vite frontend. No new
research was performed to produce this document — every claim below traces to one or
more of the 10 source reports. Where two reports disagreed, it is flagged explicitly
rather than silently resolved.

**Method note inherited from the audits:** findings are code-verified (direct reads,
live `pytest`/`boto3`/ORM reproduction, `git log`/`git show`) — not derived from prior
status docs. Per `AGENTS.md`, treat this document itself the same way: re-verify before
repeating a claim in six months, because this repo's status docs have a documented
history of drifting from code within days.

---

## 1. Executive Summary

**Overall verdict: substantial, often sophisticated engineering exists across almost
every subsystem — but the platform is not production-solid today.** The dominant
failure pattern is not "unbuilt," it's **built-twice-and-disconnected** or
**built-once-and-never-wired**: real, well-designed modules sit next to a duplicate that
disagrees with it, or sit fully coded with zero callers. Several things branded as this
platform's core differentiators (direct-apply verification, the "Career Graph" single
source of truth, AI-powered recommendations, voice interviews) are **currently
non-functional in production** despite real underlying code. The good news: most of
Phase 0 below is wiring/import/field-name fixes, not rewrites — the architecture is
mostly sound, it's disconnected.

### Top severity-ranked findings (plain language)

1. **Zero real jobs have ever been scraped into this platform.** The entire scraper
   module fails to import (`ModuleNotFoundError: No module named 'croniter'`), and even
   if that's fixed, every job-creation call passes a field (`remote_type`) that was
   removed from the database months ago — so it throws immediately, silently, on every
   attempt. This also means the platform's headline compliance promise (reject
   LinkedIn/Indeed/ZipRecruiter/Monster "apply" links) is **moot for real data** — there's
   no real data to check. *(D3)*
2. **Even when a job is correctly rejected by the verification engine, it stays publicly
   visible.** `VerificationEngine.verify_job()` never writes `Job.status`, and the public
   job list only filters on `Job.status`. This is a second, independent way the
   anti-aggregator "moat" fails in practice. *(D3)*
3. **The AI backbone (AWS Bedrock "sonnet" alias) is broken account-wide right now** —
   every "AI-powered" feature in Assessment, Interviews, CV parsing, Career Brain, and
   all 5 Rashid tools is silently degrading to generic hardcoded fallback content. Nobody
   would know from the UI. *(D6, D7)*
4. **Employer self-service registration is broken.** Completing employer signup never
   sets `User.role = "employer"`, so the new employer is immediately locked out of every
   employer-gated endpoint they just registered for. Only a manual admin fix recovers it.
   *(D1)*
5. **The platform's own "single source of truth" model (`CareerBrain`) is fully dead
   code.** Its only sync method has zero call sites anywhere. Career data is actually
   fragmented across 9 uncoordinated models in 4 apps — worse than the fragmentation the
   repo's own `AGENTS.md` already warns about. *(D1)*
6. **Both job-recommendation engines are broken**, and there are two of them, disconnected,
   solving the same problem differently. Stale field references (`job.remote_type`,
   `job.experience_required`, `profile.saved_jobs`) throw or silently degrade
   recommendation quality to zero for every real user. *(D4)*
7. **Voice interviews don't work.** Real STT→LLM→TTS pipeline code exists (not a mockup),
   but the configured AWS IAM user has zero Polly/Transcribe/S3 permissions, and
   `AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` aren't even set. *(D6)*
8. **In-app notifications are a shell that always renders empty for real users.** Real
   backend events (new application, interview started) write to one notification model;
   the frontend only ever reads a second, different model that nothing in production
   writes to. *(D8)*
9. **Multiple live 500s exist today** on endpoints already wired to the frontend:
   employer stats, interview stats, hybrid search, and (a regression of an
   already-"fixed" bug class) job recommendations via `apps/profiles/services.py`. *(D3,
   D4, D5, D6, D8)*
10. **No billing/subscription system exists at all** — zero `Subscription`/`Plan`/
    `Package`/payment-gateway code anywhere in the codebase. If monetization is near-term,
    this is a from-scratch build, not a fix. *(D9)*

### Health-by-area at a glance

| Area | Verdict |
|---|---|
| Identity/Auth/Profile/Onboarding | PARTIAL — auth core solid, employer role + Career Identity broken |
| CV/Resume/Skills | PARTIAL — real pipelines, triplicated/duplicated at every layer |
| Job Pipeline/Scraping/Verification | BROKEN AT RUNTIME — well-designed, but ingestion never runs |
| Search/Matching/Recommendations | PARTIAL/BROKEN — keyword search solid; semantic/hybrid/matching/recs broken |
| Employer/Talent Pool/Applications | PARTIAL — core CRUD solid; ranking intelligence is fake; 2 live 500s |
| Interview/Voice/Assessment/Coach | PARTIAL — real pipelines, degraded by AI outage + AWS perms; proactive coach dead |
| Rashid AI / Model Routing / Cost | PARTIAL/BROKEN — router exists, bypassed everywhere; cost dashboard broken |
| Notifications/Automation/Documents | PARTIAL — real automation, split-brain notification systems |
| Admin/Security/Analytics/Billing | PARTIAL, Security PARTIAL-STRONG, Billing MISSING entirely |
| Frontend Nav/Production Readiness | PARTIAL — most pages real; Settings is 100% non-functional shell |

---

## 2. Engine-by-Engine Status Table

Status legend: **DONE** / **PARTIAL** / **BROKEN** / **MISSING** / **REFACTOR** /
**INTEGRATE** / **REPLACE** / **BUILD**. One row per named engine/subsystem across all
10 domain reports (~41 rows).

| # | Engine | Domain | Status | One-line reason | Key file:line evidence |
|---|---|---|---|---|---|
| 1 | Auth Engine (register/login/JWT/reset) | D1 | DONE | Core mechanics real: JWT, blacklist, password reset, soft delete | `accounts/views.py:49-289` |
| 2 | Auth — employer role assignment | D1 | BROKEN | Registration never sets `User.role="employer"`; permission classes require it | `employers/views.py:53-94`; `employers/permissions.py:15-20` |
| 3 | Auth — account-type selection at signup | D1 | MISSING | No `role` field on `RegisterSerializer`; all self-registered users default jobseeker | `accounts/serializers.py:8-14` |
| 4 | User Profile Engine (CareerProfile CRUD) | D1 | PARTIAL/REFACTOR | Real & functional, but "canonical model" is an import alias, not a DB constraint; deprecated `users.UserProfile` table still live | `profiles/models.py:10-19`; `users/models.py:112-183` |
| 5 | Career Identity Engine (`CareerBrain`) | D1 | BROKEN/REPLACE | Well-designed model; its only sync method has zero call sites. Career data fragmented across 9 models/4 apps | `career/models.py:599-905` (0 callers of `update_from_profile`) |
| 6 | Onboarding flow | D1 | PARTIAL/REFACTOR | 3 disconnected implementations; 2 discard data client-side; the 1 real backend model has 0 frontend callers | `App.tsx:111-112` (TODO, discards data); `career/views_onboarding.py` (orphaned) |
| 7 | CV/Resume Engine (upload/parse/extract) | D2 | PARTIAL | Real, functional, but **triplicated**: 3 parsers, 2 upload endpoints, 3 completeness scorers | `profiles/cv_parser.py`, `career/cv_parser.py`, `intelligence/career_ai.py` |
| 8 | CV tailoring/ATS scoring | D2 | PARTIAL/MISSING | Tailoring works (has a real bug); ATS-compatibility scoring doesn't exist at all | `career/cv_tailor_service.py:7` (wrong related_name); ATS scoring: 0 matches repo-wide |
| 9 | Resume Builder (multi-version CVs) | D2 | INTEGRATE | `apps.resume.Resume` genuinely supports multi-version, but disconnected from CV-parse pipeline; auth bug (wrong localStorage key) | `ResumeBuilder.tsx:24-32` (`access_token` vs `usam_access`) |
| 10 | Resume export (PDF/DOCX) | D2 | BROKEN | DOCX "succeeds" without producing a file; PDF silently falls back to raw HTML if `xhtml2pdf` missing (not in requirements.txt) | `resume/views.py:250-278` |
| 11 | Skills/Knowledge Graph taxonomy | D2 | DONE | Real ESCO/O*NET-based taxonomy, hierarchical, embeddings, Arabic i18n | `skills/models.py:15-131` |
| 12 | Skill graph query engine | D2 | DONE (doc mismatch) | Real recursive-CTE SQL engine works; README claims Apache AGE graph DB is used — it never is | `skills/graph.py:1-202` vs `skills/README.md:80-108` |
| 13 | Skill Gap Analysis | D2/D6 | DONE | Real gap scoring, wired to a live endpoint | `career/skill_gap_analysis.py:1-312` |
| 14 | Scraping/Connector architecture | D3 | BROKEN AT RUNTIME | Well-designed orchestrator; `croniter` missing dependency crashes import of the entire tasks module | `scraper/orchestrator.py:14` |
| 15 | Job normalization | D3 | DONE (isolated) | Pure functions correct; call sites pass a removed field (`remote_type`) and crash | `scraper/tasks.py:224`, `orchestrator.py:323` |
| 16 | Deduplication | D3 | PARTIAL | 3 non-reconciled implementations; the pre-insert one is dead code (computed, never checked) | `scraper/pipeline/deduplicator.py:10-32` (dead) |
| 17 | Direct-Apply Verification Engine | D3 | DONE (logic)/BROKEN (reach) | Correctly rejects all named aggregators, 42/42 tests pass — but unreachable because ingestion never produces a `Job` row | `verification/stages/ats_fingerprint.py`, `engine.py` |
| 18 | Job Quality Engine (9 states) | D3 | MISSING | The 9-state model from `AGENTS.md` doesn't exist anywhere; state scattered across 3 uncoordinated fields | repo-wide search: 0 matches |
| 19 | Recurring re-verification (Celery beat) | D3 | PARTIAL | Beat entries exist (good), but 2 of 4 point into the broken module, and the working 2 check the wrong field | `verification/tasks.py:38-39` vs `jobs/models.py:250-255` |
| 20 | Keyword search (Typesense) | D4 | DONE | Real, health-checked, trust-score gated | `search/service.py:45-137` |
| 21 | Postgres fallback search | D4 | DONE | Automatic fallback, wired correctly | `search/plugins/postgres_plugin.py` |
| 22 | Semantic search (pgvector) | D4 | PARTIAL | Works and is wired; debug `print()`s left in prod code | `vectors/plugins/pgvector_plugin.py:202-204` |
| 23 | Vector infra "Qdrant" (documented primary) | D4 | MISSING | Zero Qdrant code exists anywhere; not even a dependency; README fiction | `vectors/README.md:7,50-52` |
| 24 | Hybrid search (RRF) | D4 | BROKEN | Calls a method that doesn't exist on `SearchService` → `AttributeError` → 500 on every call | `vectors/views.py:266-271` |
| 25 | Matching Engine (`job_matching.py`) | D4 | BROKEN | Import-broken, unwired to any URL, 2 more stale-field bugs even if import fixed | `intelligence/job_matching.py:10,113,148-149,184,346` |
| 26 | Recommendation Engine (career + search) | D4 | BROKEN/INTEGRATE | Two fully disconnected LightFM systems; both throw/degrade on stale fields | `career/recommendation_engine.py`, `search/recommendation_engine.py` |
| 27 | Application Engine (lifecycle) | D5 | DONE | Real model, knockout-bypass fix verified intact, status transitions work | `employers/models.py:166-216`; `jobs/views.py:483-623` |
| 28 | Employer/ATS Engine (job CRUD, registration) | D5 | PARTIAL | Registration/CRUD DONE; `stats()` 500s; `perform_update` edit-lock is a no-op | `employers/views.py:176-178, 263-271` |
| 29 | Talent Pool Engine | D5 | REFACTOR | Real, consent-gated pipeline (not the CV-upload anti-pattern); `TalentDiscovery` has a real consent gap | `employers/views.py:666-686` |
| 30 | Talent Intelligence / Candidate Ranking | D5 | BROKEN/INTEGRATE | Live path hardcodes 0.5 scores + fake knockout; the real AI-scoring service exists but has zero callers | `employers/views.py:566-663` vs `employers/ranking_service.py` |
| 31 | Assessment Engine | D6 | PARTIAL | Real MCQ+Judge0 grading (live-verified); no question-authoring UI; zero frontend | `assessment/views.py:118-236` |
| 32 | Interview Simulation Engine | D6 | PARTIAL/BROKEN | Text-mode flow DONE; `coding` type dead; stats endpoint 500s; 14/15 own tests fail | `interviews/views.py:404-433`; `interviews/coding_service.py` |
| 33 | Voice Engine | D6 | PARTIAL | Real cascaded pipeline code; non-functional — zero AWS IAM perms, missing settings | `interviews/voice_service.py` (live AccessDeniedException) |
| 34 | Career Coach (proactive) | D6 | PARTIAL/MISSING | Goal tracking DONE; the one proactive/continuous engine is fully built, zero callers | `rashid/proactive_service.py` (0 importers, not in Celery beat) |
| 35 | Rashid AI Engine (chat) | D7 | PARTIAL/REFACTOR | 3 disconnected implementations; the good tool-calling agent is orphaned from the live chat UI | `intelligence/agent.py` vs `rashid/service.py` |
| 36 | AI Model Router | D7 | BROKEN | Well-designed router adopted by exactly 1 call site; 4+ independent hardcoded-model-ID locations elsewhere | `intelligence/model_router.py` (1 caller); `bedrock_plugin.py:29-32` |
| 37 | AI Cost Control | D7 | PARTIAL/BROKEN | Token/cost capture real; the one admin cost dashboard throws `AttributeError` on load; a full budget service is dead code | `monitoring/views_ai_costs.py:33,40` |
| 38 | Research Engine | D7 | PARTIAL | Good source-traceable schema; only live path fabricates confidence, no real source URLs | `intelligence/research_engine.py:191-242` |
| 39 | Content/Trend Engine | D7 | DONE (core)/PARTIAL (deps) | Trend detection real & scheduled; BERTopic/content-gen soft-fail silently | `intelligence/trend_detection.py:35-133` |
| 40 | Knowledge Graph / RAG | D7 | PARTIAL/INTEGRATE | Graph-over-relational-tables is real; pgvector RAG infra exists but unused by Rashid entirely | `intelligence/knowledge_graph.py`; `vectors/service.py` (0 Rashid callers) |
| 41 | Notification Engine (frontend+backend) | D8 | REFACTOR | Frontend real (not a mock, correcting a stale claim); 2 disconnected backend models — the one written-to isn't the one read | `users/models.py:75` vs `notifications/models.py:97` |
| 42 | Automation/Workflow Engine (Celery beat) | D8 | PARTIAL | 17 scheduled tasks all resolve correctly (no phantom schedule); 2 real digest tasks never scheduled | `config/celery.py` (missing `send_notification_digest` entry) |
| 43 | Document Engine (CV pipeline stages) | D8 | PARTIAL | Upload→scan→parse→AI-structure wired end-to-end; OCR fallback unreachable (plugin order bug); local disk only, no index | `profiles/cv_parser.py:282-288` |
| 44 | Admin Control Plane | D9 | PARTIAL | Feature flags/rule engine/scraper+health dashboards all real; AI model list not admin-configurable; `PlatformConfig` has no REST endpoint | `intelligence/model_router.py:49-115`; `core/admin_urls.py` |
| 45 | Analytics Engine | D9 | PARTIAL | `EventLog` is the real, live system; `JobView`/`JobClick`/`SearchLog` are dead schema (0 writers) | `analytics/models.py:4-99` (0 writers) |
| 46 | Billing/Package Engine | D9 | MISSING | Zero `Subscription`/`Plan`/`Package`/payment code anywhere in the codebase | repo-wide search: 0 matches |
| 47 | Security/Audit (RBAC, tenant isolation, CORS) | D9 | PARTIAL-STRONG | Auth/RBAC/tenant-isolation/rate-limit/CORS substantively real; historical E-USAM bug class does NOT recur | `core/permissions.py:4-16`; `employers/views.py:218-221` |
| 48 | Observability/Monitoring | D9 | PARTIAL | Health checks/structlog/Sentry all real and working; Prometheus counters never incremented (dead instrumentation) | `core/services/prometheus_metrics.py:233-262` (0 callers) |
| 49 | Frontend Navigation/Routing | D10 | PARTIAL | Routes real; no client-side role gate for `/admin*`/`/app/employer/*`; 2 navbars show different items on the same session | `RequireAuth.tsx:4-15` (no role awareness) |
| 50 | Dynamic Application Forms | D10 | DONE | Wired end-to-end both applicant and employer side (corrects a stale roadmap claim) | `JobDetail.tsx:597-612`; `JobPostingForm.tsx:401-529` |
| 51 | Settings page | D10 | MOCK/BUILD | 100% non-functional shell — zero `onChange`/`onClick` anywhere, despite real backend endpoints existing unused | `Settings.tsx` (whole file) |

---

## 3. Cross-Cutting Patterns

Patterns that independently recurred across **multiple** domain reports — these are
architectural, not one-off bugs, and should be fixed once each rather than
whack-a-mole'd per occurrence.

| Pattern | Domains it recurs in | Representative instances |
|---|---|---|
| **Duplicated/parallel implementations of the same feature, disconnected** | D1, D2, D3, D4, D5, D6, D7, D8, D10 | 2 CV upload endpoints + 3 CV parsers (D2); 2 recommendation engines (D4); 2 ranking implementations (D5); 3 Rashid tool registries (D7); 2 notification models (D8); 2 navbars (D10); 3 anti-aggregator blocklists (D3); 2 `InterviewSession` models (D1) |
| **Stale field references after a migration renamed/removed a field** | D3, D4, D8 | `remote_type`→`work_arrangement` (D3, D4 — 4+ separate call sites); `is_active`→`status` on `Job` (partially fixed 2026-08-29, but D4 found 5 new instances and D8 found a whole file, `profiles/services.py`, the fix commit missed) |
| **Fully-built code with zero call sites ("orphaned in the write direction")** | D1, D3, D4, D5, D6, D7, D9 | `CareerBrain.update_from_profile()` (D1); pre-insert dedup hash (D3); `job_matching.py`/`ranking_service.py` (D4/D5); `ProactiveRashidService` (D6); `model_router.select_model()` (1 caller only, D7); `core/services/cost_reporting.py` (D7); Prometheus tracking decorators (D9) |
| **Real backend feature with zero frontend consumer ("orphaned in the read direction")** | D1, D6 | `OnboardingProgress` API (D1); Assessment Engine has no UI at all (D6) |
| **Documentation/README describes infrastructure that was never actually built** | D2, D4 | Apache AGE graph DB (D2 — README claims "✅ Completed", code never touches it); Qdrant as "primary" vector store (D4 — not even a dependency) |
| **AI model IDs hardcoded in multiple independent places instead of one router/config** | D2, D7, D9 | 5 separate hardcoded-model-ID locations found (`bedrock_plugin.py`, `agent.py`, `career/cv_parser.py`, `rashid/models.py`, `config/ai_config.py`) — matches `AGENTS.md`'s explicitly pre-flagged risk |
| **Silent failure / broad `except Exception` masking real errors as generic degradation** | D3, D4, D7, D8 | Scraper `Job.objects.create()` TypeError swallowed as a "failed to scrape" log line (D3); `profile.saved_jobs` FieldError silently swallowed, degrading recsys forever (D4); BERTopic/GPT-Researcher failures return empty silently (D7) |
| **Deprecated model/table left live "for safety," reachable if anyone imports it directly** | D1, D5 | `apps.users.UserProfile` (deprecated, still installed, still has migrations) (D1); `JobApplicationDetailSerializer` still reads the deprecated model, returns empty for current users (D5) |
| **Bare `fetch()`/local API client bypassing the shared auth-aware client** (the `client.ts`/`api.ts` bug `AGENTS.md` pre-flags) | D2, D8, D10 | `ResumeBuilder.tsx` (wrong localStorage key, D2); `NotificationPreferences.tsx` (no auth header at all, D8); implicitly the same duplication pattern one layer up in `Navbar.tsx`/`AuthNavbar.tsx` (D10) |
| **Multiple, disagreeing "completion %"/"score" calculators for the same underlying fact** | D1, D2 | 3 profile-completeness calculators (D2); `JobMatchScore` vs `TalentScore` as two separate "how good is this user" systems (D1) |
| **Prior status docs (roadmap, architect review) making claims later proven stale by direct code re-verification** | D1, D5, D9, D10 | `MASTER_STATE_AND_ROADMAP.md`'s `ActivityLog` "zero call sites" claim — false, 9 found (D9); its Prometheus/health-check/dashboard-orphaned claims — all 3 false (D9); its employer-nav-prefix and DynamicFormFields-dead-code claims — both false, already fixed (D10); `Profile.tsx` vs `ProfilePage.tsx` claim — stale (D1) |

---

## 4. Critical/Blocking Bugs (crash or effectively-crash in production)

Confirmed via live reproduction (pytest/boto3/ORM/tsc) where noted; otherwise
code-certain (unambiguous from direct reads, not yet reproduced live by the source
report).

| # | Bug | File:Line | Effect | Confirmed how | Report |
|---|---|---|---|---|---|
| 1 | `croniter` imported, not installed/in requirements | `scraper/orchestrator.py:14` | Entire `apps.scraper.tasks` module fails to import; **zero** scraper Celery tasks run | Live: `ModuleNotFoundError` | D3 |
| 2 | `Job.objects.create(remote_type=...)` — field removed by migration | `scraper/tasks.py:224`, `orchestrator.py:323` | Every scraped-job creation throws `TypeError`, swallowed by broad except | Live: `TypeError` reproduced | D3 |
| 3 | `orchestrator.scrape_all_sources()` called, method doesn't exist on class | `scraper/management/commands/run_scrapers.py:87` | Manual scrape command crashes | Code-certain | D3 |
| 4 | `VerificationEngine.verify_job()` never writes `Job.status` | `verification/engine.py:156-170` vs `jobs/views.py:289-295` | Rejected/aggregator jobs remain publicly visible | Code-certain | D3 |
| 5 | `SearchService.search()` doesn't exist (`search_jobs()` is the real method) | `vectors/views.py:266-271` | `GET` hybrid search endpoint → 500 on every call | Code-certain (AttributeError) | D4 |
| 6 | `from apps.vectors.services import vector_service` — wrong module/symbol | `intelligence/job_matching.py:10` | Module fails to import; never wired to any URL anyway | Code-certain | D4 |
| 7 | `job.remote_type`, `job.experience_required`, `profile.saved_jobs`, `job.job_type`/`job.is_remote` — none exist on current models | `search/recommendation_engine.py` (5 sites), `career/recommendation_engine.py:252-255`, `vectors/management/commands/index_jobs.py:93,97` | Recommendations 500 or silently degrade to zero signal; vector indexer command unusable | Code-certain | D4 |
| 8 | `JobApplication.objects.filter(job__employer=employer)` — no such relation | `employers/views.py:176-178` | `GET /api/v1/employer/profile/stats/` **500s for every employer**, every call | Live: `FieldError` reproduced | D5 |
| 9 | `perform_update` returns a `Response` from a hook DRF discards | `employers/views.py:263-271` | Draft/rejected-only edit lock is a silent no-op; published jobs editable | Code-certain | D5 |
| 10 | `views.py` missing `from django.db import models` | `interviews/views.py:404-433` (line 417) | `GET /api/v1/interviews/stats/` **500s every call** | Live: `NameError` reproduced | D6 |
| 11 | Bedrock `sonnet` alias uses a raw model ID needing an inference-profile ARN | `intelligence/bedrock_plugin.py:31` | Every AI call in Assessment/Interviews/CV/CareerBrain/Rashid silently degrades to fallback content | Live: `ValidationException` reproduced | D6 |
| 12 | AWS IAM user has zero Polly/Transcribe/S3 permissions; `AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` unset | `interviews/voice_service.py` | Voice interviews non-functional end-to-end | Live: `AccessDeniedException` reproduced | D6 |
| 13 | `JUDGE0_API_KEY` unset/invalid | `core/code_execution.py:19` | Coding-assessment grading non-functional | Live: HTTP 401 reproduced | D6 |
| 14 | `event.metadata` doesn't exist (real field is `.data`); `RashidUsage.input_tokens/output_tokens/created_at` don't exist | `monitoring/views_ai_costs.py:33,40-41,64-75` | The only admin AI-cost dashboard throws `AttributeError` on load | Code-certain | D7 |
| 15 | `Q(is_active=True)` / `.order_by('-posted_date')` — neither field exists on `Job` | `profiles/services.py:85,115,136,152` | Recommendation/similar-jobs endpoints 500 — same bug class as the 2026-08-29 "fixed" commit, in a file that fix missed | Code-certain (identical pattern to a verified-live sibling bug) | D8 |
| 16 | `from apps.notifications.models import Notification` — class doesn't exist there | `rashid/proactive_service.py:18` | Would `ImportError` if ever wired up; currently harmless (0 importers) | Code-certain | D8 |
| 17 | `ChoiceField(choices=UserNotificationSerializer.Meta.fields[11])` — indexes a field-name list, not choices | `notifications/serializers.py:115-122` | Bulk-update notification endpoint broken if hit | Code-certain | D8 |
| 18 | `useQuery(...).onSuccess` — removed in TanStack Query v5 | `frontend/src/pages/employer/JobPostingForm.tsx:37-56` | Editing an existing job posting: form silently never pre-fills | Live: `tsc --noEmit` type error + behavior reasoning confirmed | D10 |

---

## 5. Open-Source Repo Verdicts (consolidated)

| Repo | Domain | Verdict | One-line reason |
|---|---|---|---|
| `JOYCEQL/magic-resume` | D2 (CV/Resume) | **REJECT** | Commercial-license carve-out makes it legally unusable for this for-profit SaaS; also a frontend-only, no-backend tech-stack mismatch |
| `AmruthPillai/reactive-resume` (~41.7k★, MIT) | D2 (CV/Resume) | **REFERENCE** | No license blocker; its headless-Chromium "printer" microservice pattern is worth studying to fix this repo's fragile `xhtml2pdf` export |
| `OmkarPathak/pyresparser` | D2 (CV/Resume) | **REFERENCE** | NER-based parsing approach could strengthen the very shallow non-AI regex fallback, but otherwise unmaintained-feeling |
| `magicalapi/resume-parser-python` (and similar) | D2 (CV/Resume) | **REJECT** | Thin wrapper around a paid third-party API; no real code to reuse |
| `gorse-io/gorse` (~9.8k★, Go) | D4 (Search/Matching) | **ADAPT — long-term, not now** | Architecturally exactly the "one shared recsys" this repo needs, but adding it now (before consolidating the existing 2 broken engines) risks becoming a second "Qdrant README fiction" |
| `ngoanpv/DeepInterview` (Apache-2.0) | D6 (Interview/Voice) | **ADAPT (partial ideas)** | Its local-model (Ollama/Whisper/Kokoro) fallback tier and prep/live/post model-split pattern are directly relevant to this repo's Bedrock-outage resilience gap; don't adopt its LiveKit transport or hosted auth/billing |
| `IliaLarchenko/Interviewer` (Apache-2.0, Gradio) | D6 (Interview/Voice) | **REJECT (weak adapt at most)** | Gradio single-file app, architecturally incompatible with Django/DRF + React; only its multi-provider `.env` STT/LLM/TTS pattern is worth referencing |
| `santifer/career-ops` | D10 (Frontend/OSS eval) | **REJECT** | Personal Claude-Code CLI skill pack for one job-seeker, not a platform; no server, no multi-tenant model, nothing extractable except the "posting-legitimacy A-F score" concept |
| `MadsLorentzen/ai-job-search` | D10 (Frontend/OSS eval) | **REJECT** | Same category — fork-and-personalize template for one person's job hunt, no backend/DB/API to adopt |

---

## 6. Prioritized Implementation Phases

Every item below is sourced from one of the 10 domain reports — nothing new was
invented for this synthesis. Each item cites its origin report and file:line.

### Phase 0 — Critical bugs, security, compliance (block everything else)

| # | Item | Source | File:Line |
|---|---|---|---|
| 0.1 | Add `croniter` to `requirements.txt` + install; fix `run_scrapers.py:87`'s call to a nonexistent method | D3 | `scraper/orchestrator.py:14`; `run_scrapers.py:87` |
| 0.2 | Fix `remote_type=` → `work_arrangement=` at both scraper ingestion call sites | D3 | `scraper/tasks.py:224`, `orchestrator.py:323` |
| 0.3 | Make `VerificationEngine.verify_job()` write `job.status` (or a real quality-state field) on reject | D3 | `verification/engine.py:156-170` |
| 0.4 | Add an end-to-end scraper integration test (fixture ATS response → DB row → `VerificationResult`) so this class of bug can't silently regress | D3 | new test, per §recommendation |
| 0.5 | Fix `EmployerProfileViewSet.stats()` field name (`job__employer`→`job__employer_posting__employer`) | D5 | `employers/views.py:176-178` |
| 0.6 | Fix `apps/interviews/views.py` missing `from django.db import models` import | D6 | `interviews/views.py:404-433` |
| 0.7 | Fix `HybridSearchView` — call `search_jobs()` with a `SearchQuery` object, or add a compat `.search()` method | D4 | `vectors/views.py:266-271` |
| 0.8 | Fix `apps/profiles/services.py` stale `is_active`/`posted_date` fields (same class as the already-"fixed" bug, missed by that commit) | D8 | `profiles/services.py:85,115,136,152` |
| 0.9 | Fix stale `remote_type`/`experience_required`/`saved_jobs`/`job_type`/`is_remote` references across both recommendation engines + `job_matching.py` + `index_jobs.py` | D4 | see Bug table row 7 |
| 0.10 | Fix or provision the Bedrock `sonnet` alias with a proper inference-profile ARN — highest-leverage single fix in the whole platform | D6/D7 | `bedrock_plugin.py:31` |
| 0.11 | Grant AWS IAM user (`speckit-user`) `polly:SynthesizeSpeech`, `transcribe:*`, S3 read/write; set `AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` | D6 | `interviews/voice_service.py` |
| 0.12 | Set a valid `JUDGE0_API_KEY` | D6 | `core/code_execution.py:19` |
| 0.13 | Fix employer role assignment — `EmployerRegistrationView` must set `User.role = "employer"` | D1 | `employers/views.py:53-94` |
| 0.14 | Close `TalentDiscoveryViewSet` consent gap — add the same `is_discoverable` check used in `add_candidate` | D5 | `employers/views.py:666-686` |
| 0.15 | Human action: confirm AWS key `AKIAYK...TGPY` rotation status in IAM Console (code cannot verify this) | D9 | `.env` (not read, per instruction) |
| 0.16 | Fix `apps/monitoring/views_ai_costs.py` field references (`event.metadata`→`.data`; `RashidUsage` field names) | D7 | `monitoring/views_ai_costs.py:33,40-41` |
| 0.17 | Fix `JobPostingViewSet.perform_update` no-op edit-lock (raise `ValidationError` instead of returning a discarded `Response`) | D5 | `employers/views.py:263-271` |

### Phase 1 — Foundational/architectural consolidation

| # | Item | Source | File:Line |
|---|---|---|---|
| 1.1 | Decide `CareerBrain`'s fate: wire `update_from_profile()` into a signal/Celery task fired on `CareerProfile`/`CareerUserSkill`/`JobApplication`/`InterviewSession` writes, or formally retire it | D1 | `career/models.py:774-830` |
| 1.2 | Consolidate the 3 CV parsers (`profiles/cv_parser.py`, `career/cv_parser.py`, `intelligence/career_ai.py`) into one canonical parser + schema | D2 | see D2 §1.1–1.4 |
| 1.3 | Consolidate the 2 CV upload endpoints into one | D2 | `profiles/views.py:83-100`; `career/cv_parser_views.py:43-167` |
| 1.4 | Consolidate the 3 profile-completeness calculators, keep `career/completeness_calculator.py` | D2 | D2 §1.6 |
| 1.5 | Delete or wire `job_matching.py` and `ranking_service.py` — do not leave dead-but-well-designed modules unresolved | D4/D5 | `intelligence/job_matching.py`; `employers/ranking_service.py` |
| 1.6 | Merge the two recommendation engines into one; migrate `career` and `search` endpoints to the survivor | D4 | `career/recommendation_engine.py`; `search/recommendation_engine.py` |
| 1.7 | Unify the 3 anti-aggregator blocklists into the existing-but-unused `BlockedDomain`/`ApprovedATS` admin models | D3 | `verification/models.py:91-181` (currently unread by any check) |
| 1.8 | Build the 9-state Job Quality Engine field (`AGENTS.md`'s Active/Probably active/.../Direct-source verified) and migrate `Job.status`/`is_expired`/`VerificationResult.status` into it | D3 | new field, migrate 3 existing sources of truth |
| 1.9 | Deprecate `apps.users.UserProfile` for real — schema-level, not just an import alias; migrate `min_match_score` (currently permanently lost for pre-consolidation users) | D1 | `users/models.py:112-183`; `career/migrations/0004_migrate_userprofile_data.py` |
| 1.10 | Reconcile the 3 skill representations (`CareerProfile.skills` flat, `CareerUserSkill` structured, `CareerBrain.skills`) into one write path | D1/D2 | `career/models.py:111-114,297-372`; `career_brain_service.py:201-214` |
| 1.11 | Force every AI call site through `model_router.select_model()`; build `MODEL_ALIASES` dynamically from `list_foundation_models()` instead of a hardcoded dict; delete the second alias table in `agent.py` | D7 | `intelligence/model_router.py`; `bedrock_plugin.py:29-32`; `agent.py:39-49` |
| 1.12 | Point the in-app notification read path at `apps.notifications.UserNotification` (the system real events actually write to), retiring `apps.users.Notification` | D8 | `users/models.py:75`; `notifications/models.py:97` |
| 1.13 | Consolidate the 3 Rashid tool registries (`RASHID_TOOLS`, `ToolRegistry`, `agent.py`'s `@agent.tool`s) into one, and migrate the live chat path (WebSocket/REST) onto the tool-calling `agent.py` | D7 | `rashid/tools.py`; `intelligence/tools.py`; `intelligence/agent.py` |
| 1.14 | Collapse `Navbar.tsx`/`AppLayout` and `AuthNavbar.tsx`/`Layout` into one canonical pair | D10 | `components/Navbar.tsx`; `components/AuthNavbar.tsx` |
| 1.15 | Add a client-side role gate (`RequireRole`/`RequireAdmin`/`RequireEmployer`) wrapping `RequireAuth` for `/admin*` and `/app/employer/*` | D10 | `components/RequireAuth.tsx:4-15` |
| 1.16 | Reconcile `source_url` vs `direct_apply_url` vs `source_raw_url` field semantics; point recurring liveness checks at the canonical one | D3 | `verification/tasks.py:38-39,48-49`; `jobs/models.py:231,250-255` |

### Phase 2 — Feature completion

| # | Item | Source | File:Line |
|---|---|---|---|
| 2.1 | Schedule `ProactiveRashidService.check_user_triggers()` in Celery beat if continuous coaching is a real product feature | D6 | `rashid/proactive_service.py` |
| 2.2 | Wire `CareerBrainService.update_brain()` to fire automatically (signal or beat task) instead of only on explicit `POST` | D6 | `career/career_brain_service.py:154-199` |
| 2.3 | Fix `ResumeBuilder.tsx`'s localStorage key mismatch (`access_token` vs `usam_access`) so its own local `apiFetch` actually authenticates | D2 | `ResumeBuilder.tsx:24-32` |
| 2.4 | Fix resume DOCX export (currently reports success, produces nothing) and PDF export's silent HTML fallback (missing `xhtml2pdf` dep) | D2 | `resume/views.py:250-278` |
| 2.5 | Add `easyocr`/`pdf2image`/`xhtml2pdf` to `requirements.txt`; fix CV-parser plugin order so OCR is actually reachable for scanned PDFs (Docling currently always wins first for `.pdf`) | D2/D8 | `profiles/cv_parser.py:282-288` |
| 2.6 | Seed `ResumeTemplate` data — currently no fixture/seed command, `GET /resume/templates/` returns empty on a fresh DB | D2 | `apps/resume/` |
| 2.7 | Build `KnockoutQuestionResponse` (candidate-answer capture) and real evaluation, or deprecate `KnockoutQuestion` in favor of the working dynamic-form knockout | D5 | `employers/models.py:224-272` |
| 2.8 | Build hiring-team/multi-seat employer model if multi-user employer accounts are a requirement (currently 1 user = 1 employer profile, hard limit) | D5 | `employers/models.py:11-15` |
| 2.9 | Add `send_notification_digest` and `send_weekly_career_digest` to `config/celery.py`'s `beat_schedule` — both fully implemented, neither scheduled | D8 | `notifications/tasks.py:67-124`; `emails/tasks.py:351-417` |
| 2.10 | Wire `coding_interview_service` to the `coding-question/problem/solution` URLs (currently all alias the generic `start` action), or delete the dead module and misleading URL names | D6 | `interviews/coding_service.py`; `interviews/urls.py:18-20` |
| 2.11 | Build an Assessment Engine frontend — currently API-only, zero UI | D6 | n/a (new frontend page) |
| 2.12 | Fix `JobPostingForm.tsx`'s React Query v5 `onSuccess`-on-`useQuery` bug (replace with `useEffect` on `data`) | D10 | `JobPostingForm.tsx:37-56` |
| 2.13 | Wire `Settings.tsx` to the real, already-existing `updateMe`/`changePassword`/`deleteAccount` endpoints — currently zero data binding either direction | D10 | `Settings.tsx`; `services/auth.ts:87-110` |
| 2.14 | Fix `CompanyProfile.tsx`'s company-scoped jobs query (currently fetches 20 jobs platform-wide and filters client-side — misses jobs beyond page 1) | D10 | `CompanyProfile.tsx:37-43` |
| 2.15 | Add an employer acquisition funnel entry point ("For Employers"/"Post a Job" CTA) — currently zero discoverable link to `/app/employer/register` anywhere in nav/footer/landing | D10 | n/a (new UI) |
| 2.16 | Add a `PlatformConfig` REST endpoint (`admin_urls.py`) — the model is real and admin-controllable in principle but only reachable via Django-native `/admin/`, invisible to the SPA admin dashboard | D9 | `core/models.py:109-197`; `core/admin_urls.py` |
| 2.17 | Decide the fate of `config/ai_config.py` (a fully dead, unwired cheaper-Llama cost-optimization module claiming ~$112/mo savings) — wire it into the router or delete it | D7 | `config/ai_config.py:1-133` |
| 2.18 | Build ATS-compatibility scoring for CVs (keyword density, formatting/parseability) — currently doesn't exist at all | D2 | n/a (BUILD) |
| 2.19 | Build a `LearningResource` catalog model so skill-gap recommendations reference real courses instead of hardcoded generic strings | D2 | `career/skill_gap_analysis.py:223-269` |
| 2.20 | Wire `VectorService.semantic_search` into `research_engine.py` and/or Rashid's `agent.py` tools — real RAG infra currently unused by the one feature area that needs it most | D7 | `vectors/service.py`; `intelligence/research_engine.py` |
| 2.21 | Configure GPT-Researcher's search-provider API key(s) so real cited source URLs actually fire, or explicitly label the internal-data fallback's confidence score as non-computed | D7 | `intelligence/research_engine.py:148-242`; `.env.example` |
| 2.22 | **Build a Billing/Package Engine from scratch** if monetization is a near-term goal: `SubscriptionPlan`/`Package`/`Subscription` models, payment-gateway webhooks, `HasActiveSubscription` permission class | D9 | n/a (MISSING entirely) |

### Phase 3 — Polish / cleanup / consistency

| # | Item | Source | File:Line |
|---|---|---|---|
| 3.1 | Delete confirmed-dead code: pre-insert dedup hash computation, `apps/core/services/cost_reporting.py`, dead `NotificationCenter.tsx`, unused pieces of `config/ai_config.py` if not adopted | D3/D7/D8 | see respective sections |
| 3.2 | Remove leftover debug `print()`s in `pgvector_plugin.py:202-204` | D4 | `vectors/plugins/pgvector_plugin.py:202-204` |
| 3.3 | Standardize interview app response envelopes to `{"success","data"}` (fixes 14/15 currently-failing own tests) | D6 | `interviews/views.py`; `interviews/tests/test_api.py` |
| 3.4 | Remove or build out `EmployerDashboard.tsx`'s "Coming soon" dead UI stubs ("View All", "Review New Applications") | D10 | `EmployerDashboard.tsx:160-162,220-234` |
| 3.5 | Wire a `ScopedRateThrottle` to actually consume the declared-but-unused `burst` (10/sec) rate | D9 | `config/settings/base.py:160-167` |
| 3.6 | Wire `track_http_request`/`track_ai_request` as real middleware, or delete the dead Prometheus instrumentation decorators | D9 | `core/services/prometheus_metrics.py:233-262` |
| 3.7 | Fix `status='active'` vs `is_active=True` filter inconsistency within `trend_detection.py` itself (recent vs previous window use different fields) | D7 | `intelligence/trend_detection.py:45,53,97,105` |
| 3.8 | Delete or wire `apps.analytics.models` (`JobView`/`JobClick`/`SearchLog`) — zero writers, dead schema | D9 | `analytics/models.py:4-99` |
| 3.9 | Migrate the analytics dashboard from `@staff_member_required` + Django templates to `IsAdminRole` + JSON so the JWT-based SPA admin can actually consume it | D9 | `analytics/views_dashboard.py` |
| 3.10 | Fix `CourseAdvisorTool`'s hardcoded course-list stub or its misleading "fetches from edu.usamif.com" docstring | D6/D7 | `rashid/tools.py:385-404` |
| 3.11 | Fix `NotificationPreferences.tsx`'s bare `fetch()` (no auth header) — route through `apiRequest()` like every other page | D8 | `NotificationPreferences.tsx:50,59` |

---

## 7. What NOT to Touch

Confirmed **DONE**/working per the 10 reports — preserve these; do not let future work
regress them, and do not re-flag them as broken without re-verifying live first.

| Area | Why it's solid | Source |
|---|---|---|
| JWT auth core (register/login/logout/refresh/blacklist/password-reset/email-verify) | Real, tested, correctly implemented anti-enumeration pattern | D1 |
| Knockout bypass fix (dynamic-form flavor: `custom_form_fields[].knockout_value`) | Verified server-side-enforced, no client bypass possible | D5 |
| Talent pool privacy gate (`is_discoverable`) for `TalentPoolViewSet.add_candidate` + non-applicant `CandidateRankingViewSet.rank()` | Verified intact per two independent code paths | D5 |
| Direct-apply anti-aggregator enforcement — employer-posting side (`domain_verification.py`) | Real, includes SSRF protection, recurring re-verify command | D5 |
| ATS gap analysis (`ats_gap_service.py`) | Deterministic, rule-based, no AI dependency, testable | D5 |
| Typesense keyword search + Postgres fallback | Real, health-checked, trust-score gated, defensively designed | D4 |
| Skills taxonomy (ESCO/O*NET import, hierarchy, embeddings, Arabic i18n) | Real, properly normalized, not a flat tag list | D2 |
| Skill graph query engine's actual recursive-CTE SQL implementation | Working, dependency-free, correctly bounded BFS | D2 |
| Skill extraction pipeline (Claude-based, MD5-cached, ESCO-fuzzy-mapped, keyword fallback) | Real, well-designed degrade path | D2 |
| CV upload security (extension allow-list, magic-byte check, path-traversal guard, ClamAV fail-closed) | Real defense-in-depth, correct fail-closed posture | D2/D8 |
| Assessment MCQ + Judge0 coding-grading pipeline logic | Live-verified end-to-end (MCQ); Judge0 code correct (only the API key is missing) | D6 |
| Interview text-mode flow logic (technical/behavioral/system_design/case_study) | Live-verified end-to-end; degraded content quality is an AI-outage issue, not a logic bug | D6 |
| `CareerGoal`/`CareerGoalAction` CRUD + analytics | Real, correct ORM aggregation, fully wired | D6 |
| `SkillGapAnalyzer` | Real gap-severity scoring, wired to a live endpoint | D2/D6 |
| Celery beat schedule integrity (17 entries, all resolve to real functions) | No phantom automation — contradicts any "automation is fake" claim at the schedule level | D8 |
| `is_active`→`status` fix in `apps/emails/{tasks,matching}.py` (commit `3a92ce0`) | Verified landed cleanly, no regressions in those two files | D4/D8 |
| Admin feature flags, rule engine, scraper health dashboard, system health monitor | All genuinely check live state, not stubs | D9 |
| Security: RBAC, tenant isolation, global `IsAuthenticated` default, CORS allow-list | Substantively real; the specific E-USAM missing-`permission_classes` bug class does **not** recur here | D9 |
| Health checks (`/health/`, `/health/detailed/`) — real DB/Redis roundtrips, conditional 503 | Already fixed since an older snapshot; roadmap claiming otherwise is stale | D9 |
| Structured logging (`structlog` + JSON formatter) and Sentry integration | Both genuinely wired, not superficial | D9 |
| SavedJobs and Alerts pages (frontend + backend) | Fully wired end-to-end, real models, real CRUD | D10 |
| Dynamic Application Forms (applicant `JobDetail.tsx` + employer `JobPostingForm.tsx`) | Wired end-to-end both sides — corrects a stale "dead code" claim | D10 |
| Employer-portal internal navigation (`/app/employer/...` links) | All correctly prefixed — corrects a stale roadmap bug claim | D10 |
| Company registration/lookup, job posting CRUD lifecycle (draft→published→closed→reopen) | Real, correctly modeled state machine (aside from the one `perform_update` no-op bug, Phase 0) | D5 |

---

## Appendix — Report provenance

| Report | Scope |
|---|---|
| D1 | Identity/Auth/User Profile/Career Identity/Onboarding |
| D2 | CV/Resume Engine + Skills/Knowledge Graph |
| D3 | Job Pipeline: Scraping/Connectors/Normalization/Dedup/Direct-Apply Verification/Job Quality |
| D4 | Search + Matching + Recommendation Engines |
| D5 | Employer/ATS + Talent Pool + Talent Intelligence + Ranking + Applications |
| D6 | Assessment + Interview Simulation + Voice + Career Coach |
| D7 | Rashid AI + AI Model Router + AI Cost Control + Research/Content/Trend Engine |
| D8 | Notifications + Automation/Workflow + Document Engine |
| D9 | Admin Control Plane + Security/Audit + Analytics + Billing + Observability |
| D10 | Frontend Navigation/UX + Cross-Cutting Production-Readiness Spot-Check |

All 10 reports live at `audit/D{1-10}_*.md`. This document is the synthesis; consult
the originals for full narrative detail behind any row above.

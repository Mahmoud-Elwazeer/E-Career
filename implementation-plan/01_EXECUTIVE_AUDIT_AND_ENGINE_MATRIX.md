# 01 — Executive Audit & Engine Matrix (code-verified)

**Verified against:** `m:\job already web for jobs\E-Career` @ `frontend-renewal-2026-09` (= `development` `6aa73b9`).
Backend = Django/DRF, 26 apps. Frontend = React 18 + Vite + shadcn/Radix + TanStack Query + framer-motion + i18next (EN/AR). Backend suite: **497 pytest pass, 2 skipped**.

---

## A. Executive summary

E-Career is **substantially built** — far beyond an MVP. The dominant failure mode is **not "unbuilt"**; it is **built-and-disconnected** or **built-once-and-not-wired**, plus **stale planning docs** that no longer match code. The platform has real engines for auth, jobs, profiles, career, skills, resume, assessment, interviews, Rashed, intelligence, search, vectors, scraper, verification, notifications, analytics, employers, and admin.

**Top verified realities (correcting stale doc claims):**
- Scraper `croniter==2.0.1` **is** pinned in `requirements.txt` — the "module missing, scraper never runs" claim is **stale**.
- `VerificationEngine.verify_job()` **does** write `job.status` + `quality_state` on reject/duplicate (`verification/engine.py:55-81,175`) — the "never writes status" claim is **stale**.
- Employer registration assigns the employer role; hybrid search calls `search_jobs()`; scraper persists `work_arrangement` — all previously-flagged bugs are **already fixed** on this branch.
- Billing: `SubscriptionPlan`/`CompanySubscription` models + admin API **exist**, but **no entitlement check gates any employer action** and there is **no payment provider** → billing is **BACKEND-ONLY/DISCONNECTED**.

**Biggest real risks (P0/P1):**
1. **Three parallel matching/recommendation implementations** (`career/scoring_engine.py`, `search/recommendation_engine.py`, `intelligence/recommendation_service.py`) — violates single-source-of-truth; must consolidate.
2. **Billing disconnected** — plans exist but entitlements gate nothing; monetization is non-functional end-to-end.
3. **Rashed is a 5-tool assistant**, not the tool-calling agent over platform services the spec requires (~20+ tools).
4. **AI Model Router bypassed** — 6 hard-coded model IDs vs 3 router calls in `intelligence/`.
5. **Frontend presentation** weak/inconsistent (being addressed on this branch), plus large divergent git branches (`main` 43, `develop` 44).
6. **No verified live data pipeline run** — scraper/verification code exists but no evidence real jobs flow end-to-end.

**Strongest existing parts:** auth + accounts (GDPR, extension tokens), jobs model + quality_state, verification pipeline (6 stages), scraper ATS adapters (11 platforms), career scoring engine (1913 lines), skills taxonomy (ESCO/O*NET), admin control plane (13+ endpoints, 39 tests), test suite (497 passing).

---

## B. Engine matrix — all 58 canonical engines (code-verified)

Legend: status · decision · priority. "Sub-caps" = `11.md` refinements folded here.

| # | Engine | Verified location | Status | Decision | Pri |
|---|---|---|---|---|---|
| 01 | Identity | `accounts/` (views, models, permissions, models_gdpr, extension_tokens) | DONE-BUT-WEAK | KEEP+HARDEN | P1 |
| 02 | User Profile | `profiles/`, `users/` (dual profile models) | PARTIAL/DUPLICATED | MERGE→canonical CareerProfile | P1 |
| 03 | Career Identity | `career/models.py` CareerProfile/CareerBrain, `career_brain_service.py` | PARTIAL | INTEGRATE (wire CareerBrain sync) | P1 |
| 04 | CV | `resume/` (CRUD+export templates), `profiles/cv_parser.py`, `career/cv_parser_views.py` | PARTIAL/DUPLICATED | MERGE parsers→one | P1 |
| 05 | Cover Letter | `career/cover_letter_service.py` + views | DONE-BUT-WEAK | KEEP+IMPROVE | P2 |
| 06 | Skills | `skills/` (ESCO/O*NET import, graph, extraction) | DONE-BUT-WEAK | KEEP; add Skills Graph relationships | P1 |
| 07 | Assessment | `assessment/` (models, views, serializers) | PARTIAL | INTEGRATE (frontend wired via Assessments.tsx); add integrity | P2 |
| 08 | Talent Qualification | `career/` + `employers/ranking_service.py` | PARTIAL | BUILD explicit qualification state | P1 |
| 09 | Talent Pool | `employers/models.py` TalentPool/TalentDiscovery/CandidateRanking + `ranking_service.py` (613L) | PARTIAL | IMPROVE+INTEGRATE (lifecycle, consent, shortlist, compare) | P1 |
| 10 | Job Discovery | `jobs/` + `scraper/` Source registry | DONE-BUT-WEAK | KEEP | P1 |
| 11 | Scraping | `scraper/orchestrator.py` + 11 ATS adapters + pipeline | BUILT (runtime-unverified) | KEEP; verify live run | P1 |
| 12 | Connector | `scraper/ats/*`, `intelligence/` connectors, `core/github_service.py` | PARTIAL | REFACTOR→connector abstraction | P2 |
| 13 | Job Normalization | `scraper/pipeline/normalizer.py` | DONE | KEEP | P1 |
| 14 | Deduplication | `scraper/pipeline/deduplicator.py`, `verification/deduplicator.py` | PARTIAL/DUPLICATED | MERGE | P2 |
| 15 | Verification | `verification/engine.py` + 6 stages | DONE (logic) | KEEP; schedule recurring | P1 |
| 16 | Direct Apply | `jobs/` apply redirect, `employers/quick_apply_service.py`, `DirectApplyBadge` | DONE-BUT-WEAK | KEEP+HARDEN honesty | P0 |
| 17 | Search | `search/` (typesense + postgres plugins, nlp_parser) | DONE-BUT-WEAK | KEEP; add semantic/hybrid to UI | P1 |
| 18 | Matching | `career/scoring_engine.py` (1913L, 13 fns) + `search/` + `intelligence/` | PARTIAL/DUPLICATED | MERGE→canonical MatchingService; split eligibility/ranking | P0 |
| 19 | Recommendation | `career/views_recommendations.py`, `search/recommendation_engine.py`, `intelligence/recommendation_service.py` | PARTIAL/DUPLICATED | MERGE + BUILD feedback loop | P1 |
| 20 | Application | `employers/models.py` JobApplication + `users/` new endpoints + `jobs/views.py` | DONE-BUT-WEAK | KEEP; verify state machine | P1 |
| 21 | Employer | `employers/` (views, serializers, teams, permissions) | DONE-BUT-WEAK | KEEP+INTEGRATE billing | P1 |
| 22 | Candidate Intelligence | `career/`, `intelligence/career_ai.py` | PARTIAL | INTEGRATE (evidence-based) | P2 |
| 23 | Interview | `interviews/` (models, service) | PARTIAL | KEEP; add scheduling | P2 |
| 24 | Interview Simulation | `interviews/service.py` + `InterviewPractice.tsx` | DONE-BUT-WEAK | KEEP | P1 |
| 25 | Voice | `interviews/voice_service.py` | PARTIAL (provider perms unverified) | RESEARCH/HARDEN | P2 |
| 26 | Career Coach | `career/` goal_api + `rashid/` | PARTIAL | INTEGRATE with Career Identity | P2 |
| 27 | Rashed | `rashid/` (service, tools.py=5 tools, consumers, agent) + `intelligence/agent.py` | PARTIAL/DUPLICATED | MERGE surfaces; BUILD agent tools (~20) | P0 |
| 28 | AI Gateway | `intelligence/service.py`, `bedrock_plugin.py`, `llm_plugin.py` | PARTIAL | REFACTOR→single gateway | P1 |
| 29 | Model Router | `intelligence/model_router.py` (used 3x; 6 hardcoded IDs bypass it) | PARTIAL/BYPASSED | INTEGRATE (route all AI calls) | P1 |
| 30 | Research | `intelligence/research_engine.py` | DONE-BUT-WEAK | KEEP | P3 |
| 31 | Knowledge/RAG | `intelligence/knowledge_graph.py`, `vectors/` | PARTIAL | DEFER unless value proven | P3 |
| 32 | Content/Trend | `intelligence/trend_detection.py`, `content_pipeline.py`, `marketing_intelligence.py` | DONE-BUT-WEAK | KEEP (separate from recruitment) | P3 |
| 33 | Notification | `notifications/` + `users/` inbox (two namespaces) | PARTIAL/DUPLICATED | MERGE→one canonical | P1 |
| 34 | Automation | `config/celery.py` beat + app tasks | DONE-BUT-WEAK | KEEP; add workflow/SLA rules | P2 |
| 35 | Document | `resume/export_service.py`, `core/upload_security.py`, `document_processor.py` | PARTIAL | INTEGRATE (scan/OCR/retention) | P2 |
| 36 | Analytics | `analytics/` (tracking, dashboard views) + `EventLog` | DONE-BUT-WEAK | KEEP; wire dead JobView/JobClick | P2 |
| 37 | Package/Entitlement | `core/models.py` SubscriptionPlan/CompanySubscription + admin_api | BACKEND-ONLY/DISCONNECTED | BUILD entitlement enforcement | P1 |
| 38 | Admin Control Plane | `core/admin_api_views.py` (2100L), `admin_urls.py`, `AdminDashboard.tsx` | DONE-BUT-WEAK | REFACTOR (split monolith, URL tabs) | P1 |
| 39 | Security/Audit | `core/permissions.py`, `rate_limiting.py`, `security_audit.py`, GDPR, `ActivityLog` | DONE-BUT-WEAK | HARDEN (tenant isolation, object perms) | P0 |
| 40 | Observability | `core/monitoring_service.py`, `prometheus_metrics.py`, `monitoring/` health | PARTIAL | INTEGRATE (wire dead metrics) | P2 |
| 41 | Finance/Ledger | — | MISSING | BUILD (if monetization near-term) | P2 |
| 42 | Subscription | `core/` models present, no lifecycle enforcement | BACKEND-ONLY | INTEGRATE | P1 |
| 43 | Pricing | `core/` SubscriptionPlan (admin-configurable ✓) | DONE-BUT-WEAK | KEEP; build Pricing page | P1 |
| 44 | Billing/Invoice | — | MISSING | BUILD | P2 |
| 45 | Payment Provider | — | MISSING | BUILD (Stripe/Paymob abstraction) | P1 |
| 46 | Refund | — | MISSING | DEFER | P3 |
| 47 | Credit/Usage | `intelligence/` AI usage tracking (partial) | PARTIAL | INTEGRATE | P2 |
| 48 | Employer Branding | `employers/` company profile | DONE-BUT-WEAK | KEEP | P3 |
| 49 | Verification/Trust | `verification/` + `employers/domain_verification.py` | DONE-BUT-WEAK | KEEP | P1 |
| 50 | Referral | — | MISSING | DEFER | P3 |
| 51 | Career Development | `career/goal_api.py`, LearningResource model | PARTIAL | INTEGRATE | P2 |
| 52 | Learning Integration | `career/` seed_learning_resources | PARTIAL | KEEP | P3 |
| 53 | Event/Career Fair | — | MISSING | DEFER | P3 |
| 54 | API/Developer Platform | drf-spectacular schema/docs | DONE-BUT-WEAK | KEEP | P3 |
| 55 | Integration/Webhook | `events/` (consumers, emitter, types) | PARTIAL | BUILD webhook + event bus | P2 |
| 56 | Feature Flag/Config | `core/models.py` FeatureFlag + PlatformConfig | DONE-BUT-WEAK | KEEP; wire to UI | P2 |
| 57 | Consent/Privacy | `accounts/models_gdpr.py`, `core/gdpr_service.py`, is_discoverable | DONE-BUT-WEAK | KEEP+HARDEN | P0 |
| 58 | Data Retention/Deletion | `accounts/tasks_gdpr.py`, `core/gdpr_service.py` | PARTIAL | INTEGRATE (per-type policies) | P2 |

### Folded sub-capabilities (from `11.md`) — target engine
- Recruitment Workflow State Machine, SLA/Escalation → **#34 Automation** + new state fields (P2)
- Candidate 360 single record → **#03 Career Identity** view aggregation (P1)
- Skills/Competency Graph → **#06 Skills** (relationships/hierarchy) (P1)
- Evidence Engine (Signal→Evidence→Score→Explanation→Confidence) → **#03/#18** (P0 for explainability)
- Candidate Verification, Fraud/Abuse, Assessment Integrity → **#49/#39/#07** (P2)
- Interview Scheduling (calendar) → **#23** (P2)
- Communication/Engagement, Outreach/Sourcing, Employer/Talent CRM → **#33/#09/#21** (P2)
- Requisition Mgmt, JD Intelligence, Ghost-Job → **#21/#13/#15** (P2)
- Ranking (separate from Matching), Recommendation Feedback Loop → **#18/#19** (P1)
- Talent Pool Lifecycle/Filtration/Shortlist/Comparison/Scorecard → **#09** (P1)
- Explainability, Model Governance, Agent Orchestration, Human-in-loop, Bias/Fairness, Evaluation → **#27/#28/#29** (P1)
- Tenant Isolation, Permissions → **#39** (P0)
- File Intelligence, Notification Orchestration → **#35/#33** (P2)
- Import/Export (jobs has `import_export_admin`), Bulk Ops → **#38** (P2)
- Experimentation/AB, Recovery/Resilience → cross-cutting (P3/P2)
- Market/Employer/Application Intelligence → **#36/#22** (P3)

---

## C. Frontend audit (page-by-page summary)

30 pages, 12 services, shadcn/Radix design system. Detailed redesign plan already in `frontend/FRONTEND_REDESIGN_PLAN.md`. Verified state: green gate (lint 0 errors, 25/25 tests, build OK, entry bundle 475 kB after code-split).

- **Wired end-to-end (KEEP+polish):** Jobs, JobDetail, Login, Profile, Settings, EmployerDashboard, Recommendations, Notifications, NotificationPreferences, Applications, SavedJobs, Alerts, TalentScore, SalaryInsights, Assessments, InterviewPractice, ResumeBuilder, RashidChat, TalentSearch, CompanyProfile.
- **Weak/missing UI for existing backend:** skills taxonomy browser, vector/semantic search UI, admin sub-sections (many `/admin-api/` endpoints have no page), Pricing page (MISSING), Requisition/CRM (MISSING).
- **Negative-space (buttons/pages w/o backend or vice-versa):** see `02`.

## D. Backend / DB / API / Security / Infra / Testing (headlines)

- **DB:** dual profile models (`users.UserProfile` deprecated vs `career.CareerProfile`) — consolidate. `quality_state` 9-state field exists on Job. Migrations clean.
- **API:** 23 mounted routers under `/api/v1/`; drf-spectacular schema present. Two notification namespaces + two Rashed namespaces = contract duplication.
- **Security:** RBAC + rate limiting + GDPR present; **multi-tenant isolation not enforced at query level** (P0 to verify/harden); object-level perms partial.
- **Infra:** Docker compose (Postgres/Redis/Typesense/Celery), CI runs backend tests + frontend lint/test/build. Docker daemon not run in audit → live-service behavior UNKNOWN.
- **Testing:** 497 backend tests pass; frontend 25 tests. Missing: E2E candidate/employer journeys, security/tenant-isolation tests, matching/dedup unit coverage.

Full gap-by-gap detail and decisions: **`02_GAP_REGISTER_AND_DECISIONS.md`**. Sequence: **`03_ROADMAP_AND_INTEGRATION.md`**.

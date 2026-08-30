# Phase 7 — Admin Control Plane + Platform Governance Audit

> Produced: 2026-08-30
> Method: Automated code inspection of every admin-related file across
> `backend/` and `frontend/`, cross-referenced against the owner's 30-section
> mandate in `audit/prompts/PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md`.
> Every verdict is grounded in file:line citations from the CURRENT codebase.

---

## 1. Section-by-Section Classification

### Classification Key

| Verdict | Meaning |
|---------|---------|
| **DONE** | Fully implemented, no work needed |
| **PARTIAL** | Core logic exists but missing admin visibility or controls |
| **MISSING** | No code found — needs BUILD |
| **INTEGRATE** | Backend exists, needs surfacing in the React admin SPA |

### Master Classification Table

| § | Section | Verdict | Summary | Key Evidence |
|---|---------|---------|---------|--------------|
| 1 | Owner-Level Control | **PARTIAL** | React admin SPA exists (8 tabs) but the 3-layer auth split (Django admin / Django-template staff views / React DRF SPA) means no single unified control plane | `AdminDashboard.tsx` (553 lines, 8 tabs), `core/admin_views.py` (6 DRF views), `scraper/admin_views.py` (Django template, `@staff_member_required`) |
| 2 | User Management | **PARTIAL** | Admin REST CRUD exists (list/create/update/soft-delete/ban). No lifecycle timeline UI in React SPA | `accounts/views.py:466` AdminUserListView, `:503` AdminUserDetailView. `accounts/admin.py:17-113` ban/restore/promote actions. No timeline component |
| 3 | Company Management | **PARTIAL** | Company model + employer verification lifecycle exist in Django admin. No REST API for admin Company CRUD in React SPA, no timeline | `employers/admin.py:28` EmployerProfileAdmin with approve/reject. `jobs/models.py:17` Company model. No React admin company view |
| 4 | Talent Pool & Discovery | **INTEGRATE** | Models + consent enforcement solid (4 enforcement points). Admin has zero visibility into talent pool operations or consent audit trail | `employers/views.py:644,660,703,612` consent checks. TalentPool/TalentPoolCandidate NOT registered in admin. No consent-state snapshot |
| 5 | Talent Quality/Qualification | **DONE** | 7-dimension ScoringEngine (1732 lines), assessment app with coding challenges, ESCO/O*NET taxonomy, SkillBadge verification, TalentScore persistence with history and explainability | `career/scoring_engine.py`, `career/models.py:405` TalentScore, `assessment/models.py` (453 lines), `skills/models.py` (410 lines) |
| 6 | Recommendation Control | **PARTIAL** | Two recommendation engines (ML-based LightFM + intelligence layer). User-facing explainability exists. PlatformConfig has `match_weights` JSON field. No admin dashboard for tuning or viewing recommendation diagnostics | `search/recommendation_engine.py:22` LightFM engine, `intelligence/recommendation_service.py:32`, `core/models.py:142` match_weights. No admin UI for these |
| 7 | Interview Engine Control | **PARTIAL** | Full interview engine with AI-powered evaluation across 6 dimensions. Basic Django admin list view. No admin configuration panel (toggle types, difficulty, question pools) | `interviews/models.py:8` InterviewSession, `interviews/service.py:14` InterviewService, `career/admin.py:136` InterviewSessionAdmin (read-only) |
| 8 | Voice Interview Control | **PARTIAL** | AWS Polly (TTS) + Transcribe (STT) fully integrated with S3 storage. No admin configuration UI for voices, languages, or analytics | `interviews/voice_service.py:19` VoiceInterviewService (Polly line 30, Transcribe line 34). All settings hardcoded |
| 9 | Scraping Control Center | **PARTIAL** | Source model has per-source controls (`is_active`, `schedule_cron`, error tracking). `scraper_dashboard` is READ-ONLY monitoring via Django template. No start/stop/pause/run-now operational controls anywhere | `scraper/admin_views.py:18` scraper_dashboard (read-only). `jobs/models.py:111` Source.is_active. No action endpoints in scraper app |
| 10 | Scraping Workflow Differentiation | **PARTIAL** | Three workflow types exist as separate Celery tasks (discovery, revalidation, cleanup). Not unified, no admin-toggleable workflow management | `scraper/tasks.py:30` scrape_all_sources, `:257` verify_apply_urls, `:346` expire_old_jobs. `scraper/discovery/common_crawl.py:23` CommonCrawlDiscovery |
| 11 | AI-assisted Scraping | **PARTIAL** | Crawl4AI LLM extraction exists but not wired into main scraper orchestrator. AdaptiveScraperService is CSS-based, not AI | `intelligence/crawl4ai_extractor.py:33` Crawl4AIExtractor, `intelligence/adaptive_scraper.py:56` (CSS-based). No admin UI |
| 12 | Per-Job Full Inspector | **INTEGRATE** | Django admin has full Job fieldsets. JobDetailSerializer has comprehensive fields. React SPA has only list table — no per-job admin inspector component | `jobs/admin.py:71-160` JobAdmin fieldsets. `AdminJobsTable.tsx` links to public job detail, not admin inspector |
| 13 | Direct-Apply Verification Admin View | **INTEGRATE** | VerificationResult model stores all 6 stages with admin override fields. Django admin has full fieldsets. React SPA has ZERO visibility into verification data | `verification/models.py:5` VerificationResult (6 stages), `verification/admin.py:7-58` full fieldsets. `AdminDashboard.tsx` — no verification references |
| 14 | Employer/Recruiter Account Control | **DONE** | Full admin with approve/reject, EmployerTeamMember model (5 roles), verify_apply_urls action, ActivityLog audit trail | `employers/admin.py:28-103` EmployerProfileAdmin, `:107` JobPostingAdmin. `employers/models.py:48` EmployerTeamMember |
| 15 | Packages/Entitlements | **MISSING** | No Package/Subscription/Entitlement models anywhere. FeatureFlag exists and can serve as the gating mechanism | Zero results for `class.*Package\|Subscription\|Entitlement` across all apps. `core/models.py:345` FeatureFlag is the closest |
| 16 | Platform Workflow Engine | **DONE** | Prefect-based workflow orchestration with Celery fallback. Rule model with JSONB condition trees and RuleEngine with 14 operators | `intelligence/workflows.py:67-165` Prefect flows. `core/models.py:264` Rule model. `core/rule_engine.py:153` RuleEngine |
| 17 | Automation Center | **DONE** | 18 scheduled Celery Beat tasks across all domains. RuleEngine with 7 seed rules for automated actions. DB-backed scheduler (`django_celery_beat`) | `config/celery.py:21-114` beat_schedule. `core/rule_engine.py:316` seed rules. `core/admin.py:11-85` RuleAdmin |
| 18 | Notification Admin Control | **DONE** | NotificationPreference (per-user settings), UserNotification (12 types), NotificationBatch models. Full service layer with preference-aware delivery and digest | `notifications/models.py:16,97,205` three models. `notifications/service.py` delivery. `notifications/tasks.py:68` digest. `notifications/admin.py` three admin panels |
| 19 | Analytics & Reporting | **DONE** | Full analytics app: 8 API endpoints, conversion funnel, retention cohorts, job market insights, feature usage stats. Frontend admin analytics tab | `analytics/views.py:15-179` AdminStats/Charts/Click/Search/Conversion views. `analytics/views_dashboard.py:23` AnalyticsDashboardView. `AdminDashboard.tsx` analytics tab |
| 20 | Security, Data Retention, Consent | **DONE** | Complete GDPR: DataExportRequest (Article 15), AccountDeletionRequest (Article 17, 30-day grace), GDPRService with anonymization, Celery tasks, rate limiting. Minor gap: no explicit ConsentLog model | `accounts/models_gdpr.py:9,67` GDPR models. `core/gdpr_service.py:50` GDPRService. `core/middleware/rate_limiting.py:32` GDPR rate limits |
| 21 | Admin AI Copilot | **MISSING** | No admin-scoped AI agent. Rashid agent exists for users only | No `AdminCopilot`, `admin_chat` code found. `intelligence/agent.py` has user-only Rashid agent |
| 22 | Decision-Support / Alerts | **PARTIAL** | Rule engine can trigger alerts. No dedicated admin decision-support dashboard or anomaly detection UI | `core/rule_engine.py` has alert/flag actions. No frontend alert dashboard |
| 23 | Admin Navigation IA | **PARTIAL** | 8 tabs in AdminDashboard. Owner wants 20-section IA (Overview/Users/Companies/Talent/Jobs/Sources/etc.) | `AdminDashboard.tsx:26` AdminTab union type has 8 values |
| 24 | Admin Search | **MISSING** | No global admin search across entities | No admin search component or endpoint |
| 25 | Integration over Rebuild | META | Methodology — verified: this audit follows the principle. All INTEGRATE verdicts above respect existing code |
| 26 | Open-Source Research | META | See Section 3 of this document |
| 27 | Cross-System Traces | META | See Section 4 of this document |
| 28 | Implementation Order | META | See Section 6 of this document |
| 29 | Testing & Verification | META | Process item — each phase requires test coverage |
| 30 | Final Thinking Pass | META | See Section 5 of this document |

### Verdict Summary

| Verdict | Count | Sections |
|---------|-------|----------|
| **DONE** | 10 | §5, §14, §16, §17, §18, §19, §20, + meta §25/§29/§30 |
| **PARTIAL** | 10 | §1, §2, §3, §6, §7, §8, §9, §10, §11, §22 |
| **INTEGRATE** | 3 | §4, §12, §13 |
| **MISSING (BUILD)** | 3 | §15, §21, §24 |
| **META** | 4 | §26, §27, §28, §23→PARTIAL |

---

## 2. Three-Layer Admin Surface Consolidation Plan

### Current State: Three Disconnected Auth Layers

| Layer | Auth Mechanism | Entry Point | What It Controls |
|-------|---------------|-------------|-----------------|
| **Django Admin** | Session auth (`/admin/login/`) | `settings.ADMIN_URL` (env var) | 63 model registrations across 17 apps. Full CRUD for all models |
| **Django Template Staff Views** | `@staff_member_required` (session) | `/admin/scraper-dashboard/`, `/admin/health-monitor/`, AI cost dashboard | Read-only monitoring. Returns 302 to JWT-authed requests |
| **React Admin SPA** | JWT (`IsAdminRole` DRF permission) | `/admin` route in React app | 8 tabs: overview, jobs, sources, media, analytics, import, settings, logs |

**The #1 problem:** An admin must maintain two separate sessions (Django session + JWT) and context-switch between three UIs to manage the platform. The React SPA sees only a fraction of what the Django admin exposes.

### Target State: Unified React Admin SPA

The React admin SPA becomes the SINGLE control plane. Django admin remains as a fallback for raw database access but is NOT the primary admin tool. All operational controls go through DRF APIs gated by `IsAdminRole`.

### Navigation IA — Before vs. After

**BEFORE (8 tabs):**
```
Overview | Jobs | Sources | Media | Analytics | Import | Settings | Logs
```

**AFTER (20 sections, matching §23):**
```
Overview
├── KPIs, health checks, alerts
Users
├── List/CRUD, lifecycle timeline, GDPR tools
Companies
├── List/CRUD, verification workflow, team members
Talent
├── Talent scores, consent audit, pool visibility
Jobs
├── List, per-job inspector (§12), quality states
Verification
├── Per-job 6-stage breakdown, admin overrides (§13)
Sources
├── Source CRUD, operational controls (§9)
Scraping
├── Workflow status, discovery/revalidation/cleanup (§10)
Matching
├── Recommendation diagnostics, weight tuning (§6)
AI Center
├── Model router config, cost dashboard, usage tracking
Rashid
├── Chat stats, per-user usage, tool call logs
Interviews
├── Session list, config toggles, voice settings (§7/§8)
Automations
├── Celery Beat schedule viewer, rule engine CRUD (§16/§17)
Notifications
├── Template config, delivery stats, digest settings (§18)
Analytics
├── Existing analytics tab content (§19)
Packages
├── Entitlements/feature-flag packages (§15, Phase 7b)
Security
├── GDPR dashboard, data retention, consent log (§20)
Search (Admin)
├── Global entity search (§24, Phase 7b)
System Health
├── DB/Redis/Celery/Email health (consolidate health_monitor)
Settings
├── PlatformConfig, feature flags, media manager
```

### Backend API Mapping — Existing vs. New

| Nav Section | Existing Backend | New DRF View Needed |
|-------------|-----------------|-------------------|
| Overview | `analytics/views.py` AdminStatsView, AdminChartsView | Health check endpoint (wrap `scraper/admin_views.py` health_monitor logic) |
| Users | `accounts/views.py:466,503` AdminUserListView/Detail | User timeline endpoint (aggregate ActivityLog + analytics UserJourney) |
| Companies | — | AdminCompanyListView/DetailView (CRUD on Company model) |
| Talent | — | TalentPoolAdminView (read-only pool/discovery list with consent state) |
| Jobs | `core/admin_views.py` (partial) | AdminJobDetailView (expose full Job + VerificationResult) |
| Verification | — | VerificationResultView (per-job 6-stage data + admin override endpoint) |
| Sources | Existing AdminSourcesManager | Source operational controls (start/stop/run-now actions) |
| Scraping | `scraper/admin_views.py` scraper_dashboard | DRF wrapper exposing same data as template view |
| Matching | — | RecommendationDiagnosticsView (why-this-recommendation for any user×job) |
| AI Center | `monitoring/views_ai_costs.py` (template) | DRF wrapper for AI cost data + model router config CRUD on PlatformConfig |
| Rashid | — | RashidAdminStatsView (aggregate RashidUsage, session counts) |
| Interviews | — | InterviewAdminListView + config endpoint |
| Automations | — | CeleryBeatScheduleView (DRF wrapper around PeriodicTask model) |
| Notifications | Notification admin exists in Django admin | DRF NotificationAdminView (batch stats, delivery rates) |
| Analytics | `analytics/views.py` (all existing) | Already exists |
| Packages | — | Phase 7b BUILD |
| Security | `accounts/views_gdpr.py` (user-facing) | Admin GDPR dashboard (pending exports/deletions, compliance stats) |
| Search | — | AdminGlobalSearchView (multi-model search) |
| System Health | `scraper/admin_views.py` health_monitor | DRF wrapper (DB/Redis/Celery/Email status) |
| Settings | `core/admin_views.py` PlatformConfigView, FeatureFlag views | Already exists, extend PlatformConfig fields |

---

## 3. Open-Source Research

### 3.1 Admin AI Copilot (§21)

**Goal:** An admin-scoped AI agent that can answer questions about platform state, surface anomalies, and explain data.

| Option | Type | Verdict | Rationale |
|--------|------|---------|-----------|
| **Extend existing Rashid agent pattern** | Internal | **USE** | `intelligence/agent.py` already has `pydantic-ai` Agent with tool registration. Create a second `admin_agent` instance with admin-only tools (`get_scraper_health()`, `get_ai_cost_breakdown()`, etc.). Privilege separation: admin tools on a separate agent, not the user-facing Rashid. Zero new dependencies |
| [OpenAI Assistants API pattern](https://platform.openai.com/docs/assistants) | External | REFERENCE | Tool-calling pattern is similar to what pydantic-ai already provides. Not relevant since we use AWS Bedrock, not OpenAI |
| [LangChain Agent](https://python.langchain.com/) | Library | REJECT | Would add a heavy dependency (LangChain + LangGraph) when pydantic-ai already covers the agent pattern natively. Over-engineered for this use case |
| [Chainlit](https://github.com/Chainlit/chainlit) | UI Library | REFERENCE | Good chat UI patterns for admin copilot, but we already have a React frontend — building a chat component is simpler than integrating Chainlit's own server |

**Recommendation:** Build the Admin AI Copilot as a new `create_admin_agent()` function in `intelligence/agent.py` (or a new `intelligence/admin_agent.py`), registering admin-scoped tools. Expose via a new DRF endpoint gated by `IsAdminRole`. Frontend: a chat panel in the admin SPA sidebar.

### 3.2 Workflow/Automation Visibility (§16/§17)

**Goal:** Surface Celery Beat schedules and task execution history inside the React admin SPA.

| Option | Type | Verdict | Rationale |
|--------|------|---------|-----------|
| **DRF wrapper around `django_celery_beat.models.PeriodicTask`** | Internal | **USE** | Already installed (`django_celery_beat` in INSTALLED_APPS, DatabaseScheduler configured). Just needs a DRF serializer + viewset to expose `PeriodicTask` read/update. If `django_celery_results` is installed, also expose `TaskResult` for execution history |
| [django-celery-beat-admin](https://github.com/jazzband/django-celery-beat) | Built-in | ADAPT | The Django admin for celery-beat already exists (auto-registered). We need the same data via DRF for the React SPA — write a thin serializer, not a new admin |
| [Flower](https://flower.readthedocs.io/) | Monitoring | REFERENCE | Real-time Celery monitoring dashboard. Good for ops but runs as a separate server — embedding its data in our admin SPA would require its REST API. Consider as a complementary tool, not a replacement for in-SPA visibility |
| [Prefect UI](https://docs.prefect.io/) | Orchestration | REJECT | `intelligence/workflows.py` uses Prefect if available, but Prefect Cloud UI is a separate hosted service. The existing Celery Beat is the primary scheduler — focus on surfacing that |

**Recommendation:** Write a `CeleryBeatAdminViewSet` (DRF, `IsAdminRole`-gated) that serializes `PeriodicTask` (name, task, schedule, enabled, last_run_at). Check if `django_celery_results` is installed; if so, also expose `TaskResult` for execution history. Frontend: "Automations" tab showing schedule table + recent task runs.

---

## 4. Cross-System Traces

### Trace 1: Job Scraped → Verified → Published/Rejected

```
FRONTEND         API              SERVICE              DATABASE
    │               │                  │                    │
    │               │    scrape_all_   │   Job created      │
    │               │    sources()     │   quality_state=    │
    │               │    (Celery,6h)   │   needs_verification│
    │               │         │        │         │          │
    │               │         ▼        │         ▼          │
    │               │   VerificationEngine.verify()          │
    │               │   6 stages:      │                    │
    │               │   1. ATS fingerprint                  │
    │               │   2. Redirect resolution               │
    │               │   3. Domain verification               │
    │               │   4. Legitimacy scoring                │
    │               │   5. Freshness/liveness                │
    │               │   6. Deduplication                     │
    │               │         │        │                    │
    │               │         ▼        │   VerificationResult│
    │               │   trust_score    │   (per-stage data) │
    │               │   > 0.4? ───yes──► quality_state=     │
    │               │         │        │   direct_verified   │
    │               │        no        │                    │
    │               │         ▼        │                    │
    │               │   status=rejected│                    │
    │               │   quality_state= │                    │
    │               │   rejected       │                    │
    │               │                  │                    │
ADMIN VISIBILITY                                           │
    │                                                      │
    ├─ Django admin: VerificationResult full fieldsets  ✅  │
    ├─ Django admin: JobAdmin with quality_state field  ✅  │
    ├─ React SPA AdminJobsTable: NO verification data  ❌  │
    └─ React SPA: No "why rejected" display            ❌  │
```

**Broken link:** The React admin SPA (`AdminJobsTable.tsx`) contains zero references to `verification`, `trust_score`, `quality_state`, `legitimacy_flags`, or rejection reasons. An admin using the React UI cannot see WHY any job was rejected. They must fall back to Django admin.

**Fix required (Phase 7a):** New `VerificationResultView` DRF endpoint + `AdminJobInspector` frontend component showing per-stage pass/fail, trust score, and admin override controls.

### Trace 2: Candidate Recommended to Company via Talent Pool

```
FRONTEND              API                   SERVICE           DATABASE
    │                    │                      │                 │
    │  Employer searches │                      │                 │
    │  talent pool       │                      │                 │
    │         │          │                      │                 │
    │         ▼          │                      │                 │
    │  TalentDiscovery   │   queryset filter:   │   CareerProfile │
    │  ViewSet.list()    │   is_discoverable=   │   is_discoverable│
    │         │          │   True (line 644)    │   (line 129)    │
    │         │          │                      │                 │
    │  TalentPool        │   add_candidate      │                 │
    │  ViewSet           │   checks consent     │   TalentPool    │
    │  .add_candidate()  │   (line 703)         │   Candidate     │
    │         │          │                      │                 │
    │  CandidateRanking  │   AI ranking with    │   CandidateRanking│
    │  ViewSet.rank()    │   consent filter     │   (scores)      │
    │                    │   (line 612)         │                 │
    │                    │                      │                 │
ADMIN VISIBILITY                                                │
    │                                                           │
    ├─ TalentPool: NOT registered in any admin.py          ❌  │
    ├─ TalentPoolCandidate: NOT registered in admin        ❌  │
    ├─ TalentDiscoveryAdmin: shows discoveries but NO      ⚠️  │
    │   consent-state snapshot at time of action                │
    ├─ No recommendation event in ActivityLog              ❌  │
    └─ No admin ability to audit consent for specific      ❌  │
        recommendation                                         │
```

**Broken link:** Runtime consent enforcement is solid (4 enforcement points). But admin has ZERO ability to retroactively verify that consent was respected for any specific talent pool addition or recommendation event. TalentPool and TalentPoolCandidate have no admin registration at all.

**Fix required (Phase 7a):** Register TalentPool/TalentPoolCandidate in Django admin. Add a consent-audit field to TalentDiscovery (snapshot `is_discoverable` state at creation time). Log talent pool additions to ActivityLog. New DRF endpoint for admin to view pool operations with consent audit trail.

### Trace 3: AI Call Cost Tracking End-to-End

```
AI CALLER                  TRACKING              ADMIN DASHBOARD
    │                          │                       │
    │ BedrockLLMPlugin         │                       │
    │ .generate()              │                       │
    │      │                   │                       │
    │      ▼                   │                       │
    │ _track_usage()  ────────► EventLog               │
    │ (ai_model_called)        │ (model, tokens,       │
    │                          │  latency, cost_usd)   │
    │                          │                       │
    │ RashidService            │                       │
    │ .record_token_usage()───► RashidUsage            │
    │ (len(text)//4 estimate)  │ (estimated tokens)    │
    │                          │                       │
    │ pydantic-ai Agent ──────► NOTHING               ❌│
    │ (Rashid agent tools)     │ (bypasses plugin)     │
    │                          │                       │
    │                          │       ▼               │
    │                          │  views_ai_costs.py    │
    │                          │  reads BOTH tables    │
    │                          │       │               │
    │                          │  PROBLEMS:            │
    │                          │  1. Double-counting   ❌
    │                          │     (EventLog + Rashid│
    │                          │      Usage for same   │
    │                          │      Rashid calls)    │
    │                          │  2. operation='unknown'❌
    │                          │     (_track_usage     │
    │                          │      never sets it)   │
    │                          │  3. No per-user from  ❌
    │                          │     EventLog (user=   │
    │                          │     None in emit())   │
    │                          │  4. pydantic-ai Agent ❌
    │                          │     calls completely  │
    │                          │     untracked         │
```

**Blind spots identified:**
1. **Double-counting:** Rashid chat calls hit both `EventLog` (via `BedrockLLMPlugin._track_usage`) and `RashidUsage` (via `RashidService.record_token_usage` with `len(text)//4` heuristic). The dashboard reads both tables, inflating totals.
2. **No operation label:** `_track_usage` never sets an `operation` key, but `views_ai_costs.py:81` reads `data.get('operation', 'unknown')`. All feature-level cost breakdowns show "unknown."
3. **No per-user attribution from EventLog:** `_track_usage` passes `user=None` to `emit()`. Dashboard's top-users only reads RashidUsage.
4. **Pydantic-ai Agent completely untracked:** The Rashid agent (`agent.py`) uses pydantic-ai's own Bedrock model integration, bypassing `BedrockLLMPlugin` entirely. These calls produce no EventLog entry.

**Fix required (Phase 7a):** Add `operation` and `user_id` to `_track_usage` calls. Deduplicate Rashid cost counting. Wrap pydantic-ai's model call with a callback/middleware that writes to EventLog.

---

## 5. §30 Mandatory Thinking-Pass Answers

> Each answer states current behavior (verified) and what changes.

**Q1: Can I, as the platform owner, see from one screen every engine that's running, whether it's healthy, and what it did in the last 24 hours?**

**Current:** No. Health data is split across 3 surfaces. `scraper_dashboard` shows scraper health (Django template), `health_monitor` shows DB/Redis/Celery/Email status (Django template), `AdminDashboard.tsx` overview shows KPIs only. No unified "engine health" view.

**Change:** Phase 7a consolidates all health data into the React SPA Overview section via new DRF endpoints wrapping the existing template view logic.

**Q2: If a user complains "I never got recommended for that job," can I trace exactly why — the ranking factors, the consent state, the score breakdown — from the admin panel?**

**Current:** No. There is no admin view showing recommendation events or ranking factors for a specific user×job pair. The recommendation engines compute scores but don't persist per-recommendation audit trails. Consent is enforced at runtime but not snapshot-logged.

**Change:** Phase 7a adds recommendation event logging (ActivityLog entries when recommendations are served) and a consent-state snapshot on TalentDiscovery. Phase 7b's Admin AI Copilot can answer "why wasn't user X recommended for job Y" by querying the matching service live.

**Q3: If the AI cost doubles overnight, can I see which feature/model/user caused it and cap it from the admin panel?**

**Current:** Partially. `views_ai_costs.py` shows daily trends, cost by feature, model breakdown. But: (a) "by feature" shows "unknown" for all entries (missing operation label), (b) pydantic-ai Agent calls are completely untracked, (c) per-user attribution only works for Rashid, not other AI features, (d) there are no cost caps or rate limits configurable from admin.

**Change:** Phase 7a fixes the tracking blind spots (operation labels, per-user attribution, pydantic-ai wrapping). Phase 7b adds cost-limit fields to PlatformConfig (daily AI spend cap, per-model rate limits) enforced in the LLM plugin layer.

**Q4: If a scraper breaks or a source goes stale, am I alerted? Can I pause it, fix the parser, and resume — all from the admin panel?**

**Current:** Stale sources are detectable via `scraper_dashboard` (shows "stale" status). But: (a) no alert/notification is generated, (b) no pause/resume/run-now actions exist anywhere, (c) parser editing requires code changes. The `orchestrator.py` auto-disables sources after 5 consecutive failures but doesn't notify admin.

**Change:** Phase 7a adds operational controls (start/stop/pause/run-now) as DRF action endpoints on Source. Adds AlertRule for "source stale > N hours" that sends admin notification. Phase 7b's Admin AI Copilot can diagnose scraper failures.

**Q5: If I need to delete a user's data for GDPR compliance, can I do it safely with an audit trail from the admin panel?**

**Current:** Yes, partially. `GDPRService.delete_user_data()` and `delete_user_data_anonymized()` exist with cascading deletion/anonymization. `AccountDeletionRequest` model has a 30-day grace period. Celery tasks process async. Django admin shows pending requests. But: (a) no React SPA GDPR dashboard, (b) admin must use Django admin to view requests.

**Change:** Phase 7a surfaces GDPR request management in the React SPA Security section.

**Q6: Is the `is_discoverable` consent gate actually enforced everywhere, and can I prove it?**

**Current:** Enforced at 4 API points (TalentDiscoveryViewSet queryset, perform_create; TalentPoolViewSet.add_candidate; CandidateRankingViewSet.rank; ConnectionsService). However, there is NO consent-audit snapshot — admin cannot prove consent was valid at the time of a specific action.

**Change:** Phase 7a adds `was_discoverable_at_creation` boolean to TalentDiscovery model. All talent pool operations log to ActivityLog. The privacy gate itself is NOT weakened — this is an auditability improvement, not a bypass.

**Q7: Can I see, for any single job, the complete story: where it came from, how it was verified, what quality state it's in, who applied, and what AI analysis was done?**

**Current:** In Django admin, most of this is accessible across multiple admin pages (JobAdmin, VerificationResultAdmin, JobApplicationAdmin). In the React SPA, only a basic list table exists — no per-job inspector.

**Change:** Phase 7a builds the AdminJobInspector component showing all data on one page, backed by a new composite DRF endpoint that joins Job + VerificationResult + applications + AI metadata.

**Q8: Are all AI calls — not just Rashid — tracked for cost, model, latency, and user attribution?**

**Current:** No. Four blind spots exist (see Trace 3 above). The pydantic-ai Agent's Bedrock calls are completely untracked. EventLog entries lack `operation` labels and per-user attribution.

**Change:** Phase 7a fixes all four tracking gaps. Every AI call, regardless of entry point, will write to EventLog with operation, user_id, model, tokens, latency, and cost_usd.

---

## 6. Implementation Order

### Phase 7a — Consolidation (no new models, surface what exists)

**Priority:** Highest. Closes the admin visibility gaps using existing backend data.

| # | Task | Backend | Frontend | Effort |
|---|------|---------|----------|--------|
| 7a.1 | Unify admin auth: all admin DRF endpoints use `IsAdminRole` consistently | Audit existing endpoints, migrate `@staff_member_required` data to DRF wrappers | — | S |
| 7a.2 | System Health DRF endpoint | Wrap `health_monitor` logic (DB/Redis/Celery/Email checks) as DRF view | Add to Overview section | S |
| 7a.3 | Scraping Dashboard DRF endpoint | Wrap `scraper_dashboard` data as DRF view | Add Scraping section to admin nav | S |
| 7a.4 | AI Cost Dashboard DRF endpoint | Wrap `views_ai_costs.py` data as DRF view. Fix: add `operation` and `user_id` to `_track_usage`. Deduplicate Rashid counting. Wrap pydantic-ai calls | Add AI Center section | M |
| 7a.5 | VerificationResult DRF endpoint | New view: per-job 6-stage verification data + admin override PATCH | AdminJobInspector component with verification panel | M |
| 7a.6 | Source operational controls | DRF actions: start/stop/pause/run-now on Source model | Buttons in Sources section | S |
| 7a.7 | Admin Company CRUD | AdminCompanyListView/DetailView (Company model) | Companies section | S |
| 7a.8 | Talent Pool admin visibility | Register TalentPool/TalentPoolCandidate in admin. DRF read-only view. Consent snapshot on TalentDiscovery | Talent section | M |
| 7a.9 | User/Company lifecycle timeline | Aggregate ActivityLog + UserJourney analytics per user/company | Timeline component in User/Company detail | M |
| 7a.10 | Expand admin navigation to 20 sections | — | Refactor AdminDashboard.tsx from 8 tabs to 20-section sidebar nav | M |
| 7a.11 | Recommendation diagnostics endpoint | DRF view: for any user×job, return matching factors from both engines | Matching section | S |
| 7a.12 | GDPR admin dashboard | DRF view: pending exports/deletions, compliance stats | Security section | S |

**Total Phase 7a:** ~12 tasks, estimated M effort (extends existing code, no new models).

### Phase 7b — Genuine New Builds

**Priority:** Medium. Requires new models/services. Proceed ONLY after user approves Phase 7a.

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 7b.1 | Admin AI Copilot | New `create_admin_agent()` with admin-scoped tools (`get_scraper_health`, `get_ai_cost_breakdown`, `find_verification_anomalies`, `explain_recommendation`). DRF chat endpoint gated by `IsAdminRole`. Frontend chat panel | L |
| 7b.2 | Packages/Entitlements model | New `Package` model linking to `FeatureFlag` (which package unlocks which flags). Admin CRUD. **No payment/billing engine** — just the feature-gating structure. Explicit scope: entitlements, not Stripe | M |
| 7b.3 | AI cost limits + model health | Extend `PlatformConfig` with `daily_ai_spend_cap`, `per_model_rate_limit`. Enforce in `BedrockLLMPlugin.generate()`. Model health check (latency/error tracking per model alias) | M |
| 7b.4 | Admin global search | Multi-model search endpoint (Users, Companies, Jobs, Sources). Frontend Cmd+K search component | M |
| 7b.5 | Celery Beat schedule viewer | DRF wrapper around `PeriodicTask`. Read + enable/disable. Task execution history via `django_celery_results.TaskResult` if available | S |

### Phase 7c — Polish

**Priority:** Low. Analytics dashboards, decision-support alerts, UX polish.

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 7c.1 | Decision-support alerts dashboard | Frontend panel showing triggered rules, anomalies, pending decisions | S |
| 7c.2 | Interview admin config | DRF endpoint to toggle interview types, set difficulty defaults, view session stats | S |
| 7c.3 | Voice interview admin config | Expose Polly voice selection, language config, audio limits via PlatformConfig | S |
| 7c.4 | Scraping workflow admin | Unified view of discovery/revalidation/cleanup task status with toggle controls | M |
| 7c.5 | Admin AI Copilot refinements | Additional tools based on usage patterns, conversation history | S |

### Dependency Graph

```
Phase 7a (consolidation)
    ├── 7a.10 (nav restructure) — prerequisite for everything visual
    ├── 7a.1 (auth unification) — prerequisite for all new DRF endpoints
    ├── 7a.2-7a.9 (parallel work, no inter-dependencies)
    └── 7a.12 (GDPR dashboard, independent)
         │
         ▼
Phase 7b (new builds, after user approval)
    ├── 7b.1 (Admin AI Copilot — depends on 7a endpoints existing)
    ├── 7b.2 (Packages — independent)
    ├── 7b.3 (AI cost limits — depends on 7a.4 fixing tracking)
    ├── 7b.4 (Search — independent)
    └── 7b.5 (Celery viewer — independent)
         │
         ▼
Phase 7c (polish, after 7b)
    └── All items are independent refinements
```

---

## Appendix: Packages/Entitlements vs. Billing — Scope Decision Required

The owner's §15 asks for "centralized entitlement system." Phase 2 item 2.22 explicitly deferred billing as "premature while the core product doesn't yet deliver real jobs reliably."

**Proposed scope for Phase 7b.2:**
- Build `Package` model: name, description, tier (free/basic/pro/enterprise), linked `FeatureFlag` keys
- Build `UserPackage` model: user FK, package FK, valid_from, valid_until, is_active
- Admin CRUD for packages (which flags each package unlocks)
- **Do NOT build:** Stripe integration, payment processing, subscription lifecycle, invoice generation

This gives the owner the ability to assign entitlements manually (or via admin AI copilot in future) without committing to a billing engine. The FeatureFlag system already handles the gating logic — Package just bundles flags into named tiers.

**Action required:** Owner must confirm this scoping before Phase 7b.2 proceeds.

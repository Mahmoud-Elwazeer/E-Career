# D7 — Rashid AI + AI Model Router + AI Cost Control + Research/Content/Trend Engine Audit

**Scope**: `backend/apps/intelligence/*`, `backend/apps/rashid/*`, plus AI-cost-adjacent code in
`backend/apps/monitoring`, `backend/apps/core/services/cost_reporting.py`, `backend/apps/events`,
`backend/config/ai_config.py`, `backend/apps/career/cv_parser.py`, `backend/apps/vectors` (RAG infra
only — vectors is otherwise a separate domain).

**Method**: Direct code read, file:line citations, cross-reference of imports to confirm what is
actually wired vs. dead/orphaned. No code changes made (audit only). `MASTER_STATE_AND_ROADMAP.md`
does not exist in this repo — read `AGENTS.md` instead (its guidance is reflected below).

---

## Executive summary

| Area | Verdict | One-line reason |
|---|---|---|
| Rashid AI Engine | **PARTIAL / REFACTOR** | Real platform-tool calls exist in TWO places (`apps/intelligence/agent.py` Pydantic-AI agent, and `apps/rashid/tools.py`), but they are disconnected — the WebSocket chat path (the one users actually hit) never calls the tool-using agent, and `apps/rashid/tools.py` tools mostly re-derive business logic locally (reads `profile.cv_file` from disk) instead of calling the CV parsing service. |
| AI Model Router | **BROKEN (regression confirmed)** | `model_router.py` exists and is well-formed, but it is **not used by most callers**. Bedrock models are hardcoded in 3+ places outside the router (`bedrock_plugin.py` alias table, `apps/career/cv_parser.py:33`, `apps/intelligence/agent.py:42-43`), and `list_foundation_models` (dynamic discovery) is called only in a health-check, never used to build the routing table. This is the exact anti-pattern AGENTS.md flags. |
| AI Cost Control | **PARTIAL / BROKEN dashboard** | Token/cost/latency ARE captured per-call (`bedrock_plugin.py`), and a daily per-user token cap exists (`service.py`). But the one admin dashboard that's supposed to show it (`apps/monitoring/views_ai_costs.py`) reads model fields (`EventLog.metadata`, `RashidUsage.input_tokens/output_tokens/created_at`) that **do not exist** on the actual models — it will throw `AttributeError` at runtime. A second, fully-built cost/budget service (`apps/core/services/cost_reporting.py`) is **never imported anywhere** — dead code. |
| Research Engine | **PARTIAL** | Real evidence/source/confidence dataclasses exist (`Evidence`, `ResearchResult`) with `source_url`, `collected_at` (timestamp), `confidence`, but the only *actually working* path (`_research_with_platform_ai`) fabricates a single "evidence" item from internal DB data with a hardcoded `confidence=0.9`/`0.5` — it does not produce real external source URLs. The GPT-Researcher path (which would give real URLs) requires `gpt_researcher` (in requirements.txt) but has no API keys configured anywhere in `.env.example`, so it will silently fall through to the internal-data path in every real deployment. |
| Content/Trend Engine | **DONE (core), PARTIAL (deps)** | Trend detection (emerging/declining skills) is real, DB-driven, wired to Celery beat and admin-facing endpoints. BERTopic deep trend analysis and the content pipeline are implemented but depend on optional packages / are effectively best-effort with silent `except: return []` swallowing. |
| Knowledge Graph / RAG | **PARTIAL / INTEGRATE** | `knowledge_graph.py` is a real graph-over-relational-tables service, wired to endpoints — legitimate design (no separate graph DB needed). `apps/vectors` (pgvector + Cohere embed) is solid infra but is **not used by Rashid at all** — Rashid has no RAG/retrieval step; all "knowledge" comes from ad hoc DB queries in `tools.py`/`agent.py`, not vector search. |

---

## 1. Rashid AI Engine — real interface or business-logic duplication?

**Verdict: PARTIAL / REFACTOR — split-brain architecture, two competing implementations.**

There are **two independent Rashid implementations** that do not share code:

### 1a. `apps/rashid/service.py` (the one actually live via WebSocket + REST)
- `RashidService.generate_response()` (`apps/rashid/service.py:217-302`) builds a raw prompt string by
  hand-concatenating `Human:`/`Assistant:` turns (`_invoke_bedrock`, lines 304-326) and calls
  `bedrock_service.invoke_model()` directly — a single-shot text completion, **no tool-calling, no
  platform-data grounding at generation time**. It cannot look up jobs, skills, or CV data mid-conversation.
- Context is injected only at the *start* of the system prompt via `_build_user_context()`
  (`apps/rashid/service.py:77-159`), reading Career Brain / RashidProfile fields directly — this part is
  legitimate real-data grounding, not fabricated, but it's static per-turn, not queryable by the model.
- Wired at: `apps/rashid/views.py:159` (`send_message` REST action) and
  `apps/rashid/consumers.py:90-92` (WebSocket `handle_message`) — this is the **primary user-facing path**.

### 1b. `apps/rashid/tools.py` (5 "specialized tools": CV review, cover letter, interview prep, LinkedIn, course advisor)
- Each tool (`CVReviewTool`, `CoverLetterTool`, etc., `apps/rashid/tools.py:23-404`) **re-implements CV
  reading from disk** independently (`profile.cv_file.read()` / `open(cv_path, ...)` at e.g. lines 41-50,
  106-114) instead of calling the platform's actual CV parsing service
  (`apps/career/cv_parser.py` or `apps/intelligence/career_ai.py.parse_cv`). This is business-logic
  duplication exactly of the kind AGENTS.md warns about — three different "read the CV file" code paths
  now exist in the codebase (`rashid/tools.py` ×2, `career_ai.py.parse_cv`, `career/cv_parser.py`).
- `CourseAdvisorTool._get_available_courses()` (`apps/rashid/tools.py:385-404`) returns a **hardcoded
  Arabic string list of 14 courses** with a comment `"# This would normally fetch from edu.usamif.com"` —
  this is a stub, not a real integration with the course platform (`edu.usamif.com`) despite the system
  prompt telling the AI "لا تخترع أسماء دورات" (don't invent course names) — the courses ARE invented/static,
  not fetched.
- Wired at: `apps/rashid/views.py:309` (`execute_tool_endpoint`) and `apps/rashid/consumers.py:124`
  (`handle_tool`) — a **secondary path**, triggered only when the frontend explicitly sends a `tool` message
  type. Not part of the main conversational flow.

### 1c. `apps/intelligence/agent.py` (Pydantic-AI tool-calling agent — the "real" platform-intelligence interface)
- This is the only Rashid implementation that matches what AGENTS.md/the audit brief wants: a typed agent
  with `@agent.tool` functions that call real backend services — `search_jobs` →
  `apps.search.service.SearchService` (line 116-118), `analyze_skill_gap` →
  `apps.career.skill_gap_analysis.SkillGapService` (line 145), `get_career_profile` → `CareerProfile`/
  `TalentScore` models (line 173+), `get_recommendations` → `RecommendationEngine` (line 205-208),
  `get_salary_insights` → `SalaryData` (line 258-264). No business logic is duplicated here — every tool
  is a thin wrapper delegating to an existing service, matching the "no duplication" design intent stated
  in the file's own docstring (`apps/intelligence/tools.py:1-7`, which underlies a near-identical, separate
  MCP-style `ToolRegistry`).
- **BUT this agent is only reachable via `apps/intelligence/views.py:16-57` (`chat_with_rashid`)**, a
  *different* endpoint from the WebSocket/REST paths users actually hit through the Rashid UI
  (`use-rashid-chat.ts`, `use-rashid-widget.ts` per the frontend hooks found). Grep across the backend
  shows `get_rashid_agent`/`create_rashid_agent` referenced ONLY in `agent.py` itself and
  `intelligence/views.py` — i.e., **the good tool-calling agent is orphaned from the actual Rashid
  chat UI**, which instead uses the weaker `rashid/service.py` path with no tools at runtime.

### 1d. Duplicate tool registries
There are now **two separate, non-shared tool registries** doing overlapping things:
- `apps/intelligence/tools.py` — `ToolRegistry` / `get_tool_registry()`, 9 tools (search_jobs,
  get_job_detail, get_user_skills, get_skill_demand, get_career_paths, analyze_cv, get_company_info,
  get_recommendations, get_application_status, get_market_trends), used only by
  `intelligence/views.py:130-133` (`list_tools` — just lists them, doesn't call them from Rashid chat).
- `apps/rashid/tools.py` — `RASHID_TOOLS` dict, 5 different tools, used by the WebSocket/REST "tool" path.
- `apps/intelligence/agent.py` — a *third* set of `@agent.tool` functions with overlapping purpose
  (search_jobs, get_recommendations, analyze_skill_gap) but implemented independently, not reusing either
  registry above.

**Verdict detail — file:line summary:**
- `apps/rashid/service.py:217-326` — PARTIAL (real Bedrock call, real context injection, zero tool use).
- `apps/rashid/tools.py:23-404` — REFACTOR (duplicates CV-reading logic; `course_advisor` is a hardcoded stub).
- `apps/intelligence/agent.py:52-291` — DONE in isolation, but INTEGRATE (needs to become the actual chat
  backend, not a parallel unused path).
- `apps/intelligence/tools.py:1-401` — DONE in isolation, INTEGRATE (never invoked by Rashid at runtime,
  only listed via an admin-ish endpoint).

---

## 2. AI Model Router — dynamic discovery vs. hardcoded list; quality-first routing; bypass evidence

**Verdict: BROKEN — the exact repeatedly-flagged regression AGENTS.md describes.**

### 2a. Dynamic discovery: NOT implemented for routing
- `apps/intelligence/bedrock_plugin.py:99-107` (`available_models()`, `health_check()`) is the only place
  `boto3`'s `list_foundation_models` is called (line 104), and it is used **exclusively as a health-check
  boolean** (does the API respond?) — its result is discarded, never used to populate `MODEL_ALIASES` or
  `MODEL_COSTS`.
- The actual model list is a **hardcoded dict**: `MODEL_ALIASES = {"haiku": "anthropic.claude-3-haiku-...",
  "sonnet": "anthropic.claude-sonnet-4-..."}` (`bedrock_plugin.py:29-32`), and `MODEL_COSTS` hardcodes three
  specific model-id strings with their price-per-1k (`bedrock_plugin.py:23-27`). Any new Bedrock model
  (e.g. a cheaper Haiku 3.5, or Llama models referenced in `config/ai_config.py`) requires a manual code
  edit to become routable — this is precisely the "hardcode a model list instead of discovering from the
  account" regression AGENTS.md calls out.

### 2b. `model_router.py` — well-designed but bypassed by most callers
- `select_model()` (`apps/intelligence/model_router.py:134-159`) implements a genuine
  quality-first-then-cost table (`TASK_MODEL_MAP`, lines 49-115) — e.g. `CLASSIFICATION` always routes to
  cheap `haiku` regardless of quality level, `CONTENT_GENERATION` always routes to `sonnet`. This is the
  correct design pattern.
- **However, grep confirms `select_model` is called from exactly ONE call site in the entire backend**:
  `apps/intelligence/tasks.py:142,150` (`analyze_cv_document` Celery task). Every other AI call in the
  codebase — `career_ai.py`, `service.py`'s convenience methods, `research_engine.py`, `content_pipeline.py`,
  `agent.py`, `crawl4ai_extractor.py`, `apps/rashid/service.py`, `apps/rashid/tools.py` — **calls
  `invoke_model()`/`generate()` with a hand-picked `model="sonnet"` or `model="haiku"` string literal**,
  never going through `select_model()`/`TaskType`/`QualityLevel`. The router exists but is not "the one
  place all routing happens" that its own docstring claims (`model_router.py:5-7`: "No feature should
  independently select models — all routing goes through here" — false in practice).

### 2c. Direct hardcoded-model-ID bypasses (the `claude-opus-4`-equivalent anti-pattern)
Confirmed **multiple** instances of code hardcoding a full Bedrock model ID string, bypassing both the
router AND the alias table:

- **`apps/career/cv_parser.py:33`** —
  `self._model_id = getattr(settings, 'BEDROCK_MODEL_ID', 'anthropic.claude-sonnet-4-20250514-v1:0')`.
  This model ID is assigned to `self._model_id` but then **never actually used** — `extract_structured_data()`
  (line 179+) calls `self.bedrock.invoke_model(...)` (line 242) which goes through `CareerAIService` →
  `LLMRequest(model="sonnet")`, so `_model_id` is dead/unused code, but it's still a hardcoded literal
  sitting in a class attribute that looks authoritative and will mislead future maintainers.
- **`apps/intelligence/agent.py:39-49`** (`get_bedrock_model`) — hardcodes
  `"bedrock:anthropic.claude-3-haiku-20240307-v1:0"` and `"bedrock:anthropic.claude-sonnet-4-20250514-v1:0"`
  in a **second, independent alias dict**, completely separate from `bedrock_plugin.MODEL_ALIASES`. Two
  alias tables now exist and can drift out of sync (e.g. if Bedrock deprecates
  `claude-sonnet-4-20250514-v1:0`, both `bedrock_plugin.py:31` and `agent.py:43` must be edited by hand,
  and nothing enforces that both get updated).
- **`apps/rashid/models.py:26-29,32-35`** and **`apps/rashid/migrations/0001_initial.py:49,55`** —
  `RashidConfig.bedrock_model_id` defaults to a hardcoded `'anthropic.claude-sonnet-4-20250514-v1:0'`
  string and `anthropic_model` defaults to `'claude-sonnet-4'`. This is a DB-level config default, which
  is more defensible (it's admin-editable per the admin.py fieldsets), but it is **never actually read** by
  `RashidService` — `apps/rashid/service.py` calls `bedrock_service.invoke_model()` (the centralized
  `CareerAIService`), which always uses `model="sonnet"` (`career_ai.py:40`) → resolved via
  `bedrock_plugin.MODEL_ALIASES`, **completely ignoring** `RashidConfig.bedrock_model_id`/`anthropic_model`.
  So the admin-configurable model fields in Rashid's own config table are decorative — changing them in
  the admin panel has zero effect on which model actually runs.
- **`config/ai_config.py`** (whole file, lines 14-46) — a **third, independent, apparently unused** model
  config module defining `PRIMARY_AI_MODEL` = `meta.llama3-3-70b-instruct-v1:0` (claimed 89% cheaper than
  Sonnet), `ALTERNATIVE_AI_MODEL` = `meta.llama4-scout-17b-instruct-v1:0`, `FALLBACK_AI_MODEL` = Claude
  Haiku, plus `get_model_for_task()` and `get_cost_comparison()`. Grep confirms **nothing in the codebase
  imports `config.ai_config`** — it is completely dead/orphaned. This is a significant finding: someone
  built a cost-optimization plan (Llama 3.3 70B instead of Sonnet, claiming ~$112/mo savings) that was
  never wired in — the platform is still paying Sonnet/Haiku rates for everything, and a 3rd, cheaper,
  unused model tier sits disconnected from the router.
- **`apps/intelligence/crawl4ai_extractor.py:126`** — hardcodes
  `provider="bedrock/anthropic.claude-haiku-4-20250514-v1:0"` inside `LLMExtractionStrategy`, a 4th
  distinct hardcoded model-id string, different from all the above (note: `claude-haiku-4` — there is no
  such Bedrock model as of this ID pattern; likely a typo'd/aspirational model ID that would fail at
  runtime if the `crawl4ai` code path were ever exercised — see also its `except Exception` fallback at
  line 153 masking this).

**Net finding**: the router is real but decorative for ~90% of call sites; there are **4 independent,
mutually-inconsistent hardcoded-model-ID locations** plus a fully-dead 5th cost-optimization module. This
is not a single regression — it's the router pattern failing to be adopted as the single source of truth
across every subsequent feature added to `apps/intelligence` and `apps/rashid`.

---

## 3. AI Cost / Token / Latency Tracking — exists? exposed?

**Verdict: PARTIAL — collection exists, primary dashboard is BROKEN, a full budget service is dead code.**

### 3a. What's actually collected (real, working)
- `apps/intelligence/bedrock_plugin.py:79-96` — every Bedrock call computes real `tokens_in`, `tokens_out`,
  `latency_ms` (via `time.time()` delta), and `cost_usd` (via `_calculate_cost`, lines 114-117, correctly
  rate-limited per hardcoded `MODEL_COSTS`). This is genuinely per-call telemetry, not fabricated.
- `_track_usage()` (`bedrock_plugin.py:119-146`) emits an `AI_MODEL_CALLED` event
  (`apps/events/types.py:35`) via `apps.events.emitter.emit()` with `model`, `tokens_in`, `tokens_out`,
  `latency_ms`, `cost_usd`, `user_id` in the payload `data` dict — this correctly lands in
  `EventLog.data` (`apps/events/models.py:39`) since `emit()`'s `data` kwarg maps straight to that field.
- `apps/intelligence/service.py:99-111` (`_is_over_limit`/`_track_user_tokens`) enforces a real per-user
  daily token cap via Django cache (`AI_USER_DAILY_TOKEN_LIMIT`, default 50,000, `.env.example:56`).
- `apps/rashid/models.py:268-286` (`RashidUsage`) — real per-user-per-day token counter, enforced in
  `apps/rashid/service.py:195-215` (`check_token_limit`/`record_token_usage`) against
  `RashidConfig.daily_token_limit` (default 100,000). Exposed to end users via
  `apps/rashid/views.py:250-267` (`get_usage_stats`).

### 3b. Admin-facing cost dashboard — BROKEN, will throw at runtime
- `apps/monitoring/views_ai_costs.py:33` — `Event.objects.filter(event_type='ai_model_called')`, then
  line 40: `event.metadata.get('cost_usd', 0)`. **`EventLog` (aliased `Event`) has no `metadata` field** —
  its actual payload field is `data` (`apps/events/models.py:39`). Every reference to `event.metadata` in
  this file (lines 40, 81-82, 95) will raise `AttributeError: 'EventLog' object has no attribute
  'metadata'` the first time this view executes (`extract_cost()` is called at line 46 before any other
  code runs) — **the admin AI-cost dashboard is non-functional as written**, despite being routed at
  `apps/monitoring/urls.py:36` (`/monitoring/ai-costs/`) and gated correctly with `@staff_member_required`.
- Same file, lines 64-75, 102-104, 122-126 — iterates `RashidUsage` objects and reads
  `u.input_tokens`, `u.output_tokens`, and filters by `created_at__gte=...`. **`RashidUsage`
  (`apps/rashid/models.py:268-286`) has no `input_tokens`, `output_tokens`, or `created_at` fields** — it
  has only `tokens_used` and `date`. This is a second independent set of `AttributeError`s in the same
  view — the Rashid-cost half of the dashboard is equally broken.
- Net effect: **the only admin dashboard built specifically to show AI cost/token/latency is completely
  broken and would 500 on load.** This directly answers "is AI cost tracking exposed anywhere (admin
  dashboard)?" — **it is wired to a URL and gated by permissions, but not functional.**

### 3c. `apps/core/services/cost_reporting.py` — a full, well-built budget system, completely dead
- `CostReportingService` (`apps/core/services/cost_reporting.py:18-301`) implements per-user daily/monthly
  budget tracking with cache-backed aggregation (`record_cost`, `get_daily_cost`, `get_monthly_cost`,
  `get_budget_status`, `get_cost_history`), with its own `COST_PER_MILLION_TOKENS` table (lines 34-40,
  including `claude-3-opus` pricing that isn't used anywhere else in the codebase — a 5th distinct
  model-cost table).
- Grep confirms **zero import sites** for `CostReportingService`/`get_user_cost_summary` anywhere in the
  backend outside this one file. It is not registered in any URL, admin view, or service call. This is
  fully dead code — a duplicate, more complete cost system that was built and then abandoned in favor of
  (or before) the broken `views_ai_costs.py` dashboard above.

### 3d. Latency tracking — collected, never surfaced
`latency_ms` is captured on every `LLMResponse` (`llm_plugin.py:42`) and logged
(`bedrock_plugin.py:139-146`, `structlog` `ai_model_called` event with `latency_ms`), but **no dashboard,
admin view, or aggregation reads `latency_ms` back out** — not even the broken cost dashboard references
it. It only exists in structured logs and the `EventLog.data` JSON blob, unqueried.

---

## 4. Research Engine — source-traceable (URL/timestamp/confidence)?

**Verdict: PARTIAL — the data model is source-traceable; the only live code path is not.**

- `Evidence` dataclass (`apps/intelligence/research_engine.py:41-61`) genuinely supports `source_url`,
  `source_name`, `collected_at` (real timestamp via `timezone.now()` default), `quality`
  (`EvidenceQuality` enum: HIGH/MEDIUM/LOW/UNVERIFIED), `confidence` (float), and `contradicts` (list) —
  this is a well-designed, source-traceable schema, matching the audit brief's requirement.
- **However**, there are two research code paths, and only one is reachable in practice:
  - `_research_with_gpt_researcher()` (lines 148-189) — this is the path that would produce REAL external
    source URLs (via the `gpt_researcher` package, in `requirements.txt:72`). It's gated behind
    `_gpt_researcher_available()` (lines 140-146, a bare `import gpt_researcher` try/except).
  - `_research_with_platform_ai()` (lines 191-242) — the **fallback** used whenever GPT-Researcher isn't
    installed/configured or throws. This path builds exactly **one** `Evidence` object
    (lines 225-232) with `source_name="Platform internal data"`, **no `source_url`** (empty string
    default), and a **hardcoded `confidence=0.9`** — not derived from any actual measurement, just a
    literal. The `ResearchResult.confidence_score` is also hardcoded to `0.5` at line 240, regardless of
    how much (or little) internal context was actually found. This directly contradicts the file's own
    docstring claim of being "evidence-oriented... with... confidence scores" — the confidence numbers here
    are decorative constants, not computed.
  - There is **no API key configuration anywhere** for GPT-Researcher (`.env.example` has no `TAVILY_API_KEY`,
    `OPENAI_API_KEY`, or any of the search-provider keys GPT-Researcher requires to function) — meaning in
    every real deployment of this repo as configured, `_gpt_researcher_available()` may return True
    (package installed) but the actual `conduct_research()` call (line 160) would fail without a
    configured search backend, falling through the broad `except Exception` (line 187) into the
    no-URL/fabricated-confidence fallback path silently. **In practice, "research" in this platform never
    produces a real cited source URL** — it produces an AI-synthesized paragraph "grounded" in a same-DB
    query, mislabeled as high-confidence evidence.
- `_gather_platform_context()` (lines 244-277) does correctly pull real `Job`/`Company` DB rows as context
  — this part is genuine internal-data grounding, just not "research" in the external, source-citable sense
  the feature name implies.
- Wired at: `apps/intelligence/tasks.py:59-82` (`research_topic` Celery task, async, exposed via
  `apps/intelligence/views.py:86-101` `start_research` POST endpoint) and
  `apps/intelligence/workflows.py:53-58,144-149` (Prefect/fallback company-enrichment flow). Both paths
  are real Django/Celery wiring — the integration plumbing is fine; only the substance of what's returned
  is misleading about confidence/sourcing.

---

## 5. Content / Trend Engine

**Verdict: DONE (core detection), PARTIAL (deep modeling + content gen depend on soft-failing externals).**

### 5a. Trend detection — real, DB-driven, DONE
- `get_emerging_skills()`/`get_declining_skills()` (`apps/intelligence/trend_detection.py:35-133`) compute
  real period-over-period growth/decline from `Job`/`tags` DB aggregation (`Count`, date-window filters) —
  no AI call, no fabrication, straightforward and correct SQL-backed analytics.
- **Bug note**: `get_emerging_skills` filters `status='active'` (line 45) for the recent window but
  `is_active=True` (line 53) for the previous window — these are inconsistent field/flag names on the
  same `Job` model (unless `status='active'` and `is_active=True` are guaranteed equivalent elsewhere,
  this is worth flagging to the Jobs-domain audit as a possible filter inconsistency; same pattern repeats
  in `get_declining_skills` lines 97 vs 105 and in `tools.py:230-235`/`_tool_get_market_trends:360-370`).
  This audit does not own the Jobs app, flagging only for cross-domain visibility.
- Scheduled via Celery: `apps/intelligence/tasks.py:18-39` (`detect_skill_trends`, weekly) and
  `tasks.py:42-56` (`run_topic_modeling`, weekly BERTopic deep pass) — both retry on failure, real
  scheduling intent (verify actual `celery beat` schedule entries exist in `config/settings` — not
  confirmed in this pass, flagged as a follow-up check).
- Exposed at `apps/intelligence/views.py:60-81` (`get_emerging_skills`/`get_declining_skills` — user-facing)
  and `views.py:177-190` (`admin_trends_dashboard` — reads from cache keys `intelligence:emerging_skills`/
  `declining_skills`, but **nothing in `trend_detection.py` or `tasks.py` writes to those exact cache
  keys** — grep shows `_store_trend_results` referenced at `tasks.py:34` but its definition was not found
  within the read range; if it doesn't set those two cache keys, `admin_trends_dashboard` silently returns
  empty lists forever. Flagged as needs-verification, not confirmed broken in this pass).

### 5b. Deep trend modeling (BERTopic) — real but soft-fails everywhere
- `_run_topic_modeling()` (`trend_detection.py:155-182`) wraps BERTopic in try/except ImportError AND a
  broad `except Exception` — if BERTopic errors for any reason (memory, version mismatch, insufficient
  distinct topics), it silently returns `{}` (line 179/182) and callers treat that as "no trends," not as
  a surfaced failure. `bertopic==0.16.4` is in `requirements.txt:56`, so this should run, but errors are
  invisible to admins.

### 5c. Content pipeline — real generation, not fabricated claims, but web-search-free
- `ContentPipeline.generate_career_guide/skills_report/interview_guide`
  (`apps/intelligence/content_pipeline.py:69-205`) build prompts strictly from real DB-derived context
  (`_gather_role_context`, lines 207-240 — real `Job`/`JobSkill` aggregation) and always route to
  `model="sonnet"` (hardcoded literal, not through `select_model()` — another router-bypass instance,
  though lower severity since CONTENT_GENERATION's router mapping is also always `sonnet`
  (`model_router.py:80-84`), so the *outcome* happens to match what the router would have chosen).
- The module docstring's claim "All content is generated from platform data + research, not hallucinated"
  (line 11) is accurate for the DB-grounding but slightly overstated re: "+ research" — no research-engine
  call is actually made inside `content_pipeline.py`; it's DB stats + AI prose only.

### 5d. Marketing Intelligence — real, DB-driven, DONE
- `apps/intelligence/marketing_intelligence.py` — `get_platform_metrics`, `get_market_gaps`,
  `get_content_opportunities`, `get_industry_breakdown`, `get_location_insights` are all straightforward,
  correct Django ORM aggregations with sane caching (`CACHE_TIMEOUT`, line 24). No AI calls, no
  fabrication, legitimately "done." Exposed at `views.py:262-324`, all admin-gated.

---

## 6. Knowledge Graph / RAG

**Verdict: PARTIAL / INTEGRATE — two good pieces of infra that never talk to each other.**

- `apps/intelligence/knowledge_graph.py` — genuinely derives a graph (skills↔skills, roles↔skills,
  companies↔skills, career paths) from existing relational tables (`SkillRelationship`, `JobSkill`,
  `CareerPath`) rather than requiring a separate graph DB — a defensible, lightweight design. Wired to
  real endpoints (`views.py:195-257`). `DONE` as implemented, though `get_career_path_graph` (lines
  168-201) has a fragile `hasattr(path, 'to_role')` fallback to `path.title` (line 187) suggesting the
  `CareerPath` model's actual field name is uncertain even to this file's own author — worth the
  Jobs/Skills-domain audit checking `CareerPath`'s real schema.
- `apps/vectors/service.py` — solid pgvector + Cohere-embed semantic search infra (`VectorService`,
  `semantic_search`, `similar_items`), real plugin abstraction, real health checks. **Not used by Rashid,
  the research engine, or the content pipeline anywhere** — grep found no cross-references from
  `apps/rashid/*` or `apps/intelligence/research_engine.py`/`content_pipeline.py` into
  `apps.vectors.service`. Rashid has no retrieval-augmented-generation step; "knowledge" access is 100%
  direct ORM queries in `tools.py`/`agent.py`, which is functionally fine for structured data but means the
  semantic-search investment (pgvector + Cohere) is currently orphaned from the one feature area
  (Rashid/research) that would benefit most from RAG over unstructured content (job descriptions, CVs,
  career guides). **INTEGRATE recommendation**: wire `VectorService.semantic_search` into
  `research_engine.py`'s platform-context gathering and/or Rashid's `agent.py` tools.

---

## Consolidated file:line verdict table

| File | Lines | Verdict | Note |
|---|---|---|---|
| `apps/intelligence/model_router.py` | 1-166 | PARTIAL | Correct design, adopted by only 1 call site (`tasks.py:142`) |
| `apps/intelligence/bedrock_plugin.py` | 23-32 | REFACTOR | Hardcoded model list; `list_foundation_models` (104) unused for routing |
| `apps/intelligence/agent.py` | 39-49 | REFACTOR | Second, independent hardcoded model-alias table, diverges from `bedrock_plugin.py` |
| `apps/career/cv_parser.py` | 33 | REFACTOR (dead) | Hardcoded model-id literal, unused but misleading |
| `apps/rashid/models.py` | 26-35 | REFACTOR | Admin-editable model fields that are never actually read by the service |
| `config/ai_config.py` | 1-133 | BUILD/REPLACE (dead) | Entire cheaper-model cost-optimization module, never imported anywhere |
| `apps/intelligence/crawl4ai_extractor.py` | 126 | BROKEN (latent) | Hardcoded model id `claude-haiku-4-...` likely invalid; masked by broad except |
| `apps/monitoring/views_ai_costs.py` | 33,40-41,64-75,81-82,95,102-104,122-126 | **BROKEN** | References nonexistent `EventLog.metadata` and `RashidUsage.input_tokens/output_tokens/created_at` |
| `apps/core/services/cost_reporting.py` | 1-313 | BUILD/INTEGRATE (dead) | Complete budget system, zero import sites anywhere |
| `apps/intelligence/service.py` | 32-121 | DONE | Real circuit breaker + daily token cap, correctly wired |
| `apps/rashid/service.py` | 217-326 | PARTIAL | Works, but no tool-calling at generation time |
| `apps/rashid/tools.py` | 23-404 | REFACTOR | Duplicates CV-reading; `course_advisor` (385-404) is a hardcoded stub, not a real edu.usamif.com integration |
| `apps/intelligence/agent.py` | 52-291 | DONE (isolated) / INTEGRATE | Correct tool-calling design, orphaned from actual chat UI |
| `apps/intelligence/tools.py` | 1-401 | DONE (isolated) / INTEGRATE | Correct MCP-style registry, not invoked by Rashid at runtime |
| `apps/intelligence/research_engine.py` | 100-242 | PARTIAL | Good schema; live path (191-242) has no real source URLs, hardcoded confidence |
| `apps/intelligence/trend_detection.py` | 25-243 | DONE (core) / PARTIAL (BERTopic) | DB trend detection solid; deep modeling soft-fails silently; possible `status`/`is_active` filter inconsistency (45 vs 53, 97 vs 105) |
| `apps/intelligence/content_pipeline.py` | 48-250 | DONE | Real DB-grounded generation, no fabrication of stats |
| `apps/intelligence/marketing_intelligence.py` | 49-210 | DONE | Solid DB analytics |
| `apps/intelligence/knowledge_graph.py` | 52-291 | DONE | Real graph-over-relational design; `to_role`/`title` fallback (187) suggests schema uncertainty |
| `apps/vectors/service.py` | 28-199 | DONE (isolated) / INTEGRATE | Real RAG infra, unused by Rashid/research/content |

---

## Priority recommendations (for the eventual fix pass — not executed here)

1. **P0 — Fix the broken AI cost dashboard** (`apps/monitoring/views_ai_costs.py`): change
   `event.metadata` → `event.data`; change `RashidUsage.input_tokens/output_tokens/created_at` → derive
   from `tokens_used`/`date` (the model has no input/output split, so either add those fields via
   migration or approximate). This is the only admin-facing cost visibility and it currently 500s.
2. **P0 — Consolidate model routing**: make `bedrock_plugin.MODEL_ALIASES` build itself from
   `list_foundation_models()` at startup/cache-refresh (the dynamic-discovery requirement AGENTS.md
   flags), and force every caller (`career_ai.py`, `research_engine.py`, `content_pipeline.py`,
   `agent.py`, `rashid/*`, `crawl4ai_extractor.py`) through `model_router.select_model()` instead of
   literal `model="sonnet"`/`model="haiku"` strings. Delete or merge the second alias table in `agent.py`.
3. **P1 — Decide the fate of `config/ai_config.py`**: either wire its cheaper Llama-3.3 routing into the
   real router (potential real cost savings per its own claimed numbers) or delete it — right now it's
   dead weight that misleads anyone searching for "where is the model configured."
4. **P1 — Unify Rashid's chat path with the tool-calling agent**: `apps/intelligence/agent.py`'s
   Pydantic-AI agent is the correct architecture; `apps/rashid/service.py`'s tool-less prompt-concatenation
   approach is what's actually live. Migrate the WebSocket/REST chat endpoints to use `get_rashid_agent()`.
5. **P2 — Research Engine**: either configure GPT-Researcher's required search-provider API key(s) so the
   real-URL path actually fires, or stop presenting the internal-data fallback's hardcoded
   `confidence=0.9/0.5` as a computed score — compute it from something (source count, data recency) or
   label it explicitly as "internal-data-only, not externally verified."
6. **P2 — `RASHID_TOOLS`/`ToolRegistry`/`agent.py` tool triplication**: pick one tool-registration pattern
   and delete the other two; right now there are 3 separate "list of AI-callable platform tools" that will
   drift.

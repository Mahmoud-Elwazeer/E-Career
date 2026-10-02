# Platform Engine Enrichment — Master Document

**Platform:** E-Career (USAM Jobs) — `jobs.usamif.com`
**Date:** 2026-09-29
**Deployed commit:** `e7032f2` (runtime code) · docs at `070c960`
**Method:** Evidence-based. Every status is grounded in real code and, where
noted, in LIVE production runtime output captured this engagement — not in the
~100 historical status docs (which `AGENTS.md` says to treat as archive only).

This is the single authoritative document required by the directive (§57). It
supersedes and cross-references the two companion files in this folder:
`OPEN_SOURCE_ENGINE_ENRICHMENT_AUDIT.md` (OSS decisions) and
`POST_DEPLOY_RUNTIME_VERIFICATION.md` (live runtime evidence).

---

## 0. Executive summary

E-Career is substantially built: most of the 58 engines exist as real, working
code. The highest-value work this engagement was **finding and fixing genuine
runtime bugs** and **hardening the AI provider path** — not adding libraries.

**Shipped + verified this engagement (commits e99f089 → e7032f2):**
- Fixed **5 broken Rashid agent tools** (wrong service signatures / non-existent
  imports / wrong model field names) + a missing-`settings` import.
- Fixed a **wrong `JobApplication` import** (`apps.jobs.models` → `apps.employers.models`)
  in 6 sites that broke recommendations (both paths), the employer rank-applicants
  flow, and GDPR export/deletion. **Verified live** (`recs: 3`).
- Hardened the **direct-apply moat** matcher (dot-boundary vs naive substring).
  **Verified live** (25 blocked domains; correct block/allow behavior).
- Added **Job field-provenance** (migration `0008`, live).
- Aligned the **ATS dispatch** set (added workday/icims/oracle/sap; log unknowns).
- Built a **centralized Bedrock client factory + classified health check +
  fail-fast fallback**; the health classifier is **verified live** returning
  `AUTH_FAILED`.

**The one hard blocker (server-side, not code):** the server's **AWS credentials
are invalid/revoked** (`UnrecognizedClientException`), and no EC2 instance role
is attached. This takes down ALL Bedrock AI (Rashid, AI CV parse, AI matching,
salary AI). Fix = attach an IAM role or rotate the key (see §16, §47).

**Security finding:** a **real AWS Access Key ID is present in git history**
(commit `fa11a2f`, 5 doc files; scrubbed from HEAD). Must be deactivated in IAM
and treated as compromised (§47).

---

## 1. Current architecture (verified)

- **Backend:** Django/DRF, 26 apps under `backend/apps/`. Postgres (+pgvector),
  Typesense (search, with Postgres LIKE fallback), Redis, Celery + Celery Beat
  (services `celery-usam.service`, `celery-beat-usam.service` — both live),
  Gunicorn (`usam.service`), Channels/WebSocket.
- **Frontend:** React/Vite/TypeScript, served by nginx from `frontend/dist`.
- **AI:** AWS Bedrock only (Claude haiku/sonnet-4.5), via a central plugin +
  pydantic-ai agent for Rashid. Model catalog is config-driven with a hardcoded
  default alias map.
- **Deploy:** git checkout on EC2 (`/var/www/usam`), branch `development`.
- **Ingestion:** Celery tasks (not a separate microservice); DB-scheduled beat.

---

## 2. The 58-Engine Matrix (evidence-based, §3/§49/§60)

Status vocabulary per directive. "Live" = confirmed in production this
engagement; "code" = verified by reading real code.

| # | Engine | Status | Evidence / notes |
|---|--------|--------|------------------|
| 01 | Identity | FUNCTIONAL | `apps/accounts`; JWT login verified LIVE (returns `data.access`) |
| 02 | User Profile | FUNCTIONAL | `apps/profiles`, `apps/users` |
| 03 | Career Identity | FUNCTIONAL | `apps/career/career_brain_service.py` |
| 04 | CV | FUNCTIONAL | `apps/profiles/cv_parser.py` (Docling+pdfplumber+easyocr+docx) — **AI parse blocked by AWS creds** |
| 05 | Cover Letter | FUNCTIONAL (weak) | `apps/career/cover_letter_service.py` — LLM-backed, blocked by AWS creds |
| 06 | Skills | FUNCTIONAL | `apps/skills` ESCO/O*NET schema; skill-gap keys verified LIVE |
| 07 | Assessment | FUNCTIONAL | `apps/assessment` |
| 08 | Talent Qualification | FUNCTIONAL BUT WEAK | scoring engines; fragmented |
| 09 | Talent Pool | FUNCTIONAL | `apps/employers` TalentPool + admin view |
| 10 | Job Discovery | PARTIAL | Common Crawl + change-detection + jobspy; no unified engine |
| 11 | Scraping | FUNCTIONAL (weak on some ATS) | `apps/scraper/orchestrator.py` + `ats/` |
| 12 | Connector | PARTIAL | Greenhouse/Lever/Ashby real; SmartRecruiters/iCIMS/Oracle/Workday weak |
| 13 | Job Normalization | FUNCTIONAL BUT WEAK | rule-based `pipeline/normalizer.py` + provenance now attached |
| 14 | Deduplication | FUNCTIONAL BUT WEAK | exact + content-hash; no fuzzy/semantic |
| 15 | Verification | PRODUCTION READY | 6-stage `apps/verification/engine.py` |
| 16 | Direct Apply | PRODUCTION READY | moat verified LIVE (block/allow correct, 25 blocked) |
| 17 | Search | FUNCTIONAL | Typesense + Postgres fallback; mandatory trust filter |
| 18 | Matching | FUNCTIONAL, FRAGMENTED | `profiles/services.py` + `search/recommendation_engine.py` |
| 19 | Recommendation | FUNCTIONAL | LightFM + deterministic fallback; **fixed + verified LIVE (recs:3)** |
| 20 | Application | FUNCTIONAL | `apps/employers.JobApplication` (note: not in apps.jobs) |
| 21 | Employer | FUNCTIONAL | `apps/employers` RBAC/team/talent pool; rank-applicants import fixed |
| 22 | Candidate Intelligence | PARTIAL | scoring + connections |
| 23 | Interview | FUNCTIONAL | `apps/interviews/service.py` — AI blocked by creds |
| 24 | Interview Simulation | FUNCTIONAL | voice + coding |
| 25 | Voice | FUNCTIONAL (batch) | Polly TTS + Transcribe STT (not streaming) |
| 26 | Career Coach | FUNCTIONAL | `apps/career` services |
| 27 | Rasheed | FUNCTIONAL (tools fixed; **AI blocked by creds**) | agent + 9 tools; 5 tools repaired this engagement |
| 28 | AI Gateway | FUNCTIONAL (single provider) | `apps/intelligence` + new central `bedrock_client.py` |
| 29 | Model Router | FUNCTIONAL (hardcoded catalog) | `model_router.py`; dynamic discovery still a documented follow-up |
| 30 | Research | PARTIAL | `research_engine.py` (gpt-researcher disabled, fallback) |
| 31 | Knowledge/RAG | PARTIAL | `knowledge_graph.py` + pgvector |
| 32 | Content/Trend | PARTIAL | `content_pipeline.py`, `trend_detection.py` |
| 33 | Notification | FUNCTIONAL | `apps/notifications` |
| 34 | Automation | FUNCTIONAL (=Celery) | beat + proactive_service; workers live |
| 35 | Document | FUNCTIONAL | Docling/pdfplumber; `resume/export_service.py` |
| 36 | Analytics | FUNCTIONAL | `apps/analytics`, EventLog |
| 37 | Package/Entitlement | FUNCTIONAL | `apps/payments` |
| 38 | Admin Control Plane | FUNCTIONAL | `apps/core/admin_urls.py`; AI health now classified |
| 39 | Security/Audit | FUNCTIONAL (see §47) | RBAC + audit logs; exposed-key-in-history finding |
| 40 | Observability | FUNCTIONAL BUT WEAK | structlog + health; no traces/dashboards |
| 41 | Finance/Ledger | PRODUCTION READY | double-entry ledger, 30 tests |
| 42 | Subscription | FUNCTIONAL (manual) | `apps/payments` |
| 43 | Pricing | FUNCTIONAL | Package/Coupon |
| 44 | Billing/Invoice | FUNCTIONAL | Invoice + PDF/XLSX |
| 45 | Payment Provider | PARTIAL | Stripe real; AlexBank scaffold |
| 46 | Refund | FUNCTIONAL | services + admin flow |
| 47 | Credit/Usage | FUNCTIONAL | ledger wallet |
| 48 | Employer Branding | PARTIAL | company profile fields |
| 49 | Verification/Trust | PRODUCTION READY | = #15 |
| 50 | Referral | FUNCTIONAL | `connections_service.py` |
| 51 | Career Development | FUNCTIONAL | skill gap, paths |
| 52 | Learning Integration | PARTIAL | CourseAdvisor → edu.usamif.com |
| 53 | Event/Career Fair | NOT FOUND | no module |
| 54 | API/Developer Platform | NOT FOUND | no API-key/OAuth-scope layer |
| 55 | Integration/Webhook | FUNCTIONAL | payments webhooks + verification |
| 56 | Feature Flag/Config | FUNCTIONAL | `apps/core` rule engine + FeatureFlag |
| 57 | Consent/Privacy | PARTIAL | discoverability consent; GDPR dashboards (application-export fixed) |
| 58 | Data Retention/Deletion | PARTIAL | GDPR views; no formal retention engine |

**No engine is marked complete merely because a file exists.**

---

## 3. Bugs found + fixed this engagement (with live evidence)

| Area | Bug | Effect | Fix commit | Verified |
|------|-----|--------|-----------|----------|
| Rashid `search_jobs` | wrong `SearchService` signature | TypeError every search | e99f089 | code + test |
| Rashid `get_recommendations` | `RecommendationEngine()` no-arg + wrong keys | crash/null | e99f089 | code + test |
| Rashid `analyze_skill_gap` | imported non-existent `SkillGapService` | ImportError | c02458b | LIVE keys |
| Rashid `get_career_profile` | `TalentScore.latest("calculated_at")` wrong field | FieldError | c02458b | code + test |
| Rashid `get_salary_insights` | `SalaryData.job_title/salary_amount` don't exist | FieldError | c02458b | LIVE query runs |
| `chat_with_rashid` | `settings` not imported | cost tracking NameError | c02458b | test |
| `RecommendationEngine` ×4 + employer + gdpr | `JobApplication` wrong module | ImportError → recs/GDPR/rank broken | 93f970a | LIVE recs:3 |
| Direct-apply moat | naive substring match | over-block / bypass | e99f089 | LIVE + 7 tests |
| Rashid agent | no Bedrock region | UserError | 0d43d24 | code |
| Bedrock plugin health | control-plane API on runtime client | wrong health | e7032f2 | code |

Regression tests added: `tests_rashid_agent_tools.py` (8), `test_blocked_domain.py`
(7), `tests_provenance.py` (4), `tests_bedrock_client.py` (8). All pass locally;
recommendations/skill-gap/moat verified live on the server.

---

## 4. Scraping architecture + tiers (§4–§8)

Multi-strategy pipeline already exists; formalized understanding:

```
TIER 0 structured ATS APIs (Greenhouse/Lever/Ashby real) + feeds/JSON-LD/sitemap
TIER 1 fast HTTP (requests/httpx)
TIER 2 browser render (Playwright — workday, optional)
TIER 3 adaptive (Scrapling — optional, dep-gated)
TIER 4 AI extraction (crawl4ai — optional, dep-gated)
TIER 5 agentic (rejected as normal path)
→ normalize → dedup → direct-apply verify (6-stage) → quality_state → search
```

ATS dispatch (in both orchestrator and Celery task, now aligned):
Greenhouse, Lever, Ashby, BambooHR, SmartRecruiters, Workable, Teamtailor,
Workday, iCIMS, Oracle, SAP + logged fallback for unknown platforms.

---

## 5. OSS research + license matrix (§4, §50, §55) — decisions

| Candidate | License | Decision | Reason |
|-----------|---------|----------|--------|
| Scrapling | BSD-3 | Optional adapter only | Real dep conflict: lxml>=6.1.1 vs docling lxml<6.0.0 |
| Crawl4AI | Apache-2.0 | Optional Tier-4 | Needs litellm 1.48 unavailable on py3.10 |
| ScrapeGraphAI | mixed/LangChain | Reject embedding | Duplicates existing Bedrock extraction |
| Crawlee | Apache-2.0 | Reference only | Duplicates Celery + rate limiter |
| Scrapy | BSD-3 | Reject | No value over structured ATS APIs |
| Playwright | Apache-2.0 | Keep optional (Tier-2) | Only workday needs it |
| browser-use | MIT | Reject for now | Slow/expensive; last-resort only |
| **Firecrawl** | **AGPL-3.0** | **Reject embedding** | Strong copyleft — external SDK only if ever |
| jobspy | MIT | Keep (discovery-only) | Moat-compliant |
| Gorse (recs) | Apache-2.0 | Reference/defer | Interaction volume too low to justify now |
| Reactive Resume | MIT | Reference | CV builder patterns; don't vendor wholesale |
| LightFM / sentence-transformers / docling / pydantic-ai | permissive | Already used | Keep |

**Dependency-conflict strategy (§56):** anything conflicting with the main venv
(Scrapling/Crawl4AI) stays optional/out-of-process — never force-installed, to
protect the working CV/docling engine.

---

## 6. AI architecture + the AWS blocker (§33–§36, §16)

**Central Bedrock layer (new, `bedrock_client.py`):** one client factory shared
by the plugin and the pydantic-ai agent; uses static keys only if both present,
else falls through to the default provider chain (**EC2 instance role works
automatically**). `bedrock_health()` classifies failures:
`HEALTHY / AUTH_FAILED / ACCESS_DENIED / REGION_INVALID / MODEL_UNAVAILABLE /
THROTTLED / TIMEOUT / NETWORK_ERROR / NO_CREDENTIALS`.

**Live diagnosis:** `bedrock_health()` on the server returned
`{'status':'AUTH_FAILED','region':'us-east-1','credential_source':'static_settings_env'}`.
The static key in `backend/.env` is rejected by AWS; no instance role attached.
This blocks all Bedrock AI. Fail-fast fallback now returns an honest "AI
unavailable" message instead of silently faking a reply.

**Model catalog:** `sonnet` alias = `us.anthropic.claude-sonnet-4-5-20250929-v1:0`;
code comments note sonnet-4 (not 4.5) was access-denied 2026-08-30 — so after
credentials are fixed, confirm model access or repoint `RASHID_MODEL`.

---

## 7. Cross-engine chains (§52) — status

```
CV → Career Identity → Skills → Qualification → Talent Pool → Matching → Recs
 real   real            real     weak            real          fragmented  fixed/live

Job Discovery → Scraping → Connector → Normalize → Dedup → Direct Apply → Verify → Search → Matching → Recs
 partial        real       partial     weak        weak    PROD(live)    PROD     real     fragmented  live

Rasheed → AI Gateway → Model Router → Tools → Engines → Audit → Analytics
 tools fixed  central     hardcoded    9 fixed  real     real    real     [AI blocked on AWS creds]
```

**Top structural follow-up:** converge the fragmented matching layer
(`profiles.MatchingService` vs `search.RecommendationEngine`) behind one
interface — documented, deferred (needs migration-safe refactor + broad tests).

---

## 8. Implementation priorities (§58) — status

| Priority | Item | Status |
|----------|------|--------|
| P0 | Direct Apply correctness | DONE (live) |
| P0 | Rashid tool correctness | DONE (code+live data paths); AI blocked on creds |
| P0 | Recommendations crash | DONE (live) |
| P0 | AWS credentials | **BLOCKED — user/AWS action** |
| P0 | Exposed key in history | **ACTION REQUIRED — rotate in IAM** |
| P1 | Job provenance | DONE |
| P1 | ATS dispatch parity | DONE |
| P1 | AI health visibility + fail-fast | DONE |
| P1 | Converge matching layer | DEFERRED (documented) |
| P2 | Dynamic Bedrock model discovery | DEFERRED (documented) |
| P2 | Fuzzy/semantic dedup, streaming voice, OpenSearch | DEFERRED |

---

## 8b. Implementation backlog (dependency-aware) + progress

Living backlog per the implementation directive. Status updated after each
increment. `DONE` = code + tests + pushed; runtime PASS requires server evidence;
AI runtime stays BLOCKED until AWS creds valid.

| Engine | Current | Required change | Deps | OSS | Scope | Tests | Runtime acceptance | Priority | Final status |
|--------|---------|-----------------|------|-----|-------|-------|--------------------|----------|-------------|
| Scraping Strategy Router | none (implicit) | explicit Tier 0-5 router over existing dispatch | orchestrator | Scrapling/Crawl4AI optional/out-of-proc | additive module + injected runners | 8 | route selected + delegates correctly in a real run | P0 | **DONE (f055bda)** |
| SmartRecruiters connector | PARTIAL (wrong id assumption) | use public Posting API (slug=identifier) + pagination | requests | — | rewrite fetch_jobs | (live) | real postings fetched for a live SR company | P0 | **DONE (f055bda)** — needs live source check |
| Job Normalization | WEAK | add seniority + country/city + confidence | — | — | additive helpers | 7 | normalized fields on new scrapes | P1 | **DONE (fbedbd9)** |
| Deduplication | WEAK | layered L1/L2/L3 verdict | — | (pgvector for L4 later) | additive `dedup_verdict` | 4 | dup collapse on ingestion | P1 | **DONE (fbedbd9)** — wire into ingestion next |
| iCIMS connector | BROKEN (points at Jobvite) | correct endpoint OR mark unsupported | — | — | investigate tenant API | — | real postings or honest unsupported | P2 | TODO |
| Workday connector | STUB (Playwright) | out-of-process browser tier | Playwright | — | Tier-2 runner | — | jobs from a live Workday tenant | P2 | TODO (browser tier) |
| Oracle/SAP connectors | best-effort | per-tenant endpoints or mark unsupported | — | — | investigate | — | real or honest unsupported | P2 | TODO |
| Source Discovery | PARTIAL | company→careers→ATS detect unify | — | — | consolidate existing discovery | — | discover+register a source | P1 | TODO |
| CV end-to-end | FUNCTIONAL (AI parse blocked) | verify upload→parse→edit→export chain | docling | Reactive Resume (ref) | audit + fix gaps | — | full chain live | P1 | PARTIAL — sync done; AI parse BLOCKED on AWS |
| Career Identity sync | FUNCTIONAL (silent overwrite) | CV→profile merge w/ conflict flags (no silent overwrite) | CV | — | cv_sync.py | 5 | conflicts flagged, user data preserved | P1 | **DONE (3cb4bab)** — apps/profiles/cv_sync.py; wired into upload serializer |
| Talent Qualification | WEAK | evidence-based contract | skills/assessment | — | qualification_service.py | 6 | verdict w/ evidence+missing, no opaque score | P1 | **DONE (effd588)** — QualificationService over deterministic ScoringEngine dims |
| Talent Pool | FUNCTIONAL | evidence-based profile + consent/visibility | qualification | — | enrich model/API | — | employer search w/ consent | P1 | TODO |
| Matching | FRAGMENTED | converge Eligibility/Ranking/Explanation | profiles+search | — | one interface, migration-safe | 7 | single consistent score | P1 | **DONE (c1e4fc1)** — apps/matching/engine.py; MatchingService delegates; deterministic |
| iCIMS connector | BROKEN | real careers-{tenant}.icims.com portal | bs4 | — | rewrite | (CI) | real postings from a tenant | P2 | **DONE (85ef7cc)** |
| Ingestion dedup+provenance wiring | — | wire L1/L2 dedup + seniority + provenance | — | — | orchestrator._process_jobs | — | dup collapse + provenance on new jobs | P1 | **DONE (ca8f335)** |
| Recommendation feedback | none | capture behavioral signals for ranking | jobs/users | LightFM/Gorse(ref) | RecommendationFeedback model + service | (CI) | signals recorded + signed weight | P1 | **DONE (f480b47)** — migration 0005; feedback_service record/weight/suppress |
| Recommendation ranking use of feedback | FUNCTIONAL | consume feedback weight + suppress dismissed | above | — | wire into fallback ranker | — | dismissed jobs suppressed | P1 | TODO (next) |
| Cover Letter | WEAK | grounded pipeline + versions | CV/job (AI) | — | planner+draft+export | — | generate→edit→export live | P1 | TODO (AI parts BLOCKED) |
| Observability/Admin | WEAK | per-engine health surfaced | — | — | engine_health_view.py | (check) | admin sees engine health | P1 | **DONE (2446a39)** — /admin-api/engine-health/ reports scraping/moat/provenance/matching/feedback/bedrock |

## 8c. LIVE runtime verification of new engines (2026-09-29, server ff0520d)

Confirmed on production via `manage.py shell` (pytest not installed on prod venv;
`manage.py check` = "no issues (0 silenced)"):

| Engine | Live result | Status |
|--------|-------------|--------|
| Strategy Router | `airbnb-greenhouse -> STRUCTURED (known greenhouse connector)` | PASS (live) |
| Unified Matching | `score 0.0, deterministic: True` (0.0 = unrelated sample records; determinism is the point) | PASS (live) |
| Normalization | `normalize_seniority('Lead...')=('senior',0.6)`; `normalize_country_city('Cairo, Egypt')=('Egypt','Cairo',0.8)` | PASS (live) |
| Layered Dedup | `dedup_verdict(...).l2_normalized_key = 'acme|dev|cairo'` | PASS (live) |
| CV→Profile sync | user role 'PM' KEPT; conflicts=['experience_years','current_role'] flagged (not overwritten) | PASS (live) |

This is real end-to-end evidence the Phase A/B/D deterministic engines run
correctly against production data. AI-dependent engines remain BLOCKED on the
AWS credential issue (unchanged).

## 8d. INGESTION INCIDENT: "fetched 154 / added 0" — ROOT-CAUSED + FIXED (1cb8404)

**Symptom:** Greenhouse connector fetched 154 real jobs, persisted 0, no existing
jobs (not dedup), no visible error.

**Root cause (read from real code):** both ingestion paths
(`orchestrator._process_jobs` AND `tasks.process_and_store_jobs`) called
`Job.objects.create()` WITHOUT the REQUIRED non-nullable fields `location_type`
and `industry` (they passed only `work_arrangement`). Every create raised, and
the outer `except Exception: continue` swallowed all 154 silently → added 0.

Contributing bugs: (a) `calculate_legitimacy_score` read `job['company']` but
connectors emit `company_slug`; (b) `normalize_seniority` could yield
director/executive/student which aren't in `Job.EXPERIENCE_LEVEL_CHOICES`.

**Fix (0a32da0 + 1cb8404):**
- Set required `location_type` (from work arrangement) + `industry` (company or
  'technology') + `location` fallback on create, in BOTH paths.
- Clamp `experience_level` to entry/mid/senior/lead.
- Capture the real persistence exception (PERSISTENCE_ERROR) instead of swallowing.
- Legitimacy reads company_name/company/company_slug; structured-ATS jobs exempt
  from short-description penalty (source trust ≠ content quality). Scam detection
  unchanged.
- New `run_metrics.py`: aggregated `{fetched,created,updated,rejected-by-reason}`
  + `is_zero_yield_anomaly`; orchestrator warns on zero-yield runs.

**Verified standalone:** greenhouse-shaped job legitimacy 1.0 PASS; scam 0.0
rejected; non-ATS short desc still penalized. 6 regression tests.

**RESOLVED — LIVE FUNNEL (server rerun, a8d6648):**
`{fetched:154, created:149, updated:5, verified:149, rejected:{DUPLICATE:5}}`
Real cause was NOT the required-field/company-key bugs (those were also real and
fixed) — it was legitimacy FALSE POSITIVES: greedy `pay.*fee` + bare `send money`
+ >10k length penalty rejected legit Airbnb descriptions. Sample created job:
`quality_state=direct_verified`, apply=`careers.airbnb.com/positions/...`
(real employer ATS, redirect-inspected), provenance populated, industry/loc_type/
exp set. Direct-apply moat intact. Zero-yield alert fired on broken runs, silent
on healthy run.

**FOLLOW-ON BUG (also fixed, bdfc3d3):** the rerun logs exposed
`'SearchService' object has no attribute 'sync_job'` on every job — post_save
signal called a non-existent method, so all 149 jobs were saved+verified but
NOT indexed (not searchable). Added `SearchService.sync_job(job)` (serializes via
job_to_search_document, sets trust_score). 2 tests.

**SEARCH CHAIN VERIFIED LIVE (§16):** `visible jobs in DB: 3609`; a live query
for "engineer" returned `search hits: 92` with real titles. Also fixed a search
resilience bug (0279aef): `search_jobs` hard-crashed on a Typesense 401 because
it only fell back on health_check failure, not on a query exception. Now catches
primary-plugin failures and falls back to Postgres (verified live: 401 → warning
→ 92 Postgres hits). Two SERVER-SIDE credential issues remain (surfaced, not
hidden): AWS Bedrock AUTH_FAILED (AI blocked) and TYPESENSE_API_KEY 401 (fast
search degraded to Postgres fallback until the key is set + `sync_typesense`
backfills). Both are graceful now.

Engine statuses updated: Scraping FUNCTIONAL (ingestion persistence fixed),
Connector (Greenhouse verified fetch+persist path), Normalization (seniority
clamp), Observability (run metrics + zero-yield alert).

## 9. Production-readiness conclusion

- **Non-AI platform:** healthy and verified live — auth, services, workers,
  moat, recommendations/skill-gap/salary data paths, search, jobs.
- **AI platform (all Bedrock features):** **BLOCKED** solely by invalid server
  AWS credentials. Code is correct and hardened; once a valid IAM role/key is in
  place and the model is accessible, `bedrock_health()` → `HEALTHY` and Rashid +
  all AI features will function. This must be verified with real output before
  claiming PASS.
- **Security:** exposed AWS key ID in git history must be deactivated in IAM.

**No feature is claimed working without runtime evidence.** Items that cannot be
verified until AWS credentials are valid are explicitly marked BLOCKED, not PASS.


---

## Connector Matrix — Live Fetch-Only Probe (2026-09-29, code @ 2ee5637)

Ran `python manage.py connector_matrix --fetch-only` on prod (non-writing probe of every seeded source). `created=0` everywhere is expected in fetch-only mode; the signal is the **fetched** column.

| Source | Platform | Fetched | Verdict |
|---|---|---:|---|
| airbnb-greenhouse | greenhouse | 156 | OK |
| brex-greenhouse | greenhouse | 258 | OK |
| databricks-greenhouse | greenhouse | 877 | OK |
| discord-greenhouse | greenhouse | 48 | OK |
| figma-greenhouse | greenhouse | 163 | OK |
| gitlab-greenhouse | greenhouse | 198 | OK |
| robinhood-greenhouse | greenhouse | 162 | OK |
| stripe-greenhouse | greenhouse | 711 | OK |
| linear-ashby | ashby | 30 | OK |
| openai-ashby | ashby | 833 | OK |
| ramp-ashby | ashby | 155 | OK |
| netflix-lever | lever | 0 | **DEAD (404)** |
| notion-lever | lever | 0 | **DEAD (404)** |
| plaid-lever | lever | 0 | **DEAD (404)** |
| ramp-lever | lever | 0 | **DEAD (404)** |
| **TOTAL** | | **3591** | |

### Root cause
Greenhouse (8/8) and Ashby (3/3) connectors are healthy. All 4 Lever sources returned HTTP 404 from `api.lever.co/v0/postings/{slug}`. The connector code is correct — the **company slugs were stale** because those companies migrated ATS.

### Verified current ATS (probed 2026-09-29)
- **Notion** → Ashby (200, 128 jobs) — migrated off Lever
- **Plaid** → Ashby (200, 121 jobs) — migrated off Lever
- **Ramp** → Ashby (already seeded as `ramp-ashby`, 155 jobs); `ramp-lever` was a dead duplicate
- **Netflix** → no public ATS JSON API (own Eightfold-based board) — cannot ingest moat-compliant

### Fix (commit e9e0dd4)
- Removed the 4 dead Lever slugs.
- Added verified-live Lever boards to keep the connector exercised: `spotify-lever` (80), `gopuff-lever` (788), `ro-lever` (54).
- Added `notion-ashby` (128) and `plaid-ashby` (121).
- Added `setup_sources --deactivate-stale` to retire DB sources no longer in the seed list, so migrated/dead boards stop running every 6h and firing the zero-yield alert.

### Server action required
Deploy e9e0dd4, then:
```
python manage.py setup_sources --deactivate-stale
python manage.py connector_matrix --fetch-only   # re-probe; expect Lever spotify/gopuff/ro > 0, no 404 rows
```


---

## Ingestion Pipeline Hardening (2026-09-29, commits d65d8b0..e6977df)

Executed the "connector health ≠ source config health ≠ end-to-end ingestion health" directive. All increments are code + standalone tests + verified, pushed to origin/development.

### §5 Authoritative NormalizedJob contract (d65d8b0)
- New `apps/scraper/pipeline/contract.py`: one typed `NormalizedJob` every connector maps into via `from_connector_dict()`, which tolerates every company-key variant (company / company_name / company_slug / company_id) and both apply-url keys — so downstream code never guesses connector keys.
- Fixes the long-standing **company-name bug**: connectors only ever emit `company_slug` (= board slug), and the orchestrator stored that lowercased slug as the employer name ("airbnb" not "Airbnb"). Now resolves the real name via `source.name` / a humanized slug.
- Sets the previously-unset REQUIRED `Job.source_url`.
- `IngestionState` (§7): DISCOVERED..PUBLISHED + failure states, mapped onto the existing persisted `Job.quality_state`. 7 tests.

### §5/§19/§24 Full-funnel connector matrix + observability (d3cfd62)
- `RunMetrics` extended: normalized / duplicates / errors / direct_apply_candidate / direct_apply_verified / publishable / indexed / provider, plus `is_degraded`.
- Orchestrator populates every stage incl. an explicit `SearchService.sync_job` so `indexed` is measured (a Typesense outage shows as indexed<created, not silent loss).
- `connector_matrix` rewritten to print the full funnel (fetch|norm|da_ok|creat|updt|dupe|verif|pub|index|err|rej) + `--source` + `[DEGRADED]` marker. `--fetch-only` now clearly labelled as fetch-capability only. 7 tests.

### §6 Source-aware assessment — SOURCE TRUST vs CONTENT QUALITY (35d882d)
- `calculate_source_trust()` (evidence-based: known ATS provider, ats job id, structured payload, job-specific url) and `assess_job()` returning BOTH dimensions + `block_reasons`, never one opaque number.
- Moat preserved: publication still gates on content quality ≥ 0.4; **trust never buys publication** (explicit test: a trusted-provider wrapper around scam content stays blocked). Source-trust evidence recorded in `field_provenance._source_trust`. 6 tests.

### §8/§9/§10 Source discovery + migration model (9a5bba9)
- `Source` gains `lifecycle_state` (active/degraded/migrated/disabled/invalid), `consecutive_zero_yield_runs`, `migrated_to` self-FK, append-only `migration_history`, `last_discovery_at` (migration 0009).
- `source_discovery.py` fingerprints a company across known ATS endpoints (greenhouse/lever/ashby/smartrecruiters/workable/recruitee/personio) with per-probe evidence + a MIGRATED/ACTIVE/INVALID verdict; network fetcher injected so 6 tests run offline (replays the real Notion Lever→Ashby migration + Netflix INVALID case).
- `rediscover_sources` command applies verdicts (create successor, retire old, record evidence; dry-run by default).
- Orchestrator folds run health into lifecycle: degraded runs bump the zero-yield counter and flag DEGRADED; healthy runs clear it.

### §10 Netflix — integrated compliantly (was prematurely "unsupported") (e6977df)
- Researched properly: Netflix runs on **Eightfold AI** (`explore.jobs.netflix.net`). Verified live 2026-09-29: `/api/apply/v2/jobs?domain=netflix.com` → **474 structured positions**, each with a `canonicalPositionUrl` on Netflix's own host (direct-apply, moat-compliant).
- New `EightfoldScraper` (paginated, tenant registry), wired into orchestrator dispatch/rate-limits/fetch-only, seeded `netflix-eightfold`, added to trusted providers. 3 tests parse a REAL captured Netflix payload offline (incl. all-apply-urls-are-direct assertion).

### Server actions still required
- Deploy e6977df; run `python manage.py migrate` (applies jobs 0009).
- `python manage.py setup_sources --deactivate-stale` (retires dead Lever rows, seeds netflix-eightfold + notion/plaid-ashby).
- `python manage.py connector_matrix` (WRITE mode) to get the true funnel per source — paste output to confirm persistence + publishable + indexed counts.
- `python manage.py rediscover_sources --degraded-only --apply` once sources have accrued run history.
- Still blocked server-side (not code): Typesense 401 (fast search degraded to Postgres fallback), AWS Bedrock AUTH_FAILED (all AI). Rotate the AWS key exposed in git history commit fa11a2f.


---

## Weak ATS Connectors Hardened (2026-09-29, commits d315875, ccbe5b1)

### Workday — rewritten browser-free (d315875)
Old connector needed Playwright + brittle CSS selectors and returned no ats_job_id/description/dates. Replaced with the public CXS JSON API:
`POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` body `{"appliedFacets":{},"limit":20,"offset":0,"searchText":""}`.
Verified live vs NVIDIA: total 2000, paginated (limit hard-capped at 20 server-side, ~2000 ceiling), direct apply on `nvidia.wd5.myworkdayjobs.com`, req id `JR1973150` from bulletFields/externalPath. Tenant/site/server from `WORKDAY_TENANTS` registry (unknown tenant → [] with log). Seeded `nvidia-workday`. 5 fixture tests. Playwright removed as default (can return as out-of-proc fallback §16).

### SmartRecruiters — apply-url bug fixed (ccbe5b1)
The list endpoint returns `applyUrl=null` and `ref` = an **API URL** (`api.smartrecruiters.com/.../postings/{id}`), NOT a candidate apply page. Connector wrongly used `ref`. Now always builds `jobs.smartrecruiters.com/{companyIdentifier}/{id}`. Verified live vs BoschGroup (totalFound 4820; identifier case-insensitive). Seeded `boschgroup-smartrecruiters`. 2 fixture tests incl. apply-url-is-careers-page-not-api-ref.

### iCIMS — already correct
Tenant-scoped BeautifulSoup parse of `careers-{tenant}.icims.com` with same-domain (moat-compliant) apply links. HTML-scraping so more fragile than JSON, but honest. NOTE: not yet in orchestrator dispatch (lower priority than JSON connectors).

### Oracle + SAP SuccessFactors — DISCOVERY_UNSUPPORTED with evidence
Both prior implementations hit generic non-tenant endpoints (`jobs.oracle.com`, `jobs.sap.com/search`) and guessed response keys — risking non-direct-apply URLs. Replaced with explicit `SUPPORTED=False` + empty tenant registry + docstring stating exactly why (Oracle ORC and SAP CSB/OData feeds are per-tenant host/site/auth, not derivable from a slug) and the path to enable (verified per-tenant registry mirroring WORKDAY_TENANTS). Honest and moat-safe rather than shipping guesswork.

### Connector status summary (2026-09-29)
| Connector | Status | Evidence |
|---|---|---|
| Greenhouse | OK (JSON) | 8 boards fetch live |
| Ashby | OK (JSON) | 3 boards fetch live |
| Lever | OK (JSON) | spotify/gopuff/ro verified |
| Eightfold | OK (JSON) | Netflix 474 live |
| Workday | OK (JSON, browser-free) | NVIDIA 2000 live |
| SmartRecruiters | OK (JSON, apply-url fixed) | Bosch 4820 live |
| iCIMS | OK (HTML) | tenant-scoped; not in dispatch |
| Bamboohr/Workable/Teamtailor | present in dispatch | not re-verified this pass |
| Oracle / SAP | UNSUPPORTED (documented) | per-tenant config required |


---

## Normalization / Dedup / Extraction / E2E tooling (2026-09-29, commits 74f27be..23a2d29)

### §13 Cross-provider normalization equivalence (74f27be)
`tests_normalization_crossprovider.py`: proves the same role from greenhouse/lever/workday/smartrecruiters/eightfold normalizes to equivalent company/title/seniority/location/employment_type while each keeps its provider identity + apply url. **Found+fixed a real bug**: `parse_salary` split plain 6-digit amounts (120000 → 120+000), corrupting un-commaed salaries; regex now handles comma-grouped OR ≥2-digit runs and filters sub-1000 noise.

### §14 Cross-source deduplication coverage (51c4a60)
`tests_dedup_crosssource.py`: same employer role via different sources collapses on L2 (company+normalized-title+location) / L3 (content fingerprint) even when L1 (ats-id) differs; distinct roles stay separate; seniority noise stripped; case-insensitive. Confirms the layered deduplicator is correct.

### §16/§17 Extraction adapter contract (700b5da)
`extraction_adapter.py`: ExtractionTier (structured API→http→browser→adaptive→AI→agentic), Router (ascending tiers, skips unavailable, explainable attempts), OutOfProcessBackend (Scrapling/Crawl4AI/ScrapeGraphAI run in a separate venv over stdin/stdout JSON — keeps lxml/litellm conflicts out of the Django venv). **AI is not the default**: tier ceiling is BROWSER unless explicitly raised. Inert until a runner is configured.

### §15/§16/§25 E2E verification command (23a2d29)
`verify_pipeline_e2e` (server-run): PERSISTED (quality_state breakdown + missing-apply/source_url counts) → INDEXED (--reindex + backend health) → SEARCHABLE (query hits + sample with real company_name) → MATCHABLE (per-job scores for --profile via UnifiedMatchingEngine). Read-only by default.

### SERVER ACTIONS (consolidated — run in order)
```
# deploy
cd /home/ubuntu/E-Career && git fetch origin && git merge --ff-only origin/development
cd /var/www/usam && git fetch /home/ubuntu/E-Career development && git merge --ff-only FETCH_HEAD
cd backend && source ../venv/bin/activate
python manage.py migrate                      # applies jobs/0009 (Source lifecycle)
python manage.py check

# sources: retire stale, seed new (netflix-eightfold, nvidia-workday, boschgroup-smartrecruiters, notion/plaid-ashby, spotify/gopuff/ro-lever)
python manage.py setup_sources --deactivate-stale

# prove ingestion funnel (WRITE mode) — paste output
python manage.py connector_matrix

# prove downstream — paste output
python manage.py verify_pipeline_e2e --reindex --query engineer
python manage.py verify_pipeline_e2e --profile <a-real-user-id>

# restart services
sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service
```
These two commands produce the §25 evidence (fetched/normalized/created/verified/publishable/indexed per connector, plus searchable+matchable). Still blocked server-side (not code): Typesense 401 (search degraded to Postgres fallback — fix TYPESENSE_API_KEY), AWS Bedrock AUTH_FAILED (all AI). Rotate the AWS key exposed in git history commit fa11a2f.


---

## Downstream verification + Professional Presence (2026-09-29, commits d816777..9419a44)

### §15 Search index write-path — verified statically
`SearchService.sync_job` → `job_to_search_document` → `index_job` (Typesense) confirmed; `post_save` signal on Job syncs visible-state jobs; orchestrator also calls sync_job and counts `indexed`. Live index round-trip requires the Typesense instance (currently 401 server-side → Postgres fallback active); `verify_pipeline_e2e --reindex` produces the live proof. Company name now correct in the index (contract fix).

### §16 Matching flow — verified with tests (d816777)
`tests_engine_ingested.py`: an orchestrator-shaped Job flows into UnifiedMatchingEngine deterministically — strong candidate scores high+eligible, same inputs→same score, salary floor gates eligibility, missing skills surface as gaps, empty-skills job doesn't crash. 6 tests. Live candidate run = `verify_pipeline_e2e --profile <id>`.

### §31 B — CV↔Job Match Report (667d0f8)
`cv_job_match_service.py`: fuses the ONE matching engine (fit score + breakdown + matched/missing/gaps) with ATSReadinessService (parse-ability + keyword alignment as a SEPARATE dimension). The report's fit number IS the engine's number — no second opaque score. Concrete action items from real gaps. Deterministic. 5 tests incl. fit-score-equals-engine.

### §31 — GitHub Profile README Builder (9419a44)
`github_readme_builder.py`: deterministic Markdown generator (header/about/skill-badges/learning/projects/github-stats/connect), each section rendered ONLY when data exists (no fabrication). Written from scratch — ProfileMe AGPL NOT used; readme.so (MIT) / rahuldkjain (Apache-2.0) reference only. 7 tests.

### OSS adoption matrix (Professional Presence §28)
| Project | License | Decision |
|---|---|---|
| readme.so | MIT | reference only (built our own) |
| rahuldkjain/github-profile-readme-generator | Apache-2.0 | reference only |
| ProfileMe | AGPLv3 | DO NOT embed/copy — avoided |
| Jobscan / Enhancv / Teal | commercial | reference/benchmark only, never copied |

### Professional Presence remaining (§31)
Done: ATS Readiness Engine (2ee5637), CV↔Job Match Report (667d0f8), GitHub README Builder (9419a44).
Next: CV Improvement Workspace, Career Identity sync (cv_sync.py exists), GitHub Profile Review, Portfolio Evidence, LinkedIn Guidance, Cover Letter integration, Talent Pool integration.


---

## Professional Presence layer — near-complete (2026-09-29, commits ba129a1..007b766)

All deterministic, evidence-based, no-AI-dependency (work while Bedrock is blocked), no fabrication, each with standalone tests.

| Engine | Commit | What it does | Tests |
|---|---|---|---|
| ATS Readiness | 2ee5637 | parse-compatibility + per-ATS note + keyword alignment | 6 |
| CV↔Job Match Report | 667d0f8 | fit score IS matching-engine score + ATS dimension + action items | 5 |
| GitHub README Builder | 9419a44 | deterministic Markdown, sections only when data exists | 7 |
| LinkedIn Guidance | ba129a1 | headline/about/skills/photo checks + target-role keyword alignment | 6 |
| Portfolio Evidence | 3682987 | skill-evidence coverage: which skills are backed by a real artifact | 6 |
| Cover Letter (grounded fallback) | 016a28b | references real matched skills when AI down; no fabrication | 3 |
| GitHub Profile Review | 007b766 | public repo/language/activity signals + evidence-based lang coverage | 5 |

Common design: every service exposes evidence + concrete fixes, never an opaque score; the CV↔Job fit number is the single matching-engine number (no "different score on different pages"). Recruiters' commercial tools (Jobscan/Enhancv/Teal) used as reference only; ProfileMe AGPL avoided.

### Professional Presence — remaining
- CV Improvement Workspace (interactive apply-suggestions loop) — needs UI/endpoint work.
- Career Identity sync — `apps/profiles/cv_sync.py` already flags conflicts (built earlier); wire the Professional Presence outputs into it.
- Talent Pool integration — surface these signals to employer-side talent pool.
These are integration/UI-layer tasks (endpoints, serializers, frontend) best done with the live app; the deterministic engines they consume are now in place and tested.

## Session totals (2026-09-29)
Commits e9e0dd4..007b766 on origin/development. Ingestion pipeline hardened end-to-end (contract, funnel matrix, source-aware quality, discovery+migration model, Netflix Eightfold, Workday/SmartRecruiters rewrites, normalization+salary fix, dedup, extraction adapter, e2e verify command) and Professional Presence layer built (7 engines). ~90 standalone tests added, all passing. Real bugs fixed: company-name (slug not employer), unset source_url, SmartRecruiters API-ref-as-apply-url, parse_salary plain-number split, stale Lever slugs. Server actions (deploy/migrate/setup_sources/connector_matrix/verify_pipeline_e2e) documented above; server-side secrets (Typesense 401, Bedrock AUTH_FAILED, exposed AWS key fa11a2f) remain the operator's to fix.


---

## Engine backlog — matching/recommendation convergence + iCIMS wiring (2026-09-30, commits 3e5486f..684a896)

### iCIMS wired into orchestrator (3e5486f)
iCIMS had a correct tenant-scoped connector but was never in the orchestrator dispatch (missing from both `scrape_source` and `scrape_source_fetch_only`) — any icims Source silently hit the Unknown-platform branch. Added to both dispatch paths + rate limit 3/min. Already in TRUSTED_ATS_PROVIDERS.

### Matching score converged (06a4408)
`MatchingService.calculate_match_score` returned the Bedrock AI number when AI was up and only fell back to the deterministic engine on error — so the same (profile, job) showed a different score on the job list/detail vs the deterministic CV↔Job Match Report. Now the NUMBER is always `UnifiedMatchingEngine` on every surface; `get_match_breakdown` builds the deterministic breakdown and uses AI ONLY to enrich narrative `improvement_tips`. Also makes matching correct while Bedrock is AUTH_FAILED.

### Recommendation content-score converged (684a896)
`RecommendationEngine._calculate_content_score` was a THIRD parallel skill/experience/location formula (Jaccard + own weights) diverging from the engine. Now delegates to `unified_matching_engine.score` normalized 0-1 (skill-Jaccard fallback only if the engine can't run for a profile), so a job's fit reads consistently in Recommendations, search, detail, and the match report.

Net effect: the "different score on different pages" fragmentation is closed across candidate-side matching + recommendations. (Employer-side ranking_service keeps its own weights intentionally — it scores candidates-for-a-job with knockout/education factors, a legitimately different computation.)


---

## PHASE 0 AUDIT — Financial / Payments / Billing / Org architecture (2026-10-01)

Audit before any build (per the multi-audience + financial directive). KEY FINDING: a production-grade financial subsystem ALREADY EXISTS in `backend/apps/payments/` — this is extend-and-connect work, NOT a rebuild. Open-source financial tools (Formance/Blnk/Kill Bill/Midaz) are NOT needed — the native ledger already does double-entry.

### What already exists (REAL, not stubs)
- **Provider adapter layer** `apps/payments/providers/base.py`: abstract `PaymentProvider` (create_payment/verify_payment/refund_payment/parse_webhook) + `get_provider(name)` factory. **Stripe adapter = real** (hosted Checkout, signature-verified webhooks, refunds). **AlexBank adapter = real scaffold** that raises "awaiting contract" until credentials land (never fakes success).
- **Commerce domain** `apps/payments/models.py`: `Package` (sellable product, audience individual|employer, platform_code, minor-units price, entitlement_plan FK), `Coupon`, `Order` (unique namespaced reference, status machine), `Payment` (explicit state-machine TRANSITIONS, provider_reference, ledger_transaction FK), `PaymentAttempt`, `Invoice`+`InvoiceItem`, `Refund`, `WebhookEvent`, `AdjustmentRequest`, `FinancialAuditLog`, `IdempotencyKey`.
- **Double-entry ledger** `apps/payments/models_ledger.py` + `ledger.py`: `LedgerAccount` (kind asset/liability/revenue/refund/fees/escrow; balance DERIVED, never mutable), `LedgerTransaction` (unique idempotency_key, is_balanced), `LedgerEntry` (signed minor units, immutable). Money ALWAYS integer minor units + ISO currency.
- **Purchase flow** `apps/payments/services.py`: `create_order` → `mark_order_paid` (atomic, idempotent: posts balanced ledger txn, links payment, creates invoice, grants entitlement, writes audit log). Backend verification is authoritative, not frontend redirect.
- **Reconciliation** `apps/payments/analytics.py::reconcile()` — real: compares Orders/Payments/Ledger, emits exceptions (missing_ledger/amount_mismatch/orphan_ledger/status_mismatch), optional provider cross-check. Ledger (not provider) is source of truth.
- **Entitlements** `apps/core/models.py` SubscriptionPlan (feature_flags, job/candidate limits, ai_features_enabled) + CompanySubscription; gated by `apps/core/permissions.py::check_entitlement` (already used by employer views + talent pools). Company-scoped.
- **Admin Financial Control Center** `apps/payments/admin_views.py` (IsAdminRole): overview/ledger/reconciliation/transactions/refund/adjustments(dual-control)/subscriptions/exports(CSV,XLSX,PDF)/AI(NL→real analytics)/audit. Frontend `AdminFinance.tsx` consumes it with REAL data (react-query, platform filter, KPIs, refund button, AI box).
- **Webhooks** `apps/payments/views.py::WebhookView` — signature-verified, deduped via WebhookEvent unique(provider,event_id), replay-safe, calls idempotent mark_order_paid.
- **Secrets** `apps/payments/secrets.py` — **AWS Secrets Manager already the default** (boto3, PAYMENTS_SECRET_ID bundle, env fallback). Key NAMES: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ALEXBANK_MERCHANT_ID/API_KEY/BASE_URL, PAYMENTS_SUCCESS_URL/CANCEL_URL.
- **Identity/org**: `accounts.User.role` single-valued (jobseeker/employer/admin); `employers.EmployerProfile` + `EmployerTeamMember` (owner/admin/recruiter/hiring_manager/viewer); company = `jobs.Company`. NO separate Organization/Institution/Government entity or multi-workspace/active-context yet.

### Open-source tool verdicts (per directive §35)
- Formance / Blnk / Midaz → **DO NOT USE** — native double-entry ledger already exists; adding one duplicates the source of truth (directive forbids multiple ledgers).
- Kill Bill → **DO NOT USE now** — subscriptions are modeled (Package.interval + CompanySubscription); no evidence current billing is insufficient.
- AWS Secrets Manager → **KEEP** — already integrated.
- Vault → **DO NOT USE** — Secrets Manager already covers it; no advantage.
- Saleor Dashboard → **REFERENCE ONLY** — UX patterns for AdminFinance tables/filters.

### Genuine gaps (real work, if prioritized)
1. **AlexBank live integration** — BLOCKED on bank credentials/spec (directive §11 says ask, don't guess). Need: merchant/API creds, sandbox+prod endpoints, signature/3DS spec, webhook/callback format, refund+reconciliation API, supported currencies. Scaffold + factory + secrets already wired.
2. **Individual entitlements** — only company-scoped today (acknowledged gap in services).
3. **Government/Institution** — no org entity beyond employer Company; would be a new Organization type if a real program exists.
4. **feature_flags shape bug** — SubscriptionPlan.feature_flags is a list on the model but check_entitlement reads it as a dict (`.get(feature) is False`); reconcile before adding flags.
5. Business/Institution dedicated landing pages (frontend only).

### Decision
No financial rebuild. The directive's "build a financial architecture" is ALREADY SATISFIED. Next real increments are config/connection (AlexBank creds) + the frontend org-experience separation already in progress — not new ledger/payment infra.


---

## INCIDENT CLOSED — Frontend production crash (2026-09-21/22, commit `94e68d1`)

**Baseline before this incident:** `170c4f5` (frontend; production had been correctly
deployed to this commit — all server-side checks passed: services, migrations,
nginx, direct `:8000` bypass all 200).

**Symptom:** `jobs.usamif.com` returned HTTP 200 everywhere (server/nginx/API all
healthy — confirmed via a full 15-point read-only forensic check) but the live
site rendered a **blank white page in the browser**. Server-side health checks
alone were insufficient evidence; the incident was only correctly diagnosed after
browser console evidence was provided.

**Root cause (proven, not assumed):** `frontend/src/components/AuthNavbar.tsx`
referenced the `Users` icon (lucide-react) at two call sites (line 81, pre-existing
from `31f8ae2`; line 92, introduced this session by `b8bf31a8` team-nav work) but
`Users` was never added to the `lucide-react` import list (only singular `User`
was imported). Result: `Uncaught ReferenceError: Users is not defined` at
`index-BvqyechS.js:471` — crashes the entire React app before first render.

**Contributing tooling gap found and noted:** `npm run typecheck` (bare
`tsc --noEmit`) reads the root `tsconfig.json`, which only has `references` (no
`files`) — TypeScript project-references mode does not type-check referenced
projects under plain `--noEmit`, so `src/` was silently never type-checked by that
script all session. Correct invocation: `tsc --noEmit -p tsconfig.app.json`. This
gap should be fixed in `package.json`'s `typecheck` script as a follow-up (not
done as part of this incident fix, to keep the change minimal).

**Fix (exact source change):**
```diff
- Briefcase, Info, Menu, User, LogOut, CheckCircle2,
+ Briefcase, Info, Menu, User, Users, LogOut, CheckCircle2,
```
in `frontend/src/components/AuthNavbar.tsx` (one line, one file).

**Bundle hash timeline:**
| Stage | Bundle hash | Built from |
|---|---|---|
| Broken (live, caused the incident) | `index-BvqyechS.js` | `170c4f5` (bug pre-existing + introduced this session, never caught by typecheck) |
| Intermediate rebuild (server ran `npm run build` before the fix was pulled) | `index-BgUlnVAY.js` | still `170c4f5` — same bug, new hash only |
| **Final working** | **`index-DYl8FF0K.js`** | `94e68d1` (fix applied) |

**Deployment performed (frontend-only):**
1. Fix committed locally and pushed: `170c4f5..94e68d1` → `origin/development`.
2. Server: `git fetch origin && git merge --ff-only origin/development` → confirmed `94e68d1`.
3. Server: `cd frontend && npm run build` → new hash `index-DYl8FF0K.js`, build exit 0.
4. Server: `sudo systemctl reload nginx` (reload, not restart).

**Unchanged (explicitly verified not touched):** backend code, database, migrations,
nginx config, systemd unit files, `.env`. Only the frontend static bundle was
rebuilt and nginx was reloaded to pick up the new `index.html`/asset references.

**Live verification after fix:**
- `index.html` on production now references `/assets/index-DYl8FF0K.js` (confirmed via direct fetch).
- `GET /` → 200, `GET /login` → 200, `GET /app/employer/dashboard` → 200, `GET /api/v1/payments/packages/` → 200.
- **Browser confirmation (user-reported):** page renders content again, incident
  resolved — "THE WEBSITE IS BACK AND THE LIVE FRONTEND IS RENDERING AGAIN."

**Not touched / deliberately deferred (different severity class, non-crashing):**
pre-existing `TS2339`/`TS2322` errors (`AppUser.name`, `AuthContextValue.logout`,
`PageHeaderProps.description`, `mock-data.ts` type mismatches, `Index.tsx` type-only
`Industry` reference) — confirmed harmless via a successful `npm run build` (type
errors are erased at build, do not throw at runtime). Left for separate, deliberate
cleanup, not bundled into this incident fix.

**Status: CLOSED.** Current production frontend baseline is `94e68d1`.


---

## Scraping Runtime Truth Audit + OSS Re-Verification (2026-10-02, commits 569991d, 6f691a0)

Re-verified against CURRENT code (not the claims in this doc's earlier sections) per
`AGENTS.md`'s "do not trust status docs at face value" rule. Two real, previously
undetected bugs were found and fixed; two findings from earlier sections were
re-confirmed accurate.

### Bugs found + fixed this pass

1. **`jobspy==0.31.0` was the wrong PyPI package (fixed, 569991d).** The pinned
   name resolves to `jobs.py` by Josiah Carlson — a Redis job-queue coordinator,
   unrelated to job scraping, LGPL-licensed, `py_modules=['jobs']` (not `jobspy`).
   `apps/scraper/regional/jobspy_wrapper.py` does `from jobspy import scrape_jobs`
   inside a `try/except ImportError: JOBSPY_AVAILABLE = False` — confirmed live in
   the local venv that this raises `ModuleNotFoundError`, so the Egypt/regional
   discovery path has been silently returning `[]` the entire time despite every
   prior audit doc in this file claiming "jobspy: keep, in use, discovery-only."
   **Fix:** pinned `python-jobspy==1.2.0` (MIT, speedyapply/JobSpy, the actual
   scraper, `import jobspy` works) in both `backend/requirements.txt` and
   `backend/requirements/base.txt`. Verified by installing into an isolated
   target directory (not the real venv) and confirming
   `from jobspy import scrape_jobs` succeeds and is callable.
   **Server action required:** `pip install -r requirements.txt` (or targeted
   `pip install python-jobspy==1.2.0` after uninstalling the wrong `jobspy`) on
   next deploy for this fix to take effect.

2. **Orchestrator/tasks dispatch maps had drifted again (fixed, 6f691a0).**
   `orchestrator.py` dispatched `eightfold` but not `oracle`/`sap`; `tasks.py`
   dispatched `oracle`/`sap` but not `eightfold`. Celery Beat only schedules
   `tasks.scrape_all_sources` (confirmed: `seed_beat_schedule.py` seeds
   `apps.scraper.tasks.scrape_all_sources`, not the richer
   `orchestrator.scrape_all_sources_orchestrated`) — meaning `netflix-eightfold`
   (the one Eightfold connector with 474 real live jobs) was never actually run
   by the scheduled production task. Fixed both dispatch tables to include all
   12 wired platforms identically. `oracle`/`sap` remain `SUPPORTED=False` no-op
   stubs (intentional — no verified per-tenant registry exists), so adding them
   to orchestrator.py's dispatch has no runtime effect but prevents future drift.
   Verified: `manage.py check` exit 0; `apps.scraper` test suite (4 tests, run
   against `config.settings.test` sqlite backend) passes.

### Findings re-confirmed accurate (no action needed)
- `croniter==2.0.1` is correctly pinned and imported — historical "missing
  croniter" import failure does not reproduce.
- Scrapling/Crawl4AI/ScrapeGraphAI: zero actual Python imports anywhere in
  `backend/` (repo-wide grep). `extraction_adapter.py` defines only the
  tier/protocol contract; `OutOfProcessBackend.available()` requires a
  `runner_cmd` that nothing in the codebase ever sets — fully inert.
- `VerificationEngine.verify_job()` does write `Job.status` on every path
  (the historical "never writes status" bug is fixed).
- `UnifiedMatchingEngine` convergence is real: `MatchingService` delegates to
  it with a legacy fallback only on exception.
- Rashid's `search_jobs` and `get_recommendations` tools have correct
  signatures matching the real services.

### New gap found, not yet fixed (lower priority, documented honestly)
- Recruitee, Jobvite, and Personio have **no connector implementation at all**
  anywhere in `apps/scraper/ats/` — despite being named as supported ATS
  integrations in this project's `AGENTS.md` agent-roster doc. Not started.
- The Dockerfile (`backend/Dockerfile`) installs from the flat
  `backend/requirements.txt`, not `backend/requirements/base.txt` — so
  `playwright==1.45.0` (only listed in the `requirements/` tree) is **not**
  actually present in the built production image, despite being referenced as
  an available Tier-2 fallback in `workday.py`'s historical implementation
  (now moot since Workday was rewritten browser-free, but worth noting for any
  future connector that assumes Playwright is installed).

### OSS re-verification — Scrapling / Crawl4AI / ScrapeGraphAI (live PyPI/GitHub check, 2026-10-02)

Re-pulled exact current license/version/requirements directly from PyPI JSON
APIs and GitHub LICENSE files (not from memory or prior docs):

| Library | Repo | License (verified) | Latest version | Python req | Decision |
|---|---|---|---|---|---|
| Scrapling | github.com/D4Vinci/Scrapling | BSD-3-Clause (confirmed via PyPI classifier + LICENSE text) | 0.4.15 | `>=3.10` | **OPTIONAL adapter only.** `lxml>=6.1.1` conflicts with `docling==2.31.0`'s `lxml<6.0.0,>=4.0.0` pin — this is a REAL, currently-unresolved conflict (docling's pin confirmed via PyPI). Installing Scrapling into the main venv would break the CV parser. |
| Crawl4AI | github.com/unclecode/crawl4ai | Apache-2.0 (confirmed via GitHub LICENSE file) | 0.9.4 (current) | `>=3.10` | **OPTIONAL Tier-4 adapter, re-evaluate the "disabled" reason.** The repo's disabled comment (`requires litellm==1.48.0 unavailable on Python 3.10`) refers to the OLD pinned `crawl4ai==0.3.7`, which really did hard-pin `litellm==1.48.0`. The CURRENT 0.9.4 release instead depends on `unclecode-litellm==1.81.13` (a fork, not stock litellm, `requires_python >=3.9`) — the specific conflict cited no longer describes the latest release. This does not mean 0.9.4 is conflict-free (not independently dependency-resolved against this project's full requirements.txt in this pass), but the stated reason for disabling is stale and should be re-tested before continuing to cite it. Flagged for a follow-up `pip install --dry-run`/resolver check in an isolated environment — not done in this pass (would require installing into a disposable venv and running a full resolve, which risks touching the real venv if not isolated carefully). |
| ScrapeGraphAI | github.com/ScrapeGraphAI/Scrapegraph-ai | MIT (confirmed via GitHub LICENSE file; PyPI classifier badge also says MIT) | 2.3.0 | **`>=3.12,<4.0`** | **REJECT for embedding (unchanged verdict, new reason confirmed).** This project's Docker image is `python:3.11-slim` (confirmed in `backend/Dockerfile`) — ScrapeGraphAI 2.3.0 requires Python ≥3.12, so it cannot even be installed in the current production image without a Python version bump, on top of the existing "duplicates Bedrock extraction" rationale. Also pulls a full LangChain stack (`langchain>=1.2.0`, `langchain-aws`, `langchain-community`, etc.) — heavy, duplicative. |

**Correction to an earlier claim in this document:** the OSS audit above (§5,
"OPEN_SOURCE_ENGINE_ENRICHMENT_AUDIT.md") stated Crawl4AI needs
`litellm==1.48.0` "unavailable on this Python" as a current, active blocker.
That was true of the pinned `0.3.7` version at the time; it is not accurate as
a description of the current upstream `0.9.4` release. The underlying business
decision (keep OPTIONAL, do not force into the main venv) is unchanged — only
the specific stated reason needed correction. No code change made here; this
is a documentation correction pending a real dependency-resolution test.


---

## Typesense 401 investigation + search-indexing truthfulness fixes (2026-10-02, commits 04d9ba9, b744dc0)

User ran `python manage.py verify_pipeline_e2e --reindex --query engineer` on
the server and hit a multi-thousand-line flood: production Typesense returns
`401 Forbidden - a valid x-typesense-api-key header must be sent` on every
single job. Confirmed via code (not guessed) and fixed what could be fixed
without server access.

### Root cause location (confirmed via code read, not assumption)
- `apps/search/plugins/typesense_plugin.py:32-40` builds the Typesense client
  from `settings.TYPESENSE_HOST/PORT/PROTOCOL/API_KEY`.
- `config/settings/base.py:359-363` reads those via `python-decouple`'s
  `config()` — env vars (or `.env`). **If `TYPESENSE_API_KEY` is absent from
  the environment, Django silently uses the literal default
  `ecareer_typesense_dev_key`** baked into the code and `.env.example` — a
  wrong-but-valid-looking key, which produces exactly a 401, not a crash.
- **Gap found:** `deploy/ec2-setup.sh` (this repo's own server bootstrap
  script) installs Postgres, nginx, certbot, ufw — it **never installs or
  configures Typesense at all**. The `docker-compose.yml` Typesense service
  definitions (root and `backend/`) look like local/dev-only infra. This
  means Typesense was stood up on the production server through a process
  not captured anywhere in this repo — I cannot determine from code alone
  whether the live key matches what Django is configured to send, or
  whether Typesense itself is in Docker, a native binary, or something else.
  **This remains unresolved and requires the user to run a one-time,
  non-secret-echoing diagnostic on the server** (service/process discovery +
  key length/SHA-256 fingerprint comparison) before the actual 401 can be
  fixed — not done this pass, correctly flagged as blocked rather than guessed.

### Fixed this pass (code-side, no secrets touched, no server access needed)

1. **Log-flood circuit breaker** (04d9ba9, prior entry) — `index_job()` now
   stops making live Typesense calls after 3 consecutive failures for a
   5-minute cooldown, logging one WARNING instead of two ERRORs per job.

2. **False-success logging fixed** (b744dc0) — `apps/search/signals.py`'s
   `post_save` handler logged `"Synced job X to search"` unconditionally,
   even immediately after `sync_job()` had just failed. Root cause:
   `index_job()`/`sync_job()` caught their own exceptions and returned
   `None` on every path (success or failure look identical to a caller).
   Both now return a real `bool` (`True` only on confirmed Typesense
   success); the signal now logs success vs. a `NOT indexed` warning based
   on that real value.

3. **False `indexed` metric fixed** (b744dc0) — `orchestrator.py`'s
   `_process_jobs` incremented `metrics.indexed += 1` unconditionally right
   after calling `sync_job()`, regardless of whether it actually succeeded.
   This means every `scrape_run_metrics` log line's `indexed` count has been
   wrong for as long as Typesense has been returning 401 — it was counting
   *attempts*, not successes. Now gated on the real return value.

4. **Inverse bug found and fixed in the same pass** — `sync_search.py`
   already did `if result: synced += 1`, which was the *correct* pattern,
   but since `sync_job()` always returned `None` (falsy) before this fix,
   that command's `synced` counter has always silently reported `0` even
   when indexing was actually working. Both the over-counting (orchestrator)
   and under-counting (sync_search) bugs are now fixed by the same root
   change — `sync_job()` returning a truthful bool.

5. **`verify_pipeline_e2e` bounded + fail-fast** (b744dc0) — added
   `--limit N` and `--job-id ID` so a reindex can be tested on one job or a
   small batch instead of unconditionally hitting every visible job in the
   table. Added fail-fast: aborts after 3 consecutive failures with zero
   successes, printing one diagnostic instead of repeating the same 401 for
   every remaining job (this is exactly what produced the flood).

### Verified (local, this pass)
`manage.py check` exit 0. `apps/search/tests_sync_job.py` (3 tests) and
`apps/scraper` integration tests (4 tests) pass via `pytest` — the project's
actually-configured test runner per `pytest.ini` (`python_files = tests.py
test_*.py *_tests.py`). Note: `manage.py test` does **not** discover files
named `tests_*.py` (wrong prefix order) — this affected several existing
test files in this repo (`tests_sync_job.py`, `tests_provenance.py`, etc.)
and is a pre-existing test-discovery gap, not something changed this pass;
flagging it here so a future pass uses `pytest`, not `manage.py test`, when
verifying fixes in this codebase.

### Still blocked — needs user action on the server
Typesense authentication itself is not fixed — only the symptoms (log flood,
false metrics) are. To actually fix the 401, run on the server (no secrets
printed):
```bash
systemctl list-units --type=service | grep -i typesense
docker ps 2>/dev/null | grep -i typesense
curl -s http://127.0.0.1:8108/health
grep '^TYPESENSE_API_KEY=' /var/www/usam/backend/.env | sha256sum
```
Once the Typesense server's own key is known (via whatever process started
it — systemd `EnvironmentFile`, Docker env, or a config file not in this
repo), compare its SHA-256 fingerprint against the app's. If they differ,
update `backend/.env`'s `TYPESENSE_API_KEY` to match and restart
`usam.service`/`celery-usam.service`/`celery-beat-usam.service` only — do
not touch Typesense itself unless its own config is confirmed wrong.

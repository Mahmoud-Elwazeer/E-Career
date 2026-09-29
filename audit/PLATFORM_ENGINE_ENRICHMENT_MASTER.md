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

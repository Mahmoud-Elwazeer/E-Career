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

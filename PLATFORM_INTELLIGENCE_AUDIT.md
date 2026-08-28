# Platform Intelligence & Automation Audit
## Comprehensive Architecture & Open-Source Integration Plan

**Date:** 2026-08-27
**Platform:** E-Career (jobs.usamif.com)
**Stack:** Django 4.2 + React/TypeScript + PostgreSQL + Redis + Celery + Typesense + Qdrant

---

## 1. Current Architecture

### Backend (26 Django Apps)

| App | Status | Purpose |
|-----|--------|---------|
| `accounts` | Production | Custom User (email-auth, UUID, roles, soft-delete, GDPR) |
| `users` | Production | User CRUD API |
| `profiles` | Production | User profiles with CV parser |
| `jobs` | Production | Job, Company, Source, Tag models + API |
| `employers` | Production | Employer Portal (postings, applications, candidate ranking, knockout questions, talent discovery) |
| `career` | Production | CareerProfile, CareerBrain, TalentScore, CareerGoal, CoverLetter, InterviewSession, CV Parser, Skill Gap, Onboarding |
| `rashid` | Production | AI Career Advisor (WebSocket + REST, encrypted messages, tools, rate limiting) |
| `intelligence` | Production | Centralized AI service with circuit breaker, LLM plugin architecture |
| `scraper` | Production | Job scraping pipeline (11 ATS scrapers, orchestrator, pipeline) |
| `search` | Production | Typesense primary + PostgreSQL fallback, embeddings, recommendations |
| `vectors` | Production | Qdrant vector search |
| `skills` | Production | ESCO/O*NET taxonomy, relationships, occupations, career paths |
| `emails` | Production | Multi-account rotation, templates, logs, tracking |
| `notifications` | Production | Multi-channel (email, in-app, push), quiet hours, batches |
| `analytics` | Production | Job views, clicks, search logs, dashboard |
| `salary` | Production | Salary intelligence |
| `assessment` | Production | Skills assessment platform |
| `interviews` | Production | Mock interviews (text/voice/coding) with AI evaluation |
| `resume` | Production | Resume builder |
| `verification` | Production | 6-stage Direct Apply URL verification engine |
| `events` | Production | Event system (emitter, consumers, types) |
| `monitoring` | Production | Health checks, performance metrics, error logs, uptime |
| `core` | Production | Base models, PlatformConfig, ProxyPool, Rule Engine, Feature Flags, GitHub Integration, GDPR |
| `ai` | Production | AWS Bedrock service singleton |

### Frontend (React + TypeScript)
- 22+ pages, Shadcn/UI components, Rashid AI widget
- i18n (Arabic/English), dark mode, animations
- TanStack Query, React Router 6, Recharts

### Infrastructure
- Docker Compose: PostgreSQL 16, Redis 7, Typesense 27.1, Daphne, Celery Worker (4), Celery Beat
- Qdrant (separate compose)
- AWS Bedrock (Claude, Llama, Gemma via model routing)
- Cohere Embed v3 (1024d vectors)
- Nginx reverse proxy, Let's Encrypt SSL

---

## 2. Existing Capabilities (STRENGTHS)

| Capability | Implementation | Quality |
|-----------|----------------|---------|
| AI Model Layer | Centralized with plugin architecture, circuit breaker, multi-model routing | Strong |
| Scraping | 11 ATS scrapers (Greenhouse, Lever, Ashby, BambooHR, Workday, SmartRecruiters, Workable, Teamtailor, iCIMS, Oracle, SAP) | Strong |
| Direct-Apply Verification | 6-stage pipeline (ATS Fingerprint, Redirect, Domain, Legitimacy, Freshness, Dedup) | Strong |
| Skills Taxonomy | ESCO/O*NET with relationships, occupations, career paths, job-skill mappings | Strong |
| CV Parsing | pdfplumber + python-docx + docling OCR + Bedrock AI extraction | Moderate |
| Search | Typesense (faceted) + Qdrant (semantic) + PostgreSQL (fallback) | Strong |
| Recommendations | LightFM hybrid (60% collaborative, 40% content-based) | Moderate |
| Rashid AI | WebSocket chat, 8 modes, 5 tools, encrypted messages, rate limiting | Strong |
| Automation | Celery + Beat with 12+ scheduled tasks | Strong |
| Email System | Multi-account rotation, templates, tracking pixels | Moderate |
| Employer Portal | Job postings, applications, AI ranking, knockout questions, talent discovery | Strong |
| Monitoring | Health checks, performance metrics, error logs, uptime, AI cost tracking | Moderate |
| Career Intelligence | CareerBrain, TalentScore, Goals, Skill Gap Analysis, Onboarding | Moderate |

---

## 3. Missing Capabilities

| Gap | Priority | Impact |
|-----|----------|--------|
| Research Engine (web/company/market research) | HIGH | Platform intelligence, content generation |
| Content Intelligence Pipeline (research → generation → review → publish) | HIGH | SEO, user engagement, authority |
| Trend Detection (skills, jobs, market, technology) | HIGH | Competitive advantage, recommendations |
| Advanced Document Processing (unified pipeline with chunking/embeddings) | MEDIUM | Better CV parsing, job description analysis |
| Knowledge Graph (entities → relationships → evidence) | MEDIUM | Traceable AI decisions, research quality |
| Marketing Intelligence (SEO, competitor, keyword) | MEDIUM | Growth, employer acquisition |
| Business Intelligence (conversion funnels, revenue, cohort analysis) | MEDIUM | Data-driven decisions |
| Email Verification (MX, SMTP, disposable detection) | MEDIUM | Employer trust, deliverability |
| Career Page Change Monitoring (detect new job postings) | MEDIUM | Fresher jobs, reduced load |
| Entrepreneurship Intelligence (startup/funding discovery) | LOW | Future expansion |
| Adaptive Scraping (survive page redesigns without code changes) | LOW | Reduced maintenance |

---

## 4. Weak/Incomplete Capabilities

| Capability | Current State | Enhancement Needed |
|-----------|--------------|-------------------|
| CV Parsing | Basic extraction → AI structuring | Add Docling for better multi-format support, LLM-driven entity extraction |
| Rashid Tools | 5 hardcoded tools | MCP-based dynamic tool discovery, call actual platform services |
| Recommendations | LightFM with basic features | Add embedding-based similarity, explanation generation |
| Analytics | Basic view/click tracking | Funnel analytics, cohort analysis, AI decision audit trail |
| Skills Matching | ESCO taxonomy lookup | Semantic embedding-based matching, confidence scores |
| Content | None | Evidence-based generation pipeline |
| Trend Detection | None | BERTopic on job postings over time |
| Email Verification | Basic format check | MX + SMTP + disposable detection |

---

## 5. Duplicate Systems

| Function | Instances | Resolution |
|----------|-----------|-----------|
| AI Service | `backend/ai/bedrock.py` (singleton) + `backend/apps/intelligence/service.py` (plugin arch) + `backend/apps/ai/` | **Consolidate into `intelligence` app** — it has the plugin architecture and circuit breaker. The `backend/ai/bedrock.py` singleton should become the Bedrock plugin. Remove `backend/apps/ai/`. |
| CV Parsing | `backend/apps/career/cv_parser.py` + `backend/ai/bedrock.py:parse_cv()` | **Keep in `career` app** — it orchestrates extraction + taxonomy mapping. Remove standalone `parse_cv()` from bedrock.py. |
| Recommendation | `backend/apps/intelligence/recommendation_service.py` + `backend/apps/search/recommendation_engine.py` | **Consolidate into `search` app** — it owns the ML engine (LightFM). Intelligence app should call search's recommendation service. |
| Notification dispatch | `backend/apps/core/notification_service.py` + `backend/apps/notifications/` | **Consolidate into `notifications` app** — remove from core. |

---

## 6. Conflicting Systems

No critical conflicts found. The duplicate AI services use the same underlying Bedrock provider — consolidation is straightforward without behavioral changes.

---

## 7. Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                             │
│  Pages → Components → Hooks → API Client → WebSocket (Rashid)       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                      API GATEWAY (Django REST)                        │
│  Authentication → Rate Limiting → Routing → Serialization            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                    INTELLIGENCE LAYER (Unified)                       │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Model Router  │  │ Pydantic AI  │  │  MCP Tool Registry       │  │
│  │ (Bedrock)    │  │ (Agent Core) │  │  (Dynamic Discovery)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              RASHID (Unified AI Interface)                     │   │
│  │  Tools: Job Search | CV Analysis | Skills | Interview |       │   │
│  │         Research | Recommendations | Career Path              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                     SERVICE LAYER (Domain Apps)                       │
│                                                                      │
│  Jobs │ Skills │ Career │ Employers │ Search │ Scraper │ Verification│
│  Resume │ Interviews │ Salary │ Assessment │ Notifications │ Email   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                    AUTOMATION LAYER (Celery + Prefect)                │
│                                                                      │
│  Celery: Simple tasks, notifications, periodic jobs                  │
│  Prefect: Complex AI pipelines, research jobs, content generation    │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │ Scraping    │  │ Research     │  │ Content Generation       │    │
│  │ Pipeline    │  │ Pipeline     │  │ Pipeline                 │    │
│  └────────────┘  └──────────────┘  └──────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                      DATA LAYER                                       │
│                                                                      │
│  PostgreSQL (primary) │ Redis (cache/broker) │ Typesense (search)    │
│  Qdrant (vectors) │ Cohere (embeddings)                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Open-Source Candidates (Evaluated)

### Mandatory Repository Review

| Repository | Stars | License | Decision | Reason |
|-----------|-------|---------|----------|--------|
| JOYCEQL/magic-resume | 10.2k | Restricted (not Apache 2.0 for commercial) | **E. REJECT** | Commercial SaaS use explicitly prohibited. Reference patterns only. |
| MadsLorentzen/ai-job-search | 36.6k | MIT | **D. REFERENCE** | Personal CLI tool on Claude Code. Patterns: portal scraper architecture, drafter-reviewer, verification gates. |
| santifer/career-ops | 68.7k | MIT | **D. REFERENCE** | Local agent skill (JS). Patterns: ATS adapter patterns (Greenhouse/Ashby/Lever/Wellfound), evaluation rubric, portal scanning. |
| d4vinci/Scrapling | 76.7k | BSD-3 | **C. WRAP/INTEGRATE** | Production-ready adaptive scraping. Enhance existing scraper infrastructure. |

### Additional Discoveries

| Tool | Category | Stars | License | Decision |
|------|----------|-------|---------|----------|
| **GPT Researcher** | Research Engine | 29.2k | Apache 2.0 | **C. WRAP** — pip-installable, REST API |
| **last30days-skill** | Multi-platform Intelligence | 59.4k | MIT | **D. REFERENCE** — Agent skill pattern |
| **Docling** | Document Processing | 65.6k | MIT | **A. USE DIRECTLY** — Replace/enhance CV parsing |
| **BERTopic** | Trend Detection | 7.8k | MIT | **A. USE DIRECTLY** — Batch topic modeling |
| **Crawl4AI** | LLM Extraction | 79.5k | Apache 2.0 | **C. WRAP** — For unknown page layouts |
| **changedetection.io** | Change Monitoring | 33.4k | Apache 2.0 | **A. USE DIRECTLY** — Monitor career pages |
| **Pydantic AI** | Agent Framework | 19.5k | MIT | **A. USE DIRECTLY** — Rashid agent core |
| **MCP Python SDK** | Tool Protocol | Official | MIT | **A. USE DIRECTLY** — Tool registry |
| **ESCO Skill Extractor** | Skills Intelligence | 31 | MIT | **C. WRAP/ADAPT** — Enhance skills matching |
| **python-email-validator** | Email Verification | 1.4k | Unlicense | **A. USE DIRECTLY** — Registration validation |
| **disposable-email-domains** | Spam Prevention | 5.5k | CC0 | **A. USE DIRECTLY** — Block fake registrations |
| **Reacher** | Deep Email Verification | 9.5k | AGPL | **C. WRAP** — Docker API for deep checks |
| **Jobseek** | Direct-Employer Sourcing | 184 | MIT (code) | **D. REFERENCE** — Architecture patterns |
| **Freehire** | Job Deduplication | 498 | MIT | **D. REFERENCE** — Fingerprint dedup, ghost job detection |
| **pytrends-modern** | Google Trends | 61 | MIT | **A. USE DIRECTLY** — Keyword tracking |
| **GraphRAG** | Knowledge Graphs | 35.7k | MIT | **D. REFERENCE** — Architecture pattern |
| **Hyper-Extract** | Entity Extraction | 3.4k | Apache 2.0 | **D. REFERENCE** — Template-based extraction |
| **WorkRB** | Skills Benchmark | 41 | Apache 2.0 | **D. REFERENCE** — Evaluate matching models |
| **Prefect** | Workflow Orchestration | 23.7k | Apache 2.0 | **A. USE DIRECTLY** — Complex pipelines (later) |
| **LangGraph** | Stateful Workflows | 40.5k | MIT | **D. REFERENCE** — Only if needed |
| **Browserable** | Browser Automation | 1.2k | MIT | **E. REJECT** — Too heavy (8+ services) |
| **TheAgenticBrowser** | Browser Agents | 425 | Restrictive | **E. REJECT** — Dead project, restrictive license |
| **Firecrawl Web-Agent** | Research Agent | 1.2k | MIT | **D. REFERENCE** — Skills/playbook pattern |

---

## 9. License Risks

| Tool | License | Risk | Mitigation |
|------|---------|------|-----------|
| Magic Resume | Fake Apache 2.0 (commercially restricted) | Cannot use code | Reference patterns only, reimplement independently |
| Reacher | AGPL-3.0 | Must open-source modifications to the server itself | Use via Docker API as external service (not modification) |
| PyMuPDF | AGPL-3.0 | Copyleft for network services | Use pdfplumber (MIT) or Docling (MIT) instead |
| Firecrawl | AGPL-3.0 (core) | Copyleft if self-hosted | Use Crawl4AI (Apache-2.0) instead |
| Khoj | AGPL-3.0 | Cannot embed | Reference only |
| changedetection.io | Apache-2.0 | None | Safe for commercial use |
| n8n | Sustainable Use License | Commercial restrictions | Do not use |
| TheAgenticBrowser | Custom restrictive | Prohibits competing products | Do not use |

**All recommended "USE DIRECTLY" tools have permissive licenses (MIT, Apache 2.0, BSD-3, CC0, Unlicense).**

---

## 10. Integration Decisions

### Immediate (Phase 1 — Foundation)

| Integration | What | How | Effort |
|------------|------|-----|--------|
| Pydantic AI | Replace ad-hoc Bedrock calls with typed agent | Refactor `intelligence` app to use Pydantic AI agents with Bedrock | 2 weeks |
| MCP Protocol | Expose platform services as MCP tools for Rashid | Create MCP servers for jobs, skills, career, search | 2 weeks |
| Docling | Enhance CV parsing | Add as extraction layer before AI structuring | 1 week |
| python-email-validator + disposable-email-domains | Email verification | Add to employer registration flow | 2 days |

### Short-term (Phase 2 — Intelligence Enhancement)

| Integration | What | How | Effort |
|------------|------|-----|--------|
| Scrapling | Adaptive scraping for unknown career pages | Add as alternative fetcher alongside existing ATS scrapers | 1 week |
| ESCO Skill Extractor | Semantic skill matching | Enhance existing skills app with embedding-based extraction | 1 week |
| BERTopic | Trend detection on job postings | Celery task: weekly topic modeling on new job descriptions | 1 week |
| changedetection.io | Monitor employer career pages | Docker service, webhook triggers scraping pipeline | 3 days |

### Medium-term (Phase 3 — Research & Content)

| Integration | What | How | Effort |
|------------|------|-----|--------|
| GPT Researcher | Research engine for company/market intelligence | Celery task wrapper, results stored in knowledge base | 2 weeks |
| Crawl4AI | LLM-based extraction for varied page layouts | Fallback when CSS/XPath selectors fail | 1 week |
| pytrends-modern | Skill/job keyword trend tracking | Weekly Celery task, store time-series data | 3 days |
| Prefect | Complex pipeline orchestration | Add for research + content generation workflows | 2 weeks |

### Long-term (Phase 4 — Advanced Intelligence)

| Integration | What | How | Effort |
|------------|------|-----|--------|
| Knowledge Graph (custom, inspired by GraphRAG) | Evidence-based AI responses | PostgreSQL + ltree for entity relationships | 4 weeks |
| Content Pipeline | Research → Generate → Review → Publish | Prefect workflow with human approval gates | 4 weeks |
| Reacher | Deep email verification | Docker service for employer email validation | 1 week |
| FORGE/Dataforge | Company enrichment | Discover employer contact pages, tech stacks | 2 weeks |

---

## 11. Build vs. Buy vs. Adapt Decisions

| Capability | Decision | Rationale |
|-----------|----------|-----------|
| AI Agent Framework | **USE** Pydantic AI | MIT, native Bedrock, production-ready, type-safe |
| Scraping Core | **KEEP** existing + **ENHANCE** with Scrapling | Already have 11 ATS scrapers; Scrapling adds adaptive parsing |
| Document Processing | **REPLACE** with Docling for parsing layer | MIT, 65k stars, IBM-backed, handles all formats better |
| Skills Taxonomy | **KEEP** existing ESCO/O*NET | Already implemented; enhance with ESCO Skill Extractor embeddings |
| Search | **KEEP** Typesense + Qdrant | Already production, well-architected |
| Recommendations | **KEEP** LightFM + **ENHANCE** | Add explanation generation via Pydantic AI |
| CV Generation | **BUILD** (reference Magic Resume patterns) | Cannot use Magic Resume license; build independently |
| Research Engine | **WRAP** GPT Researcher | Apache 2.0, pip-installable, REST API |
| Trend Detection | **USE** BERTopic | MIT, mature, fits our batch processing model |
| Change Monitoring | **USE** changedetection.io | Apache 2.0, Docker, webhook integration |
| Workflow Orchestration | **KEEP** Celery + **ADD** Prefect later | Already have Celery; Prefect for complex pipelines |
| Email Verification | **USE** python-email-validator + **WRAP** Reacher | Permissive + Docker API for deep verification |
| Knowledge Graph | **BUILD** (inspired by GraphRAG patterns) | Custom fits better than heavyweight GraphRAG dependency |
| Content Generation | **BUILD** | Platform-specific pipeline with evidence + approval |
| Business Intelligence | **BUILD** | Platform-specific metrics and funnels |
| Marketing Intelligence | **BUILD** + pytrends-modern | Custom + Google Trends for keyword intelligence |

---

## 12. AI Model Strategy

### Current (Already Implemented)
```
Model Router (backend/apps/intelligence/)
├── Primary: meta.llama4-scout-17b-instruct-v1:0
├── Secondary: google.gemma-4-e2b
└── Task Routing:
    ├── Rashid Chat → Llama
    ├── CV Parsing → Gemma
    ├── Matching → Llama
    └── Complex Analysis → Claude Sonnet (Bedrock)
```

### Recommended Enhancement

| Task Category | Model | Reasoning |
|--------------|-------|-----------|
| Chat/Conversation (Rashid) | Llama 4 Scout (17B) | Fast, cheap, good for conversational |
| Structured Extraction (CV, JD) | Gemma 4 E2B | Good at following schemas |
| Complex Analysis (matching, ranking) | Claude Sonnet | Best reasoning quality |
| Embeddings | Cohere Embed v3 | Already integrated, 1024d |
| Bulk Classification | Llama 4 Scout | Cost-efficient for high volume |
| Content Generation | Claude Sonnet | Quality matters for published content |
| Research Synthesis | Claude Sonnet | Complex multi-source reasoning |
| Simple Validation | Llama 4 Scout | Cheapest for binary decisions |

### Principles
1. **Least expensive model that reliably satisfies quality** — never auto-use strongest
2. **Circuit breaker** on all providers (already implemented)
3. **Token/cost tracking** per user per task (already implemented via RashidUsage)
4. **Fallback chain**: Primary → Secondary → Cached response → Graceful degradation
5. **No direct model calls** outside the intelligence service

---

## 13. Research Architecture

```
┌──────────────────────────────────────────────────┐
│              RESEARCH ENGINE                       │
│                                                   │
│  Input: Topic/Query + Research Type + Depth       │
│                                                   │
│  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ GPT         │  │ Platform Data Sources     │  │
│  │ Researcher  │  │ (Jobs, Skills, Companies) │  │
│  │ (Web)       │  │                           │  │
│  └─────────────┘  └──────────────────────────┘  │
│         │                    │                    │
│         └────────┬───────────┘                   │
│                  │                                │
│  ┌──────────────┴──────────────────────────┐    │
│  │        Evidence Collection               │    │
│  │  Source + Timestamp + Confidence +       │    │
│  │  Contradiction Detection                 │    │
│  └──────────────┬──────────────────────────┘    │
│                  │                                │
│  ┌──────────────┴──────────────────────────┐    │
│  │        Synthesis (Claude Sonnet)         │    │
│  │  Structured output with citations        │    │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  Output: Report + Sources + Confidence Scores     │
└──────────────────────────────────────────────────┘
```

**Research Types:**
- Company Research → Scrape public pages + news + reviews
- Market Research → Job trends + skill demand + salary data
- Career Research → Paths + skills needed + gap analysis
- Technology Research → Trends + adoption + learning resources

**Storage:** Research results stored with provenance (source, timestamp, confidence, methodology).

---

## 14. Scraping Architecture

### Current (Keep)
```
Orchestrator (Celery Beat: every 6 hours)
├── ATS Scrapers (11 platforms)
│   ├── Greenhouse, Lever, Ashby, BambooHR
│   ├── Workday, SmartRecruiters, Workable
│   ├── Teamtailor, iCIMS, Oracle, SAP
│   └── Each with: rate limiting, auto-disable on 5 failures
├── Pipeline
│   ├── URL Resolver → Legitimacy Scorer → Deduplicator → Normalizer
│   └── Trust Score enforcement (min 0.4)
├── Regional: JobSpy wrapper
└── Discovery: Common Crawl
```

### Enhancement (Add)
```
changedetection.io (monitors career pages for changes)
    │
    │ webhook: "page changed"
    ▼
Scrapling (adaptive fetcher)
    │
    ├── Known ATS → Existing scrapers (CSS/XPath)
    ├── Unknown layouts → Crawl4AI (LLM extraction)
    └── Anti-detection: TLS fingerprint, AutoThrottle, robots.txt
    │
    ▼
Existing Pipeline (URL Resolver → Legitimacy → Dedup → Normalize)
    │
    ▼
Verification Engine (6-stage pipeline, unchanged)
```

**Key enhancement:** Monitor-then-scrape instead of blind periodic crawling. Reduces load, improves freshness, respects employer servers.

---

## 15. Document Intelligence Architecture

### Current
- pdfplumber (PDF text extraction)
- python-docx (DOCX parsing)
- docling (OCR for images)
- Bedrock AI (structured extraction from raw text)

### Enhanced (Add Docling as primary)
```
Document Input (PDF, DOCX, TXT, Images)
    │
    ▼
Docling (MIT, IBM-backed)
    ├── Layout analysis
    ├── Table structure recognition
    ├── Formula extraction
    ├── Multi-format support
    └── Output: Structured Markdown/JSON
    │
    ▼
LLM Entity Extraction (Pydantic AI + Bedrock)
    ├── Skills extraction → ESCO mapping
    ├── Experience extraction → Timeline
    ├── Education extraction → Credentials
    ├── Achievement extraction → Quantified results
    └── Output: Typed Pydantic models
    │
    ▼
Embedding Generation (Cohere)
    │
    ▼
Storage (PostgreSQL JSON + Qdrant vectors)
```

---

## 16. Skills Intelligence Architecture

### Current (Already Strong)
- ESCO/O*NET taxonomy imported
- Skill relationships (graph edges)
- Occupation-skill mappings
- Career path modeling
- User skill proficiency tracking
- Skill gap analysis service

### Enhancement
```
Existing Skills App
    │
    ├── ADD: ESCO Skill Extractor (embedding-based matching)
    │   └── When exact taxonomy match fails, find closest semantic match
    │
    ├── ADD: BERTopic (skill trend detection)
    │   └── Weekly: model topics from new job descriptions
    │   └── Track emergence/decline of skills over time
    │
    ├── ADD: Confidence scores on skill extractions
    │   └── High (exact ESCO match) / Medium (semantic) / Low (inferred)
    │
    └── ADD: Skill demand index
        └── Count skill mentions across active jobs
        └── Track change rate week-over-week
```

---

## 17. Content Intelligence Architecture (NEW)

```
Research Layer (GPT Researcher + Platform Data)
    │
    ▼
Evidence Storage (PostgreSQL)
    ├── Source URL + fetch timestamp
    ├── Extracted claims + confidence
    ├── Contradictions flagged
    └── Freshness score
    │
    ▼
Content Generation (Pydantic AI + Claude Sonnet)
    ├── Input: Evidence bundle + content type + audience
    ├── Output: Draft with inline citations
    └── Structured: title, summary, body, sources, keywords
    │
    ▼
Review Gate (Admin Dashboard)
    ├── Quality score (automated)
    ├── Factual accuracy check
    ├── Human approval required for publication
    └── Rejection → feedback loop to improve generation
    │
    ▼
Publishing (Django CMS-like system)
    ├── SEO metadata (auto-generated)
    ├── Personalization tags (industry, role, level)
    ├── Freshness expiry date
    └── Analytics tracking
```

**Content Types:**
- Career tips, Industry insights, Job-market reports
- Company spotlights, Skill trend analyses
- Interview advice, CV tips, Salary guides

---

## 18. Marketing Intelligence Architecture (NEW)

```
┌─────────────────────────────────────────────┐
│          MARKETING INTELLIGENCE              │
│                                              │
│  pytrends-modern → Keyword trends            │
│  Platform analytics → User behavior          │
│  Job data → Market demand signals            │
│  Competitor monitoring → Content gaps         │
│                                              │
│  Outputs:                                    │
│  ├── Keyword opportunities (trending up)     │
│  ├── Content gap analysis                    │
│  ├── Employer acquisition targets            │
│  ├── User acquisition channels               │
│  └── SEO recommendations                     │
└─────────────────────────────────────────────┘
```

---

## 19. Business Intelligence Architecture (ENHANCE)

### Current (Basic)
- Job views, clicks, search logs
- Performance metrics

### Enhanced
```
Event System (already exists: backend/apps/events/)
    │
    ▼
Analytics Pipeline (Celery tasks)
    ├── Funnel metrics: Visit → Search → View → Apply → Interview → Hire
    ├── Employer metrics: Post → Views → Applications → Hires → Retention
    ├── Recommendation performance: Shown → Clicked → Applied → Outcome
    ├── Rashid metrics: Conversations → Tool usage → Satisfaction
    ├── Scraper health: Sources → Success rate → Freshness → Coverage
    └── Revenue: Packages → Usage → Conversion → Churn
    │
    ▼
Dashboard (Admin, already exists — enhance with Recharts)
```

---

## 20. Entrepreneurship Intelligence Architecture (FUTURE)

**Approach:** Lightweight, content-first. Do NOT build a startup database.

```
Research Engine (same as Section 13)
    │
    ├── Startup job detection (scraper signals: "Series A", "founding team")
    ├── Funding news aggregation (via GPT Researcher)
    ├── Accelerator/incubator career pages (add to scraper sources)
    └── Entrepreneurship content generation
    │
    ▼
Content: "Startup Jobs" category + "Entrepreneurship" career path
```

---

## 21. Email Intelligence Architecture (ENHANCE)

### Current
- Multi-account email sending with rotation
- Templates, tracking pixels, rate limiting

### Enhanced
```
Registration/Employer Verification:
    python-email-validator (syntax + MX)
    + disposable-email-domains (block throwaway)
    + Custom domain verification (SPF, DMARC via dnspython)
    │
    ▼
Async Deep Verification (Celery task):
    Reacher Docker API (SMTP mailbox check, catch-all detection)
    │
    ▼
Company Contact Discovery (for employer outreach):
    FORGE/Dataforge (public career page crawling, contact extraction)
    │
    ▼
Compliance Layer:
    ├── Double opt-in for all employer communications
    ├── Suppression list (bounces, complaints, opt-outs)
    ├── Consent timestamp storage (GDPR Article 7)
    └── 10-day unsubscribe honor (CAN-SPAM)
```

---

## 22. Automation Architecture (ENHANCE)

### Current (Keep)
```
Celery + django-celery-beat
├── 12+ scheduled tasks (scraping, verification, alerts, digests, etc.)
├── 4 worker concurrency
├── Redis broker
└── Flower monitoring
```

### Enhancement (Add Prefect for complex pipelines only)
```
Simple Tasks → Celery (unchanged)
    ├── Send notification
    ├── Process single job
    ├── Send email
    └── Quick background computation

Complex Pipelines → Prefect (new)
    ├── Research job (multi-step: query → fetch → analyze → synthesize → store)
    ├── Content generation (research → draft → review → publish)
    ├── Bulk re-verification (thousands of URLs with throttling)
    └── AI training data preparation (extract → validate → format → upload)
```

---

## 23. Rashid Integration (ENHANCE)

### Current
- WebSocket + REST chat
- 8 modes (Career Path, CV Review, LinkedIn, Cover Letter, Interview, Course, Salary, General)
- 5 tools (hardcoded)
- Rate limiting, encryption

### Enhanced (Pydantic AI + MCP)
```
Rashid Agent (Pydantic AI)
    │
    ├── Model: Bedrock (Llama 4 for chat, Claude for complex)
    ├── Memory: Conversation history (PostgreSQL, encrypted)
    ├── Context: User profile, career state, recent activity
    │
    └── MCP Tool Registry (dynamic discovery)
        ├── job_search → Search service (Typesense + Qdrant)
        ├── cv_analysis → Career CV parser service
        ├── skill_gap → Skills app service
        ├── interview_prep → Interviews app service
        ├── company_research → Research engine
        ├── salary_insight → Salary app service
        ├── career_path → Skills career path service
        ├── recommendation_explain → Search recommendation engine
        ├── application_status → Employers app service
        └── market_trends → Trend detection service (BERTopic)
```

**Key change:** Rashid calls ACTUAL platform services via MCP tools instead of generating text independently. Every response backed by real platform data.

---

## 24. Admin Control Architecture (ENHANCE)

### Current
- AdminDashboard (frontend)
- Django Admin
- admin-api endpoints

### Enhanced (expose all intelligence systems)
```
Admin Dashboard Sections:
├── Sources & Scrapers
│   ├── Source health (success rate, last run, auto-disabled)
│   ├── changedetection.io status
│   ├── Add/edit/disable sources
│   └── Manual trigger scrape
├── AI & Models
│   ├── Model routing configuration
│   ├── Cost tracking per model per task
│   ├── Circuit breaker status
│   └── Token usage analytics
├── Research & Content
│   ├── Research job queue
│   ├── Content review/approval queue
│   ├── Published content management
│   └── Evidence/source quality scores
├── Skills & Taxonomy
│   ├── Skill demand dashboard
│   ├── Emerging skills (BERTopic output)
│   ├── Taxonomy health (unmapped skills)
│   └── Manual skill relationship editing
├── Verification
│   ├── Trust score distribution
│   ├── Failed verifications
│   ├── Blocked domains list
│   └── Manual override capability
├── Automation
│   ├── Celery task status (Flower embed)
│   ├── Prefect flow status (when added)
│   ├── Pipeline health
│   └── Schedule management
├── Email
│   ├── Delivery rates per account
│   ├── Bounce/complaint tracking
│   ├── Suppression list
│   └── Verification status of employers
└── Analytics & BI
    ├── Funnel metrics
    ├── Revenue/conversion
    ├── User cohorts
    └── Recommendation performance
```

---

## 25. Security/Privacy Requirements

| Requirement | Current Status | Action Needed |
|-------------|---------------|---------------|
| Data encryption at rest | Rashid messages encrypted (Fernet) | Extend to all PII fields |
| GDPR compliance | GDPR export/delete implemented | Add data processing records |
| API rate limiting | 30/min anon, 100/min auth | Keep, add per-endpoint limits |
| JWT security | 15min access, 7-day refresh, rotation + blacklisting | Keep |
| Input validation | Django serializers + Zod (frontend) | Keep |
| Scraping ethics | robots.txt compliance, rate limiting, auto-disable | Add: ToS monitoring |
| AI safety | Rashid rate limiting, encrypted chats | Add: output filtering, prompt injection defense |
| Email compliance | Rate limiting, rotation | Add: double opt-in, suppression lists |
| Dependency security | Pre-commit hooks | Add: automated CVE scanning (Dependabot/Snyk) |
| Secret management | .env files | Consider: AWS Secrets Manager for production |

---

## 26. Production Requirements

| Requirement | Current Status | Enhancement |
|-------------|---------------|-------------|
| Reliability | Circuit breaker on AI, Typesense fallback to PostgreSQL | Add: fallback on all external services |
| Observability | Health checks, performance metrics, error logs, Sentry | Add: structured logging (JSON), distributed tracing |
| Scheduling | Celery Beat (12+ tasks) | Add: Prefect for complex pipelines |
| Retry policies | Celery retry with backoff | Keep + add dead-letter queue monitoring |
| Caching | Redis | Add: cache invalidation strategies per entity type |
| Idempotency | Not documented | Add: idempotency keys on critical API endpoints |
| Cost monitoring | AI cost tracking exists | Add: per-user cost alerts, budget caps |
| Data quality | Verification pipeline | Add: automated quality scoring on scraped jobs |
| Versioning | API v1 prefix | Keep, plan v2 for breaking changes |

---

## 27. Observability Requirements

```
Existing:
├── Sentry (error tracking)
├── PerformanceMetric model (CPU, memory, response times)
├── HealthCheck model (DB, Redis, Qdrant, Celery, API)
├── UptimeRecord model
└── AI Cost monitoring

Add:
├── Structured JSON logging (replace print statements)
├── Request tracing (correlation IDs across services)
├── Celery task observability (success rate, duration histograms)
├── Scraper observability (per-source success rate dashboard)
├── AI observability (latency percentiles, token usage per task type)
└── Alerting (PagerDuty/Slack on critical failures)
```

---

## 28. Data Architecture

```
PostgreSQL 16 (Primary Store)
├── All Django models (accounts, jobs, careers, etc.)
├── JSON fields for flexible schema (cv_parsed_data, etc.)
├── ltree for hierarchical data (skill taxonomy, categories)
├── Full-text search (fallback when Typesense unavailable)
└── TimescaleDB extension (future: time-series analytics)

Redis 7 (Cache + Broker)
├── Celery task broker
├── API response cache (15min TTL)
├── Session store
├── Rate limiting counters
└── Real-time WebSocket state

Typesense 27.1 (Search Engine)
├── Job listings (full-text + faceted)
├── Autocomplete
└── Trust score enforcement

Qdrant (Vector Store)
├── Job embeddings (Cohere 1024d)
├── Skill embeddings
├── CV embeddings
└── Semantic similarity search

Future Additions:
├── Knowledge base table (research evidence, sources, confidence)
├── Content table (articles, generated content with sources)
├── Trend time-series (skill demand over time)
└── Audit trail (AI decisions with reasoning)
```

---

## 29. API/Service Boundaries

```
Public API (Django REST Framework):
├── /api/v1/auth/ — Authentication (JWT)
├── /api/v1/jobs/ — Job listings (CRUD, search, filters)
├── /api/v1/profile/ — User profile management
├── /api/v1/career/ — Career intelligence (brain, score, goals)
├── /api/v1/skills/ — Skills taxonomy and user skills
├── /api/v1/employer/ — Employer portal
├── /api/v1/search/ — Unified search (text + semantic)
├── /api/v1/rashid/ — AI chat (REST + WebSocket)
├── /api/v1/interviews/ — Mock interviews
├── /api/v1/resume/ — Resume builder
├── /api/v1/notifications/ — User notifications
└── /api/v1/salary/ — Salary intelligence

Internal Services (Celery tasks, not HTTP):
├── Scraping pipeline (orchestrator → ATS scrapers → pipeline)
├── Verification engine (6-stage)
├── Recommendation engine (LightFM)
├── AI services (Bedrock calls via intelligence app)
├── Email dispatch (rotation, tracking)
├── Research engine (when added)
└── Content pipeline (when added)

Admin API:
├── /api/v1/admin-api/ — Platform management
├── /api/v1/monitoring/ — Health + metrics
└── /api/v1/core/ — Rules, features, config
```

---

## 30. Implementation Dependencies

```
Phase 1 (Foundation) — No external dependencies
├── Consolidate duplicate AI services
├── Add Pydantic AI + MCP to intelligence app
├── Integrate Docling for document processing
├── Add email verification libraries
└── Prerequisites: None

Phase 2 (Intelligence Enhancement) — Depends on Phase 1
├── Scrapling integration (depends on: intelligence consolidation)
├── ESCO Skill Extractor enhancement (depends on: Pydantic AI)
├── BERTopic trend detection (depends on: job data pipeline)
├── changedetection.io (depends on: scraper infrastructure)
└── Prerequisites: Phase 1 complete

Phase 3 (Research & Content) — Depends on Phase 2
├── GPT Researcher integration (depends on: Pydantic AI agents)
├── Crawl4AI for diverse pages (depends on: Scrapling base)
├── Content pipeline (depends on: research engine)
├── Prefect for complex workflows (depends on: pipeline maturity)
└── Prerequisites: Phase 2 complete, research engine design

Phase 4 (Advanced) — Depends on Phase 3
├── Knowledge graph (depends on: research engine + content pipeline)
├── Full Rashid MCP integration (depends on: all services as MCP tools)
├── Business intelligence (depends on: event system maturity)
├── Admin dashboard enhancements (depends on: all systems operational)
└── Prerequisites: Phase 3 complete
```

---

## 31. Priority

| # | Initiative | Priority | Business Value | Effort | Risk |
|---|-----------|----------|---------------|--------|------|
| 1 | Consolidate duplicate AI services | Critical | Maintainability | 1 week | Low |
| 2 | Pydantic AI + MCP for Rashid | High | User experience, extensibility | 3 weeks | Medium |
| 3 | Docling document processing | High | CV parsing quality | 1 week | Low |
| 4 | Email verification (employer trust) | High | Platform integrity | 3 days | Low |
| 5 | Scrapling adaptive scraping | High | Scraper maintenance reduction | 1 week | Low |
| 6 | BERTopic trend detection | Medium | Content, recommendations | 1 week | Low |
| 7 | changedetection.io monitoring | Medium | Job freshness | 3 days | Low |
| 8 | ESCO Skill Extractor enhancement | Medium | Matching quality | 1 week | Low |
| 9 | GPT Researcher (research engine) | Medium | Platform intelligence | 2 weeks | Medium |
| 10 | Content generation pipeline | Medium | SEO, authority, engagement | 4 weeks | Medium |
| 11 | Prefect orchestration | Low (now) | Complex pipeline management | 2 weeks | Low |
| 12 | Knowledge graph | Low (now) | AI traceability | 4 weeks | High |
| 13 | Marketing intelligence | Low (now) | Growth | 3 weeks | Medium |
| 14 | Entrepreneurship section | Low | Future expansion | 2 weeks | Low |

---

## 32. Execution Phases

### Phase 1: Foundation Consolidation (Weeks 1-3)
- Consolidate AI services into single `intelligence` app
- Add Pydantic AI as agent framework
- Implement MCP tool servers for core services
- Integrate Docling for document processing
- Add email verification libraries
- **Deliverable:** Unified AI layer, Rashid calling real services

### Phase 2: Intelligence Enhancement (Weeks 4-6)
- Integrate Scrapling for adaptive scraping
- Deploy changedetection.io for career page monitoring
- Add ESCO Skill Extractor for semantic skill matching
- Implement BERTopic trend detection (weekly batch)
- Enhance Rashid with MCP tools (job search, skills, career)
- **Deliverable:** Smarter scraping, skill trends, Rashid with real data

### Phase 3: Research & Content (Weeks 7-12)
- Implement research engine (GPT Researcher wrapper)
- Build content generation pipeline with evidence
- Add Crawl4AI for diverse page extraction
- Add Prefect for complex pipelines
- Implement admin content review/approval
- **Deliverable:** Automated evidence-based content, research capabilities

### Phase 4: Advanced Intelligence (Weeks 13-20)
- Build knowledge graph (PostgreSQL + ltree)
- Full business intelligence dashboard
- Marketing intelligence (pytrends + SEO)
- Complete Rashid MCP integration (all services)
- Reacher email deep verification
- Company enrichment (FORGE/Dataforge patterns)
- **Deliverable:** Complete intelligence ecosystem

---

## 33. Acceptance Criteria

| Phase | Criteria |
|-------|---------|
| Phase 1 | All AI calls route through single intelligence service; Rashid uses Pydantic AI agent; CV parsing accuracy improves measurably with Docling; email verification blocks disposable domains |
| Phase 2 | Career page changes detected within 1 hour; skill trends visible in admin; adaptive scraping handles at least 3 non-ATS career pages without custom code |
| Phase 3 | Research engine produces company reports with 5+ citations; content pipeline generates articles requiring < 20% human editing; admin can approve/reject content |
| Phase 4 | All AI responses traceable to source data; funnel analytics show full journey; Rashid can answer questions using all platform services |

---

## 34. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Pydantic AI breaking changes (fast-moving project) | Medium | High | Pin version, test suite, wrap in adapter |
| GPT Researcher cost at scale | Medium | Medium | Rate limit research jobs, cache results, use Llama for simple queries |
| Scrapling not mature enough for edge cases | Low | Medium | Fallback to existing ATS scrapers (already working) |
| BERTopic GPU requirements | Medium | Low | Use CPU mode (slower but functional), or spot GPU instances |
| changedetection.io resource usage | Low | Low | Monitor Docker container, limit concurrent checks |
| Employer career pages blocking us | Medium | Medium | Scrapling anti-detection + proxy rotation (already have ProxyPool) |
| Content quality without human review | High | High | Mandatory admin approval gate, never auto-publish |
| Scope creep from intelligence features | High | Medium | Strict phase gates, do not start Phase N+1 until Phase N meets acceptance criteria |

---

## 35. Open Questions

1. **Hosting budget for new services** — changedetection.io + Reacher Docker containers need additional server resources. Current EC2 instance sufficient?
2. **BERTopic GPU** — Should we run on CPU (slower, cheaper) or add GPU spot instance for weekly batch?
3. **Prefect hosting** — Self-hosted Prefect Server or Prefect Cloud (managed)?
4. **Content approval workflow** — Who reviews generated content? Single admin or editorial team?
5. **Research engine rate limits** — How many research jobs per day? (API costs scale linearly)
6. **Knowledge graph scope** — Start with skills/jobs entities only, or include companies/people from day one?
7. **MCP server deployment** — In-process (same Django server) or separate microservices?
8. **Reacher AGPL** — Legal review needed: does calling via Docker HTTP API constitute "modification" under AGPL?

---

## 36. Explicitly Rejected Ideas and Why

| Idea | Reason for Rejection |
|------|---------------------|
| **Use Magic Resume in production** | License explicitly prohibits commercial SaaS use |
| **Replace Celery with Temporal** | Operational complexity too high for current team size; Celery works fine for 80% of tasks |
| **Use n8n for automation** | Restrictive license (Sustainable Use), wrong tech stack (Node.js), poor Django integration |
| **Use Airflow** | Designed for data engineering ETL, massive operational overhead, overkill for application tasks |
| **Use BullMQ** | Node.js-first; Python SDK is second-class citizen |
| **Use Dagster** | Asset-centric model is wrong paradigm for task-oriented automation |
| **Use TheAgenticBrowser** | Restrictive custom license, abandoned (18 months dormant, 18 commits total) |
| **Use Browserable** | Requires 8+ Docker services; operational complexity unjustified for our scale |
| **Use Firecrawl self-hosted** | AGPL-3.0 copyleft would require open-sourcing our platform |
| **Use AutoGen** | In maintenance mode; Microsoft directing users to new framework |
| **Use CrewAI as primary** | Multi-agent team paradigm doesn't fit single-assistant-with-tools pattern (Rashid) |
| **Use LangGraph as primary** | Heavier dependency chain, indirect Bedrock support; save for specific complex workflows only |
| **Use Khoj** | AGPL license restrictive for commercial embedding |
| **Use PyMuPDF** | AGPL license; Docling (MIT) provides equivalent functionality |
| **Replace Typesense with Elasticsearch** | Typesense already working, lighter operational burden |
| **Build custom scraping framework** | Scrapling (BSD-3, 76k stars) does it better than we could build |
| **Build custom research engine from scratch** | GPT Researcher (Apache 2.0, 29k stars) already production-proven |
| **Add startup database** | Mission creep; focus on jobs/careers. Lightweight content approach instead. |
| **Use GraphRAG directly** | Too expensive (LLM call per document for indexing); build lighter knowledge base inspired by its patterns |
| **Replace existing ATS scrapers** | They work. Enhance with Scrapling for NEW sources, keep existing for known ATS platforms. |
| **Implement all phases simultaneously** | Risk of scope creep, technical debt, and shipping nothing. Sequential phases with acceptance gates. |

---

## Appendix A: Complete Open-Source Registry

### A. USE DIRECTLY (permissive license, production-ready, pip/Docker install)

| Tool | Version | License | Install | Purpose |
|------|---------|---------|---------|---------|
| Pydantic AI | 2.35.0 | MIT | `pip install pydantic-ai[bedrock]` | Agent framework for Rashid |
| MCP Python SDK | latest | MIT | `pip install mcp` | Tool protocol |
| Docling | latest | MIT | `pip install docling` | Document processing |
| BERTopic | latest | MIT | `pip install bertopic` | Topic/trend modeling |
| python-email-validator | 2.3.0 | Unlicense | `pip install email-validator` | Email validation |
| disposable-email-domains | latest | CC0 | `pip install disposable-email-domains` | Spam blocking |
| pytrends-modern | latest | MIT | `pip install pytrends-modern` | Google Trends |
| changedetection.io | latest | Apache-2.0 | Docker | Page monitoring |
| Prefect | latest | Apache-2.0 | `pip install prefect` | Complex workflows |

### B. ADAPT/FORK (needs customization for our use case)

| Tool | License | Adaptation Needed |
|------|---------|-------------------|
| ESCO Skill Extractor | MIT | Integrate with our existing skills app, add Arabic support |
| FORGE/Dataforge | MIT | Extract company contact discovery logic only |

### C. WRAP/INTEGRATE (use as external service via API)

| Tool | License | Integration Method |
|------|---------|-------------------|
| Scrapling | BSD-3 | Import as library in scraper app |
| GPT Researcher | Apache 2.0 | pip install + Celery task wrapper |
| Crawl4AI | Apache-2.0 | Docker API or library import |
| Reacher | AGPL-3.0 | Docker container, HTTP API calls only |

### D. REFERENCE ONLY (patterns and architecture inspiration)

| Tool | What to Learn |
|------|--------------|
| career-ops | ATS adapter patterns for Greenhouse/Ashby/Lever/Wellfound |
| ai-job-search | Portal scraper architecture, drafter-reviewer agent pattern |
| Jobseek | Direct-employer sourcing architecture, CDC export pattern |
| Freehire | Fingerprint-based dedup, ghost job detection, pgvector embeddings |
| openings-mcp | 23 ATS platform endpoint mapping (41k companies) |
| GraphRAG | Knowledge graph extraction pipeline architecture |
| Hyper-Extract | Template-based entity extraction patterns |
| WorkRB | Skills matching benchmark methodology |
| last30days-skill | Multi-platform research agent architecture |
| Firecrawl Web-Agent | Skills/playbook pattern for reusable extraction |

### E. REJECT (do not use)

| Tool | Reason |
|------|--------|
| Magic Resume | Commercial use prohibited |
| TheAgenticBrowser | Restrictive license, abandoned |
| Browserable | Excessive infrastructure (8+ services) |
| n8n | Restrictive license |
| AutoGen | Maintenance mode |
| PyMuPDF | AGPL (use Docling instead) |
| Firecrawl self-hosted | AGPL copyleft |

---

## Appendix B: Existing Platform Capabilities NOT to Duplicate

These systems are already well-implemented. Do NOT rebuild them:

1. **ATS Scrapers** (11 platforms) — enhance, don't replace
2. **Verification Engine** (6-stage) — keep unchanged
3. **LightFM Recommendations** — enhance with explanations, don't replace
4. **Typesense Search** — keep, enhance facets
5. **Qdrant Vector Search** — keep, add more embedding types
6. **Celery Automation** (12+ tasks) — keep, add Prefect alongside
7. **JWT Authentication** — keep unchanged
8. **WebSocket Chat (Rashid)** — keep transport, upgrade agent logic
9. **Event System** — keep, add more event types
10. **ESCO/O*NET Skills** — keep, enhance with embeddings
11. **Email Rotation System** — keep, add verification layer
12. **Monitoring/Health Checks** — keep, add structured logging

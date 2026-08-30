# E-Career (USAM Jobs) — Agent Operating Guide

E-Career (production domain: jobs.usamif.com) is a career + hiring operating
system, not just a job board: Django/DRF backend + React/Vite frontend,
Postgres+pgvector, Typesense, Qdrant, Celery, Channels, AWS Bedrock model
routing. Core data/workflow graph: User → Profile → CV → Skills → Jobs →
Matching → Applications → Interviews → Career Growth → Talent Pool →
Employer → Hiring → Outcomes → Learning/Recommendations. One shared
intelligence layer is meant to power all of it — avoid re-fragmenting into
disconnected per-feature modules (a repeatedly-flagged risk in this repo:
`career`/`skills`/`rashid` apps drifting into separate schemas instead of
one Career Graph).

**Do not trust status docs at face value.** ~100+ planning/status markdown
files exist at the repo root (`*_SUMMARY.md`, `*_REPORT.md`, `*_PLAN.md`)
and have previously contradicted each other and the real code (verified:
one day's Architecture score was 8.7, another day's independent check on the
same week found 6.65; one report claimed "Interview app doesn't exist",
another the same week claimed "100% ready with voice" — no run evidence
between them). Always verify against real code/live behavior before
repeating a status claim.

**Security history:** a real AWS access key was previously found live in
`backend/.env` (not `.env.example` — that one was already git-clean). Before
any task that touches `.env`, `backend/.env`, or credentials, verify no live
secret is present and flag immediately if one is found — do not wait to be
asked.

## Standing agent roster for this project

This project has THREE tiers of specialist agents available in every Hermes
session opened here — use them proactively, don't wait to be asked by name.

### 1. `virtual-agent-team` skill (42 roles) — load via `skill_view(name='virtual-agent-team')`
Most relevant here:
- `backend-engineer` — Django/DRF, data model (esp. the Career Graph schema
  vs. fragmented per-app models), Celery/Channels correctness
- `frontend-engineer` — React/Vite; this repo has a documented duplicate-API-
  client bug (`services/client.ts` vs `services/api.ts` with inconsistent
  prefixing) that broke Recommendations end-to-end — check for recurrence
  patterns before trusting any "it works" claim on a page
- `security-researcher` — exposed secrets, auth boundaries (job-application
  intermediary rejection rules are a business-logic security concern too:
  LinkedIn/Indeed/ZipRecruiter/Monster "Apply" links must be rejected, only
  direct employer/ATS links accepted)
- `data-scientist` — matching/recommendation model quality, embedding search
  (pgvector/Qdrant) correctness
- `web-intelligence` (role) / `agency_agents` `universal-scraping-architect`
  (specialist) — job/company data ingestion pipeline (ATS integrations:
  Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Teamtailor, Recruitee,
  BambooHR, Personio, Jobvite, Workday)
- `career-coach` / `recruiter` — feature-level sanity checks on CV writer,
  interview simulator, career recommendation UX
- `cto` — AWS Bedrock model routing should discover available models
  dynamically from the account (quality-per-cost routing), not hardcode a
  model list — flag regressions

### 2. `claude-skills` pack (364 skills) — load via `skill_view(name='<skill-name>')`
Bare names, no prefix. Relevant: `engineering` (rag-architect, database-
designer, api-design-reviewer, dependency-auditor), `marketing-skill` (seo-
audit, schema-markup — for job-listing SEO), `security` roles (senior-
security, secrets-vault-manager).

### 3. `agency-agents-router` plugin (273 specialists) — deferred tools
Call via `tool_search(queries=[...])` then `tool_call(name='agency_agents_search'|
'agency_agents_inspect'|'agency_agents_load'|'agency_agents_delegate', arguments={...})`.
Relevant divisions: `sales` (sales-engineer for employer-side features),
`specialized` (business-strategist, model-qa-specialist), `testing`.

## Standard workflow

1. Read real code first — never accept a `*_SUMMARY.md`/`*_REPORT.md` claim
   about a feature's completeness without verifying against
   `backend/api/<app>/` directly and, where relevant, live behavior on
   jobs.usamif.com.
2. For any "is X done?" question, check ALL of: backend model/serializer/view,
   frontend component + the API client it actually imports (verify
   client.ts vs api.ts consistency), and one real request/response if
   feasible.
3. Treat this file + any single most-recent, code-verified audit as the only
   authoritative source; the ~100 historical planning docs are archive only.
4. Flag direct-application-verification rule violations immediately: any job
   record whose application URL routes through a third-party apply
   intermediary (LinkedIn/Indeed/ZipRecruiter/Monster) should be rejected per
   this platform's stated moat/policy — this is a product-correctness bug,
   not just a nice-to-have.

## Pitfalls specific to this repo

- Don't assume README/roadmap docs reflect current code — this repo's
  documentation-to-code gap has been large and repeatedly measured.
- The Career Graph (skills-as-relationships, not flat attributes) is the
  central architectural bet — any schema change should be checked against
  whether it reinforces or fragments that graph.
- Job Quality Engine states (Active/Probably active/Needs verification/
  Expired/Archived/Broken/Duplicate/Rejected/Direct-source verified) should
  be recomputed on a recurring cadence, not just at ingestion time — verify
  a recurring verification job actually exists before assuming freshness.

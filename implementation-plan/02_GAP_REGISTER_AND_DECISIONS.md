# 02 — Gap Register, Decisions & Negative-Space Audit

Every item: **ID · area · verified state · decision · priority · approach · dependencies**.
Decisions use the unified verbs; priorities P0–P3. Nothing here is a rebuild-from-scratch unless justified inline.

---

## A. P0 — Production blockers

| ID | Area | Verified state | Decision | Approach | Depends on |
|---|---|---|---|---|---|
| G-01 | Matching duplication | 3 parallel engines (`career/scoring_engine.py`, `search/recommendation_engine.py`, `intelligence/recommendation_service.py`) | MERGE→BUILD canonical `MatchingService` | Pick `career/scoring_engine` as base (richest, 1913L). Define `MatchResult` contract; **separate eligibility (hard filters) from ranking (score)**. Migrate search+intelligence callers to it; delete duplicates after parity tests. Preserve existing API response shapes for `Recommendations.tsx`/`scores.ts`. | G-05 (evidence) |
| G-02 | Tenant isolation | Multi-employer data access not enforced at query layer | HARDEN | Add company-scoped querysets + object-level permission checks on every employer/candidate/talent-pool view; add regression tests proving cross-company denial. | Permissions map |
| G-03 | Direct-apply honesty | Redirect/ATS vs internal distinction exists but not fully guaranteed | HARDEN | Ensure every job exposes explicit `application_type` (internal/external/ats/redirect); UI badge must reflect it; reject aggregator apply URLs at ingestion. | #15 verification |
| G-04 | Consent/privacy leakage | `is_discoverable` exists; not enforced on all talent-discovery paths | HARDEN | Gate every candidate-visible-to-employer path on consent; add tests. | G-02 |
| G-05 | Explainability/Evidence | Scores exist without consistent `Signal→Evidence→Score→Explanation→Confidence` | BUILD | Introduce `Evidence` records + `MatchExplanation` attached to every score surfaced to users; no opaque AI scores. | G-01 |
| G-06 | Rashed = assistant, not agent | 5 tools; not wired over platform services; 2 namespaces | MERGE+BUILD | Consolidate `rashid` + `intelligence/rashid/chat` to one path; expand tool registry (~20: search_jobs, get_job, compare_candidate_job, search_talent_pool, evaluate_candidate, shortlist, create_job, analyze_job, etc.) with per-tool auth+audit. | G-01, G-10 |

## B. P1 — Critical for launch

| ID | Area | Verified state | Decision | Approach | Depends on |
|---|---|---|---|---|---|
| G-10 | AI Gateway + Model Router bypass | Router used 3x; 6 hardcoded model IDs | REFACTOR+INTEGRATE | Route ALL AI calls through one gateway→router; remove hardcoded IDs; add usage/cost/fallback + admin config. | — |
| G-11 | Billing entitlements disconnected | Plans/subscriptions models exist; 0 enforcement; no payment provider | BUILD+INTEGRATE | Add entitlement service + decorators gating employer actions (job posts, candidate unlocks, talent-pool access); build payment provider abstraction (Stripe/Paymob); Pricing page. | Admin config |
| G-12 | Profile source-of-truth duplication | `users.UserProfile` (deprecated) vs `career.CareerProfile` | MERGE | Make CareerProfile canonical; migrate/redirect deprecated readers; remove after backfill. | — |
| G-13 | CV parser triplication | `profiles/cv_parser.py`, `career/cv_parser_views.py`, `intelligence/career_ai.py` | MERGE | One canonical parse pipeline; others call it. | G-12 |
| G-14 | Notification duplication | `users/me/notifications` inbox + `notifications/` prefs/CRUD | MERGE | One canonical notification model+API; migrate inbox reads. | — |
| G-15 | Recommendation feedback loop | Weak/partial | BUILD | Track impression→click→save→apply→outcome; feed ranking. | G-01 |
| G-16 | Talent Pool lifecycle | Models + ranking exist; lifecycle/consent/shortlist/compare incomplete | IMPROVE+INTEGRATE | Add pool state machine, consent gate, shortlist, candidate comparison, explainable match report; wire TalentSearch.tsx fully. | G-01,G-04,G-05 |
| G-17 | Career Identity (Candidate 360) | CareerBrain model exists; sync partial | INTEGRATE | Wire `career_brain_service` sync from CV/skills/assessments/applications; single candidate record view. | G-12,G-13 |
| G-18 | Skills Graph | Taxonomy import present; relationships thin | IMPROVE | Add skill relationships/hierarchy/transferable/emerging; wire to matching + gap analysis. | — |
| G-19 | Admin monolith | `AdminDashboard.tsx` local-tab, `admin_api_views.py` 2100L | REFACTOR | Split into URL-routed sections; expose all `/admin-api/` endpoints in UI; keep endpoints. | — |
| G-20 | Live data pipeline unproven | Scraper/verification code present, no run evidence | RESEARCH+TEST | Run one source end-to-end (fixture ATS→DB→verification→listing); add integration test. | Docker/services |
| G-21 | Semantic/vector search UI | `vectors/` + `search/` exist; no UwI | INTEGRATE | Expose hybrid search in Jobs/Search UI; one canonical retrieval path. | G-01 |
| G-22 | Frontend redesign completion | In progress on this branch | IMPROVE | Continue per `FRONTEND_REDESIGN_PLAN.md` (shells, tokens, states, a11y, RTL). | — |
| G-23 | Git branch divergence | `main` +43, `develop` +44 vs development | INTEGRATE | Reconciliation branch; cherry-pick tested; pick one canonical trunk (see `03`). | — |

## C. P2 — Important

| ID | Area | State | Decision | Approach |
|---|---|---|---|---|
| G-30 | Interview scheduling | Missing calendar | BUILD | Availability/timezone/reminders; integrate calendar connector. |
| G-31 | Requisition + JD Intelligence + Ghost-Job | Missing / partial (legitimacy) | BUILD | Requisition→approval→job flow; JD parse/quality; ghost-job risk score. |
| G-32 | Communication/Engagement + Outreach + CRM | Missing | BUILD | Templates/sequences; recruiter outreach; talent CRM pipelines. |
| G-33 | Assessment integrity | Partial | IMPROVE | Question pools, time/attempt limits, plagiarism signals. |
| G-34 | Webhook/Event bus | `events/` partial | BUILD | Events with retries/idempotency/DLQ/replay; consumers. |
| G-35 | Bulk ops + Import/Export | Partial (jobs import_export_admin) | BUILD | Bulk shortlist/reject/tag/reindex; CSV/GDPR export. |
| G-36 | Document engine hardening | Partial | INTEGRATE | Virus scan, MIME validate, OCR fallback, retention. |
| G-37 | Analytics dead schema | JobView/JobClick/SearchLog 0 writers | INTEGRATE | Wire writers or delete; connect Prometheus counters. |
| G-38 | Observability wiring | Metrics defined, not incremented | INTEGRATE | Increment counters at call sites; dashboards. |
| G-39 | Data retention policies | Partial | INTEGRATE | Per-type retention + deletion jobs. |

## D. P3 — Enhancement / post-launch
Finance/Ledger, Refund, Referral, Event/Career Fair, RAG (only if value proven), Content/Trend expansion, Market/Employer/Application Intelligence, Experimentation/AB, Developer API platform.

---

## E. Duplication resolution register (from `04.md` §3 / `MASTER §28`)

| Duplicate | Instances | Decision | Authoritative |
|---|---|---|---|
| Matching/Recommendation | career/scoring_engine + search/recommendation_engine + intelligence/recommendation_service | MERGE | `career` base → new `matching/` service module |
| Profile model | users.UserProfile + career.CareerProfile | MERGE→DELETE deprecated | career.CareerProfile |
| CV parser | profiles + career + intelligence | MERGE | one canonical parser |
| Notification | users inbox + notifications app | MERGE | notifications app |
| Assistant surface | rashid/ + intelligence/rashid/chat | MERGE | rashid/ |
| Onboarding | career backend + frontend OnboardingFlow/Wrapper | MERGE | one server-backed controller (frontend already deduped) |
| Deduplication | scraper/pipeline + verification | MERGE | verification stage |

## F. "Negative space" audit (from `11.md` — what's missing between the parts)

Verify and fix each (P1 unless noted):
- **Buttons without backend:** Settings toggles (fixed→link), any employer action lacking entitlement (G-11).
- **APIs without frontend consumer:** most `/admin-api/*` (G-19), `/skills/*` taxonomy, `/vectors/*` semantic search (G-21).
- **DB models without consumer:** `analytics.JobView/JobClick/SearchLog` (G-37); dead scoring placeholders.
- **Workers without trigger / events without consumer:** verify Celery beat entries map to real tasks; `events/` consumers (G-34).
- **AI output not stored / scores not explainable:** attach Evidence+Explanation to all surfaced scores (G-05).
- **Talent Pool data not in matching; matching not in recommendation; recommendation not learning from feedback:** G-01, G-15, G-16.
- **Features not tied to permissions/billing:** G-02, G-11.
- **Admin settings with no real effect:** FeatureFlag/PlatformConfig wiring (G-56/G-10).
- **External application mislabeled as internal:** G-03.
- **Orphaned data after deletion / non-idempotent automations:** G-39, G-34.

## G. Cleanup (remove only after review)
- `config/settings/base.py.bak`, stray `*.log` files, `test_scraper.py` at backend root, archived planning docs already moved to `archive/`.
- Deprecated `users.UserProfile` — remove **after** G-12 migration + backfill, never before.
- Dead analytics models — remove **after** G-37 decision.

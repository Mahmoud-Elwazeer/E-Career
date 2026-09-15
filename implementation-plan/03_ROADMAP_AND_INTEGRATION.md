# 03 — Dependency-Aware Roadmap, Source-of-Truth Map & Integration

Sequence follows `04.md` phases 0–16, reordered by the **actual** dependencies found in code. Every phase ends with the checkpoint gate. No phase starts while the prior has unresolved build/test/regression issues.

---

## A. Source-of-truth map (canonical owners)

| Domain | Canonical model | Service | API prefix | Frontend owner |
|---|---|---|---|---|
| User/Identity | `accounts.User` | accounts | `/api/v1/auth/` | use-auth, Login |
| Candidate profile | `career.CareerProfile` (canonical) | career_brain_service | `/api/v1/profile/`,`/career/` | ProfilePage, services/profile |
| Career Identity (360) | `career.CareerBrain` | career_brain_service | `/career/` | TalentScore, ProfilePage |
| Skills | `skills.Skill` (+graph) | skills.graph | `/skills/` | (needs UI) |
| CV/Resume | `resume.Resume` | resume + one parser | `/resume/` | ResumeBuilder |
| Company | `employers.Company` | employers | `/employer/` | EmployerDashboard |
| Job | `jobs.Job` (+quality_state) | jobs + scraper | `/jobs/` | Jobs, JobDetail |
| Job Source | `jobs.Source` | scraper.orchestrator | admin-api | Admin |
| Application | `employers.JobApplication` | jobs+users views | `/jobs/`,`/users/` | Applications |
| Talent Pool | `employers.TalentPool` | ranking_service | `/employer/` | TalentSearch |
| Match | new `MatchResult` | canonical MatchingService | `/career/`,`/search/` | Recommendations, scores |
| Recommendation | reco + feedback | MatchingService + feedback | `/career/recommendations/` | Recommendations |
| Interview | `interviews.*` | interviews.service | `/interviews/` | InterviewPractice |
| Assessment | `assessment.*` | assessment | `/assessment/` | Assessments |
| Verification | `verification.*` | verification.engine | (worker) + admin-api | Admin |
| Subscription/Plan | `core.SubscriptionPlan` | entitlement (new) | `/admin-api/`,`/employer/` | Pricing, Admin |
| AI Session | `intelligence.*`,`rashid.*` | AI Gateway + Router | `/rashid/`,`/intelligence/` | RashidChat |
| Notification | `notifications.*` (canonical) | notifications.service | `/notifications/` | Notifications |
| Audit | `core.ActivityLog` | security_audit | admin-api | Admin |

Rule: if two models claim a domain, the "canonical" column wins; the other is migrated then removed.

## B. Integration matrix (must-connect; verify each link)

```
Career Identity → CV → Skills → Assessment → Qualification → Talent Pool → Matching → Recommendation → Rashed
Job Source → Scraping → Connector → Normalization → Deduplication → Verification → Search → Matching → Recommendation → Application
Employer → Job → Requirements → Matching → Talent Pool → Candidate Intelligence → Screening → Interview → Hire → Analytics
Rashed → AI Gateway → Model Router → {Career Identity, CV, Jobs, Search, Matching, Recommendation, Talent Pool, Interviews, Notifications, Documents}
Entitlement → {Job post, Candidate unlock, Talent Pool access, AI usage} (currently missing — G-11)
```
Every arrow must be a real, tested call path. Broken arrows are logged in `02`.

## C. State machines to formalize (from `MASTER §23`)
User, Company, Job (`discovered→parsed→normalized→verified→published→stale→reverified→expired→archived`), Application, TalentPool membership, Interview, Assessment, Subscription, Payment, ScrapingRun, Verification, Recommendation, AI task, Notification. Each transition: allowed-from, actor, permission, timestamp, reason, audit event.

## D. Phase roadmap (dependency-ordered)

- **Phase 0 — Stabilization & git reconciliation** (G-23): pick canonical trunk; reconciliation branch; green gate baseline; remove obvious dead files (§G cleanup). *Gate: build+lint+tests green.*
- **Phase 1 — Source-of-truth & architecture correction** (G-12, G-13, G-14, duplication register): consolidate profile/CV/notification; define MatchResult contract. *Gate: migrations + parity tests.*
- **Phase 2 — Security & config foundation** (G-02, G-04, G-57, G-10 gateway skeleton): tenant isolation, consent gates, permissions map, AI gateway. *Gate: security/tenant tests pass.*
- **Phase 3 — Career Identity / Candidate 360** (G-17, G-05 evidence): wire CareerBrain sync; evidence records. 
- **Phase 4 — CV / Skills / Evidence / Assessment** (G-13, G-18, G-33): one parser; skills graph; assessment integrity.
- **Phase 5 — Employer / Company / Jobs** (G-31 requisition/JD): employer flows + billing hooks scaffold.
- **Phase 6 — Job pipeline live** (G-20, G-03): prove scrape→normalize→dedupe→verify→publish end-to-end; direct-apply honesty.
- **Phase 7 — Search / Matching / Recommendation** (G-01, G-21, G-15): canonical matching (eligibility vs ranking), semantic search UI, feedback loop.
- **Phase 8 — Talent Pool** (G-16): lifecycle, consent, shortlist, comparison, explainable reports.
- **Phase 9 — Applications** (state machine).
- **Phase 10 — Interviews / Simulation / Voice** (G-30 scheduling).
- **Phase 11 — Rashed / AI Gateway / Model Router** (G-06, G-10): agent tools, route all AI, governance/human-in-loop.
- **Phase 12 — Notifications / Automation / Documents / Events** (G-34, G-36, workflow rules).
- **Phase 13 — Billing / Packages / Entitlements / Payments** (G-11, G-45): enforcement + provider + Pricing page.
- **Phase 14 — Admin Control Plane** (G-19, G-35): split monolith, expose all endpoints, bulk ops.
- **Phase 15 — Analytics / Observability / Security hardening** (G-37, G-38, G-39).
- **Phase 16 — Full production validation** (Stage 6/7): 58-engine verification, E2E candidate+employer journeys, load, launch readiness, ops runbooks.

Reorder if code dependencies dictate; Phase 1+2 must precede feature work.

## E. Per-phase checkpoint (mandatory, from `04.md §25`)
Run: build · lint · type-check · unit · integration · API · relevant E2E · migration validation · security checks → then **feature regression audit** → record changed files + remaining gaps → **await approval before next major phase**.

## F. OSS research (evaluate, don't blindly adopt — `MASTER §14`)
| Need | Candidate | License | Decision |
|---|---|---|---|
| Search | Typesense (in use) / Meilisearch | GPL-ish/MIT | KEEP Typesense |
| Vector | pgvector (in use) / Qdrant | PostgreSQL/Apache-2 | KEEP pgvector; Qdrant only if scale demands |
| Scraping | Playwright/Scrapy (adapters custom) | Apache/BSD | KEEP custom ATS adapters |
| Voice | faster-whisper / AWS Transcribe+Polly | MIT/commercial | RESEARCH per cost+perms |
| Workflow | Celery (in use) | BSD | KEEP; add rules layer, not Temporal/n8n |
| UI marketing | Magic UI / Aceternity | MIT | ADAPT (owned files) for landing |
| Payments | Stripe / Paymob (MENA) | commercial SDK | ADOPT provider abstraction |
| ATS reference | OpenCATS | GPL | REFERENCE ONLY (GPL blocks SaaS reuse) |

Never adopt GPL into the SaaS core; use as reference only.

## G. Testing strategy (from `04.md §21`)
Pyramid: unit (matching/normalization/dedup/verification/entitlement/router) → service → API → integration → workflow → E2E (candidate: register→onboard→profile→CV→identity→search→match→reco→apply→interview; employer: register→company→job→publish→search→talent-pool→match→screen→interview→hire) → security (authz, tenant isolation, privilege escalation, file access, AI tool perms) → performance → resilience. Add regression tests before each refactor.

## H. Definition of "complete" (Stage 6 bar)
A feature is complete only when its full traceability chain works: **URL → Page → Component → API → Service → DB → Worker → Event → AI → Integration → Notification → Admin → Permission → Audit → Tests**. Anything short of that stays in the gap register.

---

## Immediate recommended next action (awaiting your go-ahead)
Given no-commit policy: **Phase 0 + Phase 1** are the safe, high-leverage start (git reconciliation decision + source-of-truth consolidation) and unblock everything downstream. I will not begin broad changes until you approve the phase and the target trunk (`development` vs `origin/main`).

# Individual vs Company/Employer Separation — Audit + Architecture + Plan

> Code-verified (backend + frontend). Marks what is ALREADY separated vs the real
> gaps. Then the implementation plan. Repo: `development` branch.

---

## A. Current Architecture (verified)

- **Auth/identity:** `User.role ∈ {user, employer, admin}`. JWT + allauth.
- **Individual profile:** `apps/career.CareerProfile` (OneToOne user) + legacy `apps/users.UserProfile`. Holds skills, certifications, job prefs, `is_discoverable` consent flag.
- **Employer/org:** `apps/jobs.Company` (org, rich brand fields) + `apps/employers.EmployerProfile` (OneToOne user↔Company, admin-verified) + `EmployerTeamMember` (owner/admin/recruiter/hiring_manager/viewer + invited_by).
- **Jobs:** `apps/employers.JobPosting` (FK EmployerProfile + FK Company, `mirrored_job` → public `jobs.Job` on publish). Ownership isolated via queryset scoping; apply-URL must be on company domain (direct-apply moat).
- **Talent Pool:** `apps/employers` — `TalentPool` (owned by EmployerProfile), `TalentPoolCandidate`, `TalentDiscovery`, `CandidateRanking` (AI scores). All employer-scoped; consent-gated by `CareerProfile.is_discoverable`.
- **Frontend:** role-based routing (`lib/role-routing`), `/for-individuals` + `/for-businesses`, distinct individual vs employer nav arrays, `/app/employer/*` gated by `RequireEmployer`, account-type selector at registration.

## B. Current Individual Experience
Dashboard, Jobs, Recommendations, Rasheed, Resume/CV, Cover letters, Interviews, Talent Score, Career Graph, Skills, Salary, Assessments, Applications, Saved, Alerts, Profile, Billing, Settings.

## C. Current Company Experience
Employer dashboard, Post/Manage jobs (ownership-isolated), Applications, Talent Pool (pools + rank applicants), Talent Search page, Billing & Plans, Settings. Public read-only Company Profile page.

## D. Gap Analysis (the real, code-verified gaps)

| # | Gap | Type | Severity |
|---|---|---|---|
| 1 | `CareerProfile.is_discoverable` has **no frontend toggle** (default False) → no candidate is ever discoverable; manual add/search talent path is a dead-end | Missing UI + functional | HIGH |
| 2 | Employers **cannot edit their own company brand** (description/logo/size/HQ/links) — only admin can (`adminUpdateCompany`); `EmployerProfileWriteSerializer` exposes only job_title/phone/company-link | Missing capability | HIGH |
| 3 | **Team RBAC coded but not enforced** — `IsOwnerEmployer/CanPostJobs/CanViewApplicants` exist but unused; `EmployerTeamViewSet.invite/update/destroy` lack owner/admin check → any team member can manage the team | Security/authorization | HIGH |
| 4 | `insider_connections` endpoint is `IsAuthenticated` only → a job seeker can query company-people connections | Authorization | MEDIUM |
| 5 | Company Profile page doesn't surface stored brand fields (size/HQ/links); TalentSearch lacks candidate filters/add-to-pool/contact | Incomplete UI | MEDIUM |
| 6 | `TalentPool` owned by `EmployerProfile` not `Company` → pools not shared across a company's hiring team | Architecture | MEDIUM |

**What is already correctly separated (do NOT rebuild):** data models, job ownership isolation, talent-pool employer scoping, backend consent enforcement, role routing, RequireEmployer gating, account-type registration.

## E. Recommended Architecture
Keep the existing clean separation. Close the gaps additively:
- Individual gets a **discoverability/visibility control** (opt-in to Talent Pool) in profile/settings.
- Employer gets a **company-profile edit** surface (self-service brand editing, scoped to their own company).
- Enforce **team RBAC** on the team endpoints (owner/admin only for member management).
- Gate `insider_connections` to employers.
- (Later) migrate `TalentPool` ownership to `Company` so a hiring team shares pools.

## F–H. DB / Backend / Frontend changes
- **DB:** none required for gaps 1–4 (fields exist). Gap 6 (pool→Company) is an additive FK migration, deferred.
- **Backend:** (2) extend employer company-edit endpoint with object-level ownership; (3) apply `IsOwnerEmployer` to team management actions; (4) add employer permission to `insider_connections`.
- **Frontend:** (1) discoverability toggle in Settings/Profile; (2) employer "Company Profile" edit page; (5) surface brand fields + improve TalentSearch.

## I. Talent Pool — current → required → final
- **Current:** employer-scoped pools + AI ranking of applicants; consent gate exists but unreachable (no UI opt-in).
- **Required now:** individual opt-in UI (unblocks discovery); keep consent enforcement.
- **Final (later):** company-shared pools, candidate search filters, add-to-pool, contact-with-consent.

## J. Company Roles & Permissions (RBAC)
`owner` (full), `admin` (manage company + team + jobs + candidates), `recruiter` (jobs + candidates + applications), `hiring_manager` (candidates + applications view), `viewer` (read). Enforce via existing `permissions.py` classes on the relevant viewsets.

## K. Migration Strategy
All additive/non-destructive. No data reset. Team-RBAC enforcement is a permission change (no schema). Discoverability + company-edit use existing fields. Pool→Company FK is a future additive migration with backfill.

## L. Implementation Plan (this pass)
1. **Individual discoverability control** (backend endpoint + Settings UI) — unblocks Talent Pool. [DOING]
2. **Employer company-profile self-edit** (backend + page). [DOING]
3. **Enforce team RBAC** + gate `insider_connections`. [DOING]
4. Verify (tests + build), commit, deploy runbook.
Deferred (needs decision/larger migration): pool→Company ownership, full candidate search UI.

## M. Testing Plan
Backend: discoverability endpoint (owner-only), company-edit ownership (employer can only edit own company), team management denied for non-owner/admin, insider_connections denies plain user. Frontend: build + lint. Regression: existing employer/career tests.

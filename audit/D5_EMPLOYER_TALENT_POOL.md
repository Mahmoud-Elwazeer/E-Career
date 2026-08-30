# D5 — Employer/ATS + Talent Pool + Talent Intelligence + Candidate Ranking + Applications Audit

**Scope:** `backend/apps/employers/` (models.py, views.py, ranking_service.py, serializers.py,
permissions.py, admin.py, urls.py, domain_verification.py, ats_gap_service.py), plus the
cross-cutting Application submission path in `backend/apps/jobs/views.py` and the privacy gate
in `backend/apps/career/models.py`.

**Method:** Full read of every file in `apps/employers/`, cross-referenced against
`apps/jobs/models.py`, `apps/jobs/views.py`, `apps/career/models.py`, `apps/accounts/permissions.py`,
git history (`git log --all --oneline | grep -i "knockout\|talent.pool\|privacy"`), and one live
Django ORM query check against the dev settings to confirm/deny a suspected FieldError.

**Note on doc claims:** `MASTER_STATE_AND_ROADMAP.md` does not exist in this repo (searched, not
found — closest analog is `PLATFORM_INTELLIGENCE_AUDIT.md`, dated 2026‑08‑27, read for context).
`AGENTS.md` was read in full. All findings below are code-verified, not doc-derived.

---

## 0. Prior security-fix verification (AGENTS.md claim)

Commit `35f797b` ("fix: test infrastructure ... security hardening (talent pool privacy gate,
knockout bypass fix, voice upload validation) ...") is real and is on top of the working tree
(`git log` confirms it's the current HEAD of the relevant branch history). Verifying the two
specific claims:

### 1. "Talent pool privacy gate" — **INTACT, but narrow**
- `CareerProfile.is_discoverable` (opt-in, default `False`) was added in migration
  `apps/career/migrations/0006_add_is_discoverable.py` (`apps/career/models.py:129`).
- Enforced in exactly two places in `apps/employers/views.py`:
  - `CandidateRankingViewSet.rank()` line 605-612: when `rank_all=False`, candidate_ids are
    filtered to `is_discoverable=True` before ranking.
  - `TalentPoolViewSet.add_candidate()` line 726-730: rejects with 403 if the target user's
    `CareerProfile.is_discoverable` is not `True`.
- **Gap 1 (real gap, not the fixed one):** when `rank_all=True` in `rank()` (views.py:598-603),
  candidates are pulled from `JobApplication.objects.filter(job=job)` with **no discoverability
  check at all** — comment says "applicants have implicitly consented" (line 599). This is a
  deliberate design choice (applying = consent to be ranked for that job), not a bypass of the
  gate that was fixed — but it means the discoverability flag only gates the *proactive* talent
  pool / non-applicant ranking flow, not applicant ranking. Reasonable but should be documented
  as intentional, since it's easy to mistake for a hole.
- **Gap 2 (real gap):** `TalentDiscoveryViewSet` (views.py:666-686) — the model used to log
  "proactive talent discovery" (employer viewing/searching a candidate outside an application) —
  has **zero discoverability check** on create. An employer can `POST
  /api/v1/employer/talent-discoveries/` with any arbitrary `user` id and it will succeed
  (`TalentDiscoveryCreateSerializer` fields are `user, source, search_query, matched_skills,
  saved, notes` — no validation against `is_discoverable`). This does not itself leak profile
  *data* (TalentDiscovery only stores employer-supplied notes/tags about a user id — see §4 below
  for the actual "can they see profile data" answer), but it is the one candidate-facing model
  in this app whose name explicitly promises to police discovery and doesn't.

### 2. "Knockout bypass fix" (implicitly-required fields) — **INTACT and correctly server-side**
- Verified in `apps/jobs/views.py:522-573` (`JobSubmitApplicationView.post`):
  - Line 526: `is_required = field.get("required") or field.get("knockout_value") is not None`
    — any field carrying a `knockout_value` is now treated as required even if the employer
    didn't tick "required", closing the "leave it blank to dodge the knockout" bypass. This
    matches the commit message exactly.
  - Knockout evaluation itself (lines 538-573) runs entirely server-side against
    `custom_form_responses` supplied in the request body, compared against
    `custom_form_fields[].knockout_value` read from `job.employer_posting.custom_form_fields`
    (server-stored, not client-supplied) — the client cannot pass a fake schema to defeat it.
  - On a knockout match, `application_status` is forced to `"rejected"` **before** the
    `JobApplication` row is created (line 579-585) — there is no code path where the client can
    submit a value that trips the knockout condition and still get `status="applied"`. This is
    genuinely enforced server-side, not just client-side (confirmed also by frontend
    `services/jobs.ts` merely *displaying* `knockout_reason`/`knockout_results` returned by the
    server, not computing them).
  - **However** — this knockout system (dynamic-form `knockout_value` on `JobPosting.custom_form_fields`)
    is entirely separate/parallel to the `KnockoutQuestion` model in `apps/employers/models.py`
    (see §3 below), which is a different, half-built knockout system that IS bypassable/inert.
    The fix that's "intact" only covers the dynamic-form flavor of knockout, not the
    `KnockoutQuestion` model flavor — these should not be conflated when reporting status.

**Verdict on AGENTS.md's flagged prior work: both fixes are real and still present in the code.**
The dynamic-form knockout fix is solid. The talent-pool privacy gate is real but only covers 2 of
3 employer→candidate discovery paths (see Gap 2, and §4's overall verdict).

---

## 1. Application Engine (lifecycle, status tracking)

Two parallel, only loosely-linked implementations exist — this is itself a finding.

| Path | Status | Evidence |
|---|---|---|
| `JobApplication` model | **DONE** | `apps/employers/models.py:166-216`. Fields: user, job, applied_at, cv_snapshot, status (applied/viewed/shortlisted/rejected), custom_form_responses. `unique_together('user','job')` blocks duplicate applications. |
| On-platform submission (`JobSubmitApplicationView`) | **DONE** | `apps/jobs/views.py:483-623`. Validates required/knockout fields server-side, evaluates knockout, creates `JobApplication`, emits `JOB_APPLIED` event. Well-built. |
| Legacy click-tracking (`JobApplyView`) | **PARTIAL** | `apps/jobs/views.py:401-...`. Just logs an apply-click event and returns the source URL — does not create a `JobApplication` row. Two "apply" concepts (click-through vs on-platform submission) coexist without a documented reconciliation; a job could have applicants tracked via click-only with no `JobApplication` at all, meaning employer-side stats/rankings would silently miss them. |
| Status transitions: applied → viewed | **DONE** | `apps/employers/views.py:420-447` (`JobApplicationViewSet.update`) auto-transitions `applied`→`viewed` on any PUT, emits `EMPLOYER_CANDIDATE_VIEWED`. |
| Status transitions: → shortlisted / rejected | **DONE** | `apps/employers/views.py:449-489`, dedicated `.shortlist()`/`.reject()` actions. No state-machine guard (e.g., you can reject an already-rejected application, or shortlist a rejected one) — **PARTIAL**, cosmetic risk only. |
| Employer applicant list (per-job) | **BROKEN (queryset bug)** | `apps/employers/views.py:397-401`: `JobApplication.objects.filter(job__employer_posting__employer=employer)`. Verified live against Django ORM (dev settings) that this filter path resolves without a FieldError (unlike the sibling bug in §2), because `Job.employer_posting` is a real reverse-OneToOne accessor. This one is fine. |
| Employer applicant list via `JobPostingViewSet.applicants()` | **DONE** | `apps/employers/views.py:364-383`: filters `JobApplication.objects.filter(job=job_post.mirrored_job)` — correct, uses the mirrored `Job` FK directly. |
| `EmployerProfileViewSet.stats()` — application counters | **BROKEN — confirmed FieldError** | `apps/employers/views.py:176-178`: `JobApplication.objects.filter(job__employer=employer)`. **Verified live**: `Job` model has no `employer` field/relation (only `employer_posting`, a reverse OneToOne from `JobPosting`). Running this against the dev DB settings raises `django.core.exceptions.FieldError: Unsupported lookup 'employer' for ForeignKey or join on the field not permitted.` This means **`GET /api/v1/employer/profile/stats/` will 500 for every employer**, any time this endpoint is hit — a fully broken feature, not a partial one. Fix: change to `job__employer_posting__employer=employer` (matching the working pattern used two views away in the same file). |
| Application detail (employer view of candidate) | **DONE** | `JobApplicationDetailSerializer` (`serializers.py:178-208`) surfaces `user_phone`/`user_profile` via `obj.user.userprofile` (the deprecated `UserProfile` model in `apps/users/models.py`, not the canonical `CareerProfile`) — wrapped in try/except so it silently returns `None` for most users since data now lives in `CareerProfile`. **PARTIAL / stale**: this serializer reads from a deprecated model and will return empty candidate-profile data for essentially all current users, degrading the "employer reviews applicant profile" UX without erroring. |

---

## 2. Employer / ATS Engine

| Feature | Status | Evidence |
|---|---|---|
| Company registration/lookup | **DONE** | `company_search` (views.py:492-513), `EmployerRegistrationView` (53-94), `EmployerRegistrationSerializer` (serializers.py:211-233) — validates company is active, blocks duplicate employer profiles per user. |
| Employer verification workflow | **PARTIAL** | `EmployerProfile.is_verified/verified_at/verified_by` exist (models.py:26-34); `request_verification()` (views.py:131-155) is a no-op stub — comment admits "For now, we just mark that they requested it" but doesn't even persist a "requested" flag/timestamp; verification is admin-only via Django admin. Functionally fine for a small operator-run marketplace, but there is no notification to admins and no audit trail of who requested when. |
| Hiring team / multi-user per company | **MISSING** | `EmployerProfile.user` is a `OneToOneField` (models.py:11-15) — exactly one platform account per employer profile, one employer profile per company allowed implicitly (no explicit uniqueness constraint on `company`, so multiple *unrelated* accounts could each separately register against the same `Company` and each would get their own isolated `EmployerProfile`, with no concept of a shared "hiring team," roles, or permissions between them). There is no hiring-team/invite/role model anywhere in `apps/employers/`. If "hiring team/permissions" is a stated requirement, it is entirely unbuilt (BUILD, not REFACTOR). |
| Permission classes — declared but partially unused | **REFACTOR** | `apps/employers/permissions.py` defines `IsOwnerEmployer`, `CanPostJobs`, `CanViewApplicants` (lines 39-102) — all imported into `views.py` (lines 39-41) but **never assigned to any `permission_classes`** anywhere in the file (grep-verified: only `IsAuthenticated`, `IsEmployer`, `IsVerifiedEmployer` are actually used as `permission_classes`). Dead/aspirational code: `CanViewApplicants.has_object_permission` (which correctly checks `obj.employer.user == request.user`) is never wired to `JobPostingViewSet.applicants()`, so that endpoint currently relies solely on `get_queryset()` scoping (`JobPosting.objects.filter(employer=self.request.user.employer_profile)`) for isolation — which happens to be correct, but only because DRF's generic `get_object()` re-derives from the already-employer-scoped queryset. Still safe today, but fragile: if anyone swaps `get_queryset()` for an unscoped one during a refactor, there is no object-level permission backstop. |
| Job creation/management (CRUD, publish/close/reopen) | **DONE** | `JobPostingViewSet` (views.py:203-383) covers create→pending_review→published→closed→draft(reopen); `perform_update` blocks edits outside draft/rejected (263-271, though note: this returns a `Response` from inside `perform_update`, which DRF ignores — see below); `publish()` validates required fields before submitting for review (273-305). |
| — bug: `perform_update`'s early-return `Response` is silently discarded | **BROKEN (logic bug, not security)** | `views.py:263-271`: `perform_update(self, serializer)` is a hook called by DRF's `update()`; returning a `Response` object from it does nothing — DRF discards the return value and continues with the normal 200 response flow, meaning **the "only draft/rejected can be edited" guard does not actually block the update**; `super().perform_update(serializer)` is called on the next line regardless because the `return` only exits `perform_update`, not the request. Net effect: a published or closed job posting *can* currently be edited via `PUT`, contrary to the stated business rule and the docstring. Needs to move this check into `update()` or raise a `ValidationError` instead of returning a `Response`. |
| Direct-apply-URL / anti-aggregator enforcement | **DONE** | `serializers.py:115-139` (`validate_apply_url` — enforces same-domain-as-company at creation time) + `domain_verification.py` (full module: `BLOCKED_DOMAINS` set of major aggregators, `verify_domain_ownership`, `check_url_accessibility` with SSRF protection via `apps.core.safe_fetch`, `verify_job_posting_url`, `bulk_verify_unverified_postings`) + management command `verify_employer_domains`. This directly satisfies the AGENTS.md "reject third-party apply intermediaries" policy on the employer-portal side. Solid implementation, includes a recurring/bulk re-verification path (though it must be scheduled via cron/Celery Beat externally — not itself confirmed as a recurring task in this app; that's for the scraper/verification-app auditors to check for the `Job`-side pipeline). |
| ATS gap analysis | **DONE** | `ats_gap_service.py` (220 lines) — rule-based scoring (title/description/requirements/salary/location/apply_url/custom_form_fields), no AI dependency, deterministic and testable. Wired via `ats_gap_analysis` view (views.py:779-795). |

---

## 3. Talent Pool Engine — is it a real pipeline, or "CV upload → candidate"?

**Verdict: it is a real, if thin, qualification/curation pipeline — not the "upload CV, become candidate" anti-pattern AGENTS.md warns against — but two of its three sibling models are functionally hollow.**

- `TalentPool` (models.py:404-427) + `TalentPoolCandidate` (430-466): a genuine named-collection
  model with `tags`, `notes`, `rating` (1-5), `source` (manual/search/application/recommendation),
  `unique_together('pool','user')`. CRUD + `add_candidate`/`remove_candidate`/`update_candidate`
  actions all present in `TalentPoolViewSet` (views.py:689-776). **DONE** as a data model and CRUD
  surface — this is a legitimate curated-pipeline concept, gated by the `is_discoverable` consent
  flag on add (§0).
- `TalentDiscovery` (models.py:352-401): intended to log "employer discovered this candidate via
  search/recommendation/profile_view/skill_match" — but nothing in the codebase ever calls
  `TalentDiscoveryViewSet.perform_create` from an actual search or recommendation flow; it is a
  bare CRUD endpoint an employer can `POST` to directly with an arbitrary payload. There is no
  employer-facing *candidate search* endpoint in this app at all (grep across `apps/employers` and
  `apps/career` for a "search candidates by skill" view found nothing beyond the two gated call
  sites in §0) — so "Talent Discovery" is a shell for a search feature that does not yet exist.
  **PARTIAL/MISSING**: the model + CRUD exists, the actual discovery mechanism it's meant to
  record does not.
- `CandidateRanking` (models.py:275-349): real per-job, per-candidate score row with
  `unique_together('job','user')`, explainability JSON, knockout fields — but see §4, its
  `overall_score` is populated by two different code paths that disagree (a real AI-scored path
  in `ranking_service.py`, and a hardcoded `0.5` placeholder path in `views.py`'s `rank()` action —
  they are never reconciled, and only one of the two is actually wired to a URL, see §4).
- There is no evidence anywhere of the "user uploads CV → automatically becomes a talent-pool
  candidate" anti-pattern. Entry into a pool is always an explicit employer action
  (`add_candidate`), gated by candidate opt-in (`is_discoverable`). This is the correct shape.
  **Assessment: REFACTOR** (finish `TalentDiscovery`'s actual discovery/search wiring; reconcile
  the two ranking code paths) rather than MISSING or a fundamental anti-pattern.

---

## 4. Talent Intelligence / Candidate Ranking Engine

### 4a. Two disconnected ranking implementations — pick one
- **Path A (wired, used by frontend):** `CandidateRankingViewSet.rank()` action in
  `apps/employers/views.py:566-663`. This is the one `frontend/src/pages/employer/TalentSearch.tsx`
  and `services/employer.ts` actually call. Its scoring is **entirely fake**: every candidate gets
  hardcoded `overall_score/skill_match_score/experience_score/education_score/salary_expectation_score
  = 0.5` on first creation (`get_or_create` defaults, lines 621-627) and its knockout evaluation is
  a stub that ignores the candidate entirely (`if not question.pass_if_matches: fail` — lines
  638-646 — this fails a candidate purely based on the *employer's* `pass_if_matches` config flag,
  never reading anything about the candidate's actual answer, because no candidate answer to a
  `KnockoutQuestion` is ever stored anywhere in the schema — there is no
  `KnockoutQuestionResponse`/answer model at all). **BROKEN as an intelligence feature** — it
  returns a plausible-looking API response but the "AI ranking" and "knockout" are non-functional
  placeholders wired to production URLs.
- **Path B (built, NOT wired to any URL):** `CandidateRankingService` in `ranking_service.py`
  (557 lines) — genuinely computes skill/experience/location/salary match scores from
  `CareerUserSkill`/`CareerBrain`/`CareerProfile` data (`_calculate_skill_match` etc., lines
  219-301), calls Bedrock for Arabic-language AI explanations with a rule-based fallback
  (`_generate_explanations`/`_generate_fallback_explanations`, 303-392), and has
  `generate_shortlist()`/`compare_candidates()` for auto-shortlisting and comparison. Verified via
  `search_files` and `grep`: **`ranking_service`/`CandidateRankingService` is imported and
  instantiated nowhere else in the codebase** — no view, no URL, no Celery task references it.
  This is a fully-built, unused module — dead code sitting next to (and duplicating the intent of)
  the broken Path A. Its own knockout check (`_check_knockout_questions`,
  `_evaluate_knockout_question`, lines 394-430) is **also a stub that unconditionally returns
  `True`** (line 430: `return True` with a comment "This is a placeholder — implement actual
  evaluation logic"), so even if this path were wired up, KnockoutQuestion enforcement would still
  not work. **Assessment: INTEGRATE** — wire `CandidateRankingViewSet.rank()` to call
  `ranking_service.rank_candidates()` instead of its own hardcoded logic, and implement real
  answer-based evaluation for `_evaluate_knockout_question`/the KnockoutQuestion model generally.

### 4b. Knockout Questions (`KnockoutQuestion` model) — distinct from the dynamic-form knockout
- CRUD is real and correctly scoped: `KnockoutQuestionViewSet` (views.py:521-543) filters/creates
  against `self.request.user.employer_profile` only — no cross-tenant leakage.
- **But there is no schema anywhere to store a candidate's *answer* to a `KnockoutQuestion`.**
  The model (models.py:224-272) has `question_text`, `question_type`, `required_answer`,
  `pass_if_matches`, `weight` — all employer-authored criteria — with zero FK/JSON field linking
  it to any per-candidate response. Contrast with the *separate*, working dynamic-form knockout
  system on `JobPosting.custom_form_fields`/`JobApplication.custom_form_responses`
  (`apps/jobs/views.py`), which does correctly store and evaluate real candidate answers.
  **Verdict: `KnockoutQuestion` is effectively MISSING/BROKEN as a functioning knockout
  mechanism** — it exists as a data model and admin/API CRUD surface, but every evaluation of it
  in the codebase (both in `views.py`'s `rank()` and in `ranking_service.py`) is a stub that either
  ignores candidate data entirely or hardcodes `True`. This is the system AGENTS.md's "knockout
  bypass fix" commit did **not** touch — that fix (see §0) applies only to the dynamic-form
  flavor, which is the one actually used by the live "submit application" flow. **There is no
  active bypass risk today only because this half of the feature is never actually invoked to
  gate anything real** — but if a future dev wires `KnockoutQuestion` into a live gating decision
  without building the answer-capture piece first, it will silently pass or silently fail everyone,
  not "bypass" in the security sense, but be functionally broken either way.

### 4c. Dynamic application forms
- `JobPosting.custom_form_fields` (models.py:141-148) + `JobApplication.custom_form_responses`
  (203-207): real JSON-schema-driven dynamic form, editable in
  `frontend/src/pages/employer/JobPostingForm.tsx`, validated and knockout-evaluated server-side in
  `apps/jobs/views.py` (§1, §0). **DONE** — this is the actually-working knockout/dynamic-form
  system, separate from and more mature than the `KnockoutQuestion` model.

---

## 5. Explicit privacy/consent check: can an employer see a candidate's profile without consent?

**Answer: Largely no for the two flows that matter most (talent-pool add, non-applicant ranking),
but yes for two lower-severity paths that should be closed:**

1. **Talent pool add-candidate** — gated correctly (`is_discoverable` check, 403 if not opted in).
2. **Non-applicant candidate ranking** (`rank_all=False`) — gated correctly (filtered to
   `is_discoverable=True` before any `CandidateRanking` row is created).
3. **Applicant ranking** (`rank_all=True`) — **not gated by `is_discoverable`**, but this is
   arguably correct by design: a candidate who submitted a `JobApplication` for that specific job
   has already handed the employer their CV/answers for that job (see `JobApplicationSerializer`
   including `cv_url`), so ranking them for the job they applied to isn't a new disclosure. This
   is a reasonable, if undocumented, distinction — **flag as a documentation gap, not a privacy
   bug**.
4. **`TalentDiscoveryViewSet.create`** — **no consent check at all**. An employer can log a
   "discovery" record against any arbitrary `user_id`, with free-text `notes`/`search_query`. This
   endpoint does not itself return the candidate's `CareerProfile` data (the serializer only
   echoes back what the employer submitted plus `user_name`/`user_email` — which are themselves
   exposed with no gate). **So yes: an employer can retrieve a non-discoverable candidate's name
   and email via `TalentDiscoverySerializer`/`TalentDiscoveryCreateSerializer` with zero consent
   check**, by simply guessing/incrementing a `user_id` and POSTing a discovery record, then
   GETting it back. This is a real, if minor (name+email only, not full profile), consent
   bypass — **should be fixed by adding the same `is_discoverable` guard used in
   `TalentPoolViewSet.add_candidate`.**
5. **`JobApplicationDetailSerializer.get_user_profile`** (serializers.py:197-208) — reads from
   the user's applicant-submitted data path (`obj.user.userprofile`), which is consistent with #3
   above (applicant already consented by applying); not a bypass, just stale-model risk (§1).
6. No endpoint anywhere in `apps/employers/` performs a raw, ungated `CareerProfile.objects.get(user=...)`
   or full-profile serialization keyed purely off an arbitrary `user_id` supplied by an employer —
   the two places that touch arbitrary user IDs (`TalentPoolViewSet.add_candidate`,
   `CandidateRankingViewSet.rank`) both check `is_discoverable` before doing anything with the
   target user. `TalentDiscoveryViewSet` (item 4) is the one exception and should be patched.

**Overall privacy-gate verdict: substantially intact per the AGENTS.md claim, with one
un-covered endpoint (`TalentDiscoveryViewSet`) that leaks name+email without consent — a real
but narrow gap, not a wholesale failure of the gate.**

---

## 6. Summary status table

| Component | File:Line | Status |
|---|---|---|
| JobApplication lifecycle model | employers/models.py:166-216 | DONE |
| On-platform application submission + knockout (dynamic form) | jobs/views.py:483-623 | DONE |
| Knockout bypass-by-omission fix (implicit required) | jobs/views.py:526 | DONE — verified intact |
| Legacy click-only "apply" tracking | jobs/views.py:401+ | PARTIAL — doesn't create JobApplication |
| Application status transitions (shortlist/reject) | employers/views.py:449-489 | PARTIAL — no state-machine guard |
| `EmployerProfileViewSet.stats()` | employers/views.py:176-178 | **BROKEN — confirmed FieldError, endpoint 500s** |
| `JobPostingViewSet.perform_update` edit-lock | employers/views.py:263-271 | **BROKEN — Response from hook is discarded, guard is a no-op** |
| Employer registration/company lookup | employers/views.py:53-94, 492-513 | DONE |
| Employer verification workflow | employers/views.py:131-155 | PARTIAL — stub, no admin notification/audit |
| Hiring team / multi-seat permissions | (none found) | **MISSING — BUILD** |
| `IsOwnerEmployer`/`CanPostJobs`/`CanViewApplicants` permission classes | employers/permissions.py | REFACTOR — dead code, not wired |
| Direct-apply URL / anti-aggregator verification | employers/domain_verification.py | DONE |
| ATS gap analysis | employers/ats_gap_service.py | DONE |
| TalentPool / TalentPoolCandidate CRUD + consent gate | employers/models.py:404-466, views.py:689-776 | DONE |
| TalentDiscovery (search/recommendation logging) | employers/models.py:352-401, views.py:666-686 | PARTIAL/MISSING — no real discovery source wired, **no consent gate (privacy gap)** |
| Talent pool privacy gate (`is_discoverable`) | career/models.py:129, employers/views.py:609,726 | DONE (2 of 3 relevant endpoints) — verified intact per AGENTS.md claim |
| `CandidateRanking` model | employers/models.py:275-349 | DONE (schema); scoring logic is fake (see below) |
| `CandidateRankingViewSet.rank()` (wired, live) | employers/views.py:566-663 | **BROKEN as intelligence — hardcoded 0.5 scores, knockout stub ignores candidate** |
| `CandidateRankingService` (real AI scoring, unwired) | employers/ranking_service.py | **INTEGRATE — built but never called from any URL/task** |
| `KnockoutQuestion` model + CRUD | employers/models.py:224-272, views.py:521-543 | DONE (CRUD); **MISSING/BROKEN as an enforcement mechanism — no answer schema, all evaluators are stubs** |
| Knockout bypass fix scope | — | Applies only to dynamic-form knockout (jobs/views.py), NOT to `KnockoutQuestion` model — verified, correctly scoped by AGENTS.md's claim (it didn't claim to fix the latter) |
| Dynamic application form (custom_form_fields/responses) | employers/models.py:141-148,203-207 | DONE |
| Candidate profile privacy bypass check | employers/views.py (TalentDiscoveryViewSet) | **Real narrow bypass — name+email retrievable without consent check** |

---

## 7. Priority fixes (for the owning team, not actioned here — audit only)

1. **P0 — fix `EmployerProfileViewSet.stats()`** (`job__employer=employer` →
   `job__employer_posting__employer=employer`) — currently 500s every time it's called.
2. **P0 — fix `JobPostingViewSet.perform_update`** — the draft/rejected-only edit guard is
   silently inert; either raise `serializers.ValidationError` or override `update()` directly.
3. **P1 — close the `TalentDiscoveryViewSet` consent gap** — add the same `is_discoverable`
   check used in `TalentPoolViewSet.add_candidate` before allowing a `TalentDiscovery` record
   against an arbitrary user, and gate `TalentDiscoverySerializer.user_name/user_email` output too.
4. **P1 — reconcile the two ranking implementations** — either delete
   `ranking_service.py`/`CandidateRankingService` and formally document Path A as the placeholder
   it is, or (better) wire `CandidateRankingViewSet.rank()` to call
   `ranking_service.rank_candidates()` and finish `_evaluate_knockout_question` with real
   answer-comparison logic.
5. **P2 — decide the fate of the `KnockoutQuestion` model** — either build a
   `KnockoutQuestionResponse` (candidate answer) model and real evaluation, or deprecate it in
   favor of the working `custom_form_fields[].knockout_value` mechanism to avoid future confusion
   (a dev could plausibly wire this into a real gate later, assume it works because it "passed"
   testing with the stub, and ship a silent no-op knockout).
6. **P2 — hiring-team/multi-seat model** is a genuine BUILD item if multi-user employer accounts
   are a product requirement; currently one platform user = one employer profile, full stop.
7. **P3 — wire `IsOwnerEmployer`/`CanPostJobs`/`CanViewApplicants`** into their intended
   `permission_classes`, or remove the dead imports — current safety relies entirely on
   `get_queryset()` scoping, which is correct today but has no object-level backstop.

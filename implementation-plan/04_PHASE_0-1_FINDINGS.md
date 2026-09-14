# 04 — Phase 0–1 Findings & Decisions (analysis only — no destructive changes made)

**Date:** 2026-09-10 · **Branch:** `frontend-renewal-2026-09` (= `development`) · **Commits made:** none · **Code changed:** none (this is analysis + this report).

This phase executed the safe, high-leverage start ("do the ideal"): stabilization, non-destructive branch/dead-code analysis, and source-of-truth verification. **Every planning-doc claim was re-checked against real code** — several were stale and are corrected below.

---

## Decisions taken (engineering judgment)

1. **Canonical trunk = `development`.** Newest, passes 497 backend tests, contains the real fixes. `origin/develop` (+44) and `origin/main` (+43) are **archival only**.
2. **No work is lost** by treating develop/main as archival (proven — §1).
3. Proceed with **analysis-only** Phase 0–1; hold all destructive/consolidation actions for your approval (§4).

---

## 1. Branch reconciliation (Phase 0a) — verdict: SAFE

`development` is ahead by **251 commits**; develop/main have ~44/43 older unique commits. I diffed the file trees. Every code file unique to develop/main is **superseded or intentionally replaced** on development:

| develop/main file | development equivalent | Verdict |
|---|---|---|
| `backend/ai/bedrock.py` | `intelligence/bedrock_plugin.py` | superseded |
| `apps/career/services.py` | `career_brain_service` + `ats_scoring_service` + `cover_letter_service` + `cv_tailor_service` | superseded (better decomposed) |
| `search/postgres_plugin.py`, `typesense_plugin.py`, `interfaces.py` | `search/plugins/*` | superseded |
| `vectors/plugins/qdrant_plugin.py` | `vectors/plugins/{pgvector,cohere,embedding,vector}_plugin.py` | superseded (dev has more) |
| `frontend/services/api.ts`, `lib/api.ts` | `services/client.ts` | **intentionally removed** — this is the duplicate-API-client bug AGENTS.md flags ✓ |
| `Navbar.tsx` | `AuthNavbar.tsx` | superseded |
| `Profile.tsx` | `ProfilePage.tsx` | superseded |
| `github.ts` | `core/github_service.py` | superseded |
| `config/ai_config.py` (static model list) | dynamic `intelligence/model_router.py` | intentionally replaced (aligns with AGENTS.md: route dynamically, don't hardcode) |

Everything else unique to develop/main = stale planning `.md` docs. **No recovery needed.**

## 2. Dead-code / cleanup candidates (Phase 0b) — recorded, NOT deleted

| Item | State | Recommended action | Needs approval? |
|---|---|---|---|
| `full_scrape.log`, `scrape_output.log`, `scrape_test.log` (repo root) | **git-tracked** despite `*.log` ignore rule (predate it) | `git rm --cached` (keep on disk) | Yes |
| `audit/*.stderr.log`, `backend/logs/django.log` | untracked, already ignored | leave | No |
| `backend/apps/intelligence/recommendation_service.py` (622L) | **orphaned dead code**, 0 external callers | DELETE after final grep | Yes |
| deprecated `users.UserProfile` (model + table) | 0 direct importers (alias serves consumers) | retire **after** data-migration check | Yes |
| legacy `users.Notification` model | inbox uses canonical model instead | retire **after** writer/data check | Yes |
| `base.py.bak`, `backend/test_scraper.py` | **do not exist** on this branch | none | — |

## 3. Green baseline (Phase 0c) — recorded

- **Frontend:** lint 0 errors / 201 warnings · 25/25 vitest pass · build OK (entry 476 kB).
- **Backend:** **497 passed, 2 skipped** (137s, `config.settings.test`).
This is the regression reference for every subsequent phase.

### ⚠️ Security flag (AGENTS.md-mandated)
`backend/.env` contains **1 live AWS access-key-id pattern (`AKIA…`)**. It is **untracked + gitignored** (not leaked via git) ✓. I did **not** read or echo the value. **Action for you:** rotate that key in AWS IAM if it is a real credential (this repo has a documented history of a live key here). I did not modify `.env`.

## 4. Source-of-truth re-verification (Phase 1) — HEALTHIER than the plan assumed

The Pass-4 gap register (G-01, G-12/13/14) flagged "3 matching engines" and profile/CV/notification duplication. Code says otherwise:

### Matching / recommendation (G-01 revised)
- `career/scoring_engine.py` (1913L) = **candidate TalentScore** engine (skill/experience/education/portfolio/growth/interview/AI-confidence → composite). Live callers in career tasks/views/views_api/views_recommendations. **Not a matching duplicate → KEEP** (this is Candidate Intelligence #22).
- `search/recommendation_engine.py` (887L) = **live job recommendation** (LightFM content+collaborative). Callers: career/views_recommendations, search/views, intelligence/agent (Rashed). **KEEP as authoritative Recommendation #19.**
- `intelligence/recommendation_service.py` (622L) = **orphaned LightFM duplicate, 0 external callers**. **DELETE (safe).**
- **Revised verdict:** not 3 competing engines — **2 distinct engines (KEEP) + 1 dead duplicate (DELETE)**. Remaining real work is small: (a) delete the dead one, (b) confirm eligibility-vs-ranking separation in the live engine, (c) attach explainability (Evidence→Score→Explanation→Confidence).

### Profile (G-12 revised)
- `profiles/models.py:12` already aliases `UserProfile = career.CareerProfile` (canonical). All consumers (matching, tasks, views, serializers, Rashed tools) get the canonical model transparently. Deprecated raw `users.UserProfile` has **0 direct importers**. **Consolidation is effectively DONE**; only the dead table remains to retire (after data check).

### CV (G-13 revised)
- Career decomposed into 4 focused services; a `profiles/cv_parser.py` + `career/cv_parser_views.py` remain. Whether these are duplicated or layered needs a closer read → **defer detail to Phase 4** (candidate/CV phase). Not urgent, not risky today.

### Notification (G-14 revised)
- Two API namespaces exist (`/users/me/notifications/` inbox + `/notifications/` prefs/digest/batches). **But the inbox already reads the canonical `notifications.UserNotification`** (users/views.py:9). Legacy `users.Notification` model is the dead one. **Keep both endpoints** (they serve different jobs), document one canonical model, retire the legacy model after a writer check. **Not a rebuild.**

**Net:** the platform's source-of-truth is in materially better shape than the historical docs implied. This confirms the AGENTS.md warning that status docs drift from code — verifying first saved us from unnecessary "consolidation" churn.

---

## 5. Proposed next actions — AWAITING YOUR APPROVAL

None of these are done yet. Grouped by risk:

**A. Zero-risk cleanups (recommend approve):**
1. `git rm --cached` the 3 tracked `*.log` files (keep on disk).
2. Delete `intelligence/recommendation_service.py` (dead, 0 callers) — after a final confirmatory grep.

**B. Low-risk, needs a data check first:**
3. Retire deprecated `users.UserProfile` model + `users.Notification` model — only after confirming no rows/writers depend on them (a migration with data check, reversible).

**C. Then continue the roadmap (Phase 2 onward):**
4. Security foundation (tenant isolation, consent gates) → then the feature phases per `03_ROADMAP_AND_INTEGRATION.md`.

I will not touch code until you say which of A/B/C to proceed with. My recommendation: **approve A now** (safe, keeps gate green), **schedule B** with a data-check migration, and continue to **Phase 2** as the next real build step.

---

## 6. Phase B execution result (data-check) — CORRECTED FINDING

Executing the "retire legacy models" step surfaced a **real bug**, so I did NOT delete anything and revised the decision:

### `users.Notification` is NOT dead — it's a split-brain notification bug (P1)
- **Inbox reads** `notifications.UserNotification` (`users/views.py:134`).
- **Canonical writer** `create_and_deliver_notification()` correctly writes `notifications.UserNotification` (used by interviews, emails). ✓
- **BUT two writers still write the legacy `users.Notification`:**
  - `employers/views.py:315` — job-submission → admin notification
  - `core/admin_api_views.py:1986-1989` — admin broadcast (`bulk_create`)
  - (+ `accounts/.../seed_data.py:274` seed)
- **Effect:** notifications created via the employer/admin path are written to a model the inbox never reads → they silently never appear. This is exactly the disconnection AGENTS.md warns about.
- **DECISION (revised):** do **NOT** retire `users.Notification`. Instead, **converge these 2 writers onto `create_and_deliver_notification`** (→ `UserNotification`). Scheduled as a **Phase 12 (Notifications) task**, with the legacy model retired only after writers are migrated and a data check confirms no rows are orphaned. This is a correctness fix, not a cleanup.

### `users.UserProfile` retirement — DEFERRED (safe)
- Only writer resolves through the `profiles.models` alias → `CareerProfile` (`emails/views.py`). No raw bypass writer found.
- Retiring the deprecated table needs a live DB row-count (DB not confirmed running in this environment). **DEFERRED** to a reversible data-checked migration; no action taken.

**Net for B:** 0 destructive changes (correctly — the "legacy" model was live). One real P1 bug identified and scheduled. This is why the data-check gate exists.

---

## 7. Phase 2 (Security foundation) — verified ALREADY IMPLEMENTED (major plan correction)

Before writing any tenant-isolation/consent/entitlement code, I verified the current state. **It is already implemented and tested.** Adding more would be redundant churn (violates "if correct, KEEP IT").

### Tenant isolation — ENFORCED ✓
- `JobPostingViewSet.get_queryset` → `filter(employer=request.user.employer_profile)` (`employers/views.py:224`)
- `JobApplicationViewSet.get_queryset` → `filter(job__employer_posting__employer=employer)` (`:423`)
- `EmployerProfileViewSet` → `filter(user=request.user)` (`:113`); Knockout/Ranking/TalentPool viewsets similarly scoped.
- Tested: `employers/tests.py` has `other_company` fixture + owner-passes / non-owner-denied object-permission tests (~L472-535).

### Consent (`is_discoverable`) — ENFORCED ✓
- Talent discovery/pool/ranking all gate on `is_discoverable=True` (`:633, :664, :689, :733`).
- Ranking path is consent-correct: `rank_all` only ranks applicants (implicit consent); otherwise filters to discoverable (`:625-636`).
- Tested: `employers/tests_phase5_services.py` covers discoverable True/False (L109/128/141).

### Entitlement / billing gating — ENFORCED ✓ (corrects gap G-11)
- `check_entitlement(company, type, count)` (`core/permissions.py:5`) reads `CompanySubscription` + `plan.job_posting_limit`, raises `PermissionDenied` on exceed, soft-allows when no subscription.
- Called at 2 real gates: job creation (`employers/views.py:243`) and candidate search (`:686`).
- Tested: `core/tests/test_admin_api_7b.py` — limit enforced, unlimited plan, no-subscription-allows.

**Corrected verdict:** G-02 (tenant isolation), G-04 (consent), and G-11 (entitlement gating) are **substantially DONE**, not missing. The plan/audit docs (and my Pass-4 register) **overstated** these gaps — another instance of doc-vs-code drift the operating guide warns about.

### Actual residual security-adjacent work (narrowed)
1. **Notification split-brain** (§6) — writers bypass the inbox model → P1, scheduled Phase 12.
2. Broaden entitlement coverage to other monetizable actions (talent-pool access, AI usage) — P2, Phase 13.
3. Add explicit cross-company API-level regression tests (object perms are tested; add a few view-level 403 tests) — P2.
4. Object-level perms on any candidate-document download path — verify in Phase 8/Document phase.

**No new isolation/consent/entitlement code was written** (correctly — it exists and passes tests). Phase 2 is effectively satisfied by the existing implementation; its residual items are folded into later phases.

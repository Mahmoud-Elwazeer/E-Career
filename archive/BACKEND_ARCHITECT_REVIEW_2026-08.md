# Backend Architect Review — Frontend API Client & AI Shim Migration
**Date:** 2026-08-29 | **Scope:** Two specific architectural-drift items flagged in `MASTER_STATE_AND_ROADMAP.md` (2026-08-28). This report re-verifies both against the live repo at `M:\job already web for jobs\E-Career` and supersedes the prior audit's claims wherever the code has since moved.

**⚠️ IMPORTANT — live drift during this review:** the repo was being actively edited by another process/agent *while this review was in progress* (commits/uncommitted edits appeared mid-session touching `frontend/src/lib/api.ts`, `frontend/src/services/{profile,github,intelligence}.ts`, `frontend/src/pages/Applications.tsx`). All findings below are pinned to specific git commits and a final verified build (`npx vite build`, exit 0) taken at the end of the session — **08:45 local time, 2026-08-29, on top of commit `fc16378` plus the uncommitted working-tree changes described in §1.5**. If you re-run these checks and the frontend has moved again, re-verify before acting on this report's line numbers.

---

## 1. Frontend API client unification

### 1.1 The base-URL discrepancy — STATUS: NO LONGER REPRODUCIBLE AS DESCRIBED (root cause already removed)

The audit's claim was: `services/client.ts` has `/api/v1` prefix, `services/api.ts` doesn't, and pages import the wrong one → 404s.

**Verified:** `frontend/src/services/api.ts` **does not exist on disk**. It was deleted in commit `35f797b` ("fix: test infrastructure... Migrated frontend services to apiRequest", 2026-08-29 00:39:59 +0300) — confirmed via `git show 35f797b --stat`, which lists `frontend/src/services/api.ts | 99 --` (99 lines deleted, file removed). `git log --oneline --diff-filter=D -- frontend/src/services/api.ts` returns `35f797b`.

So as of `35f797b`, there is only **one** low-level HTTP client on disk:

- **`frontend/src/services/client.ts`** (152 lines) — fetch-based, exports `apiRequest<T>()`.
  - **Line 6**: `const API_BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000") + "/api/v1";` — this is the correct, `/api/v1`-prefixed base URL the audit wanted made canonical.
  - Handles JWT refresh-on-401 (lines 100–121), envelope-unwrapping (lines 136–140).

The deleted `services/api.ts` (axios-based, `BASE_URL` with **no** `/api/v1` suffix — confirmed from its now-git-only content via `git show 35f797b^:frontend/src/services/api.ts`) is gone, so the specific two-clients-diverging-on-base-URL bug **cannot recur via that file** — it doesn't exist to import.

**This is a bigger change than "one line fixes Recommendations" — it deleted one of the two clients outright**, rather than just aligning URLs. That's the correct fix, just not literally a one-line diff as the prior audit speculated (verify that specific claim: **false as stated**, though the *outcome* — Recommendations working — is achieved).

### 1.2 Fallout from the deletion — a NEW, worse-in-the-moment problem existed, now fixed

Deleting `services/api.ts` outright without migrating every importer left a **broken build** for a window of this review. At the point I first ran `npx vite build --mode production` (commit `fc16378`, no working-tree changes yet), the build failed:

```
error during build:
Could not resolve "./api" from "src/services/profile.ts"
```
and, after the first fix was made externally:
```
[vite:load-fallback] Could not load .../src/services/api (imported by src/lib/api.ts): ENOENT
```
and then:
```
"apiClient" is not exported by "src/services/client.ts", imported by "src/services/intelligence.ts"
```

These three build failures each correspond to a still-wrong import site that referenced the deleted `services/api.ts` (or a nonexistent `apiClient` export). All three were fixed **during this review, by activity outside this report's edits** (I made no source edits — this task is read-only per instructions). By the end of the session:

- `frontend/src/services/profile.ts` line 5 was changed from `import api from './api';` to `import { apiRequest } from './client';` — confirmed via `git diff`.
- `frontend/src/services/github.ts` line 6: same fix, `import { apiRequest } from './client';`.
- `frontend/src/services/intelligence.ts` line 11: `import { apiRequest } from "./client";` (was `import { apiClient } from "./client"` — `apiClient` was never exported by `client.ts`, only `apiRequest` is — see `client.ts` line 79).
- `frontend/src/lib/api.ts` line 19: `export { apiRequest } from "@/services/client";` (was `import apiClient from "@/services/api"; export default apiClient;` — dead-ended on the deleted file).
- `frontend/src/pages/Applications.tsx` line 22: `import { apiRequest } from "@/lib/api";` (was `import api from "@/lib/api";`).

**Final verification: `npx vite build --mode production` exits 0** (confirmed at end of session — `✓ 3407 modules transformed`, `built in 8.15s`, output chunks written to `dist/`). The production build is currently green.

### 1.3 Remaining wrong/legacy import sites — file:line, as of the final verified state

Two files still import from `@/lib/api` (the re-export shim) rather than directly from `@/services/client`. This is **not broken** — `lib/api.ts` now correctly re-exports `apiRequest` from `client.ts` (§1.2) — but it is legacy indirection that should be collapsed for the "single source of truth" goal:

- **`frontend/src/hooks/use-seo.ts:3`** — `import { getCachedCompany as getCompany } from "@/lib/api";` (a compatibility stub, always returns `undefined` — see `lib/api.ts` lines 38–39: `export function getCachedCompany(_id: string) { return undefined; }`). Dead code path, not an API-client bug per se, but worth deleting.
- **`frontend/src/pages/Jobs.tsx:13`** — `import { logSearch } from "@/lib/api";` (also a no-op stub — `lib/api.ts` line 36: `export async function logSearch(...) {}`).

No file currently imports a `services/api.ts` that would break at runtime with the wrong base URL — **that specific failure mode is closed**. The only "wrong client" pattern remaining is stylistic (importing through `lib/api.ts`'s re-export instead of `services/client.ts` directly) plus the two no-op logging stubs above, which were already no-ops before this review and don't affect correctness of Recommendations.

**Verified import inventory (final grep, all `.ts`/`.tsx` under `frontend/src`):**
- Correct (`services/client.ts` / its `apiRequest`): `components/notifications/NotificationCenter.tsx`, `hooks/use-auth.tsx`, `hooks/__tests__/use-auth.test.tsx`, `lib/api.ts`, `pages/Notifications.tsx`, `services/{admin,auth,employer,intelligence,jobs,profile,recommendations,scores,userdata}.ts`.
- Legacy-indirect (`@/lib/api` re-export, functionally fine but not canonical): `hooks/use-seo.ts:3`, `pages/Jobs.tsx:13`, `pages/Applications.tsx:22` (this one now imports `apiRequest` specifically, not the removed default `api`).
- **No file** imports a nonexistent `services/api.ts` anymore.

### 1.4 Recommendations page — re-verify the 404 claim

`frontend/src/pages/Recommendations.tsx` and `frontend/src/services/recommendations.ts` both import via `services/client.ts`'s `apiRequest` (confirmed: `recommendations.ts` is in the "correct" list above, mtime `Aug 28 03:34`, predating the `api.ts` deletion). Since `services/api.ts` never existed on the Recommendations code path to begin with (it already used `client.ts`), and `client.ts`'s base URL has always had the correct `/api/v1` prefix (line 6), **the specific 404 the audit described for Recommendations should already be resolved, and was likely resolved before this review started** (the file predates the API-client consolidation commit). Unverified: I did not have a live backend running to make an actual HTTP request and confirm a 200 response — this is a static-code verification only, not an end-to-end behavioral one.

### 1.5 Working-tree caveat

At the time of writing, `git status --short` shows these files as **modified but uncommitted**:
```
M frontend/src/lib/api.ts
M frontend/src/pages/Applications.tsx
M frontend/src/services/github.ts
M frontend/src/services/intelligence.ts
M frontend/src/services/profile.ts
```
on top of committed HEAD `fc16378`. **Someone/something needs to commit these** — until committed, a fresh `git clone`/checkout of `fc16378` will reproduce the three build failures in §1.2. This is the single most important immediate action item (see §5).

### 1.6 CareerDashboard.tsx vs TalentScore.tsx — re-verify which is routed

**Audit claim:** `CareerDashboard.tsx` is routed at `/app/career` with mock data; `TalentScore.tsx` is unrouted despite being the real, working version.

**Current reality — this has already been fixed**, in the same commit that deleted `services/api.ts` (`35f797b`):
- `git log -p --follow -- frontend/src/App.tsx` shows: at `746d576` (an earlier commit), `App.tsx` imported `CareerDashboard` and routed `/app/career` to it. At `35f797b`, that diff shows:
  ```
  -import CareerDashboard from "./pages/CareerDashboard";
  +import TalentScore from "./pages/TalentScore";
  -<Route path="/app/career" element={<RequireAuth><CareerDashboard /></RequireAuth>} />
  +<Route path="/app/career" element={<RequireAuth><TalentScore /></RequireAuth>} />
  +<Route path="/app/talent-score" element={<RequireAuth><TalentScore /></RequireAuth>} />
  ```
- **Confirmed in the current `frontend/src/App.tsx`** (lines 18, 60, 61): `TalentScore` is imported and routed at both `/app/career` and `/app/talent-score`. `CareerDashboard` is **not** imported anywhere in `App.tsx` (`grep -n "CareerDashboard" App.tsx` → 0 matches).
- **`frontend/src/pages/CareerDashboard.tsx` still exists on disk** (301 lines) and still contains the mock data the audit flagged (`frontend/src/pages/CareerDashboard.tsx:27`: `const profileCompleteness = 65;` with comment "// Mock profile completeness"; line 111: hardcoded `<p className="text-4xl font-bold text-primary">72</p>`). But it is now **orphaned dead code** — `grep -rln "CareerDashboard" frontend/src` returns only `pages/CareerDashboard.tsx` itself (the file's own `export default function CareerDashboard()` at line 22). No other file imports it.
- **TalentScore.tsx** (`frontend/src/pages/TalentScore.tsx`, 475 lines) confirmed to use real API calls: line 46 `import scoresApi, { calculateGrade, getGradeColor, getTrendColor } from '../services/scores';`, and lines 136–150 call `scoresApi.getScores()`, `scoresApi.getScoreTrends()`, `scoresApi.getAllScoresWithActions()` inside `loadScores()` — genuine backend integration, no hardcoded numbers.

**Verdict: the routing swap the audit recommended (action item #11 in `MASTER_STATE_AND_ROADMAP.md`) has already been executed**, in `App.tsx`. **Remaining cleanup (not yet done):** delete the now-dead `frontend/src/pages/CareerDashboard.tsx` file — it's confirmed unreferenced and safe to remove (zero import sites outside itself).

### 1.7 Profile.tsx vs ProfilePage.tsx — re-verify which is routed

Same pattern, same commit (`35f797b`):
```
-import Profile from "./pages/Profile";
+import ProfilePage from "./pages/ProfilePage";
-<Route path="/app/profile" element={<RequireAuth><Profile /></RequireAuth>} />
+<Route path="/app/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
-<Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
+<Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
```
- **Confirmed current `App.tsx`**: line 16 `import ProfilePage from "./pages/ProfilePage";`, lines 59 and 86 both route to `<ProfilePage />`. No `import Profile from "./pages/Profile"` remains in `App.tsx`.
- **`frontend/src/pages/Profile.tsx` still exists on disk** (232 lines) — also now orphaned. It uses `@/services/auth` (`uploadAvatar`, line 18) for its one API call and otherwise is saved-jobs/alerts-hook-driven (`use-saved-jobs`, `use-alerts`), i.e. it's a legitimately different, older feature set, not simply "the mock version" — but it is unrouted dead code regardless.
- **`ProfilePage.tsx`** (per §1.2 above) genuinely calls `profileApi.getProfile`, `.getCompletion`, `.uploadCV`, `.updateSkills`, `.updatePreferences` via `services/profile.ts`, confirmed at `ProfilePage.tsx` lines 4, 15, 21, 26, 352, 439.

**Verdict: this swap is also already done.** Remaining cleanup: delete orphaned `frontend/src/pages/Profile.tsx`.

### 1.8 Notifications.tsx mock-data claim — re-verify

**Audit claim:** `mockNotifications: Notification[] = []` — permanently empty stub, zero API call.

**Current reality: false as of now.** `frontend/src/pages/Notifications.tsx` has **no** `mockNotifications` identifier anywhere (`grep -n "mockNotifications"` → 0 matches). The current file (204 lines) makes real calls: line 18 `import { apiRequest } from "@/services/client";`, line 62 `apiRequest<Notification[]>('/users/me/notifications/')`, line 73 mark-all-read POST, line 82 per-item PATCH. This looks like it was already fixed at some point before or during the same consolidation pass — **the audit's claim on this specific file no longer holds.**

### 1.9 GitHub OAuth component — bonus finding, not in the original audit scope

`frontend/src/components/github/GitHubConnect.tsx` imports `connectGitHub`/`getGitHubConnections` from `@/services/github` — but `GitHubConnect` itself is **never imported anywhere** (`grep -rln "GitHubConnect\b"` returns only its own definition file). Dead component, same "built but unrouted" pattern as CareerDashboard/Profile. Flagging for the same cleanup pass; not fixing per report-only scope.

---

## 2. AI shim migration status

### 2.1 The `apps.ai` / root `ai.bedrock` import count — STATUS: FULLY MIGRATED, COUNT IS NOW 0 (drifted down from the audit's 15)

**Verified by direct grep across `backend/` (excluding `venv/` and `__pycache__/`):**
- `grep -rn "ai\.bedrock\|apps\.ai\.bedrock\|apps\.ai\b" --include=*.py .` → **0 matches**.
- `grep -rEn "^\s*from ai import|^\s*import ai\b" --include=*.py .` → **0 matches** (excluding `backend/ai/__init__.py` itself).
- **`backend/apps/ai/` no longer exists on disk at all** — confirmed via `test -d apps/ai` → "DOES NOT EXIST". It was deleted in the same commit `35f797b` whose message explicitly says: *"Deleted orphaned apps/ai/ and apps/search/interfaces.py"* — confirmed via `git show 35f797b --stat`:
  ```
  backend/apps/ai/__init__.py         |   6 -
  backend/apps/ai/bedrock.py          |   8 -
  backend/apps/ai/bedrock_batch.py    | 355 -
  backend/apps/ai/prompt_versioning.py| 380 -
  ```
- **`backend/ai/` (the root-level package) still exists but is now a trivial 5-line re-export**, not a shim with real logic: `backend/ai/__init__.py`:
  ```python
  """
  DEPRECATED — import from apps.intelligence.career_ai instead.
  """
  from apps.intelligence.career_ai import career_ai_service as bedrock_service  # noqa: F401

  __all__ = ['bedrock_service']
  ```
  There is **no `backend/ai/bedrock.py` file anymore** (confirmed: `test -f ai/bedrock.py` → GONE, only `__init__.py` remains in that directory). `git log --oneline --diff-filter=D -- backend/ai/bedrock.py` shows the deletion happened at `35f797b`.
- Crucially: **nothing in the codebase imports `backend/ai/__init__.py` either.** All 18 real call sites already import directly from `apps.intelligence.career_ai`:
  ```
  ./apps/assessment/views.py
  ./apps/career/career_brain_service.py
  ./apps/career/cover_letter_service.py
  ./apps/career/cv_tailor_service.py
  ./apps/emails/tasks.py
  ./apps/employers/ranking_service.py
  ./apps/intelligence/job_matching.py
  ./apps/intelligence/workflows.py
  ./apps/interviews/coding_service.py
  ./apps/interviews/service.py
  ./apps/profiles/serializers.py
  ./apps/profiles/services.py
  ./apps/rashid/proactive_service.py
  ./apps/rashid/service.py
  ./apps/rashid/tools.py
  ./apps/skills/extraction.py
  ./apps/skills/management/commands/extract_skills_from_jobs.py
  ```
  (18 files, all via `from apps.intelligence.career_ai import career_ai_service as bedrock_service` — using the *new* canonical path, not the old shim.)

**Verdict on the audit's core claim: it has drifted, and drifted *for the better* — from 15 files on two legacy paths (`ai.bedrock`, `apps.ai.bedrock`) down to 0 files on either legacy path.** The `MASTER_STATE_AND_ROADMAP.md` claim (dated 2026-08-28) was accurate as of its own snapshot, but the same-day/next-day commit `35f797b` (2026-08-29 00:39:59) completed the consolidation the audit called out as unfinished. **This portion of the audit is now stale — re-running the audit's own recommended action (#6/#7 in its priority list: "migrate parse_cv etc. out of the shim; unify the 15 files on one import path") is unnecessary; it's done.**

### 2.2 The four business-logic functions — re-verify location

**Audit claim:** `parse_cv`, `calculate_match_score`, `generate_interview_questions`, `rank_candidates_for_job` exist ONLY in the old shim; `apps.intelligence` has no equivalent; deleting the shim would break these features.

**Current reality:** all four now live **directly inside `apps.intelligence`**, not in any shim:
- `backend/apps/intelligence/career_ai.py:52` — `def parse_cv(self, cv_text):`
- `backend/apps/intelligence/career_ai.py:143` — `def calculate_match_score(self, profile_data, job_data):`
- `backend/apps/intelligence/career_ai.py:324` — `def generate_interview_questions(self, role, experience_level, interview_type='technical'):`
- `backend/apps/intelligence/career_ai.py:443` — `def rank_candidates_for_job(self, job_data, candidate_profiles):`

These are methods on `class CareerAIService` (defined starting line 16 of the same file), instantiated as the module-level singleton `career_ai_service` (confirmed via the 18 import sites' `from apps.intelligence.career_ai import career_ai_service as bedrock_service` pattern, and `career_ai.py:634`: `bedrock_service = career_ai_service` — a second same-file alias). `career_ai.py`'s `parse_cv` implementation (lines 52–141) calls `self.invoke_model(...)` (line 124), which in turn (lines 34–50) delegates to `apps.intelligence.llm_plugin.LLMRequest` and `apps.intelligence.service.get_ai_service()` (lines 25, 35) — i.e., real, non-stub logic routed through the consolidated intelligence layer, not a placeholder.

There is a **second, unrelated `parse_cv`** at `backend/apps/profiles/cv_parser.py:357` (`def parse_cv(self, file: UploadedFile) -> ParsedCVData:`) — this is a different class/purpose (a `CVParser.parse_cv` that takes an `UploadedFile` and does the file-handling/orchestration, not the AI-extraction step) and is not a duplicate of `career_ai.py`'s AI-based `parse_cv(self, cv_text)`, which takes raw text. Not a conflict — different layers of the same pipeline (`workflows.py:38` shows `career_ai.py`'s `parse_cv` being called with pre-extracted text inside a Celery task, separate from `cv_parser.py`'s file-upload orchestration).

**Verdict: the audit's "only in the shim, not in apps.intelligence" claim is now false — these functions live in `apps.intelligence.career_ai` and nowhere else.** No shim deletion risk remains because there is effectively no more shim with real logic to delete (§2.1) — `backend/ai/__init__.py` is now a harmless 5-line re-export nobody imports.

### 2.3 What remains for the AI layer (smaller, lower-risk items than the audit implied)

Since the heavy migration is done, the only remaining architectural-drift item in this area is cosmetic:
- **`backend/ai/__init__.py`** (5 lines, `DEPRECATED` docstring) is dead code with zero importers — confirmed via the exhaustive `apps.ai`/`ai.bedrock` grep in §2.1 returning 0 real usages. It can be deleted with no migration risk (nothing depends on it).
- All 18 call sites already alias the import as `bedrock_service` for readability (`... as bedrock_service`) even though the canonical name is `career_ai_service` — this is a naming-consistency nit, not a correctness issue, and not worth churning 18 files over.

---

## 3. Verification-of-verification — does the 2026-08-28 audit still hold?

| Audit claim | Status as of 2026-08-29 review | Evidence |
|---|---|---|
| Two frontend clients (`client.ts` w/ `/api/v1`, `api.ts` w/o) cause Recommendations 404 | **STALE — root file (`services/api.ts`) deleted in `35f797b`.** Recommendations already used `client.ts`, so the described 404 mechanism doesn't apply to it as described. | §1.1, §1.4 |
| "One line fixes Recommendations" | **False as literally stated** — the actual fix was a file deletion + ~5 files' import-statement migration (some of which were still in-flight/uncommitted during this review). | §1.2, §1.3, §1.5 |
| CareraDashboard (mock) routed, TalentScore (real) orphaned | **STALE — already swapped in `35f797b`.** `TalentScore` is now routed at `/app/career`; `CareerDashboard.tsx` is dead code, not deleted yet. | §1.6 |
| Profile.tsx routed, ProfilePage.tsx orphaned | **STALE — already swapped in `35f797b`.** `ProfilePage` is now routed; `Profile.tsx` is dead code, not deleted yet. | §1.7 |
| `Notifications.tsx` has permanently-empty `mockNotifications` array | **STALE / false now.** No `mockNotifications` identifier exists in the current file; it makes real `apiRequest` calls. | §1.8 |
| 15 files import `ai.bedrock`/`apps.ai.bedrock` | **STALE — drifted to 0.** `apps/ai/` was deleted; the root `ai/bedrock.py` was deleted; all 18 real call sites use `apps.intelligence.career_ai` directly. | §2.1 |
| `parse_cv`/`calculate_match_score`/`generate_interview_questions`/`rank_candidates_for_job` exist only in the old shim | **STALE — false now.** All four live in `apps/intelligence/career_ai.py` (lines 52, 143, 324, 443) exclusively; the old shim paths no longer exist. | §2.2 |
| Deleting the shim now would break these features | **Moot — the shim (with real logic) is already gone**, and the features were re-pointed at `apps.intelligence` in the same commit. Only a 5-line dead re-export file remains, safely deletable. | §2.1, §2.3 |

**Bottom line: both architectural-drift items this task was scoped to were substantially already fixed by commit `35f797b` (2026-08-29 00:39:59), one day after the audit's 2026-08-28 snapshot — but that same commit's frontend-side changes left three build-breaking import errors that were still being patched, live, during this review** (§1.2, §1.5). The AI-shim side of `35f797b` appears to have landed clean with no equivalent breakage.

---

## 4. What is genuinely new (not in the prior audit)

1. **The `services/api.ts` deletion temporarily broke the production build** (`Could not resolve "./api"` / `ENOENT` / `"apiClient" is not exported`) — this is a regression the prior audit could not have seen (it postdates the 2026-08-28 snapshot) and is worse in the short term than the drift it fixed, because a broken build blocks *everything*, not just Recommendations. By end of session this was resolved and `npx vite build --mode production` passes (exit 0).
2. **Five files are currently uncommitted working-tree changes** (`lib/api.ts`, `pages/Applications.tsx`, `services/{github,intelligence,profile}.ts`) that fix the above build break. If lost (uncommitted, no stash), the build breaks again for the next person who pulls `fc16378`.
3. **`CareerDashboard.tsx`, `Profile.tsx`, and `GitHubConnect.tsx` are confirmed dead code** (zero import sites) that the routing-swap commits left behind instead of deleting — small cleanup debt, not a functional bug.
4. **`backend/ai/__init__.py`** is a harmless but pointless 5-line dead shim with zero importers — trivial deletion candidate.

---

## 5. Prioritized action list

1. **Commit the five uncommitted frontend files** (`frontend/src/lib/api.ts`, `frontend/src/pages/Applications.tsx`, `frontend/src/services/github.ts`, `frontend/src/services/intelligence.ts`, `frontend/src/services/profile.ts`) immediately. Without this, `git clone` + `npm run build` on the current `HEAD` (`fc16378`) fails with three separate module-resolution errors (§1.2). This is the single highest-impact, lowest-effort fix available right now — it's the difference between a working and a broken production build. *(Verify with `npx vite build --mode production` → must exit 0 before and after commit.)*
2. **Collapse the two remaining `@/lib/api` legacy-indirection imports** (`frontend/src/hooks/use-seo.ts:3`, `frontend/src/pages/Jobs.tsx:13`) to import directly from `@/services/client`, then delete `frontend/src/lib/api.ts` entirely (it's now a thin re-export whose only real value — `fetchJobs`/`fetchJobBySlug`/etc. — duplicates what's already in `@/services/jobs`). This finishes the "single source of truth" goal the prior audit set for the frontend client.
3. **Delete the three orphaned frontend files**: `frontend/src/pages/CareerDashboard.tsx`, `frontend/src/pages/Profile.tsx`, `frontend/src/components/github/GitHubConnect.tsx` (and its sibling import in `frontend/src/services/github.ts` if nothing else uses it — re-check import sites at delete time). All three are confirmed to have zero import sites as of this review; each is a self-contained deletion with no migration risk.
4. **Delete `backend/ai/__init__.py`** (and remove the now-empty `backend/ai/` directory). Zero importers confirmed (§2.1, §2.3) — this is the last remnant of the AI shim and is risk-free to remove.
5. **Re-run an end-to-end (not just static) check on the Recommendations page** — hit the live `/app/recommendations` route against a running backend and confirm a 200, not just a 404-shaped code path. This report's finding that the 404 mechanism no longer applies is based on static import analysis only (§1.4); no backend was running during this review to confirm behaviorally.
6. **Note for the next status-doc audit:** this review's own findings will go stale just as fast as the prior one did — three of its four AI-shim/frontend-client items were already resolved one day after they were written, and the frontend side was still being actively patched *during this review's own session*. Re-verify against live code before trusting either this report or the prior one on a future pass.

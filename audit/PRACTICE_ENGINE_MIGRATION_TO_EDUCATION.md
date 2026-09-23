# Practice Engine → USAM Education: Migration Plan (code-verified)

_Date: 2026-09-23. Per the platform directive, standalone Coding Practice does
not belong as a core Career feature; it belongs in USAM Education. This documents
the current footprint and the migration, and records what was changed now._

## Why

Career's job is **discover → understand → prepare → grow → apply directly**.
Open-ended coding practice / problem solving is a *learning* activity. Keeping it
as a standalone Career nav item dilutes the Career information architecture. The
directive requires: remove it from Career navigation, preserve the engine, and
document how it moves to Education — without breaking dependencies.

## Current footprint (verified)

### Frontend
- **Page**: `frontend/src/pages/CodingPractice.tsx` — full UI: difficulty +
  language pickers, problem generation, code editor, run + evaluate. Uses
  `AppShell`.
- **Route**: `App.tsx` → `/app/coding-practice` (lazy `CodingPractice`,
  `RequireAuth`).
- **Navigation**: `PublicNavMenu.tsx` `individualFeatures` had a "Coding
  Practice" mega-menu entry (`/app/coding-practice`). **[REMOVED this pass]**
  It is **not** present in `AuthNavbar` authenticated nav arrays (confirmed via
  grep), so no authenticated-nav change is required.
- **Services**: `services/interviews.ts` → `generateCodingProblem`,
  `submitCodingSolution`, `evaluateCodingSolution` (+ types `CodingProblem`,
  `ExecutionResult`, `EvaluationResult`).

### Backend
- Served by `apps/interviews` (the coding-practice endpoints live alongside
  interview simulation). The engine (problem generation, code execution,
  AI evaluation) is functional and shared with interview prep.

## What changed now (safe, reversible)

- **Removed the "Coding Practice" entry from the Career public nav**
  (`PublicNavMenu.tsx` `individualFeatures`). The feature is no longer surfaced
  as a standalone Career capability.
- **Route + page + backend left intact.** `/app/coding-practice` still resolves
  (no dead links, no broken deps, no data loss). This is a *navigation/IA*
  correction, not a deletion — exactly what the directive asked ("do not simply
  hide the pages" was about not orphaning them; here the engine is preserved and
  documented for migration rather than thrown away).

## Target architecture (USAM Education)

```
CAREER  →  Job / Skill Gap  →  Required Skills  →  Learning Recommendation
        →  USAM EDUCATION  →  Practice (coding, problems, challenges)
        →  Assessment  →  Evidence / Skill Progress
        →  Career Profile  →  Better Job Matching
```

Education should own:
- Coding Practice, Problem Solving, Technical Challenges
- Skill Assessments, project-based practice
- Progression, scoring, difficulty, mastery, certificates

## Migration steps (for the Education platform work, tracked)

1. **Move the engine**: relocate the coding problem-generation / execution /
   evaluation logic out of `apps/interviews` into an Education service (or a
   shared `apps/practice` used by Education), keeping interview-specific coding
   prep as a thin consumer.
2. **Move the UI**: `CodingPractice.tsx` becomes an Education page; the Career
   route can 301/redirect to the Education entry once Education exists.
3. **Shared contract**: expose practice results as skill evidence the Career
   Graph can consume (feeds matching + Talent Score).
4. **Delete from Career** only after Education consumes it and the redirect is in
   place — so no user hits a dead route.

## Not done yet (needs the Education platform to exist)

- Physically relocating the backend engine and the page.
- The Career↔Education evidence bridge (practice result → skill progress →
  match boost).
These are Education-platform tasks; this pass performs only the safe Career-nav
removal + documentation so nothing breaks in the meantime.

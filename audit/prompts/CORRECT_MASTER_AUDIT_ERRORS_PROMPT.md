# PROMPT — E-Career: Correct 4 Verified Errors in MASTER_PLATFORM_AUDIT_2026-08-31.md, Then Continue Real Remaining Work

You are a senior full-stack engineer working on E-Career at
`M:\job already web for jobs\E-Career`. A file
`audit/MASTER_PLATFORM_AUDIT_2026-08-31.md` was just produced by "4
parallel deep-audit agents." **Before doing ANY new work, correct 4
verified factual errors in that report** — these were caught by direct
code inspection (not by re-reading the report), and following the
report's original (wrong) claims would cause you to rebuild working
code from scratch, wasting effort and risking duplication/conflicts.

## Part 1 — Fix these 4 verified errors in the audit report itself

**Error 1: `apps/resume/` is NOT empty/a stub.** The report's own line
says *"Resume Builder backend is a STUB — apps/resume/ has no
models/views."* This is false. Direct inspection confirms:
- `apps/resume/models.py` — 377 lines: `ResumeTemplate`, `Resume`,
  `ResumeExport`, `ProfileSection`, `SkillVerification` models, all real.
- `apps/resume/views.py` — 455 lines: `get_resume_templates`,
  `get_user_resumes`, `get_resume`, `create_resume`, `update_resume`,
  `delete_resume`, `export_resume`, `get_profile_sections`,
  `create_profile_section`, `get_skill_verifications` — all real DRF
  views.
- `apps/resume/export_service.py` — 132 lines, a real export service.
- `apps/resume/urls.py` is real and **is wired into `config/urls.py`**
  at `path("resume/", include("apps.resume.urls"))` — confirmed present.
- **What to actually verify instead**: run the resume endpoints live
  (real HTTP request with a real JWT, same pattern as every prior
  live-verification pass) — create a resume, export it, confirm the
  export actually produces a file (PDF/DOCX) and isn't a silent no-op.
  Check if `apps/resume/` has ANY test file (a real gap — confirmed
  `find apps/resume -iname "test*.py"` returns nothing) — write tests if
  none exist. This is the real, narrower gap: **test coverage**, not
  "backend doesn't exist."

**Error 2: `apps/salary/` is NOT a stub either.** The report says
*"apps/salary/ is a complete stub — no models, views, or services."*
Also false. Direct inspection confirms:
- `apps/salary/models.py` — 450 lines, real models.
- `apps/salary/views.py` — 366 lines: `get_salary_benchmark`,
  `get_market_rates`, `get_salary_insights`, `get_salary_alerts`,
  `mark_alert_as_read` — all real.
- Wired into `config/urls.py` at `path("salary/", include("apps.salary.urls"))`.
- **What to actually verify instead**: same as Error 1 — live-test each
  endpoint with real data, check test coverage (verify if any exists,
  add if missing), and specifically verify `get_salary_insights`'s
  actual data source — is the salary data real (scraped/aggregated from
  somewhere) or does it degrade to an AI-only estimate with no
  structured backing data? That distinction matters for the "Salary
  Intelligence Module" gap the report flagged — the gap may be DATA
  SOURCING quality, not missing code.

**Error 3: Scrapling verdict is wrong given the user's explicit request
and the already-made architecture decision.** The report says *"SKIP —
our ATS-specific API connectors are more reliable"* — this compares
Scrapling to the WRONG use case. `scrapling==0.4.15` is already pinned
in `requirements.txt` (a decision made in an earlier phase, before this
report), and `apps/intelligence/adaptive_scraper.py` (230 lines, real,
well-designed with a `is_available` check + BeautifulSoup fallback) uses
it specifically for **unknown/custom career pages that have no ATS
connector** — NOT as a replacement for the 10 existing ATS connectors
(Greenhouse, Lever, Ashby, etc., which correctly keep using direct API
calls — the report is right that those shouldn't change). The real
finding: **Scrapling is pinned but not actually installed**
(`pip show scrapling` → not found), so `adaptive_scraper.py` currently
always falls through to its weaker BeautifulSoup fallback. Fix per
`audit/prompts/PHASE_10_SCRAPLING_OSS_PROMPT.md` (already written, read
it in full) — install it, verify the real Scrapling path engages (not
just the fallback), and confirm the import paths in
`adaptive_scraper.py` (`from scrapling import Fetcher` /
`from scrapling import StealthyFetcher`) match the actually-installed
package's real API (the installed package may expose these from
`scrapling.fetchers` instead — verify and fix if so).

**Error 4: Rashid tool count discrepancy (9 vs 15) — resolve, don't guess.**
The report claims "15 tools registered." Direct inspection of
`apps/intelligence/agent.py` via `grep -c "@agent.tool"` finds exactly
**9**. Before continuing: find where the other 6 tools the report counted
might be registered (check if `apps/rashid/tools.py`, confirmed real and
touched in the Final Platform Completion pass, registers additional
tools through a different mechanism than the `@agent.tool` decorator —
e.g. a separate tool registry merged at agent-creation time) OR confirm
the report simply miscounted. Report the corrected, verified number in
your final report — do not carry forward an unverified count.

## Part 2 — Also verify: LightFM (same install-check pattern as pydantic-ai and Scrapling)

`apps/search/recommendation_engine.py` tries `import lightfm` and logs
`"LightFM not installed, using fallback recommendations"` if it fails —
this is the SAME pattern now found 3 times in this codebase (pydantic-ai
in Phase 7c, Scrapling in Phase 10, now potentially LightFM): a real,
sophisticated capability gated behind an optional import that silently
degrades. Check `pip show lightfm` — if not installed, this means the
platform has been running on **fallback content-based matching only**,
not the ML collaborative-filtering hybrid the report describes as fully
working ("LightFM + content-based hybrid... 60/40 collaborative/content"
— if LightFM was never installed, that 60/40 hybrid never actually ran,
and matching has been 100% content-based this whole time). This is
potentially a bigger finding than Scrapling — LightFM affects every job
recommendation shown to every user. Install it if missing, verify the
collaborative-filtering path actually engages with real interaction data
(saves, applications, dismissals — confirm E-Career actually logs these
as training signals for LightFM, not just stores them for display), and
re-run a live recommendation request to confirm the model-based path
(not the fallback) is what's actually responding.

## Part 3 — After Part 1/2 fixes, address the report's 3 CORRECTLY identified real gaps

These 3 do appear to be genuine, correctly-identified gaps (spot-check
each yourself before building, same discipline as everything above):

1. **6 placeholder scoring functions in `apps/career/scoring_engine.py`**
   — confirmed via direct inspection: `calculate_experience_score`
   (company quality placeholder, responsibility growth placeholder),
   `calculate_education_score` (degree relevance placeholder),
   `calculate_growth_score` (goal completion placeholder),
   `calculate_communication_score` (CV clarity placeholder),
   `calculate_ai_confidence` (consistency check placeholder) — plus check
   the 6th the report mentions in `apps/employers/ranking_service.py`
   (education scoring, knockout evaluation). For each, implement real
   logic:
   - Company quality: use existing company data (size, industry,
     verification status) rather than a fabricated score.
   - Responsibility growth: compare seniority/title progression across
     a user's `CareerUserSkill`/experience history entries chronologically.
   - Degree relevance: match degree field against target role's
     typical requirements (can use the existing ESCO/O*NET skill
     taxonomy's occupation-to-education mappings if present — check
     `apps/skills/` models first before inventing a new mapping table).
   - Goal completion: use real `CareerGoal`/`CareerGoalAction` completion
     data (models already exist per the Phase 9 cross-check).
   - CV clarity: a real, lightweight NLP heuristic (sentence length
     variance, passive-voice ratio, vague-phrase detection) — NOT another
     AI model call for something this cheap to compute directly, per the
     project's own cost-consciousness principle.
   - Consistency check: cross-reference dates/claims across CV-parsed
     experience entries for contradictions (overlapping employment dates,
     impossible timelines) — a real, useful check, not a fabricated
     score.
2. **Progressive onboarding doesn't skip CV-known fields** — this
   matches Phase 9's task 9.5 exactly (already scoped in
   `audit/prompts/PHASE_9_MASTER_CROSSCHECK_PROMPT.md` — if Phase 9 has
   already run and fixed this, don't duplicate; check its completion
   report first).
3. **CV/Resume PDF export** — per Error 1's finding, `export_service.py`
   already exists; verify it ACTUALLY produces a working PDF/DOCX via a
   real test before concluding this needs building rather than testing.

## Rules

- Do not rebuild `apps/resume/` or `apps/salary/` from scratch — they
  are real, working (pending live verification), substantial
  implementations. Extend/test/fix, never replace.
- Local commits only, do not push.
- Real test coverage for every fix in this pass — apps/resume and
  apps/salary currently have ZERO test files each; this is the actual,
  correctly-identifiable gap the original report almost found but
  mis-described as "no backend."
- Run full backend test suite + `npx tsc --noEmit` + `npx vite build
  --mode production` before considering this pass complete.

## When done

Overwrite the erroneous sections of `audit/MASTER_PLATFORM_AUDIT_2026-08-31.md`
in place (fix Errors 1-4 with corrected, verified information — don't
leave the wrong claims standing) and write
`audit/MASTER_PLATFORM_AUDIT_CORRECTIONS_REPORT.md` documenting exactly
what was wrong, why (likely: an audit sub-agent checked directory
existence/names without opening files), what the real state was, and
what you did about the LightFM finding specifically (this may be the
single highest-impact fix in this entire pass if confirmed — every job
recommendation on the platform could have been running in fallback mode
this whole time).

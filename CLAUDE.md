# E-Career — Claude Code Project Memory

**Repo root (this file's directory):** `M:\job already web for jobs\E-Career`
Django/DRF backend in `backend/` (venv at `backend/venv/`), React/Vite
frontend in `frontend/`. Production domain: jobs.usamif.com.

## Mandatory reading order for ANY task in this repo

1. `AGENTS.md` — project conventions, known pitfalls, architecture bets
   (Career Graph, direct-apply verification moat), security history.
2. `MASTER_IMPLEMENTATION_PLAN.md` — the ONE authoritative synthesis of 10
   independent code-verified domain audits (2026-08-29). Supersedes every
   other `*_SUMMARY.md`/`*_REPORT.md`/`*_PLAN.md` in the repo, including
   `MASTER_STATE_AND_ROADMAP.md` and `BACKEND_ARCHITECT_REVIEW_2026-08.md`
   (both partially stale now — MASTER_IMPLEMENTATION_PLAN.md's §3 flags
   the specific claims that were wrong).
3. `audit/D1_*.md` through `audit/D10_*.md` — full detailed evidence behind
   the synthesis, if you need more than the summary tables.
4. `audit/prompts/PHASE_{0,1,2,3}_PROMPT.md` — the actual execution
   prompts, each self-contained, each with a numbered item list, each with
   file:line evidence per item. **Execute these in order — 0 before 1
   before 2 before 3** — later phases assume earlier ones landed.

## Hard rules

- **Never read, print, log, or commit `backend/.env`** or any secret. Some
  tools block this by design — respect it, don't work around it.
- **Do not trust any status doc at face value, including this one and
  MASTER_IMPLEMENTATION_PLAN.md.** This repo has a documented history of
  status docs drifting from code within days. Before fixing an item,
  re-verify the cited file:line against CURRENT code — if already fixed or
  moved, say so in your completion report and skip it; don't re-break
  working code.
- **Local git commits only — do not `git push`.** The human will push
  after reviewing. Commit each logical group of fixes separately with a
  clear message; don't squash a whole phase into one commit.
- Write each phase's completion report to
  `audit/PHASE_{N}_COMPLETION_REPORT.md` exactly as each phase prompt
  specifies, before considering that phase done.
- Run relevant tests after each fix where tests exist. If AWS
  credentials/CLI access for Bedrock/Polly/Transcribe/Judge0-key items
  aren't available in this environment, document as a human action item
  in the completion report rather than failing the whole phase.
- venv Python: `backend/venv/Scripts/python.exe` (Windows). Activate via
  `source backend/venv/Scripts/activate` in bash, or invoke the exe
  directly.

## Architecture context (from AGENTS.md, condensed)

One shared intelligence layer is meant to power the whole platform — the
repeatedly-flagged risk is re-fragmenting into disconnected per-feature
modules. `MASTER_IMPLEMENTATION_PLAN.md` §3 "Cross-Cutting Patterns"
documents exactly this happening in ~10 places (duplicated CV parsers,
duplicated recommendation engines, duplicated notification models, etc.) —
Phase 1 exists specifically to consolidate these.

Direct-apply verification (rejecting LinkedIn/Indeed/ZipRecruiter/Monster
"Apply" links, only accepting direct employer/ATS links) is this
platform's stated moat — treat regressions here as high severity.

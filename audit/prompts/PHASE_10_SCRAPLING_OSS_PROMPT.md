# PROMPT — E-Career Phase 10: Install Scrapling (Already-Chosen, Uninstalled Dependency) + Adopt Free OSS Patterns from ai-job-search

You are a senior full-stack engineer working on E-Career at
`M:\job already web for jobs\E-Career`. Read `AGENTS.md`, `CLAUDE.md`,
and `audit/PHASE_9_MASTER_CROSSCHECK_REPORT.md` (if it exists yet —
Phase 9 may still be running) first.

## 🔴 Critical finding — same pattern as the Phase 7c `pydantic_ai` bug, found again

Direct inspection just before writing this prompt found:

1. **`scrapling==0.4.15` is already pinned in `requirements.txt`** (this
   was a deliberate, already-made architecture decision by an earlier
   phase — not a new suggestion) but **is not actually installed** in the
   venv (`pip show scrapling` → "Package(s) not found").
2. **`apps/intelligence/adaptive_scraper.py`** (230 lines) is a real,
   well-designed wrapper around Scrapling's `Fetcher`/`StealthyFetcher`
   — it correctly checks `is_available` before use and has a genuine
   BeautifulSoup-based fallback (`_fallback_scrape`) when Scrapling is
   absent, so **this is NOT a hard crash like the pydantic-ai bug was** —
   the platform runs safely without it, just at reduced scraping
   capability (no Cloudflare/anti-bot bypass, no adaptive CSS selectors
   that survive page redesigns, plain BeautifulSoup link-scanning only).
3. **It IS wired to a live Celery task** —
   `apps/scraper/tasks.py`'s `scrape_single_url` (triggered by
   changedetection.io when a career page changes) imports and calls
   `get_adaptive_scraper().scrape_career_page(url)`. So installing
   Scrapling activates a real, already-integrated capability rather than
   introducing a new one — this is a pure unlock, not new integration
   work.

**User-requested repo `d4vinci/Scrapling`** (BSD-3-Clause, fully free,
no commercial restriction, 195k+ downloads per PyPI stats referenced in
its README, actively maintained, includes CLI + MCP server + spider
framework) **is exactly the dependency already chosen and pinned** — the
task here is to actually install and verify it, not evaluate a new
adoption. This is the single highest-leverage, lowest-effort item in this
phase.

## Task 1 — Install and verify Scrapling (do this first)

1. `pip install scrapling==0.4.15` (or `pip install "scrapling[fetchers]"`
   if the base install alone doesn't include `Fetcher`/`StealthyFetcher`
   — check Scrapling's own docs for which extras are needed; the repo's
   README shows `pip install scrapling` for the parser only and
   `pip install "scrapling[fetchers]"` for the fetcher classes this
   codebase actually imports).
2. Run `scrapling install` afterward (per Scrapling's own setup
   instructions) to download the browser binaries `StealthyFetcher`
   needs — confirm this step is required and document the exact command
   that worked.
3. Confirm `python -c "from scrapling.fetchers import Fetcher,
   StealthyFetcher; print('ok')"` succeeds.
4. Update `AdaptiveScraperService.is_available` in
   `apps/intelligence/adaptive_scraper.py` if the import path differs
   from what's currently coded (`from scrapling import Fetcher` vs. the
   real package's `from scrapling.fetchers import Fetcher` — verify
   against the actually-installed package's real API, don't assume the
   existing code guessed correctly; the Scrapling README's own quickstart
   uses `from scrapling.fetchers import Fetcher, AsyncFetcher,
   StealthyFetcher, DynamicFetcher` — cross-check `adaptive_scraper.py`'s
   `from scrapling import Fetcher` and `from scrapling import
   StealthyFetcher` lines against this and fix if the import path is
   wrong for the installed version).
5. Write a real test: mock or hit a real simple public career page (pick
   a stable, scraping-tolerant target, or use a local fixture HTML file
   served via a test HTTP server — do not hit unpredictable live sites in
   CI) and confirm `scrape_career_page()` actually returns `ScrapedJob`
   objects via the Scrapling path (not silently falling through to the
   BeautifulSoup fallback due to a broken import).
6. Run the existing scraper test suite (`apps/scraper/tests/`,
   `apps/intelligence/` if it has tests for this file) and confirm no
   regressions.

## Task 2 — Evaluate `MadsLorentzen/ai-job-search` again, precisely

The prior Phase 9 audit prompt already gave this repo a REJECT verdict
for direct code integration (it's a personal Claude-Code-CLI job-hunt
tool run by an individual job seeker in their own terminal — a
`/setup`, `/scrape`, `/apply` workflow with LaTeX CV compilation, Danish
job-portal-specific scraping skills, and file-based state in a personal
git fork — not a multi-tenant Django/React SaaS platform). **This verdict
stands — do not attempt to import its code or architecture wholesale.**
However, since the user is asking specifically about this repo again,
extract and evaluate 3 CONCRETE, PORTABLE PATTERNS it demonstrates well,
each independently:

1. **Its `/apply`'s ATS-parseability check** (mentioned in its README:
   `pip install pypdecode` for a PDF-based ATS check with a Poppler
   `pdftotext` fallback, degrading gracefully to visual keyword review if
   neither is available). E-Career already has `ats_scoring_service.py`
   (Phase 2/5 work) — compare its approach to this repo's degrading-
   fallback pattern (best method → next-best → manual-style fallback,
   never a hard failure). If E-Career's `ats_scoring_service.py` doesn't
   already have this 3-tier graceful degradation, consider adding it —
   this is a pattern worth adopting, not code to import.
2. **Its drafter-reviewer 2-agent pipeline for cover letters** (draft
   agent writes, a second reviewer agent critiques and the draft is
   revised before final output — described in its README's workflow
   diagram). Compare to E-Career's `apps/career/cover_letter_service.py`
   — does it currently do single-pass generation, or does it already have
   a review/revision step? If single-pass, evaluate adding a lightweight
   2-call review pattern (generate → have a second, possibly cheaper,
   model call critique against the job requirements → revise) using
   E-Career's own `model_router.py` for cost-appropriate model selection
   at each step (a cheap model for review, not necessarily the same
   model as drafting) — this is a genuine quality improvement pattern
   worth adopting if not already present.
3. **Its `/outcome followup` pattern** (surfaces applications that have
   gone quiet after N days, drafts — never auto-sends — a follow-up
   message using only claims already in the submitted materials).
   Compare against E-Career's existing `apps/rashid/proactive_service.py`
   (confirmed real and already wired to some notification triggers) — if
   it doesn't already have an "application gone quiet, suggest a
   follow-up draft" trigger, this is a concrete, valuable, easy addition
   that fits the existing proactive-service architecture exactly (same
   pattern as Task 9.3 in the Phase 9 prompt if that phase already added
   trigger types — check first, don't duplicate).

**Do NOT**: fork the repo, install its CLI tools (`bun`-based Danish job
portal skills, LaTeX resume compilation), adopt its file-based
"documents/ folder as system of record" data model, or introduce a
Claude-Code-CLI dependency into the platform's own runtime — none of
that fits a multi-tenant Django/React SaaS. The 3 patterns above are
implementable natively in E-Career's existing Django services using
E-Career's own AI Model Router and existing service architecture.

## Task 3 — Confirm no other requirements.txt-pinned-but-uninstalled dependencies exist

Given this is now the SECOND time a real dependency was pinned in
`requirements.txt` but never actually installed (`pydantic-ai-slim` in
Phase 7c, `scrapling` here), do a full sweep:

```
pip install -r requirements.txt --dry-run 2>&1 | grep -i "already satisfied" > /tmp/satisfied.txt
# then diff against every package name in requirements.txt to find any NOT already satisfied
```

Or more directly: `pip freeze > /tmp/installed.txt` and diff against
every `==`-pinned line in `requirements.txt`. For every package found
pinned-but-not-installed, determine (same rigor as Tasks 1-2 above): is
it (a) truly unused dead code (like the Prefect case in Phase 7a — safe
to remove from requirements.txt), or (b) real code waiting to be
unlocked (like this Scrapling case — install it and verify), or (c)
something in between (partially wired, needs investigation). Fix each
one found, don't just report them.

## Rules

- Local commits only, do not push.
- Do not adopt `JOYCEQL/magic-resume`'s code (commercial-license
  restriction, per the Phase 9 audit's REJECT verdict — unchanged).
- Do not fork or integrate `MadsLorentzen/ai-job-search` directly — only
  the 3 named patterns, implemented natively.
- Real test coverage for the Scrapling activation and any new
  proactive-service trigger types.
- Respect scraping ethics already established in this codebase
  (robots.txt, rate limits, ToS) — Scrapling's own docs describe
  anti-bot bypass capabilities; use them only for E-Career's own
  legitimate career-page scraping within the existing verification/
  blocklist framework (`BlockedDomain` model), never to circumvent a
  site's explicit anti-scraping policy in bad faith.
- Run full backend test suite + `npx tsc --noEmit` + `npx vite build
  --mode production` before considering this phase complete.

## When done

Write `audit/PHASE_10_SCRAPLING_AND_OSS_PATTERNS_REPORT.md`: Task 1's
before/after (scraping capability unlocked, with a real before/after
test showing Scrapling actually engaging, not falling to fallback), Task
2's 3 pattern evaluations (adopted/not-adopted with reasoning for each,
independently), and Task 3's full dependency sweep results. End with:
**"Are there any other real, uninstalled-but-pinned dependencies still
silently degrading platform capability?"** — a definitive yes/no, not a
hedge.

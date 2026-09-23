# Phase 0 — Job Ingestion & Direct-Apply Moat Audit (code-verified)

_Date: 2026-09-23. Verified against real backend code, not status docs._

## Executive finding

USAM already has a **complete, well-built ingestion + verification engine**. The
platform looked empty ("21+ opportunities") not because the engine is missing,
but because of a small number of wiring/seed gaps. Those gaps are now fixed
(see "Fixes applied").

## What exists (verified)

- **`apps/scraper/`** — `ScraperOrchestrator` (`orchestrator.py`) with a real
  pipeline: `scrape_all_sources` → `scrape_source` (dispatch by
  `source.ats_platform`) → `_process_jobs` (aggregator filter → ATS fingerprint
  → legitimacy score ≥ 0.4 → Company get_or_create → dedup on
  `(ats_job_id, ats_platform)` → `Job.objects.create` → `verify_job`).
- **ATS connectors** (`apps/scraper/ats/`): `greenhouse` (real public API:
  `api.greenhouse.io/v1/boards/{slug}/jobs`), `lever`, `ashby`, `bamboohr`,
  `smartrecruiters`, `workable`, `teamtailor` (public-API pattern). `workday` is
  a Playwright stub; `icims/oracle/sap` exist but aren't dispatched.
- **`apps/verification/`** — `VerificationEngine.verify_job` runs 6 stages
  (ATS fingerprint → redirect resolver → domain verifier → legitimacy scorer →
  freshness → deduplicator), computes a weighted `trust_score`, and sets
  `apply_url_verified` + `quality_state='direct_verified'` when
  `trust_score >= SEARCH_TRUST_SCORE_THRESHOLD` (default 0.4). A blocked
  aggregator short-circuits to `rejected`.
- **`BlockedDomain`** — seeded by migration `0003` with 25 aggregators
  (LinkedIn, Indeed, Glassdoor, ZipRecruiter, Monster, Bayt, Wuzzuf,
  GulfTalent, Tanqeeb, …).
- **Celery tasks** — `scrape_all_sources`, `verify_apply_urls`,
  `expire_old_jobs`, verification liveness/reverification.

## Root causes of "only ~21 jobs" (verified)

1. **No usable `Source` rows.** `setup_sources.py` seeded aggregator/careers
   URLs with **no `ats_platform`** and `type='job_board'`. The orchestrator
   dispatches by `ats_platform`, so every source hit "Unknown platform →
   return []". Nothing scraped. (Those aggregators are also blocklisted and
   violate the moat.)
2. **`ApprovedATS` never seeded.** The allow-list half of the moat was inert.
3. **Scheduler mismatch.** `CELERY_BEAT_SCHEDULER=DatabaseScheduler` but no
   `PeriodicTask` rows exist, so the static `beat_schedule` in `config/celery.py`
   never fires — the scraper is effectively manual-only.
4. **The ~21 live jobs are demo seed rows** (`seed_jobs.py`) that bypass
   verification and are shown only because the public listing gated on
   `status='active'` alone.
5. **Read-layer gate ignored the Quality Engine.** `JobListView.get_queryset()`
   filtered on `status='active'` only — never on `quality_state`,
   `apply_url_verified`, or `is_expired`. So rejected/duplicate/broken jobs
   could surface and the moat wasn't enforced at read time.

## Fixes applied (this pass)

- **Read-layer moat enforcement** — `JobListView.get_queryset()` now also
  requires `quality_state in QUALITY_VISIBLE_STATES` and excludes
  `is_expired=True`. Rejected/duplicate/broken jobs no longer surface.
- **`seed_approved_ats` command** — seeds the `ApprovedATS` allow-list
  (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable, Teamtailor,
  Recruitee, BambooHR, Jobvite, Personio, iCIMS, Oracle, SAP SuccessFactors).
- **`setup_sources` rewritten** — seeds **real, moat-compliant** ATS boards
  (Greenhouse/Lever/Ashby public APIs) with correct `ats_platform` and
  `type='scraper'`, so the orchestrator actually dispatches to a connector.
  Adds `--purge-aggregators` to deactivate legacy blocklisted sources.

## Operator runbook (make jobs flow)

```bash
# 1. Seed the allow-list moat
python manage.py seed_approved_ats

# 2. Seed real scrapable sources (and retire aggregators)
python manage.py setup_sources --purge-aggregators

# 3. First real ingestion run (sync, proves the path)
python manage.py run_scrapers            # orchestrator; --dry-run to preview

# 4. (Optional) verify existing apply URLs + expire stale jobs
python manage.py verify_apply_urls
python manage.py expire_old_jobs

# 5. Confirm real verified jobs exist
#    quality_state='direct_verified', apply_url_verified=True
```

For continuous ingestion, either create `PeriodicTask` rows for
`scrape-all-sources` / `verify-apply-urls` / `expire-old-jobs` (DatabaseScheduler
is active), or switch `CELERY_BEAT_SCHEDULER` to the default so
`config/celery.py`'s static schedule is honored — and ensure a Celery **beat**
and **worker** are running.

## Remaining (tracked, not yet done)

- Seed/managed `PeriodicTask` rows (or scheduler switch) for automated runs.
- Purge the demo `seed_data` jobs from production once real jobs flow.
- Wire `icims/oracle/sap` connectors and finish `workday` if in scope.
- Consolidate the duplicate scrape path (`orchestrator.py` vs `tasks.py`).

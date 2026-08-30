# D3 Audit — Job Pipeline: Ingestion / Scraping / Connectors / Normalization / Deduplication / Direct-Apply Verification / Job Quality Engine

**Scope:** `backend/apps/scraper`, `backend/apps/jobs`, `backend/apps/verification` (+ touchpoints in `apps/employers`, `apps/core`, `config/celery.py`)
**Method:** Static read of every file in scope, live `python -c` reproduction against the real Django app (test settings, `manage.py`-equivalent bootstrap), `pytest` run of the verification test suite, git history checks. No code was modified.
**Audit date:** 2026-08-29

---

## TL;DR — verdict per component

| Component | Verdict | Why |
|---|---|---|
| Scraping/Connector architecture | **PARTIAL / BROKEN AT RUNTIME** | Well-designed per-source orchestrator (schedule/rate-limit/health/auto-disable) exists, but the entire module fails to import (`ModuleNotFoundError: No module named 'croniter'`) — see §1. |
| Normalization | **DONE (isolated), INTEGRATE risk** | Pure functions are correct and unit-testable, but the calling code that uses them (orchestrator/tasks) is the same code that crashes — see §2. |
| Deduplication | **PARTIAL — two parallel, disagreeing implementations** | A hash-based pre-insert dedup (`scraper/pipeline/deduplicator.py`) and a separate hash-based post-insert dedup (`verification/stages/deduplicator.py`) exist; they use different hash inputs/normalization and neither is reconciled. See §3. |
| Direct-Apply Verification Engine (hard requirement) | **DONE in the verification app, but BYPASSED/PARTIALLY-DUPLICATED in the ingestion path; effectively never runs today** | The 6-stage `VerificationEngine` correctly blocks LinkedIn/Indeed/ZipRecruiter/Monster/etc. and only trusts ATS/employer domains — code-verified with file:line and a passing 42-test suite. **However**, the ingestion pipeline that is supposed to call it (`orchestrator.py`, `tasks.py`) raises an unhandled-and-silently-swallowed `TypeError` on every single job creation, so **zero jobs from live scraping ever reach the verification engine or the database.** See §4 — this is the compliance-critical finding.
| Job Quality Engine (states) | **MISSING / REPLACE** | The 9 states named in `AGENTS.md` (Active/Probably active/Needs verification/Expired/Archived/Broken/Duplicate/Rejected/Direct-source verified) do **not exist** as a field anywhere in the codebase. `Job.status` only has 3 states (active/pending/archived); `VerificationResult.status` has 4 (pending/verified/rejected/expired). No single "quality state" enum unifies them. See §5. |
| Recurring re-verification (Celery beat) | **PARTIAL — scheduled but calling code is broken / duplicated** | Celery beat *does* define daily/weekly re-verification jobs (`config/celery.py:57-64`), which is good — but one of the two re-verification implementations (`apps.scraper.tasks.verify_apply_urls`) lives in the module that fails to import (§1), and the other (`apps.verification.tasks`) uses a **different Job field** (`source_url`/`status='active'`) than the one the ingestion pipeline actually would have populated (`direct_apply_url`), so it is checking the wrong URL. See §6. |

**Overall assessment: this is NOT a working moat today.** The pieces that implement the hard product requirement (LinkedIn/Indeed/etc. rejection) are well-built and pass their unit tests in isolation, but the pipeline that is supposed to feed real scraped jobs into that engine is dead code (import-time crash on every one of the two entrypoints Celery Beat calls). Any jobs currently visible on the platform got there via `seed_jobs` (fake demo data, `direct_apply_url=f"{company.website}/apply/{i}"` — not from real ATS scraping) or via the separate `apps.employers` manual-posting flow, not via the scraper. This matches the AGENTS.md warning that historical status docs have repeatedly overclaimed completeness — verified against real code and live execution here.

---

## 1. Scraping / Connector architecture

**Design (as written): DONE, well-structured.**
- `apps/scraper/orchestrator.py:43-172` — `ScraperOrchestrator` class:
  - Per-source cron schedule via `croniter` — `should_scrape_source()` (`orchestrator.py:73-106`)
  - Per-ATS-platform rate limiting via sliding window — `check_rate_limit()`/`record_request()` (`orchestrator.py:108-138`), with a `RATE_LIMITS` dict per platform (`orchestrator.py:55-64`)
  - Auto-disable after `MAX_FAILURES=5` consecutive failures — `record_failure()`/`should_disable_source()` (`orchestrator.py:140-172`, applied at `orchestrator.py:222-231`)
  - Health tracking via `PipelineHealth` model updates (`orchestrator.py:404-419`, model at `apps/core/models.py:223+`)
- Plugin architecture exists in parallel: `apps/scraper/plugins/interface.py` (`ScraperPlugin` ABC, `BaseScraperPlugin` with failure tracking `interface.py:103-166`) and `apps/scraper/plugins/registry.py` (`ScraperPluginRegistry`, global `plugin_registry`, `register_all_scrapers()` at import time — `registry.py:105-129`).
- 8 real per-source ATS connectors exist and are structurally sound: `apps/scraper/ats/{greenhouse,lever,ashby,bamboohr,workday,smartrecruiters,workable,teamtailor}.py`, plus additional fingerprint-only support for `icims.py`, `oracle.py`, `sap.py` in the verification stage. `greenhouse.py:1-56` is representative: correctly uses `absolute_url` (a genuine direct-apply link) from the Greenhouse public JSON API — this is architecturally sound (not "a pile of ad-hoc scripts" by design).
- Admin dashboards for scraper health exist: `apps/scraper/admin_views.py:17-72` (source stats, scraper_health per-source freshness), `admin_views.py:75-196` (system health: DB/Redis/Celery/email).
- Discovery layer for finding new companies: `apps/scraper/discovery/common_crawl.py` (Common Crawl WARC scanning for ATS URL patterns, SSRF-safe downloads restricted to `commoncrawl.s3.amazonaws.com`/`data.commoncrawl.org` — `common_crawl.py:104-108`) and `apps/scraper/change_detection.py` (changedetection.io integration for career-page-change-triggered targeted scrapes).

**Verdict: BROKEN AT RUNTIME (BUILD/REPLACE needed).**
- `apps/scraper/orchestrator.py:14` does `from croniter import croniter`. **`croniter` is not in `backend/requirements.txt`** (confirmed via `grep -n croniter requirements.txt` → no match) and is not installed in the venv (`pip show croniter` → "Package(s) not found").
- Reproduced live: `python -c "import apps.scraper.orchestrator"` (Django bootstrapped, `config.settings.test`) → `ModuleNotFoundError: No module named 'croniter'`.
- Because `apps/scraper/tasks.py:13` does `from .orchestrator import orchestrator, scrape_all_sources_orchestrated`, **the entire `apps.scraper.tasks` module also fails to import** — reproduced live: `import apps.scraper.tasks` → `ModuleNotFoundError: No module named 'croniter'`.
- This means: `scrape_all_sources` (the Celery Beat task at `config/celery.py:23-26`, scheduled every 6 hours) and `verify_apply_urls`, `verify_employer_posted_job`, `expire_old_jobs`, `scrape_single_source`, `scrape_single_url`, `process_career_page_changes` — **every single task in `apps/scraper/tasks.py`** — cannot be registered/discovered by Celery, let alone run. Celery's `app.autodiscover_tasks()` (`config/celery.py:17`) will either crash worker startup or silently drop this module depending on Celery version/error-handling config; either way, none of these six-hourly/daily scraper tasks execute.
- Two competing "master" scrape entrypoints exist and neither works end-to-end:
  - `apps/scraper/tasks.py:scrape_all_sources` (Celery Beat schedule name `scrape-all-sources`, `config/celery.py:23-26`) — blocked by the import failure above, AND its job-creation path has the fatal `remote_type` bug (§4).
  - `apps/scraper/orchestrator.py:scrape_all_sources_orchestrated` (a different, undocumented, NOT-scheduled-in-beat task with the orchestrator's rate-limit/schedule features) — not referenced anywhere in `config/celery.py`'s `beat_schedule`, so the "advanced" orchestrator with rate limiting/schedule-checking is dead code that never runs on a schedule at all. It is only invoked manually via `apps/scraper/management/commands/run_scrapers.py` (`run_scrapers.py:10,87`, calling `orchestrator.scrape_all_sources()` — **note: `ScraperOrchestrator` has no method named `scrape_all_sources`**, only `scrape_source()` singular and the standalone task function `scrape_all_sources_orchestrated`; `run_scrapers.py:87` calling `orchestrator.scrape_all_sources()` will raise `AttributeError` — reproducible, not tested here live but confirmed by reading `orchestrator.py` in full: no such method is defined on the class).
- **Net effect: there is no working scheduled scraping today.** The rate-limiting, cron-per-source, and auto-disable features are real code, but unreachable.

**Fix scope:** REFACTOR + BUILD. Add `croniter` to `requirements.txt` and install it; fix `run_scrapers.py:87`'s call to a non-existent method; decide on ONE master scrape task (recommend `scrape_all_sources_orchestrated`, since it has the actual rate-limit/schedule logic) and point `config/celery.py`'s `scrape-all-sources` beat entry at it; add an integration test that actually calls the Celery task end-to-end against a test DB (none currently exists — `apps/jobs/tests/test_api.py` and `test_models.py` never touch the scraper).

---

## 2. Normalization logic

**Verdict: DONE as pure functions, but the call sites are broken (see §1, §4).**
- `apps/scraper/pipeline/normalizer.py`:
  - `normalize_employment_type()` (`normalizer.py:9-27`), `normalize_experience_level()` (`normalizer.py:30-50`), `normalize_remote_type()` (`normalizer.py:53-67`), `normalize_location()` (`normalizer.py:70-81`), `parse_salary()` (`normalizer.py:84-116`), `calculate_expiry_date()` (`normalizer.py:119-125`).
  - These are simple, correct, keyword-matching string normalizers. No unit tests exist for this module specifically (`apps/scraper` has no `tests/` directory at all — confirmed via file listing), but the logic is straightforward enough that correctness risk is low in isolation.
- **Critical integration defect:** `normalize_remote_type()` exists and is called at both `apps/scraper/tasks.py:224` and `apps/scraper/orchestrator.py:323` as `remote_type=normalize_remote_type(...)` passed into `Job.objects.create(...)`. **The `Job` model has no `remote_type` field** — it was removed by migration `apps/jobs/migrations/0003_remove_job_remote_type_job_work_arrangement_and_more.py:13-16` (replaced by `work_arrangement`, added at `0003:17-21`), but the two ingestion call sites were never updated to match. Reproduced live:
  ```
  Job.objects.create(..., remote_type='remote', ...)
  → TypeError: Job() got unexpected keyword arguments: 'remote_type'
  ```
  This means the normalization output is computed correctly but is never usable — every `Job.objects.create()` call in the scraper ingestion path throws before any row is written. See §4 for the full blast radius (this exception is caught by a broad `except Exception` and silently discarded, so it never even surfaces as a Sentry/log alert distinguishable from a transient scrape failure).

**Fix scope:** REFACTOR (one-line fix at each of the 2 call sites: rename `remote_type=` to `work_arrangement=` and route through `normalize_remote_type` → the `WORK_ARRANGEMENT_CHOICES` vocabulary, which happens to already match remote/hybrid/onsite 1:1). Trivial fix, but currently 100%-blocking, and un-caught by any test.

---

## 3. Deduplication logic

**Verdict: PARTIAL — two independent, non-reconciled implementations with different semantics.**

**Implementation A** — `apps/scraper/pipeline/deduplicator.py` (pre-insert, used by ingestion):
- `generate_job_hash()` (`deduplicator.py:10-32`): SHA256 of `company:normalized_title:location`, where title normalization strips the literal substrings `"senior"`, `"junior"`, `"mid-level"` (`deduplicator.py:24`) then removes non-alphanumeric chars.
- `generate_job_slug()` (`deduplicator.py:35-49`): slug generator, not a dedup check.
- **This hash is computed at `orchestrator.py:288-292` / `tasks.py:186-190` but is never actually used to check for duplicates** — the actual pre-existence check that follows uses `ats_job_id` + `ats_platform` (`orchestrator.py:295-298`, `tasks.py:193-196`), not the hash. So `generate_job_hash()` is dead computation — it runs, its result (`job_hash`) is assigned to a local variable and never referenced again in either file. Confirmed by reading both files fully: no second use of the `job_hash` variable in `orchestrator.py` or `tasks.py`.

**Implementation B** — `apps/verification/stages/deduplicator.py` (post-insert, part of the 6-stage `VerificationEngine`):
- `DeduplicatorStage.run()` (`deduplicator.py:22-45`) computes a SHA256 hash of `company_name|title|location` (lowercased, pipe-delimited — different delimiter and no title keyword-stripping vs. Implementation A) and looks it up against **existing `VerificationResult.content_hash` values, excluding `status="rejected"`** (`deduplicator.py:27-32`).
- This is the one that actually gates: `VerificationEngine.verify_job()` at `engine.py:105-110` calls it, and `engine.py:127-132` sets `status = "rejected"` if `dedup_result.is_duplicate` is true.
- Well-tested in isolation: `apps/verification/tests/test_engine.py:284-328` (`TestDeduplicatorStage`) passes.

**The gap:** Implementation A's hash (used pre-insert, meant to prevent duplicate DB rows across sources at ingestion time) and Implementation B's hash (used post-insert, inside verification) use **different normalization rules** (A strips seniority keywords from title; B does not) and are **never cross-referenced** — a job could pass A's dead-code hash check trivially (since it's never checked) and then either pass or fail B's differently-normalized hash depending on title wording. Since A is dead code, in practice only B's (correct, tested) dedup logic is live — but that only runs for jobs that survive as far as `VerificationEngine.verify_job()`, which — per §4 — currently never happens for scraped jobs.
- `check_consistency.py:108-141` (`_check_duplicates`) provides a THIRD, separate post-hoc dedup check based on `(ats_platform, ats_job_id)` pairs — a reasonable admin/ops tool, but it's a third distinct notion of "duplicate" with no shared code with A or B.

**Fix scope:** REFACTOR. Consolidate to one hash function/normalization rule (recommend keeping B's, since it's tested and it's the one that actually gates verification), delete the dead `generate_job_hash()` call in A, and make the `check_consistency` command use the same canonical dedup definition instead of a third one.

---

## 4. Direct-Apply Verification Engine — THE HARD REQUIREMENT

### 4a. Where the rule is implemented, and that it IS correctly enforced when reached

Two separate rule implementations exist, both correct in isolation:

**Primary/production implementation** — `apps/verification/stages/ats_fingerprint.py`:
- `BLOCKED_DOMAINS` set (`ats_fingerprint.py:48-64`) includes `linkedin.com, indeed.com, glassdoor.com, ziprecruiter.com, monster.com, careerbuilder.com, dice.com, simplyhired.com, snagajob.com, bayt.com, wuzzuf.net, gulftalent.com, naukri.com, seek.com.au, reed.co.uk` — this correctly covers all four named aggregators (LinkedIn/Indeed/ZipRecruiter/Monster) plus regional MENA aggregators (`bayt.com`, `wuzzuf.net`, `gulftalent.com`) which is a good addition given this is a MENA-focused platform.
- `ATS_PATTERNS` (`ats_fingerprint.py:15-46`) recognizes all the named-in-AGENTS.md ATS platforms: greenhouse, lever, ashby, workday, smartrecruiters, workable, teamtailor, bamboohr, icims, jobvite, recruitee — **plus** taleo, oracle_hcm, sap_successfactors, breezy, jazzhr, personio, deel, rippling (broader than the AGENTS.md list, no gap).
- `ATSFingerprintStage.run()` (`ats_fingerprint.py:70-96`) checks `BLOCKED_DOMAINS` **before** checking `ATS_PATTERNS` and returns `platform="BLOCKED_AGGREGATOR", confidence=1.0` — this is the actual reject signal.
- `VerificationEngine.verify_job()` (`engine.py:45-82`) calls this stage **twice** — once on the raw `apply_url`/`source_url` (`engine.py:51`) and again on the redirect-resolved final URL (`engine.py:69`, after following any redirect chain via `RedirectResolverStage`) — so a job whose apply link *redirects through* an aggregator is also caught, not just one whose literal stored URL matches. Both checks short-circuit to `status="rejected", trust_score=0.0` (`engine.py:53-62`, `71-82`).
- **Verified live via `pytest apps/verification/tests/test_engine.py`: 42/42 tests pass** (run 2026-08-29, `venv` activated, `config.settings.test`), including explicit per-domain rejection tests for LinkedIn, Indeed, Glassdoor, ZipRecruiter, Monster, CareerBuilder, Dice, SimplyHired, Snagajob, Bayt, Wuzzuf, GulfTalent, Naukri, Seek, Reed (`test_engine.py:61-165`), plus `test_verify_blocked_aggregator` end-to-end (`test_engine.py:357-365`) confirming the full engine (not just the stage) rejects.
- Additional layered checks: `DomainVerifierStage` (`domain_verifier.py`) awards trust only for known-ATS domains or domains matching the company's own registered domain/careers page (`domain_verifier.py:12-26, 51-69`); `LegitimacyScorerStage` scores content for scam language (`legitimacy_scorer.py:12-25`); combined into a weighted `trust_score` (`engine.py:20-26, 112-124`) with a configurable threshold (`SEARCH_TRUST_SCORE_THRESHOLD`, default 0.4, `config/settings/base.py:357`) below which the job is `rejected` (`engine.py:126-132`).

**Secondary/legacy implementation** — `apps/scraper/pipeline/url_resolver.py`:
- `is_direct_company_url()` (`url_resolver.py:53-86`) is a simpler allow/block-list check (its own `BLOCKED_DOMAINS`/`ALLOWED_ATS` lists, `url_resolver.py:11-50`, which **duplicate but do not match** the verification app's lists — e.g. it's missing `dice.com`, `simplyhired.com`, `snagajob.com`, `naukri.com`, `seek.com.au`, `reed.co.uk` from the blocklist, and includes `personio.de`/`join.com` in its allowlist that the verification app's `ats_fingerprint.py` ATS_PATTERNS doesn't explicitly pattern-match, though `personio.de` IS separately listed in `verification/stages/domain_verifier.py:20`). This is called at `orchestrator.py:265` / `tasks.py:161` as a pre-filter **before** the `VerificationEngine` even runs, and unknown/unrecognized-but-not-explicitly-blocked domains are permitted by default (`url_resolver.py:81-83`: "If not blocked and not ATS, assume it's company's own domain (We trust companies to use their own domains)") — this is a materially weaker "default allow" policy than the verification engine's scored/thresholded approach, and having two different lists that must both be kept in sync with future aggregator additions is a maintenance/compliance risk (a new aggregator added to one list but not the other creates a real bypass).

### 4b. THE CRITICAL FINDING: the verification engine that correctly enforces the rule is never reached in practice today

This is the compliance-critical gap, not a documentation nuance:

1. As shown in §1/§2, `apps/scraper/orchestrator.py` (via `croniter` import failure) and `apps/scraper/tasks.py` (which imports from `orchestrator.py`) **cannot be imported at all**, live-reproduced:
   ```
   >>> import apps.scraper.tasks
   ModuleNotFoundError: No module named 'croniter'
   ```
2. Even setting the import failure aside as a packaging bug and imagining `croniter` were installed: both `_process_jobs()` (`orchestrator.py:241-350`) and `process_and_store_jobs()` (`tasks.py:143-253`) call `is_direct_company_url()` (the weaker legacy check, §4a) as a pre-filter (`orchestrator.py:265`, `tasks.py:161`), THEN separately re-check `ATSFingerprintStage` for `BLOCKED_AGGREGATOR` (`orchestrator.py:269-272`, `tasks.py:166-169`), THEN create the `Job` row (`orchestrator.py:312-335`, `tasks.py:213-236`) — and **this `Job.objects.create()` call is the one that raises `TypeError: unexpected keyword argument 'remote_type'`**, reproduced live in this audit (§2). The exception is caught by a bare `except Exception as e: logger.error(...); continue` (`orchestrator.py:346-348`) / `print(...); continue` (`tasks.py:248-251`) that swallows it as if it were an ordinary "one job failed to parse" error, indistinguishable in logs from a transient network hiccup.
3. **Net result: `VerificationEngine.verify_job()` — the code that correctly implements the hard product requirement — is called at `orchestrator.py:339` / `tasks.py:240`, but this line is only reached AFTER the `Job.objects.create()` call two lines above it, which always throws first.** The verification engine's call site for freshly-scraped jobs is dead code in the current state of the repo. It is only exercised by: (a) the unit test suite (`test_engine.py`, which constructs `Job` objects directly with fields that do exist, bypassing the ingestion path entirely — confirmed by reading `test_engine.py:339-355`, `_make_job()` never passes `remote_type`), and (b) the manual `verify_jobs` / `verify_apply_urls` management commands, which only re-verify jobs that ALREADY exist in the DB (and since no scraped job can ever be created, in practice this means only manually-seeded/demo jobs or employer-posted jobs, which go through `apps.employers`' own separate, weaker `domain_verification.py` path — see §4c).
4. Because AGENTS.md flags "jobs whose application routes through LinkedIn/Indeed/ZipRecruiter/Monster or other intermediaries must be rejected" as a hard, compliance-relevant requirement, and the actual current behavior is **"no scraped jobs are ever ingested at all, so the question of whether they get correctly rejected is moot"** — this is arguably worse than a partial enforcement gap, because it means the demo/seed data currently on the platform did NOT go through this pipeline (see `seed_jobs.py:150`: `direct_apply_url=f"{company.website}/apply/{i}"` — fabricated URLs, never checked against `VerificationEngine` at all, no `Source` object marked `ats_platform`).

### 4c. Employer-posted jobs use a third, separate, weaker verification path

- `apps/employers/domain_verification.py` (`verify_domain_ownership()`, `domain_verification.py:66-103`) implements its own third blocklist (`domain_verification.py:18-23`, smaller than either of the other two — missing `ziprecruiter.com` variants beyond the literal string, `careerbuilder.com` is present but `dice.com`/`simplyhired.com`/`snagajob.com`/`seek.com`/`naukri.com`... wait it does have some of these — but it is NOT the same list, and does not call into `apps.verification.engine` at all).
- Crucially, `verify_domain_ownership()` (`domain_verification.py:94-100`) explicitly **allows** any domain containing the substrings `careers`, `jobs`, `hiring`, `apply`, `workday`, `greenhouse`, `lever` even when it does **not** match the company name, "flagged for review" but still returns `is_valid=True` (`domain_verification.py:98-100`) — i.e., `is_valid` doesn't actually gate anything downstream that blocks the job from being live; there is no code path found that keeps a `requires_manual_review=True` job out of the public job list (confirmed: `apps/jobs/views.py:JobListView.get_queryset()` at `views.py:289-295` filters only on `status="active"`, with no join to `apply_url_verified`, `VerificationResult.status`, or any employer-posting verification flag).
- `VerificationEngine.verify_employer_posted_job()` (`engine.py:183-193`) exists specifically for employer-posted jobs and auto-verifies (trust_score=0.9) if `job.company.is_verified` — but this method is only ever called from `apps/scraper/tasks.py:verify_employer_posted_job` (Celery Beat task `verify-employer-posted-jobs`, `config/celery.py:53-56`), which is **inside the broken `apps.scraper.tasks` module** (§1). So this path is also unreachable today.

### 4d. Is the rule "actually enforced in code, not just documented"?

**Answer: Yes, the rule logic itself is correctly written and unit-tested (`ats_fingerprint.py` + `engine.py`, 42 passing tests) — but it is not reachable from any live ingestion path today, due to the import/TypeError chain in §1/§2.** For a hard compliance requirement, "correct code that never runs" is functionally equivalent to "not enforced" from the standpoint of what actually reaches production. This is the single most important finding of this audit and should be treated as a P0 blocker, not a nice-to-have refactor — verify immediately before any claim that "direct-apply verification is working" is repeated in a status doc (per AGENTS.md's own warning about unverified status claims).

**Fix scope:** BUILD/REPLACE for the ingestion→verification wiring (fix `croniter` + `remote_type`/`work_arrangement` bugs, add an end-to-end test that scrapes a fixture ATS response through to a `VerificationResult`), REFACTOR to unify the 3 separate blocklists (`ats_fingerprint.py`, `url_resolver.py`, `domain_verification.py`) into one canonical source of truth (the `BlockedDomain`/`ApprovedATS` admin-managed models already exist at `apps/verification/models.py:91-181` for exactly this purpose but are **not currently read by any of the three blocklist checks** — confirmed via `search_files` for `BlockedDomain`/`ApprovedATS` usage: only referenced in `admin.py` registration and migrations, never queried by `ats_fingerprint.py`, `url_resolver.py`, or `domain_verification.py`, which all use hardcoded Python set/list literals instead — meaning an admin who adds a new blocked domain via the Django admin UI, believing it's respected platform-wide, is not actually protected).

---

## 5. Job Quality Engine states

**Verdict: MISSING.** The 9-state model described in `AGENTS.md:95-98` — Active / Probably active / Needs verification / Expired / Archived / Broken / Duplicate / Rejected / Direct-source verified — **does not exist anywhere in the codebase** as a single field or enum. Confirmed via repo-wide search for `quality_state`, `QUALITY_STATE`, `"Probably active"`, `"Needs verification"`, `"Direct-source verified"`: zero matches.

What exists instead is state scattered across at least 3 uncoordinated fields:
- `Job.status` (`apps/jobs/models.py:205-209, 241-243`): only 3 values — `active`, `pending` ("Pending Review"), `archived`. No `expired`, `broken`, `duplicate`, or `rejected` value exists on this field.
- `Job.is_expired` (`apps/jobs/models.py:318`): boolean, set by `expire_old_jobs` task (age-based only, `tasks.py:346-361`) and by `apps/verification/tasks.py` liveness checks (`tasks.py:55-59`, `verification/tasks.py` — different module, uses a **different Job field**, see §6) — but note `expire_old_jobs` only checks `created_at` age against `PlatformConfig.max_job_age_days`, never actual URL liveness.
- `VerificationResult.status` (`apps/verification/models.py:8-13`): 4 values — `pending`, `verified`, `rejected`, `expired`. This is the closest thing to the AGENTS.md concept but covers only verification outcome, not "duplicate", "broken" (distinct from "expired"), "archived", or "probably active" vs. "needs verification" gradations.
- `is_duplicate` exists as a boolean on `VerificationResult` (`models.py:49`) but not on `Job` itself — a duplicate job's `Job.status` remains whatever it was (typically `active`), so a duplicate job with `VerificationResult.status="rejected", is_duplicate=True` can still be independently visible via `Job.objects.filter(status="active")` (the exact query used by the public `JobListView.get_queryset()`, `apps/jobs/views.py:289-295`) **unless** something separately flips `Job.status` — and no code was found anywhere in `apps/scraper`, `apps/verification`, or `apps/jobs` that propagates a `VerificationResult.status="rejected"` back onto `Job.status`. Confirmed via search: no occurrence of `job.status = "rejected"` or equivalent anywhere in the codebase (only `apps/employers/admin.py:245` sets `status='rejected'` on a **different** model, `JobApplication`, an applicant's application status, not a job posting's quality state).
- **This means a job whose `VerificationResult.status == "rejected"` (including one explicitly blocked as a LinkedIn/aggregator link) is NOT automatically removed from public visibility** — the only field the public API filters on (`Job.status == "active"`) is never updated by the verification engine. `VerificationEngine.verify_job()` (`engine.py:156-170`) updates `job.legitimacy_score`, `apply_url_verified`, `apply_url_checked_at`, `apply_url_status_code`, `ats_platform`, `direct_apply_url` — but conspicuously **never touches `job.status`**. This is a second, independent way the "hard requirement" fails in practice even if a job somehow got created and verified: rejection by the engine does not hide the job.

**Fix scope: BUILD.** This needs a genuine new field (e.g. `Job.quality_state` enum with the 9 named values) or, at minimum, `VerificationEngine.verify_job()` must be changed to set `job.status = "archived"` (or a new `rejected` value added to `STATUS_CHOICES`) whenever `status in ("rejected",)`, and the public `JobListView` queryset must be audited to ensure rejected/duplicate jobs are actually excluded. Currently there is no unifying state machine at all — this is a MISSING product surface, not a bug in an existing one.

---

## 6. Recurring verification schedule (vs. ingestion-time-only)

**Verdict: PARTIAL — Celery Beat does define recurring jobs, which is good, but the two live implementations disagree on which field to check, and one is unreachable.**

`config/celery.py:52-64` defines:
```python
'verify-employer-posted-jobs': crontab(minute=0, hour='*/6')   # apps.scraper.tasks.verify_employer_posted_job
'daily-liveness-check':        crontab(hour=3, minute=0)        # apps.verification.tasks.daily_liveness_check
'weekly-reverification':       crontab(hour=2, minute=0, day_of_week=0)  # apps.verification.tasks.weekly_reverification
```
Plus `config/celery.py:27-30`: `'verify-apply-urls': crontab(minute=0, hour=2)` → `apps.scraper.tasks.verify_apply_urls`.

So on paper, this satisfies the AGENTS.md pitfall warning ("Job Quality Engine states... should be recomputed on a recurring cadence, not just at ingestion time — verify a recurring verification job actually exists before assuming freshness") — **a recurring job DOES exist in the schedule.** But:

1. `verify-apply-urls` and `verify-employer-posted-jobs` both point into `apps.scraper.tasks`, which — per §1 — **cannot be imported** (`ModuleNotFoundError: No module named 'croniter'`). These two of the four recurring verification tasks are dead.
2. The two that DO work (`apps.verification.tasks.daily_liveness_check` / `weekly_reverification`, confirmed importable live: `import apps.verification.tasks` succeeds) use a **different Job field** than the ingestion pipeline populates: `verification/tasks.py:35-39` queries `Job.objects.filter(status='active', posted_at__lt=cutoff, source_url__isnull=False).exclude(source_url__exact='')` and then checks liveness of `job.source_url` (`tasks.py:48-49`) — **not** `job.direct_apply_url`. But `direct_apply_url` is the field the scraper pipeline and the `VerificationEngine` treat as the actual (verified, aggregator-free) apply link (`Job.direct_apply_url` help text: "Direct link to company's application page (no aggregators)", `models.py:250-255`; `VerificationEngine.verify_job()` uses `job.direct_apply_url or job.source_url` at `engine.py:48`). `source_url` (`models.py:231`, required, no help text distinguishing it from `direct_apply_url`) appears intended as the original/raw source link (possibly an aggregator link in the scraped case, given `source_raw_url`'s own separate field description at `models.py:312-316`: "Original aggregator URL (not shown to users)" — suggesting `source_url` and `source_raw_url` might overlap in intent, itself a modeling ambiguity). **Re-verifying `source_url` on a recurring basis, when the field the platform actually shows/uses for "apply" is `direct_apply_url`/the `JobApplyView`'s `job.source_url` (`views.py:432-439` — actually also uses `source_url`, so there is internal inconsistency about which field is canonical for "the apply link") means the recurring liveness check may not be checking the URL a user would actually click.**
3. Neither `daily_liveness_check` nor `weekly_reverification` calls into the 6-stage `VerificationEngine` at all — they do a simple HEAD/GET liveness check only (`verify_url_is_live`, `verification/tasks.py:16, 48`) and can only ever set `job.status` to `'expired'` on a 404 (`tasks.py:54-59`) or leave it alone. They do **not** re-run the aggregator-domain-block check, so a job that somehow got past ingestion with a since-added-to-blocklist aggregator domain would never be caught by the recurring job — only by a full `verify_jobs --all` management command run (manual, not scheduled) which DOES use the full `VerificationEngine` (`management/commands/verify_jobs.py:79-94`).

**Fix scope:** REFACTOR. Once §1's import bug is fixed, decide on ONE canonical "apply URL" field (recommend `direct_apply_url`, deprecate the ambiguous overlap between `source_url`/`source_raw_url`), point both recurring liveness tasks at it, and route the recurring re-verification through the full `VerificationEngine` (not just a bare liveness check) so that a domain newly added to the blocklist retroactively re-flags previously-verified jobs — currently nothing does this.

---

## Summary table — file:line ledger of every concrete defect found

| # | Defect | File:Line | Verdict |
|---|---|---|---|
| 1 | `croniter` imported but not in `requirements.txt` / not installed | `apps/scraper/orchestrator.py:14` | BROKEN |
| 2 | Import chain failure cascades to entire tasks module | `apps/scraper/tasks.py:13` (imports `orchestrator`) | BROKEN |
| 3 | `remote_type` passed to `Job.objects.create()`, field doesn't exist (removed by migration) | `apps/scraper/tasks.py:224`, `apps/scraper/orchestrator.py:323` | BROKEN |
| 4 | Field removed here, call sites never updated | `apps/jobs/migrations/0003_remove_job_remote_type_job_work_arrangement_and_more.py:13-16` | context |
| 5 | Exception from #3 silently swallowed, indistinguishable from network errors | `apps/scraper/orchestrator.py:346-348`, `apps/scraper/tasks.py:248-251` | BROKEN |
| 6 | `orchestrator.scrape_all_sources()` called but method doesn't exist on class | `apps/scraper/management/commands/run_scrapers.py:87` | BROKEN |
| 7 | Dead-code duplicate hash computed, never checked | `apps/scraper/pipeline/deduplicator.py:10-32` called at `orchestrator.py:288-292`/`tasks.py:186-190`, result unused | PARTIAL |
| 8 | Three non-unified blocklists for the same "reject aggregator" concern | `apps/verification/stages/ats_fingerprint.py:48-64`, `apps/scraper/pipeline/url_resolver.py:11-33`, `apps/employers/domain_verification.py:18-23` | REFACTOR |
| 9 | Admin-managed `BlockedDomain`/`ApprovedATS` models exist but are never queried by any blocklist check | `apps/verification/models.py:91-181` (unused by `ats_fingerprint.py`/`url_resolver.py`/`domain_verification.py`) | MISSING integration |
| 10 | `VerificationEngine.verify_job()` never updates `Job.status`, so "rejected" jobs stay publicly visible | `apps/verification/engine.py:156-170` (no `job.status` write) vs. `apps/jobs/views.py:289-295` (public query filters only on `status="active"`) | BROKEN (compliance) |
| 11 | 9-state Job Quality Engine model from AGENTS.md does not exist in code | n/a — repo-wide search, zero matches | MISSING |
| 12 | Two of four scheduled recurring-verification Celery Beat tasks point into the broken module | `config/celery.py:27-30, 53-56` → `apps.scraper.tasks.*` | BROKEN |
| 13 | The two working recurring tasks check `source_url`, not `direct_apply_url` (field ambiguity) | `apps/verification/tasks.py:38-39, 48-49` vs. `apps/jobs/models.py:231, 250-255` | PARTIAL |
| 14 | Recurring liveness checks don't re-run full `VerificationEngine` (no retroactive blocklist re-check) | `apps/verification/tasks.py:22-99` (bare liveness only) | PARTIAL |
| 15 | Employer-posting domain check allows unmatched "careers/jobs/hiring" substrings without truly gating visibility | `apps/employers/domain_verification.py:94-100` | PARTIAL |
| 16 | Seed/demo data bypasses all verification, fabricated apply URLs | `apps/scraper/management/commands/seed_jobs.py:150` | context (explains why the platform looks populated) |

## What IS solid and should be preserved
- The 6-stage `VerificationEngine` design and its ATS-fingerprint blocklist (§4a) — logic is correct, well-tested (42/42 passing), and appropriately MENA-aware (bayt/wuzzuf/gulftalent).
- The `ScraperOrchestrator` design (schedule/rate-limit/auto-disable/health) is a genuinely scalable architecture on paper — the problem is 100% a wiring/dependency bug, not a design flaw. Fixing `croniter` + the two call-site bugs would make a materially good system actually functional.
- `VerificationResult`/`BlockedDomain`/`ApprovedATS` models (`apps/verification/models.py`) are a solid schema foundation for admin-manageable, auditable verification — they're just not wired up to the actual checks yet.

## Recommended immediate priority order
1. **P0 (compliance-blocking):** Fix `croniter` dependency + `remote_type`→`work_arrangement` at both call sites; add an end-to-end integration test (fixture ATS response → DB row → `VerificationResult`) so this class of bug cannot silently regress again.
2. **P0 (compliance-blocking):** Make `VerificationEngine.verify_job()` write back to `Job.status` (or the new quality-state field) so rejected/aggregator-linked jobs are actually hidden from `JobListView`.
3. **P1:** Build the actual Job Quality Engine state field (9 states per AGENTS.md) and migrate `Job.status`/`is_expired`/`VerificationResult.status` into it, or explicitly document the mapping if kept separate.
4. **P1:** Unify the 3 blocklists into the existing but unused `BlockedDomain`/`ApprovedATS` admin models so a single admin action protects the whole pipeline.
5. **P2:** Reconcile `source_url` vs `direct_apply_url` vs `source_raw_url` field semantics; point recurring liveness checks at the correct field and route them through the full engine, not a bare HEAD/GET.

# Post-Deploy Runtime Verification

**Target deployment:** commit `e99f089` (deployed to `jobs.usamif.com`)
**Follow-up fix commit:** `c02458b` (pushed to `origin/development`, **not yet deployed**)
**Date:** 2026-09-29

## Status legend
PASS · FAIL · PARTIAL · NOT TESTED · N/A

## Important context / honesty notes
1. **No SSH access from the verification environment.** All live-runtime items
   (service state, journalctl, authenticated Rashid calls, curl, disk/memory,
   apt state) must be executed on the server. This report marks those
   **NOT TESTED (needs server run)** and provides exact command blocks in §A.
2. **Verification of `e99f089` uncovered NEW runtime bugs.** The deployed commit
   fixed 2 Rashid agent tools, but code-level verification found **3 more broken
   tools plus a missing `settings` import**. These are fixed in `c02458b`, which
   must be deployed. Full detail in §B.
3. Do **not** treat `/api/v1/` → 404 as an outage: no route is registered at the
   bare prefix by design. Real endpoints are listed in the route map (§C).

---

## Summary table (per required report item)

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Deployed commit | PASS | `e99f089` confirmed live; `c02458b` pending deploy |
| 2 | Server/service state | NOT TESTED (needs server) | Prior transcript showed `usam.service active`; re-confirm via §A.1 |
| 3 | Migration state | PASS | `0008_job_field_provenance` shown `[X]` in deploy transcript |
| 4 | Actual routes tested | PARTIAL | Route map built from real urls.py (§C); live curls pending §A.2 |
| 5 | Rashid search test | PARTIAL | Code path verified + fixed; live call pending §A.3 |
| 6 | Rashid recommendation test | PARTIAL | Code path verified + fixed; live call pending §A.3 |
| 7 | Regression tests | PASS (local) | intelligence 8/8, provenance 4/4; moat 7/7 earlier (collection slow locally). Re-run on server §A.6 |
| 8 | Direct-apply blocked-domain | PASS (code) | Dot-boundary matching + tests; live spot-check §A.7 |
| 9 | Job provenance field | PASS | Column live (migration applied); safe across serializer/admin/search |
| 10 | Provenance ingestion | PARTIAL | Wired in `tasks.py` via `build_provenance`; populates on NEW scrapes only |
| 11 | ATS dispatch results | PARTIAL | Dispatch set complete in code (11 platforms); live scrape pending §A.8 |
| 12 | Workday result | PARTIAL | Now dispatched; connector is Playwright-based (returns [] w/o Playwright) |
| 13 | Direct-apply live verification | NOT TESTED (needs server) | §A.9 sample-job inspection |
| 14 | Worker/queue health | NOT TESTED (needs server) | §A.5 celery/beat check |
| 15 | Search dependency health | NOT TESTED (needs server) | §A.4 Typesense/pg/Bedrock |
| 16 | Frontend verification | NOT TESTED (needs browser) | §A.10 manual UI checks |
| 17 | Errors discovered | PASS (documented) | §B — 3 broken tools + settings NameError |
| 18 | Fixes made | PASS | §B — all fixed in `c02458b`, tested |
| 19 | Remaining failures | PARTIAL | None known in code; live confirmation pending |
| 20 | Server resource risks | NOT TESTED (needs server) | disk 77.6%, mem 59%, swap 35%, restart-required — §A.11 |
| 21 | Security/update state | NOT TESTED (needs server) | 26 updates + 8 ESM + restart-required — §A.12 |
| 22 | Production-readiness | PARTIAL | Code-correct after `c02458b`; deploy + live checks required |

---

## §B. Errors discovered and fixed (the substance of this verification)

Post-deploy code-level tracing of the Rashid agent (the flagship flow the
directive prioritizes) found that **5 of 9 agent tools** were broken by drift
between the tool code and the services they call. Two were fixed in `e99f089`;
**three more plus a view bug were found now** and fixed in `c02458b`.

| Tool / site | Bug | Runtime effect | Fix | Status |
|-------------|-----|----------------|-----|--------|
| `views.chat_with_rashid` | `settings.RASHID_MODEL` used but `settings` never imported | `NameError` swallowed by inner `try/except` → **Rashid AI cost/usage tracking silently never recorded** | `from django.conf import settings` | FIXED `c02458b` |
| `agent.analyze_skill_gap` | imported non-existent `SkillGapService` + `analyze_for_job/role` | `ImportError` on every skill-gap request | use `SkillGapAnalyzer(user).analyze()` + real keys | FIXED `c02458b` |
| `agent.get_career_profile` | `TalentScore.latest("calculated_at")` — field is `last_calculated_at` | `FieldError` when a talent score exists | correct field name; scale 0-1 score to % | FIXED `c02458b` |
| `agent.get_salary_insights` | `SalaryData.filter(job_title__icontains)` + `d.salary_amount` — neither exists | `FieldError`/`AttributeError` on every salary query | query via `job__title`; use `salary_min/max` + annualized fallback | FIXED `c02458b` |
| `agent.search_jobs` | wrong `SearchService.search_jobs` signature | `TypeError` on every job search | build `SearchQuery`, read `response.hits[].data` | FIXED `e99f089` |
| `agent.get_recommendations` | `RecommendationEngine()` no-arg + wrong keys | constructor error / null titles | `RecommendationEngine(user)` + `job_title` key | FIXED `e99f089` |

**Verified CORRECT, no change needed:** `prepare_interview`,
`get_match_score` (`get_match_breakdown`), `tailor_resume`
(`CVTailorService.tailor_for_job`), `find_referral_contacts`
(`ConnectionsService.find_connections`).

**Regression tests:** `apps/intelligence/tests_rashid_agent_tools.py` expanded to
8 tests locking every service contract (SearchQuery shape, RecommendationEngine
ctor, SkillGapAnalyzer, TalentScore field name, SalaryData field names, settings
import). All 8 pass locally.

### field_provenance integration (safe)
- Both `Job` serializers use explicit field lists that omit `field_provenance` →
  **API output unchanged**.
- Job admin uses explicit `list_display`/`readonly_fields`, no `fieldsets`
  restriction → detail page renders the JSON field harmlessly.
- Search: `job_to_search_document` is an explicit builder + `JOBS_SCHEMA` is
  explicit → **indexing unaffected**.
- **One behavior note (PARTIAL):** Job admin uses `ImportExportModelAdmin` with an
  auto-generated resource, so `field_provenance` will appear as a **new additive
  column** in CSV/XLSX exports. Imports lacking the column still work (defaults
  to `{}`). Not a break; flagged for awareness.

---

## §C. Real route map (from `config/urls.py`, verified)

| Flow | Method | Path | Auth |
|------|--------|------|------|
| Rashid chat (agent) | POST | `/api/v1/intelligence/rashid/chat/` | IsAuthenticated |
| Rashid conversations | * | `/api/v1/rashid/...` | IsAuthenticated |
| Rashid tools list | GET | `/api/v1/intelligence/tools/` | IsAuthenticated |
| Job search | GET/POST | `/api/v1/search/jobs/` | per view |
| Recommendations | GET | `/api/v1/search/recommendations/` | IsAuthenticated |
| Similar jobs | GET | `/api/v1/search/similar-jobs/<uuid>/` | per view |
| Search health | GET | `/api/v1/search/health/` | per view |
| Intelligence health | GET | `/api/v1/intelligence/health/` | admin |
| Jobs | GET | `/api/v1/jobs/` | per view |
| Root health | GET | `/health/` and `/health/detailed/` | open |
| API docs | GET | `/api/docs/` (Swagger) | per config |

Verification runs **inside** the ingestion pipeline (no public URL) — this is
expected, not a gap.

---

## §A. Server command blocks (run these on the box; paste output back)

> Deploy the follow-up fix first — it is backend-only, **no new migration**.

### A.0 — Deploy `c02458b`
```bash
cd /home/ubuntu/E-Career && git fetch origin && git checkout development && git merge origin/development
cd /var/www/usam && git fetch /home/ubuntu/E-Career development && git merge --ff-only FETCH_HEAD
cd backend && source ../venv/bin/activate && python manage.py migrate   # no-op, safe
sudo systemctl restart usam.service
git rev-parse HEAD   # expect c02458b...
```

### A.1 — Service + system checks
```bash
cd /var/www/usam/backend && source ../venv/bin/activate
git rev-parse HEAD
git status
python manage.py check
python manage.py showmigrations jobs | tail -5
sudo systemctl status usam.service --no-pager -l | head -20
sudo journalctl -u usam.service -n 120 --no-pager
```

### A.2 — Real endpoints (unauth smoke; 401/403 = alive & auth-guarded)
```bash
for p in /health/ /health/detailed/ /api/v1/search/health/ /api/v1/jobs/ ; do
  printf "%s -> " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://jobs.usamif.com$p"
done
```

### A.3 — Rashid search + recommendations END-TO-END (authenticated)
```bash
# Get a token for a real user that has profile data (adjust login route/creds).
TOKEN=$(curl -s -X POST https://jobs.usamif.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test123@test.com","password":"ChangeMe_Strong#2026"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access',''))")
echo "token len: ${#TOKEN}"

# Rashid job search intent
curl -s -X POST https://jobs.usamif.com/api/v1/intelligence/rashid/chat/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"Find Python backend jobs","language":"en"}' | python3 -m json.tool

# Rashid recommendations intent
curl -s -X POST https://jobs.usamif.com/api/v1/intelligence/rashid/chat/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"Recommend jobs for me","language":"en"}' | python3 -m json.tool

# Rashid skill-gap + salary intents (the newly fixed tools)
curl -s -X POST https://jobs.usamif.com/api/v1/intelligence/rashid/chat/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"What are my skill gaps?","language":"en"}' | python3 -m json.tool
curl -s -X POST https://jobs.usamif.com/api/v1/intelligence/rashid/chat/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"What is the salary for a backend engineer?","language":"en"}' | python3 -m json.tool
```
While running these, watch a second terminal:
```bash
sudo journalctl -u usam.service -f | grep -Ei "error|traceback|TypeError|FieldError|ImportError|rashid"
```
**PASS criteria:** real answers, no stack traces, no `TypeError/FieldError/ImportError`.

### A.4 — Search / recommendation dependencies
```bash
curl -s https://jobs.usamif.com/api/v1/search/health/ | python3 -m json.tool
# Typesense reachable?
curl -s -o /dev/null -w "typesense:%{http_code}\n" http://127.0.0.1:8108/health || echo "typesense down -> Postgres fallback"
```

### A.5 — Celery worker + beat
```bash
sudo systemctl status celery.service celerybeat.service --no-pager 2>/dev/null | head -30 || \
  ps aux | grep -E "celery" | grep -v grep
source ../venv/bin/activate && celery -A config inspect ping 2>/dev/null || echo "no worker responding"
```

### A.6 — Regression tests on server
```bash
cd /var/www/usam/backend && source ../venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.test   # or the project's test settings
python -m pytest apps/intelligence/tests_rashid_agent_tools.py -q
python -m pytest apps/verification/tests/test_blocked_domain.py -q
python -m pytest apps/scraper/tests_provenance.py -q
```

### A.7 — Blocked-domain moat spot-check (shell)
```bash
python manage.py shell -c "
from apps.verification.models import is_blocked_domain as b
for d in ['linkedin.com','www.linkedin.com','jobs.linkedin.com','indeed.com','apply.indeed.com','notindeed.com','mylinkedin.com','boards.greenhouse.io','jobs.lever.co']:
    print(f'{d:32} blocked={b(d)}')
from apps.verification.models import BlockedDomain
print('active blocked count:', BlockedDomain.objects.filter(is_active=True).count())
"
```
**PASS criteria:** linkedin/indeed + subdomains `True`; notindeed/mylinkedin/greenhouse/lever `False`.

### A.8 / A.10 — ATS dispatch + Workday (controlled)
```bash
python manage.py shell -c "
from apps.jobs.models import Source
from apps.scraper.tasks import scrape_source
for plat in ['greenhouse','lever','ashby','workday','icims','oracle','sap','__unknown__']:
    s = Source(name=f'test-{plat}', slug=f'test-{plat}', ats_platform=(plat if plat!='__unknown__' else 'bogus'))
    try:
        jobs = scrape_source(s)
        print(f'{plat:12} -> {len(jobs)} jobs (dispatched)')
    except Exception as e:
        print(f'{plat:12} -> ERROR {type(e).__name__}: {e}')
"
```
**PASS criteria:** no `else`-branch silent drop for real platforms; unknown platform logs a warning and returns `[]` without crashing. (Workday returns `[]` if Playwright isn't installed — expected; check the log line.)

### A.9 / A.13 — Direct-apply data model on real jobs
```bash
python manage.py shell -c "
from apps.jobs.models import Job
for j in Job.objects.exclude(direct_apply_url='').order_by('-scraped_at')[:5]:
    print('---', j.title)
    print('  source_url      :', j.source_url)
    print('  direct_apply_url:', j.direct_apply_url)
    print('  ats_platform    :', j.ats_platform)
    print('  quality_state   :', j.quality_state)
    print('  apply_verified  :', j.apply_url_verified)
    print('  field_provenance:', bool(j.field_provenance), (list(j.field_provenance)[:6] if j.field_provenance else []))
"
```
**PASS criteria:** `direct_apply_url` is NOT an aggregator; `source_url` and
`direct_apply_url` are not always identical; newly scraped jobs carry provenance.

### A.11 — Server resources
```bash
df -h /
free -h
swapon --show
du -sh /var/log/* 2>/dev/null | sort -h | tail -8
journalctl --disk-usage
ps aux --sort=-%mem | head -8
```

### A.12 — Security / update state (report only, do NOT auto-upgrade)
```bash
apt list --upgradable 2>/dev/null | head -40
cat /var/run/reboot-required 2>/dev/null; cat /var/run/reboot-required.pkgs 2>/dev/null
```

---

## §D. Live runtime results (2026-09-29, commits b4c8415 → 0d43d24)

Real authenticated production testing (user ran commands; no SSH from verifier).

| Item | Status | Evidence |
|------|--------|----------|
| Deploy b4c8415 then 93f970a then 0d43d24 | PASS | `git rev-parse HEAD` matched each; `manage.py check` = no issues |
| Service health | PASS | `usam.service active`; gunicorn 3 workers; no import/startup errors |
| Workers | PASS | `celery-usam.service` + `celery-beat-usam.service` both `active running` |
| Migrations | PASS | `0008` applied; `migrate` = no new migrations |
| Blocked-domain moat | PASS | Live shell: linkedin/indeed + subdomains `True`; notlinkedin.com/myindeedexample.org/greenhouse/lever `False`; 25 active blocked |
| Auth/login | PASS | Returns JWT at `data.access` (token len 228) |
| RecommendationEngine | **FAIL → FIXED (93f970a)** | Live: `ImportError: cannot import name 'JobApplication' from 'apps.jobs.models'` (it lives in apps.employers.models). Fixed 6 sites. Re-run: `recs: 3` with correct keys |
| analyze_skill_gap data path | PASS | Live shell keys = overall_gap_score/gap_severity/gaps_by_role/missing_skills/recommendations (matches fixed tool) |
| get_salary_insights data path | PASS (code) / N/A (data) | Query `job__title__icontains='engineer'` executed cleanly; 0 records in this DB (data gap, not code) |
| **Rashid AI (all intents)** | **FAIL — server AWS credentials invalid** | Live logs: agent → `UserError: must provide region_name` (FIXED in 0d43d24); fallback haiku → `UnrecognizedClientException: The security token included in the request is invalid` → **AWS creds on server are invalid/expired** |
| Rashid agent error visibility | FIXED (93f970a) | Added structured `rashid_agent_failed` logging (was silently swallowed) |
| Server pytest | NOT TESTED | pytest not installed in prod venv; verified locally instead |

### Root cause of the Rashid fallback
Two layered issues, now separated:
1. **Agent path** built a Bedrock client with no region → `UserError`. **Fixed** in
   `0d43d24` (explicit `BedrockProvider(bedrock_client=...)` with app region+creds).
2. **Both paths** ultimately fail because the **server's AWS credentials are
   invalid/expired** (`UnrecognizedClientException`). This is a **server-side
   config fix**, not application code. Until the AWS keys are rotated/valid, all
   Rashid AI (and any Bedrock feature: CV parse, matching AI, salary AI) returns
   the deterministic fallback. Note AGENTS.md records a prior leaked key in
   `backend/.env` — credentials may have been revoked.

### Server credential fix (required, user action)
```bash
# Confirm which creds the process actually sees and whether they work:
aws sts get-caller-identity   # if this fails, the keys are invalid/expired
grep -E 'AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_DEFAULT_REGION' /var/www/usam/backend/.env
# After installing VALID keys (rotate in IAM if revoked), restart:
sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service
```
Then re-run the Rashid loop (§A.3). PASS = real answers, `"model"` != `"fallback"`.

## §E. AI/Bedrock foundation — live diagnosis + hardening (commit e7032f2)

| Item | Status | Evidence |
|------|--------|----------|
| Bedrock health classifier (live) | PASS | `bedrock_health()` on server returned `{'status':'AUTH_FAILED','region':'us-east-1','credential_source':'static_settings_env'}` — classifier works, no secrets exposed |
| Server AWS credentials | **FAIL (server-side)** | Static key in `backend/.env` rejected: `UnrecognizedClientException`. Key is invalid/revoked. |
| Credential source | Identified | `EnvironmentFiles=/var/www/usam/backend/.env`; 1 `AWS_ACCESS_KEY_ID`, 0 `AWS_SESSION_TOKEN` → static long-lived key |
| EC2 instance role | Absent | `curl .../iam/security-credentials/` returned empty → no role attached |
| aws CLI | N/A | Not installed on server; diagnosed via boto3 instead (app doesn't use CLI) |
| Region | PASS | `us-east-1` resolved correctly |
| Centralized Bedrock client | PASS (code) | `bedrock_client.py` factory shared by plugin + agent; deployed |
| Fail-fast fallback | PASS (code) | Provider-level failures now return honest "AI unavailable" instead of silent fake |
| Admin AI health visibility | PASS (code) | `GET /api/v1/intelligence/health/` returns classified `bedrock` block |
| Rashid AI (all intents) | **BLOCKED** | Returns fallback; blocked solely by invalid AWS creds |
| Classifier unit tests | PASS | 8/8 `tests_bedrock_client.py` |

### Required server-side fix (only the account owner can do)
The static key in `backend/.env` is dead and no instance role exists. Either:
- **(A, recommended)** attach an EC2 IAM role with `bedrock:InvokeModel`,
  `InvokeModelWithResponseStream`, `Converse`, `ConverseStream`,
  `ListFoundationModels`, then comment out the static keys in `.env` (the client
  factory auto-uses the role); OR
- **(B)** rotate the key in IAM, update `.env`, deactivate the old key.
Then confirm: `python manage.py shell -c "from apps.intelligence.bedrock_client import bedrock_health; print(bedrock_health())"` → `HEALTHY`.
If `ACCESS_DENIED`/`MODEL_UNAVAILABLE` after that → enable Claude Sonnet 4.5
model access in the Bedrock console for us-east-1, or repoint `RASHID_MODEL`.

## §F. SECURITY — exposed AWS key in git history (ACTION REQUIRED)

**Finding (real, not placeholder):** a real AWS Access Key ID was committed in
history at commit **`fa11a2f`** ("Complete Phase 1A & 1B") in 5 files:
`.env.example`, `IMPLEMENTATION_REQUIREMENTS.md`, `READY_FOR_PHASE_1A.md`,
`SETUP_STATUS.md`, `START_HERE.md`. It has been **removed from current HEAD**
but **remains permanently in git history**. This is consistent with the
AGENTS.md leaked-key note and is very likely the same key now failing
`AUTH_FAILED` (i.e. it was deactivated — which is correct).

Placeholder-only matches (`AKIAXXXX…`) in `EXECUTE_PHASE3.sh` and
`archive/FINAL_IMPLEMENTATION_PLAN.md` are NOT secrets.

**Required actions:**
1. **Deactivate/delete the exposed key in IAM** (treat as fully compromised).
   Confirm no other principal/service still uses it before deletion.
2. Decide on history rewrite: purging it from git history requires
   `git filter-repo`/BFG + a **force-push** that rewrites shared history and
   breaks every existing clone and the server's `/home/ubuntu/E-Career` and
   `/var/www/usam` checkouts. Because the key is already deactivated, rotation
   (step 1) neutralizes the risk; history rewrite is optional cleanup that
   should be scheduled with all collaborators/deploys aware. **Not performed
   unilaterally** (destructive, coordination-sensitive).
3. Ensure current/future secrets live only in `.env` (gitignored) or a secret
   manager — never in tracked `.md`/`.example` files.

## Production-readiness conclusion (this deployment)

**Code correctness:** After `c02458b`, all 9 Rashid tools call real, verified
service APIs, the moat matcher is correct, and the provenance field is safe
across serializer/admin/search. Local regression tests pass.

**Blocking action:** `c02458b` **must be deployed** (§A.0) — `e99f089` alone still
has 3 broken Rashid tools + silent AI-cost-tracking failure.

**Then confirm live** (§A.1–A.13). This report will be updated to PASS/FAIL per
item once server output is provided. Until then, live-runtime items are honestly
marked **NOT TESTED (needs server run)** rather than assumed working.

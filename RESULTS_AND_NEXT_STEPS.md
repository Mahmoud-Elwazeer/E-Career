# Results & Next Steps

**Date:** 2026-09-29 · **Deployed:** `e7032f2` (code) · **Docs:** `070c960`
**Domain:** jobs.usamif.com

This summarizes what was done for the platform-wide engine/OSS/hardening
directive (`caaaa.md`), the results per area, and exactly what still needs
action. Full detail: `audit/PLATFORM_ENGINE_ENRICHMENT_MASTER.md`.

---

## 1. What was done and verified

### Fixed and confirmed working LIVE on the server
- **Recommendations engine** — was crashing with `ImportError` (`JobApplication`
  imported from the wrong module in 6 places). Fixed → live check returned
  `recs: 3` with correct fields.
- **Direct-Apply moat** — hardened domain matching (exact + subdomain, no naive
  substring). Live check: LinkedIn/Indeed and subdomains blocked; lookalikes and
  real ATS (greenhouse/lever) correctly allowed; 25 active blocked domains.
- **Rashid skill-gap & salary data paths** — fixed to call the real services;
  live checks return correct data structures.
- **Services & workers** — `usam.service`, `celery-usam.service`,
  `celery-beat-usam.service` all active; `manage.py check` clean; migration
  `0008` applied.

### Fixed in code + tests (deployed)
- **5 broken Rashid agent tools** total (search_jobs, get_recommendations,
  analyze_skill_gap, get_career_profile, get_salary_insights) + a missing
  `settings` import that silently broke AI cost tracking.
- **Job provenance** field added (migration 0008) and populated on ingestion.
- **ATS dispatch** aligned (added Workday/iCIMS/Oracle/SAP; unknown platforms
  now logged, not silently dropped).
- **Centralized AWS Bedrock client** + **classified health check** + **fail-fast
  fallback** so the platform no longer silently pretends AI works.

### OSS research (decisions, not blind installs)
- Scrapling / Crawl4AI: keep OPTIONAL (real dependency conflicts with docling).
- Firecrawl: REJECT embedding (AGPL copyleft risk).
- ScrapeGraphAI / Scrapy / browser-use / Crawlee: reject or reference-only.
- jobspy, LightFM, sentence-transformers, docling, pydantic-ai: keep (in use).

### Authoritative documents produced
- `audit/PLATFORM_ENGINE_ENRICHMENT_MASTER.md` — 58-engine matrix, OSS/license
  matrix, scraping tiers, AI architecture, cross-engine chains, priorities.
- `audit/OPEN_SOURCE_ENGINE_ENRICHMENT_AUDIT.md` — OSS decisions.
- `audit/POST_DEPLOY_RUNTIME_VERIFICATION.md` — live runtime evidence.

---

## 2. THE ONE BLOCKER — server AWS credentials (you must fix)

All AI features (Rashid, AI CV parsing, AI matching, salary AI, cover letters)
are down because the server's AWS key is invalid/revoked.

**Proof (live):** `bedrock_health()` →
`{'status': 'AUTH_FAILED', 'region': 'us-east-1', 'credential_source': 'static_settings_env'}`
The static key in `/var/www/usam/backend/.env` is rejected by AWS
(`UnrecognizedClientException`), and no EC2 instance role is attached.

### Fix — choose ONE

**Option A (recommended): EC2 IAM instance role**
1. AWS Console → IAM → create a role for EC2 with a policy allowing
   `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`,
   `bedrock:Converse`, `bedrock:ConverseStream`, `bedrock:ListFoundationModels`
   (scoped to your region/models, not `*`).
2. EC2 → this instance → Actions → Security → Modify IAM role → attach it.
3. On the server, disable the dead static keys (the app auto-uses the role):
   ```bash
   sudo sed -i 's/^AWS_ACCESS_KEY_ID=/#AWS_ACCESS_KEY_ID=/; s/^AWS_SECRET_ACCESS_KEY=/#AWS_SECRET_ACCESS_KEY=/' /var/www/usam/backend/.env
   sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service
   ```

**Option B: rotate the static key**
1. IAM → create a new access key for the Bedrock user; deactivate the old one.
2. Update `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in `backend/.env`.
3. `sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service`

### Verify the fix
```bash
cd /var/www/usam/backend && source ../venv/bin/activate
python manage.py shell -c "from apps.intelligence.bedrock_client import bedrock_health; print(bedrock_health())"
```
- `HEALTHY` → run the Rashid loop; expect real answers (`"model"` != `"fallback"`).
- `ACCESS_DENIED` / `MODEL_UNAVAILABLE` → enable Claude Sonnet 4.5 model access
  in the Bedrock console for `us-east-1`, or repoint `RASHID_MODEL`.

---

## 3. SECURITY — exposed AWS key in git history (action required)

A **real AWS Access Key ID** was committed in history at commit `fa11a2f`
(files: `.env.example`, `IMPLEMENTATION_REQUIREMENTS.md`, `READY_FOR_PHASE_1A.md`,
`SETUP_STATUS.md`, `START_HERE.md`). It is removed from the current code but
remains in history. It is very likely the same now-dead key.

**Do:**
1. **Deactivate/delete that key in IAM** (treat as compromised). Confirm nothing
   else uses it first.
2. Optional cleanup: purge from history with BFG/`git filter-repo` — but this is
   a **force-push that rewrites shared history** and breaks the server's
   checkouts and every clone. Since deactivating the key removes the risk,
   schedule history rewrite only with all collaborators aware. Not done
   automatically (destructive).
3. Keep secrets only in gitignored `.env` or a secret manager — never in tracked
   `.md`/`.example` files.

---

## 4. What is verified working vs blocked

| Area | Status |
|------|--------|
| Auth / login | ✅ PASS (live) |
| Services + Celery workers | ✅ PASS (live) |
| Direct-Apply moat | ✅ PASS (live) |
| Recommendations | ✅ PASS (live, after fix) |
| Skill-gap / salary data paths | ✅ PASS (live) |
| Job provenance | ✅ PASS |
| AI health classification | ✅ PASS (live — correctly reports AUTH_FAILED) |
| Rashid AI answers / all Bedrock AI | ⛔ BLOCKED — server AWS credentials |
| AI cost/usage tracking | ⛔ BLOCKED — needs a successful AI call to verify |
| Salary data coverage | ⚠️ DATA GAP — 0 records for "engineer" (populate real data; do not fake) |
| Exposed key in git history | 🔴 ACTION — deactivate in IAM |

---

## 5. Deferred (documented, not rushed)

- Converge fragmented matching layer (`MatchingService` vs `RecommendationEngine`).
- Dynamic Bedrock model discovery (replace hardcoded catalog).
- Fuzzy/semantic dedup; streaming voice; OpenSearch/Meilisearch evaluation.
- OS maintenance: 17 pending updates + 8 ESM + restart-required — separate
  maintenance window (kept out of the AI fix by request).

---

## 6. After you fix AWS credentials

Paste back the output of:
```bash
python manage.py shell -c "from apps.intelligence.bedrock_client import bedrock_health; print(bedrock_health())"
```
and the Rashid loop. Once Bedrock is `HEALTHY` and Rashid returns non-fallback
answers, the remaining AI items (tool execution tracing, cost tracking, other
Bedrock features) will be verified and moved to PASS.

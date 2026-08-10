# FINAL IMPLEMENTATION PLAN — E-Career Platform
## Single Source of Truth for All Remaining Work
## Created: August 10, 2026

---

## PREAMBLE

This file consolidates and supersedes ALL previous planning documents:
- ADVANCED_FEATURES_ROADMAP.md (outdated — many items marked "missing" are actually implemented)
- CLINE_REMAINING_TASKS.md (partially outdated)
- REMAINING_WORK_PROMPTS.md (partially outdated)
- IMPLEMENTATION_PLAN.md (outdated — June 29)
- IMPLEMENTATION_STATUS.md (partially outdated)
- All PHASE_* completion docs
- All Phase 1/2/3 audit responses in this conversation

**Do NOT reference previous planning docs for implementation decisions. Use THIS file only.**

---

## CURRENT STATE SUMMARY (Verified August 10, 2026)

### What Is Actually Implemented and Working

| System | Status | Evidence |
|--------|--------|----------|
| 27 Django apps | ✅ Production | All deployed, 76 models |
| 181 job embeddings (pgvector) | ✅ Working | Semantic search returns results |
| Typesense full-text search | ✅ Working | Deployed, indexed |
| 11 ATS scrapers (Ashby, BambooHR, Greenhouse, iCIMS, Lever, Oracle, SAP, SmartRecruiters, Teamtailor, Workable, Workday) | ✅ Code exists | In apps/scraper/ats/ |
| Verification pipeline (6 stages) | ✅ Code exists | apps/verification/ |
| LightFM recommendation engine | ✅ Code exists | apps/intelligence/recommendation_service.py |
| Career Brain service | ✅ Code exists | apps/career/career_brain_service.py |
| CV parser (pdfplumber + docx + Bedrock Claude) | ✅ Code exists | apps/career/cv_parser.py |
| Interview simulation (text + voice + coding) | ✅ Code exists | apps/interviews/ (service.py, voice_service.py, coding_service.py) |
| Rashid AI assistant | ✅ Working | apps/rashid/ with encrypted conversations |
| Skills taxonomy (ESCO + O*NET models) | ✅ Models exist | apps/skills/ with graph.py (Apache AGE) |
| Employer portal | ✅ Working | apps/employers/ with ranking, knockout questions |
| Resume builder | ✅ Code exists | apps/resume/ |
| Salary intelligence | ✅ Code exists | apps/salary/ |
| Assessment system | ✅ Code exists | apps/assessment/ |
| Notifications | ✅ Code exists | apps/notifications/ |
| Email system | ✅ Code exists | apps/emails/ (7 Celery tasks) |
| Monitoring | ✅ Code exists | apps/monitoring/ |
| Feature flags + Rules engine | ✅ Code exists | apps/core/models.py (FeatureFlag, Rule) |
| Rate limiting middleware | ✅ Code exists | apps/core/middleware/rate_limiting.py |
| Proactive Rashid service | ✅ Code exists | apps/rashid/proactive_service.py |
| AI circuit breaker + cost tracking | ✅ Code exists | apps/intelligence/service.py |
| Common Crawl discovery | ✅ Code exists | apps/scraper/discovery/common_crawl.py |
| Celery + Redis + Beat | ✅ Configured | config/celery.py |
| Docker Compose | ✅ Configured | docker-compose.yml |
| CI/CD (GitHub Actions) | ✅ Active | .github/workflows/ci.yml |
| Production deployment | ✅ Live | jobs.usamif.com (EC2, eu-north-1) |

### What the ADVANCED_FEATURES_ROADMAP.md Gets WRONG

These are marked "Missing" in that file but ACTUALLY EXIST in the codebase:

| Item Listed as Missing | Actual Status |
|----------------------|---------------|
| LightFM integration | ✅ IMPLEMENTED (recommendation_service.py, full WARP loss, user features) |
| Career Brain model | ✅ IMPLEMENTED (CareerBrain model in career/models.py) |
| Career Brain updater | ✅ IMPLEMENTED (career_brain_service.py) |
| to_prompt_context() | ✅ IMPLEMENTED (in career brain service) |
| Integrate into Rashid | ✅ IMPLEMENTED (Rashid uses Career Brain context) |
| Proactive notifications | ✅ IMPLEMENTED (proactive_service.py, 5 triggers) |
| CV tailoring tool | ✅ PARTIALLY (AI infrastructure ready, needs endpoint) |
| AI candidate ranking | ✅ IMPLEMENTED (CandidateRanking model + employers app) |
| Knockout questions | ✅ IMPLEMENTED (KnockoutQuestion model) |
| Rule model | ✅ IMPLEMENTED (Rule model in core) |
| Judge0 deployment | ✅ INTEGRATED (coding_service.py uses Judge0 via RapidAPI) |
| Code execution service | ✅ IMPLEMENTED (coding_service.py, 10 languages) |
| Coding problem generator | ✅ IMPLEMENTED (in coding_service.py via Bedrock) |
| Solution evaluator | ✅ IMPLEMENTED (in coding_service.py) |
| AWS Polly TTS | ✅ IMPLEMENTED (voice_service.py) |
| Voice interview | ✅ IMPLEMENTED (voice_service.py with Polly + Transcribe) |
| Pdfplumber integration | ✅ IMPLEMENTED (cv_parser.py) |
| Docling integration | ✅ IMPLEMENTED (cv_parser.py, DocumentConverter) |
| Skill extraction from CV | ✅ IMPLEMENTED (cv_parser.py, Bedrock extraction) |
| Map extracted skills to ESCO | ✅ IMPLEMENTED (cv_parser.py, fuzzy matching) |
| Semantic search endpoint | ✅ IMPLEMENTED (vectors/views.py) |
| Hybrid search | ✅ IMPLEMENTED (HybridSearchView in vectors/views.py) |
| Talent discovery search | ✅ IMPLEMENTED (TalentDiscovery model in employers) |
| OpenAPI/drf-spectacular | ✅ CONFIGURED (in urls.py: /api/schema/, /api/docs/) |

---

## WHAT ACTUALLY REMAINS TO BE DONE

After cross-referencing all three audit phases against the actual codebase, here is the definitive list of remaining work, organized by dependency order.

---

## PHASE A: CRITICAL SECURITY & STABILITY (P0)
**Must complete before any feature work. Estimated: 4 hours.**

### A1: Rotate AWS Credentials
- **Reason:** Credentials exposed in git-tracked .md files (PHASE3_STATUS.md, README_PHASE3.md)
- **Action:** 
  1. AWS Console → IAM → Rotate access key for the exposed key (AKIAXXXXXXXXXXXXXXXXXX)
  2. Update /var/www/usam/backend/.env with new credentials
  3. Restart usam.service
- **Files:** AWS Console, server .env
- **Risk:** HIGH if not done — anyone with git history can access AWS
- **Acceptance:** Old key deactivated, new key works, services running

### A2: Remove Credentials from Git-Tracked Files
- **Action:** Remove AWS keys from all .md files that contain them
- **Files:** PHASE3_STATUS.md, README_PHASE3.md, PHASE3_COMMANDS.txt, REMAINING_WORK_PROMPTS.md
- **Command:** `grep -rl "AKIAXXXXXXXXXXXXXXXXXX" *.md *.txt` → edit each file
- **Acceptance:** `grep -r "AKIA" *.md *.txt` returns nothing

### A3: Verify Database Backups
- **Action:** Confirm automated PostgreSQL backups exist (pg_dump cron or AWS RDS snapshots)
- **If missing:** Add daily pg_dump cron to /etc/cron.d/
- **Acceptance:** `ls /var/backups/postgres/` shows recent dumps OR RDS snapshots confirmed

### A4: Verify Celery Beat Schedule Active
- **Action:** Check config/celery.py for beat_schedule, verify celery-beat-usam.service is running
- **Command:** `sudo systemctl status celery-beat-usam.service`
- **If not running:** Enable and start it
- **Acceptance:** `celery -A config inspect active` shows workers; beat is scheduling tasks

### A5: Remove Dead Code (search/embeddings.py)
- **Reason:** Duplicate of vectors/plugins/cohere_embed_plugin.py (uses direct Cohere API instead of Bedrock)
- **Action:**
  1. `grep -r "from apps.search.embeddings" backend/` → identify imports
  2. Redirect any consumers to vectors service
  3. Delete apps/search/embeddings.py
- **Risk:** Low — verify no active imports first
- **Acceptance:** File deleted, no import errors on service restart

### A6: Fix .gitignore
- **Action:** Ensure .env, *.log, venv/, node_modules/, __pycache__/ are gitignored
- **File:** .gitignore at repo root
- **Acceptance:** `git status` does not show .env or venv files

---

## PHASE B: DATA FOUNDATION (P1)
**Populate the platform with real data. Estimated: 6 hours.**
**Dependencies:** Phase A complete.

### B1: Full ESCO Skills Import
- **Reason:** Only 20 sample skills imported; full taxonomy has 13,939
- **Action:** `python manage.py import_esco --file backend/data/esco/skills_en.csv`
- **Note:** Command and CSV both exist already
- **Acceptance:** `Skill.objects.count()` ≥ 13,000

### B2: Full O*NET Occupations Import
- **Action:** `python manage.py import_onet --file backend/data/onet/Occupation_Data.csv`
- **Acceptance:** `Occupation.objects.count()` ≥ 900

### B3: ESCO-O*NET Mapping
- **Action:** `python manage.py map_esco_onet`
- **Acceptance:** Mappings created between ESCO skills and O*NET occupations

### B4: Generate Skill Embeddings
- **Action:** `python manage.py embed_skills`
- **Depends:** B1 complete
- **Acceptance:** vectors_skills table populated with embeddings for all skills

### B5: Scale Job Data (Run Scrapers)
- **Action:** Run all 11 ATS scrapers to bring job count from 181 to 500+
- **Command:** `python manage.py run_scrapers`
- **Depends:** A4 (Celery Beat active)
- **Acceptance:** 500+ active jobs in database; all pass verification pipeline

### B6: Generate Embeddings for New Jobs
- **Action:** `python manage.py embed_jobs`
- **Depends:** B5
- **Acceptance:** All active jobs have embeddings in vectors_jobs table

---

## PHASE C: AUTHENTICATION & AUTHORIZATION (P1)
**Proper role enforcement. Estimated: 8 hours.**
**Dependencies:** Phase A complete.

### C1: Add Role Field to User Model
- **Action:** Add `role` CharField with choices (jobseeker, employer, admin) to User model
- **File:** backend/apps/accounts/models.py
- **Migration:** `python manage.py makemigrations accounts`
- **Default:** 'jobseeker' for existing users
- **Acceptance:** All users have a role; field visible in admin

### C2: Create DRF Permission Classes
- **Action:** Create IsEmployer, IsJobSeeker, IsAdmin permission classes
- **File:** backend/apps/accounts/permissions.py (new)
- **Acceptance:** Employer endpoints return 403 for non-employers

### C3: Apply Permissions to Views
- **Action:** Add permission_classes to employer views, admin views
- **Files:** apps/employers/views.py, apps/core/views.py (admin API)
- **Acceptance:** Unauthenticated/wrong-role requests return 403

### C4: Per-User API Throttling
- **Action:** Add UserRateThrottle (100/min) and AnonRateThrottle (30/min) to DRF settings
- **File:** config/settings/base.py (REST_FRAMEWORK config)
- **Acceptance:** 101st request in a minute returns 429

### C5: Onboarding Progress Model
- **Action:** Add OnboardingProgress model tracking which steps user completed
- **File:** backend/apps/career/models.py
- **Fields:** user (FK), steps_completed (JSONField), completed_at, career_stage, primary_interest
- **Migration required**
- **Acceptance:** Model exists, API endpoint created

### C6: Onboarding API Endpoints
- **Action:** GET/PATCH /api/v1/career/onboarding/ 
- **Files:** apps/career/views.py, serializers.py, urls.py
- **Acceptance:** Frontend can read/update onboarding progress

---

## PHASE D: USER EXPERIENCE (P1)
**Make the platform usable for new users. Estimated: 12 hours.**
**Dependencies:** Phase C (C5, C6).

### D1: Onboarding Frontend Flow
- **Action:** Create multi-step onboarding page shown after first login
- **File:** frontend/src/pages/Onboarding.tsx (new)
- **Steps:** Role → Career stage → Skills/CV upload → Preferences → Goals
- **Integration:** On completion, triggers profile embedding generation
- **Acceptance:** New user sees onboarding; data saved to backend; redirects to dashboard

### D2: Consolidate Frontend HTTP Client
- **Action:** Migrate all `services/client.ts` consumers to `services/api.ts`
- **Files:** All files importing from `services/client.ts`
- **Then:** Delete `services/client.ts`
- **Acceptance:** Single HTTP client, all API calls work

### D3: Employer Domain Verification
- **Action:** On employer registration, verify company email domain matches company website
- **Files:** apps/employers/views.py (register endpoint), add domain check logic
- **Acceptance:** Employer from @company.com registering for company.com = auto-approved; mismatch = pending admin review

### D4: Application Tracker Page
- **Action:** Create user-facing page showing their applications and statuses
- **File:** frontend/src/pages/Applications.tsx (new)
- **API:** Already exists (JobApplication model in employers app)
- **Acceptance:** Users can see their application history and current status

---

## PHASE E: DIRECT-APPLY ENFORCEMENT (P1)
**Core competitive advantage. Estimated: 6 hours.**
**Dependencies:** Phase A.

### E1: BlockedDomain Model
- **Action:** Create model for admin-managed blocked application domains
- **File:** apps/verification/models.py
- **Fields:** domain, reason, added_by, created_at
- **Seed data:** indeed.com, linkedin.com, ziprecruiter.com, monster.com (apply subdomains)
- **Admin:** Register in admin.py
- **Acceptance:** Admin can add/remove blocked domains

### E2: ApprovedATS Model
- **Action:** Create model for known-good ATS domains
- **File:** apps/verification/models.py
- **Fields:** domain, name, url_pattern, added_by, created_at
- **Seed data:** greenhouse.io, lever.co, ashbyhq.com, boards.greenhouse.io, jobs.lever.co, apply.workable.com, etc.
- **Acceptance:** Admin can manage approved ATS list

### E3: Integrate Models into Verification Pipeline
- **Action:** In the redirect resolution/domain classification step, check against BlockedDomain and ApprovedATS tables instead of hardcoded lists
- **File:** apps/verification/pipeline/legitimacy.py (or wherever domain check occurs)
- **Acceptance:** Jobs with blocked destination domains are auto-rejected; approved ATS auto-verified

### E4: Admin Override for Verification
- **Action:** Add `admin_override` boolean + `override_by` FK to VerificationResult
- **File:** apps/verification/models.py
- **Admin:** Add action button "Override verification" in admin
- **Acceptance:** Admin can manually approve/reject any job's verification

---

## PHASE F: AI FEATURES (P2)
**New AI-powered features leveraging existing infrastructure. Estimated: 16 hours.**
**Dependencies:** Phases A-E.

### F1: Cover Letter Generation Service
- **Action:** Create service that generates a tailored cover letter given user profile + job
- **File:** apps/career/cover_letter_service.py (new)
- **Model:** CoverLetter (user FK, job FK, content, version, created_at) — new model, migration required
- **AI:** Use Sonnet via intelligence gateway
- **Context:** User's CareerProfile + skills + experience + Job description + requirements
- **API:** POST /api/v1/career/cover-letter/ {job_id}
- **Acceptance:** Returns professional cover letter tailored to specific job

### F2: Cover Letter Frontend
- **Action:** Add "Generate Cover Letter" button on job detail page
- **Files:** frontend/src/pages/JobDetail.tsx, new component
- **Acceptance:** User clicks button, sees loading, then cover letter displayed with copy/download

### F3: CV Tailoring Suggestions
- **Action:** Create service that suggests CV modifications for a specific job
- **File:** apps/career/cv_tailor_service.py (new)
- **AI:** Compare user's CV/profile against job requirements; suggest additions/emphasis changes
- **API:** POST /api/v1/career/cv-tailor/ {job_id}
- **Acceptance:** Returns list of specific suggestions (add skill X, emphasize experience Y)

### F4: Match Explanation API
- **Action:** Add endpoint returning breakdown of why a job matches a user
- **File:** apps/jobs/views.py or apps/vectors/views.py
- **API:** GET /api/v1/jobs/{id}/match-explanation/
- **Response:** Score breakdown (skill_match, experience, seniority, location, semantic) + top reasons + gaps
- **Acceptance:** Frontend can show "Why this job matches you" card

### F5: Job-Specific Interview Practice
- **Action:** Connect interview generation to specific job requirements
- **File:** apps/interviews/service.py (extend)
- **API:** POST /api/v1/interviews/start/ {job_id: optional}
- **When job_id provided:** Generate questions from that job's description and requirements
- **Acceptance:** Interview questions reference the specific role/company

### F6: Weekly Career Digest Email
- **Action:** Celery Beat task sending weekly email with: new matching jobs, career tips, progress update
- **Files:** apps/emails/tasks.py (add task), create email template
- **Schedule:** Every Monday 9 AM
- **Acceptance:** Active users receive weekly digest; unsubscribe works via NotificationPreference

---

## PHASE G: ADMIN & OPERATIONS (P2)
**Administrative visibility and control. Estimated: 10 hours.**
**Dependencies:** Phases A-E.

### G1: AI Cost Dashboard
- **Action:** Admin view aggregating RashidUsage (tokens, cost) by day/week/month
- **File:** apps/monitoring/views.py or admin template
- **Acceptance:** Admin sees total AI spend, top users, cost per feature

### G2: Prompt Versioning
- **Action:** Store AI prompts in DB instead of code; version them
- **Model:** PromptVersion (name, version, content, model_target, active, created_by, created_at)
- **File:** apps/intelligence/models.py (new model)
- **Admin:** Editable in Django admin
- **Acceptance:** AI services load prompts from DB; admin can edit without deploy

### G3: Scraper Health Visibility
- **Action:** Enhance scraper dashboard to show last run time, success/fail counts, jobs found per source
- **File:** apps/scraper/admin_views.py (existing custom dashboard)
- **Acceptance:** Admin sees at a glance which scrapers are healthy

### G4: GDPR Data Export/Deletion
- **Action:** Endpoint for user to request full data export or account deletion
- **Model:** DataExportRequest (user, status, file_path, requested_at, completed_at)
- **File:** apps/accounts/views.py, apps/accounts/tasks.py (Celery task to generate export)
- **API:** POST /api/v1/auth/data-export/, DELETE /api/v1/auth/account/
- **Acceptance:** User can download all their data as JSON; deletion removes PII within 30 days

---

## PHASE H: PRODUCTION HARDENING (P2-P3)
**Reliability, performance, testing. Estimated: 16 hours.**
**Dependencies:** Phases A-G substantially complete.

### H1: Integration Tests
- **Action:** Write tests for critical flows: auth, job pipeline, search, AI fallback
- **Files:** backend/apps/tests/
- **Target:** 50+ tests, critical path coverage
- **Acceptance:** `pytest` passes; CI green

### H2: Load Test at 500+ Jobs
- **Action:** Verify search latency < 200ms with current data volume
- **Tool:** Simple curl timing or locust
- **Acceptance:** Semantic search and Typesense search both < 200ms at p95

### H3: AWS Budget Alarm
- **Action:** Set AWS Budget alarm at $50/month for Bedrock + other services
- **Tool:** AWS Budgets console
- **Acceptance:** Email alert when 80% of budget reached

### H4: Move Sync AI to Celery (Where Blocking)
- **Action:** Identify any AI calls in request/response cycle that block Gunicorn workers
- **Specific targets:** Cover letter generation, CV tailoring, interview question generation
- **Pattern:** Return task_id immediately, frontend polls for completion
- **Acceptance:** No Bedrock calls in synchronous Django views (except Rashid chat which needs streaming)

### H5: Documentation Cleanup
- **Action:** Move all planning/status .md files to `docs/archive/` directory
- **Keep at root:** Only README.md
- **Create:** docs/ARCHITECTURE.md (brief), docs/DEPLOYMENT.md, docs/API.md (link to /api/docs/)
- **Acceptance:** Root directory clean; docs organized

### H6: Frontend Build Optimization
- **Action:** Add CloudFront or at minimum ensure Nginx serves frontend with proper caching headers
- **File:** deploy/nginx.conf
- **Acceptance:** Static assets cached; Time to First Byte < 500ms

---

## DEPENDENCY GRAPH

```
Phase A (Security) ─────────────────────────────────────┐
    │                                                    │
    ├── Phase B (Data) ──────────────────────────┐       │
    │                                            │       │
    ├── Phase C (Auth) ──────────┐               │       │
    │       │                    │               │       │
    │       └── Phase D (UX) ────┤               │       │
    │                            │               │       │
    ├── Phase E (Direct-Apply) ──┤               │       │
    │                            │               │       │
    │                            ├── Phase F (AI Features)
    │                            │               │
    │                            ├── Phase G (Admin)
    │                            │
    │                            └── Phase H (Hardening)
    │
    └── [Can run C, E in parallel after A]
```

---

## EFFORT SUMMARY

| Phase | Effort | Priority | Can Parallelize With |
|-------|--------|----------|---------------------|
| A: Security | 4 hours | P0 | Nothing — do first |
| B: Data | 6 hours | P1 | C, E (after A) |
| C: Auth | 8 hours | P1 | B, E (after A) |
| D: UX | 12 hours | P1 | After C |
| E: Direct-Apply | 6 hours | P1 | B, C (after A) |
| F: AI Features | 16 hours | P2 | After D, E |
| G: Admin | 10 hours | P2 | After E, parallel with F |
| H: Hardening | 16 hours | P2-P3 | After F, G |
| **TOTAL** | **~78 hours** | | |

---

## WHAT IS EXPLICITLY NOT IN SCOPE (Deferred to Future)

These are real features but NOT needed for the current milestone:

| Feature | Reason for Deferral |
|---------|-------------------|
| Payment/subscription system | Business model not defined yet |
| Full Arabic UI translation | Partial exists; complete when user base demands it |
| Video interview presence analysis | Research needed; ethical considerations |
| Mobile native app | PWA sufficient for now |
| Learning management integration | External dependency (which courses platform?) |
| Candidate messaging (employer → user) | Complex; build after employer adoption |
| Natural language search parser | Semantic search already handles this |
| Geo-search | Location filter sufficient for now |
| GitHub OAuth / portfolio import | Nice-to-have, not core value |
| A/B testing framework | Premature until significant traffic |
| Prometheus/Grafana deployment | Existing monitoring app + Sentry sufficient |
| Frontend Monaco editor for coding | Judge0 handles execution; simple textarea sufficient for MVP |
| LiveKit/Faster-Whisper | AWS Polly/Transcribe already implemented |

---

## GIT STRATEGY

```bash
# All work on development branch (solo developer workflow)
git checkout development

# For each phase, one commit or small commit series:
# "fix: Phase A security — rotate creds, remove dead code"
# "feat: Phase B — full ESCO import, skill embeddings, scraper run"
# "feat: Phase C — user roles, permissions, throttling, onboarding model"
# "feat: Phase D — onboarding UI, employer verification, application tracker"
# "feat: Phase E — direct-apply enforcement models"
# "feat: Phase F — cover letter, CV tailor, match explanation"
# "feat: Phase G — admin cost dashboard, prompt versioning, GDPR"
# "refactor: Phase H — tests, docs cleanup, performance"
```

---

## FIRST IMPLEMENTATION TASK

**Start with Phase A1: Rotate AWS credentials.**

This is the highest priority because exposed credentials are a live security vulnerability.

```bash
# On production server:
# 1. Go to AWS Console → IAM → Users → find the key AKIAXXXXXXXXXXXXXXXXXX
# 2. Create new access key
# 3. Update /var/www/usam/backend/.env with new key
# 4. sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service
# 5. Verify services work
# 6. Deactivate old key in AWS Console
# 7. Delete old key after 24h confirmation
```

Then immediately proceed to A2 (remove creds from .md files).

---

## CONSISTENCY CHECK ✅

| Check | Status |
|-------|--------|
| Direct employer application requirement | ✅ Phase E enforces via BlockedDomain + verification pipeline |
| Aggregator discovery only | ✅ jobspy used for discovery; canonical URL resolved |
| ATS integrations | ✅ 11 exist; ApprovedATS model adds admin control |
| Job scraping | ✅ Production code exists; Phase B activates schedule |
| Job normalization | ✅ In scraper pipeline |
| Deduplication | ✅ In verification pipeline |
| Freshness/Expiration | ✅ Commands exist; Phase A4 activates schedule |
| Canonical URL | ✅ Redirect resolver in verification |
| Direct Apply Verification | ✅ Phase E adds admin-controlled gate |
| Company verification | ✅ Phase D3 adds domain check |
| User onboarding | ✅ Phase C5-D1 builds complete flow |
| CV upload + parsing | ✅ Already implemented (cv_parser.py) |
| Career profile | ✅ CareerProfile model exists and is populated |
| Skills taxonomy | ✅ Models exist; Phase B imports full data |
| Career graph | ✅ Apache AGE + ORM fallback implemented |
| Job recommendations | ✅ LightFM implemented |
| Candidate matching | ✅ Scoring exists; Phase F4 adds explanation |
| Employer search | ✅ TalentDiscovery implemented |
| Talent pool | ✅ CareerProfile + embeddings = searchable talent |
| Candidate ranking | ✅ CandidateRanking model + AI ranking |
| Employer ATS/workflow | ✅ JobApplication stages implemented |
| Screening questions | ✅ KnockoutQuestion model implemented |
| AI Career Coach | ✅ Rashid + Career Brain fully implemented |
| CV tailoring | ✅ Phase F3 adds endpoint (AI infrastructure ready) |
| Cover letters | ✅ Phase F1-F2 builds this |
| Interview simulation | ✅ Text + Voice + Coding all implemented |
| Voice + STT/TTS | ✅ Polly + Transcribe implemented |
| Interview scoring | ✅ 6-dimension evaluation implemented |
| Career development | ✅ CareerGoal + CareerGoalAction exist |
| Notifications | ✅ System exists; Phase F6 adds digest |
| Email | ✅ 7 Celery tasks, templates, tracking |
| Admin control plane | ✅ Unfold + custom dashboards + FeatureFlag + Rule |
| Analytics | ✅ JobView, JobClick, SearchLog models |
| AI model routing | ✅ Intelligence gateway with Haiku/Sonnet routing |
| AWS Bedrock | ✅ Active and working |
| Cost controls | ✅ Circuit breaker + daily limits + RashidUsage |
| Security | ✅ Phase A fixes critical gap; Phase C adds RBAC |
| Privacy | ✅ Field encryption exists; Phase G4 adds GDPR |
| RBAC | ✅ Phase C implements role-based permissions |
| Audit logs | ✅ ActivityLog + EventLog exist |
| Observability | ✅ Monitoring app + Sentry; Phase G enhances |
| Queues/workers | ✅ Celery + Redis configured |
| Retry/failure recovery | ✅ Celery retry + circuit breaker |
| Scalability | ✅ Plugin architecture; Phase H tests at scale |
| Testing | ✅ Phase H1 adds integration tests |
| Open-source licenses | ✅ All compliant (Apache-2.0, MIT, external SaaS) |
| Deployment strategy | ✅ EC2 + Gunicorn + systemd + deploy scripts |
| Rollback strategy | ✅ deploy/rollback.sh exists |

**No gaps found. All requirements covered by existing code + this implementation plan.**

---

## END OF PLAN

**This is the single source of truth. Begin with Phase A.**

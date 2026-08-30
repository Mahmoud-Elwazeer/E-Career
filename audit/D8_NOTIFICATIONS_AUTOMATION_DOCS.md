# D8 Audit — Notifications + Automation/Workflow + Document Engine

**Scope:** apps/notifications, apps/emails, Celery beat schedule, CV upload/parse pipeline
(apps/profiles, apps/resume). Read-only, code-verified. No edits made.

**Method:** Read AGENTS.md + git log for the referenced 2026-08-29 bugfix; read every
relevant backend file end-to-end; grepped for dangling references, unused/duplicate
notification models, and beat-schedule task resolution; read frontend Notifications
pages/hooks/components verbatim (no assumptions from prior audits).

**Verdict key:** DONE / PARTIAL / BROKEN / MISSING / REFACTOR / INTEGRATE / REPLACE / BUILD

---

## 0. Executive summary

| Area | Verdict | One-liner |
|---|---|---|
| Notification Engine (frontend) | **PARTIAL** (prior "hardcoded-empty mock" claim is **FALSE**, but a real bug exists) | Real backend-driven fetch, NOT a mock array. But 3 different frontend components/pages read from **2 incompatible backend notification systems**, and one page bypasses auth entirely. |
| Notification Engine (backend) | **REFACTOR** (duplicate systems) | Two parallel, non-integrated notification models: `apps.users.Notification` (simple, used by the actual `/users/me/notifications/` API the frontend calls) vs. `apps.notifications.UserNotification` (rich preferences/digest/batch system, used by `emails`/`interviews` apps to create notifications). They do not share data — notifications created via `create_and_deliver_notification()` (rich system) never appear in the page the user actually sees. |
| Automation/Workflow Engine (Celery beat) | **PARTIAL** | 15 real scheduled tasks, all resolve to real functions — no phantom schedules. But one real, working task (`send_notification_digest`) is **MISSING** from the schedule, so daily/weekly notification digest preferences silently never fire. |
| Document Engine (CV pipeline) | **PARTIAL** | Upload→validation→malware-scan→parse(OCR fallback)→AI-structuring→profile-update is real and wired end-to-end. No dedicated "indexing" stage for CVs (only skill list is later used in job-matching, no search-index of resumes). Storage is local `MEDIA_ROOT` filesystem only (no S3/object storage). |
| emails/tasks.py + matching.py `is_active` bugfix | **DONE** (fix landed) but **incomplete sibling bug found** | The 2026-08-29 fix (`3a92ce0`) correctly changed `is_active=True`→`status='active'` in `apps/emails/tasks.py` (2 sites) and `apps/emails/matching.py` (2 sites) — verified in current code. However the **same bug class still exists, unfixed**, in `apps/profiles/services.py` (not in the fix commit's file list). |

---

## 1. Notification Engine

### 1.1 Frontend — verifying the "mockNotifications: [] " claim

**Claim in prior audit:** `Notifications.tsx` had `mockNotifications: Notification[] = []` permanently empty (a hardcoded mock, never wired to backend).

**Current code (verified line-by-line):** `frontend/src/pages/Notifications.tsx:52,59-69` —
```ts
const [notifications, setNotifications] = useState<Notification[]>([]);
...
const fetchNotifications = async () => {
  const data = await apiRequest<Notification[]>('/users/me/notifications/');
  setNotifications(Array.isArray(data) ? data : []);
};
```
This is a **real `useState([])` initial value + a real `useEffect`-triggered fetch** from
`apiRequest('/users/me/notifications/')` (an authenticated call using `services/client.ts`,
which attaches the JWT bearer token and does 401-refresh). **The prior audit's claim is
FALSE as of current code** — `Notifications.tsx:52` — **DONE**. Mark‑as‑read (`:80-92`,
PATCH) and mark‑all‑read (`:71-78`, POST) also call real endpoints. — DONE.

Likely origin of the stale claim: `frontend/src/hooks/use-notifications.ts:14`
(`const [notifications, setNotifications] = useState<Notification[]>([])`) — an empty
array *initializer*, immediately overwritten by `load()` in the same file via
`fetchNotifications()` from `services/userdata.ts:92-97`. A superficial grep for
`Notification[] = []` would hit this and misreport it as a permanent mock. — no action
needed, but flag for future auditors to distinguish `useState([])` from a hardcoded
constant.

### 1.2 Frontend — real bugs found (not previously flagged)

- **`frontend/src/pages/NotificationPreferences.tsx:50,59` — BROKEN.** Uses bare
  `fetch('/api/v1/notifications/preferences/')` / `fetch('/api/v1/notifications/preferences/', {method:'PUT', ...})`
  instead of `apiRequest()` from `services/client.ts`. This endpoint
  (`apps/notifications/views.py:32` `notification_preferences`) requires
  `IsAuthenticated`, but the bare `fetch()` sends **no Authorization header** and doesn't
  go through the app's configured `API_BASE`/dev proxy consistently — every load/save on
  this page will 401 in production. This is the exact "duplicate API client" antipattern
  AGENTS.md already flags for Recommendations — same bug, different page.

- **Two incompatible frontend `Notification` interfaces reading from two different
  backend systems, silently:**
  - `pages/Notifications.tsx:22-31` and `hooks/use-notifications.ts` (via
    `services/userdata.ts:81-90`) hit `GET /users/me/notifications/` →
    `apps.users.views.NotificationListView` → `apps.users.models.Notification`
    (fields: `title, body, type, is_read, metadata, created_at`).
  - `components/notifications/NotificationCenter.tsx:9-20` **also** calls
    `apiRequest('/users/me/notifications/')` but declares a `Notification` interface with
    a `message` and `severity` field that **do not exist** on the actual serializer
    (`apps/users/serializers.py:43-50` only exposes `title, body, type, is_read,
    metadata, created_at` — no `message`, no `severity`). `notification.message` and
    `getSeverityColor(notification.severity)` will render `undefined`/fall through to the
    default color for every notification. — **BROKEN** (`NotificationCenter.tsx:16,93-102,141,149`).
  - Is `NotificationCenter.tsx` even mounted anywhere?

    grep across `frontend/src` found **zero import sites** for
    `NotificationCenter`/`NotificationBadge` outside their own file — **dead component**,
    not currently rendered. Lower severity than it looks, but still tech debt /
    REFACTOR: delete or fix before someone wires it up expecting `message`/`severity`
    to work.

- **NotificationBell.tsx** (`components/NotificationBell.tsx:51-57`) reads `n.body` (not
  `n.message`) — this one is field-correct against the real serializer. — DONE.

### 1.3 Backend — two non-integrated notification systems (REFACTOR)

1. **`apps.users.models.Notification`** (`apps/users/models.py:75-109`) — simple model:
   `title, body, type (alert_match/system/welcome), is_read, metadata`. Backed by
   `apps/users/views.py:123-165` (`NotificationListView`, `NotificationDetailView`,
   `MarkAllNotificationsReadView`), routed at `/api/v1/users/me/notifications/...` — this
   is the **only** system the current frontend actually calls (Notifications.tsx,
   NotificationBell.tsx, NotificationCenter.tsx, use-notifications.ts all hit this).
   Nothing in the codebase currently *writes* rows into this table except test fixtures
   (`backend/tests/integration/test_features.py:259,266,274,275`) — i.e. **no production
   code path creates a `users.Notification` row**. — **MISSING**: the read side is real,
   the write side (the actual event→notification bridge for this specific model) does
   not exist in application code.

2. **`apps.notifications.UserNotification`** (`apps/notifications/models.py:97-203`) —
   rich model: `notification_type` (12 choices), `status` (unread/read/archived),
   `priority`, `related_id/type/url`, `sent_at`, `read_at`, `expires_at`. Backed by
   `apps/notifications/views.py` (`user_notifications`, `bulk_update_notifications`,
   `mark_all_as_read`, `get_notification_summary`, etc.), routed under
   `notifications/notifications/...` (`apps/notifications/urls.py:19-23`) — **not called
   by any current frontend page** (grep of `frontend/src` for `/notifications/notifications`
   or `/notifications/preferences` found only the broken bare-`fetch` in
   `NotificationPreferences.tsx`, which only hits `/preferences/`, not
   `/notifications/`). This is the system that **is** actually written to by real
   application code:
   - `apps/emails/tasks.py:242-254` (`send_employer_application_notification` →
     `create_and_deliver_notification(...)`) — DONE, real, fires on new application.
   - `apps/interviews/views.py:112-122` (interview session started) — DONE, real.
   - `apps/notifications/tasks.py:20-64` (`deliver_notification`) — real delivery-by-email
     for `alert_frequency='instant'` users — DONE.
   - `apps/notifications/tasks.py:67-124` (`send_notification_digest`) — real
     daily/weekly digest batching — DONE as code, but see §2 (never scheduled).

   **Net effect:** real backend events (new application, interview started) create rich
   `UserNotification` rows with working email delivery — but the **in-app bell/list the
   user actually sees never shows them**, because the frontend only reads
   `apps.users.Notification`, a model nothing writes to in production. The in-app
   notification feature is effectively a **shell that always renders empty for real
   users** (confirmed no `users.Notification.objects.create(...)` call sites outside
   tests) even though the email side of the same events works.

   **Recommendation (INTEGRATE):** either (a) point `NotificationListView` /
   `apiRequest('/users/me/notifications/')` at `apps.notifications.UserNotification`
   instead, or (b) have `create_and_deliver_notification()` also write a
   `users.Notification` row. Given `apps.notifications` has the preferences/digest/batch
   infrastructure already built and working, (a) is the lower-effort correct fix.

3. **`apps/rashid/proactive_service.py:18,291-318`** —
   `from apps.notifications.models import Notification` — **`Notification` does not
   exist in `apps.notifications.models`** (verified via `python -c "from
   apps.notifications.models import Notification"` → `ImportError: cannot import name
   'Notification'`). The class that does exist there is `UserNotification`, and even
   that has no `notification_type='rashid_proactive'`, no `data=` field, no `read=`
   field (it's `status` not `read`) — `create_notification_record()`
   (`proactive_service.py:291-318`) would raise both an `ImportError` at module load AND,
   if the import were fixed, a `TypeError`/`FieldError` on `.objects.create(...)`
   (wrong field names throughout). **BROKEN** — but harmless in current state because
   **the module is never imported anywhere else in the codebase** (grep confirmed zero
   importers) — dead/orphaned module, not wired into any view, task, or signal. —
   `apps/rashid/proactive_service.py:18` (bad import), `:306-317` (wrong field names) —
   **BROKEN / MISSING** (feature was apparently scaffolded then abandoned before wiring).

### 1.4 Notification models/serializers hygiene

- `apps/notifications/serializers.py:122` —
  `status = serializers.ChoiceField(choices=UserNotificationSerializer.Meta.fields[11])`
  — indexes into a **list of field name strings**, not a choices tuple
  (`UserNotificationSerializer.Meta.fields[11]` evaluates to the string `'priority'`,
  which is then passed as `choices=` to a `ChoiceField`, i.e. `choices='priority'` — this
  iterates the *characters* of the string `"priority"` as valid choices). This is broken
  and would only surface when `NotificationBulkUpdateSerializer` is actually validated
  (bulk-update endpoint) — **BROKEN**, `apps/notifications/serializers.py:115-122`.

---

## 2. Automation / Workflow Engine (Celery beat)

**Config:** `backend/config/celery.py` — beat schedule defined via `app.conf.beat_schedule`
(plain dict, static — NOT `django_celery_beat` DB-driven despite
`CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'` being set in
`config/settings/base.py:312` and `django_celery_beat` being an installed app
(`base.py:85`) — the scheduler class is configured for DB-backed periodic tasks, but
**no `PeriodicTask`/`IntervalSchedule`/`CrontabSchedule` rows are created anywhere**
(grepped `PeriodicTask.objects.create|get_or_create` — 0 hits) — the static dict in
`celery.py` is what actually runs; the `django_celery_beat` DatabaseScheduler will read
`app.conf.beat_schedule` as its seed but any admin-created override infrastructure is
unused. Not broken, just an unused-capability gap — REFACTOR-note only.

### 2.1 Full list of scheduled tasks (file:line, cadence, resolution check)

| Beat key | Task path | Cadence | celery.py line | Task def location | Resolves? |
|---|---|---|---|---|---|
| `scrape-all-sources` | `apps.scraper.tasks.scrape_all_sources` | every 6h | `celery.py:23-26` | `apps/scraper/tasks.py:29` | ✅ DONE |
| `verify-apply-urls` | `apps.scraper.tasks.verify_apply_urls` | 2 AM daily | `celery.py:27-30` | `apps/scraper/tasks.py` (grep confirmed `@shared_task`) | ✅ DONE |
| `expire-old-jobs` | `apps.scraper.tasks.expire_old_jobs` | 3 AM daily | `celery.py:31-34` | `apps/scraper/tasks.py:256/326/345/364/385/411/427` (one of these) | ✅ DONE |
| `send-job-alerts` | `apps.emails.tasks.send_job_alerts` | hourly | `celery.py:36-39` | `apps/emails/tasks.py:46` | ✅ DONE (uses the fixed `status='active'` filter) |
| `send-weekly-digest` | `apps.emails.tasks.send_weekly_digest` | Mon 8 AM | `celery.py:40-43` | `apps/emails/tasks.py:137` | ✅ DONE (fixed filter) |
| `reset-email-counters` | `apps.emails.tasks.reset_email_account_counters` | midnight daily | `celery.py:44-47` | `apps/emails/tasks.py:192` | ✅ DONE |
| `send-re-engagement` | `apps.emails.tasks.send_re_engagement_emails` | Sun 10 AM | `celery.py:48-51` | `apps/emails/tasks.py:301` | ✅ DONE |
| `verify-employer-posted-jobs` | `apps.scraper.tasks.verify_employer_posted_job` | every 6h | `celery.py:53-56` | `apps/scraper/tasks.py` | ✅ DONE |
| `daily-liveness-check` | `apps.verification.tasks.daily_liveness_check` | 3 AM daily | `celery.py:57-60` | `apps/verification/tasks.py:22` (first `@shared_task`) | ✅ DONE |
| `weekly-reverification` | `apps.verification.tasks.weekly_reverification` | Sun 2 AM | `celery.py:61-64` | `apps/verification/tasks.py` | ✅ DONE |
| `recalculate-all-talent-scores` | `apps.career.tasks.batch_recalculate_talent_scores` | Sun 2 AM | `celery.py:66-69` | `apps/career/tasks.py` | ✅ DONE |
| `cleanup-old-gdpr-exports` | `apps.core.tasks.cleanup_old_gdpr_exports` | 4 AM daily | `celery.py:71-74` | `apps/core/tasks.py` | ✅ DONE |
| `detect-skill-trends` | `intelligence.detect_skill_trends` | Mon 5 AM | `celery.py:76-79` | `apps/intelligence/tasks.py:18` (`name="intelligence.detect_skill_trends"`) | ✅ DONE |
| `run-topic-modeling` | `intelligence.run_topic_modeling` | Mon 6 AM | `celery.py:80-83` | `apps/intelligence/tasks.py:42` | ✅ DONE |
| `process-career-page-changes` | `apps.scraper.tasks.process_career_page_changes` | hourly | `celery.py:85-88` | `apps/scraper/tasks.py` | ✅ DONE |
| `compute-esco-embeddings` | `apps.skills.tasks.compute_esco_embeddings` | Sun 4 AM | `celery.py:90-93` | `apps/skills/tasks.py:18` | ✅ DONE |
| `aggregate-daily-analytics` | `apps.events.tasks.aggregate_daily_analytics` | 1 AM daily | `celery.py:95-98` | `apps/events/tasks.py:39` | ✅ DONE |

**All 17 scheduled entries resolve to real, existing task functions** — no phantom/dead
schedule entries found. This contradicts any prior "automation is fake" claim at the
schedule level — the schedule itself is real. — **DONE** for schedule integrity.

### 2.2 Missing from schedule (real code, orphaned)

- **`apps.notifications.tasks.send_notification_digest`** (`apps/notifications/tasks.py:67-124`)
  — fully implemented, batches unread `UserNotification`s for `alert_frequency='daily'`
  and `'weekly'` users and emails a digest, updates `NotificationBatch` counters — **but
  is not present anywhere in `config/celery.py`'s `beat_schedule` dict**. Users can set
  `alert_frequency='daily'`/`'weekly'` in `NotificationPreferenceSerializer` (exposed via
  the — broken, see §1.2 — `NotificationPreferences.tsx` page), but nothing ever
  triggers this task. Only the `instant`-frequency path (`deliver_notification`, fired
  synchronously from `create_and_deliver_notification()`) actually sends. —
  **MISSING** (`config/celery.py` — needs a new `beat_schedule` entry).

- **`apps.emails.tasks.send_weekly_career_digest`** (`apps/emails/tasks.py:351-417`,
  docstring literally says "Runs every Sunday at 9 AM") — also fully implemented (F6
  feature: matching jobs + progress stats + AI skill tip) — **also absent from
  `config/celery.py`**. Despite the docstring claiming a schedule, no `beat_schedule`
  entry exists for it. — **MISSING** (`config/celery.py`).

Both are real, working, non-trivial pieces of "automation" that are effectively dead
because nothing calls them on a cadence — a meaningful gap for anyone assessing "does
the automation engine actually run these."

### 2.3 The `is_active`→`status` bugfix — verification

- Confirmed via `git show 3a92ce0` that the fix commit changed exactly:
  - `apps/emails/matching.py:39` (`get_matching_jobs_for_user`) and `:141`
    (`get_weekly_job_summary`) — `is_active=True` → `status='active'` — **DONE**,
    verified present in current file content.
  - `apps/emails/tasks.py:67` (`send_job_alerts`) and `:164,167`
    (`send_weekly_digest`) — same fix — **DONE**, verified present.
- Repo-wide grep for `Job.objects.filter(...)`/`Job.objects.get(...)` combined with
  `is_active=` (the exact bug pattern) turned up **zero remaining hits** on the `Job`
  model specifically — all other `is_active=True` hits in the codebase are on unrelated
  models that genuinely have an `is_active` field (`EmailAccount`, `Source`, `Company`,
  `User`, `ResumeTemplate`, `RashidConversation`, etc.) — those are correct as written.
- **However, the same bug class was missed in one file not covered by the fix commit's
  list:** `apps/profiles/services.py` (`MatchingService`, actively used by
  `apps/profiles/views.py:24,295,332,347` — `get_job_recommendations`,
  `get_job_match_breakdown`, `get_similar_jobs` endpoints):
  - `apps/profiles/services.py:85` — `query = Q(is_active=True)` inside
    `get_recommended_jobs()` — **`Job` has no `is_active` field** (verified:
    `apps/jobs/models.py:177-239` — only `status` CharField with choices
    active/pending/archived, `posted_at` DateField). This filter will raise
    `django.core.exceptions.FieldError` at runtime — **BROKEN**, same root cause as the
    fixed bug, in a file the fix commit's description did not enumerate.
  - `apps/profiles/services.py:136` — `query = Q(is_active=True)` inside
    `get_similar_jobs()` — same bug — **BROKEN**.
  - `apps/profiles/services.py:115` — `Job.objects.filter(query)...order_by('-posted_date')`
    — `Job` has no `posted_date` field either (it's `posted_at`,
    `apps/jobs/models.py:239`) — **BROKEN**, a second/related field-name bug in the same
    method, also missed.
  - `apps/profiles/services.py:152` — same `.order_by('-posted_date')` bug in
    `get_similar_jobs()` — **BROKEN**.
  - **Net:** `GET /api/v1/.../recommendations/` (the `matching_service` path via
    `apps/profiles/views.py`) will 500 with `FieldError` the same way
    `apps/career/recommendation_engine.py` did before the fix — this is a live,
    unfixed regression of the exact same class the 2026-08-29 commit was meant to
    eradicate. **Recommend**: apply the identical `is_active=True`→`status='active'` and
    `-posted_date`→`-posted_at` fix to `apps/profiles/services.py:85,115,136,152`.

  Note: `apps/profiles/views.py:233` already correctly uses `Job.objects.filter(status='active')`
  in `calculate_matches` — so the bug is isolated to the `MatchingService` class in
  `services.py`, not the view file itself.

---

## 3. Document Engine (CV upload → parse pipeline)

**Located in:** `apps/profiles/` (CV upload/parsing — the real "document engine" for job
seekers) and `apps/resume/` (a separate resume-*builder*/export feature, not part of the
upload/OCR pipeline — templates, generated resumes, PDF/DOCX export via
`apps/resume/export_service.py`; not audited further as it's out of scope for "document
engine" per the task's own definition).

### 3.1 Stage-by-stage assessment

| Stage | Location | Verdict | Notes |
|---|---|---|---|
| **Upload** | `apps/profiles/views.py:83-100` (`ProfileViewSet.upload_cv`), `apps/profiles/serializers.py:147-230` (`CVUploadSerializer`) | **DONE** | Real `MultiPartParser` endpoint, `POST /api/profile/upload-cv/`. |
| **Validation** | `apps/core/upload_security.py:39-113` (`UploadValidator`) | **DONE** | Real: extension whitelist, 10MB size cap, magic-byte content-type verification (`_verify_magic_bytes`), filename sanitization, path-traversal check. Called from `CVUploadSerializer.validate_cv_file` (`serializers.py:152-157`). |
| **Security scan** | `apps/core/upload_security.py:116-229` (`scan_stream_for_malware`/`scan_file_for_malware`, ClamAV via `pyclamd`) | **PARTIAL** | Real integration, correctly fail-closed by default (`CLAMAV_FAIL_CLOSED` default `True`, `settings/base.py:318`) — but depends on an actual `clamd` daemon being reachable (`CLAMAV_HOST`/`CLAMAV_SOCKET`, `base.py:315-317`, both default to local dev paths). If `pyclamd` isn't installed or clamd isn't running in an environment, **every upload is rejected** (by design, fail-closed) rather than silently skipping — correct security posture, but means the CV upload feature is **entirely blocked** in any deployment without a working ClamAV daemon. Called from `serializers.py:159-162`. |
| **Storage** | `CareerProfile.cv_file` (`apps/career/models.py:37-42`, a `FileField`) written at `serializers.py:221` (`profile.cv_file = cv_file`) | **PARTIAL** | Real Django `FileField` write to local filesystem (`MEDIA_ROOT`, `settings/base.py:257`, default `BASE_DIR/media`). **No S3/object storage configured** (grepped settings — no `AWS_STORAGE_BUCKET_NAME`/`django-storages`/`STORAGES` config) — fine for a single-server dev/staging deploy, a real gap for production durability/scaling (files live on local disk, not backed up independently, won't survive a redeploy on ephemeral infra). |
| **OCR** | `apps/profiles/cv_parser.py:136-184` (`EasyOCRParserPlugin`) | **DONE** (code) / **PARTIAL** (deployability) | Real EasyOCR + `pdf2image` integration for scanned/image CVs, with graceful `ImportError` handling if the (heavy) `easyocr` package isn't installed — falls through to empty string, not a crash. Plugin chain order (`cv_parser.py:280-288`): Docling → pdfplumber → EasyOCR → docx → txt, matched by `can_handle()` per file type — **first matching plugin wins**, meaning for PDFs, **Docling is always tried first, OCR is never reached for a text-based PDF** (only reached if file type is image, or if used directly — code path shows OCR is a plugin in the list, but `_find_parser` picks the **first** plugin where `can_handle()` is true, and `DoclingParserPlugin.can_handle` also returns `True` for `"pdf"`, so `EasyOCRParserPlugin` — which also claims `"pdf"` in its `can_handle` — is **unreachable for any PDF** since Docling is earlier in the list and matches first). **This means OCR fallback for scanned/image-only PDFs never actually triggers** — Docling/pdfplumber will return empty text for a scanned PDF (no extractable text layer) and the pipeline will silently produce an empty `raw_text` rather than falling back to OCR. `apps/profiles/cv_parser.py:282-288` (plugin order bug) — **BROKEN** (logic present, but unreachable for its primary intended use case: scanned CVs). |
| **Extraction (structuring)** | `apps/profiles/serializers.py:191-282` (`CVUploadSerializer.save`, `_update_from_parsed_data`), delegating to `apps/intelligence/career_ai.py` (`career_ai_service.parse_cv`) | **PARTIAL** | Real AI-based structuring (Bedrock) with a documented fallback: if `bedrock_service.is_available` is `False` or parsing throws, `parsed_data` stays `None` and `profile.cv_parse_status = 'pending'` (`serializers.py:198-203,223`) — i.e. **no non-AI structured-extraction fallback exists**; if Bedrock is down/misconfigured, the CV is stored with raw text extracted but **never structured** (no skills/experience/education populated) and status stays `'pending'` forever (no retry task found — grepped for `cv_parse_status.*pending` retry logic, none exists). — MISSING: retry/backfill task for `cv_parse_status='pending'` profiles. |
| **Indexing** | — | **MISSING** | No dedicated CV/resume search-index stage exists. The parsed `skills` list is stored on `CareerProfile` and later consumed by matching services (`apps/profiles/services.py`, `apps/vectors/matching_service.py`) for job-matching, but there is no indexing of CV *content* itself (no Typesense/Qdrant/pgvector document for the CV text) — unlike jobs, which do have a `apps/vectors/management/commands/index_jobs.py` indexer. If "indexing" in the task's pipeline sense means "make the CV findable/searchable," that stage does not exist for CVs — only downstream *consumption* of the extracted skills field. |

### 3.2 Summary verdicts for Document Engine

- Upload/Validation/Security-scan: **DONE** (real, correctly implemented, fail-closed).
- Storage: **PARTIAL** (real but local-disk only, no cloud object storage).
- OCR: **BROKEN** (implemented but structurally unreachable for PDFs due to plugin
  ordering — `cv_parser.py:282-288`).
- Extraction/structuring: **PARTIAL** (real AI path, no non-AI fallback, no retry for
  failed/pending parses).
- Indexing: **MISSING** (no CV-content search index; only the extracted skills list
  feeds matching).

---

## 4. File:line index of all findings (for quick reference)

| # | Severity | File:line | Issue |
|---|---|---|---|
| 1 | Info/False-claim-correction | `frontend/src/pages/Notifications.tsx:52,59-69` | NOT a hardcoded mock — real backend fetch. Prior audit claim is stale/false. |
| 2 | High | `frontend/src/pages/NotificationPreferences.tsx:50,59` | Bare `fetch()` with no auth header on an `IsAuthenticated` endpoint — page will 401. |
| 3 | Medium | `frontend/src/components/notifications/NotificationCenter.tsx:16,93-102,141,149` | Reads `.message`/`.severity` fields that don't exist on the real serializer; also unused/dead component (0 import sites). |
| 4 | High | `apps/users/models.py:75` vs `apps/notifications/models.py:97` | Two disconnected notification models; frontend reads the one nothing in production code writes to. |
| 5 | High | `apps/rashid/proactive_service.py:18,291-318` | Imports nonexistent `Notification` class from `apps.notifications.models`; wrong field names throughout. Dead/orphaned module (0 importers) so currently harmless. |
| 6 | Medium | `apps/notifications/serializers.py:115-122` | `NotificationBulkUpdateSerializer.status` choices built from a field-name-list index, not real choices — broken if hit. |
| 7 | Medium | `config/celery.py` (whole file) | `send_notification_digest` and `send_weekly_career_digest` are real, fully implemented tasks never added to `beat_schedule` — daily/weekly digests never fire. |
| 8 | High (regression, unfixed) | `apps/profiles/services.py:85,115,136,152` | Same `is_active=True`/`-posted_date` bug class as the 2026-08-29 fix commit, present in a file that commit's file list did not include. Live 500 risk on recommendation/similar-jobs endpoints. |
| 9 | Confirmed fixed | `apps/emails/tasks.py:67,164,167`, `apps/emails/matching.py:39,141` | Verified fix landed exactly as described in commit `3a92ce0`. |
| 10 | Medium | `apps/profiles/cv_parser.py:282-288` | Parser plugin order means EasyOCR is unreachable for any PDF (Docling always matches first) — scanned/image-only PDFs silently produce empty text instead of OCR fallback. |
| 11 | Low/Info | Document Engine — storage | Local `MEDIA_ROOT` filesystem only; no S3/object storage configured. |
| 12 | Low/Info | Document Engine — indexing | No CV-content search index exists (only extracted skills feed matching). |
| 13 | Low/Info | Document Engine — extraction fallback | No retry/backfill mechanism for CVs stuck at `cv_parse_status='pending'` when Bedrock is unavailable. |

---

## 5. What is genuinely solid (don't re-flag)

- Upload security (`apps/core/upload_security.py`) — real defense-in-depth, correct
  fail-closed ClamAV posture.
- Celery beat schedule integrity — all 17 configured entries resolve to real functions;
  no phantom automation.
- The specific 2026-08-29 `is_active`→`status` fix in `apps/emails/{tasks,matching}.py`
  — verified landed correctly, no regressions in those two files.
- Real event→notification wiring exists and works end-to-end for at least two flows
  (new employer application, interview session started) through the
  `apps.notifications` rich system, including working email delivery
  (`deliver_notification`) — the gap is that the *in-app* list doesn't reflect it, not
  that the automation itself is fake.
- CV upload → validation → malware scan → text extraction → AI structuring → profile
  update is a real, mostly-working pipeline, not a stub.

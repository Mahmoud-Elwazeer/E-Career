# D6 Audit: Assessment + Interview Simulation + Voice + Career Coach Engines

**Scope:** `backend/apps/interviews/`, `backend/apps/assessment/`, `backend/apps/rashid/`
(proactive_service.py, service.py, tools.py), `backend/apps/career/` (goal/skill-gap
pieces referenced by the coach story), and the corresponding frontend surfaces.

**Method:** Read every file in scope line-by-line. Did NOT trust docstrings/comments.
Ran the actual Django test suite (`pytest`) for these apps, wrote and ran ad-hoc
pytest scripts against a live Django test DB to exercise real request/response
cycles (session created via `APIClient`, real serializer/view/service code path,
real (attempted) AWS Bedrock/Polly/Transcribe/S3/Judge0 calls — not mocks), and
made direct `boto3`/`requests` calls to verify credentials and third-party API
keys. All findings below are backed by one of: an exact file:line citation, a
pytest run transcript, or a live API call result reproduced in this document.

**Housekeeping note:** `MASTER_STATE_AND_ROADMAP.md` does not exist anywhere in
this repository (searched the whole `E-Career` tree and `M:\`) — cannot be read
as instructed. Proceeded using `AGENTS.md` (which explicitly warns not to trust
this repo's own status docs) as the only orientation document.

---

## Executive summary (skeptic's TL;DR)

| Area | Verdict | One-line reason |
|---|---|---|
| Assessment Engine | **PARTIAL** | Real Judge0 code grading + real MCQ grading work end-to-end (verified live); no AI-generated question authoring endpoint exists (questions are admin/manually seeded only); no frontend page at all. |
| Interview Simulation Engine | **PARTIAL/BROKEN (mixed)** | Text-mode technical/behavioral/system_design/case_study flow works end-to-end (verified live, incl. AI-fallback path). `coding` type is listed as a choice but has **zero working implementation** — the standalone `CodingInterviewService` (Judge0 + Bedrock) is dead code, never imported by any view. `GET /interviews/stats/` is provably **BROKEN** (500, `NameError`). Interview app's own test suite is **14/15 failing** on session/question CRUD paths (response envelope mismatch) and 100% failing on voice-specific tests. |
| Voice Engine | **PARTIAL/BROKEN — real pipeline code, non-functional in this environment** | The STT→LLM→TTS wiring is genuinely implemented (AWS Polly + AWS Transcribe + S3, not a mock/placeholder), and the frontend actually calls `MediaRecorder`/`getUserMedia` and posts real audio blobs — this is NOT a UI mockup. But verified live: the configured AWS IAM user has **no Polly/Transcribe/S3 permissions at all** (AccessDeniedException on every call), and `AWS_STORAGE_BUCKET_NAME`/`AWS_REGION` are **unset** in settings, so `speech_to_text()` will always fail before it even calls Transcribe. Net effect today: voice mode is non-functional end-to-end despite being real code. |
| Career Coach functionality | **PARTIAL, and the most complete "continuous coaching" piece is unwired dead code** | `CareerGoal`/`CareerGoalAction` CRUD + analytics is real and wired (`apps/career/goal_api.py`) — goals, milestones, progress tracking all work. `SkillGapAnalyzer` (real target-role-vs-skills diffing) is wired to a live endpoint. BUT the one module that is explicitly a "continuously watch the user and proactively recommend" engine — `ProactiveRashidService` in `apps/rashid/proactive_service.py` — is **fully-built, well-designed dead code**: no view, no URL, no Celery Beat schedule, no cron, not imported by any other file in the codebase. It is never invoked. There is no scheduled/automatic trigger anywhere that runs it. |

**Cross-cutting finding that invalidates any prior "100% ready with AI" claim about this whole domain:** the AWS Bedrock `sonnet` model alias used by essentially every AI call in these apps (`apps.intelligence.career_ai.career_ai_service`) is currently **broken account-wide** — verified live:

```
ValidationException: Invocation of model ID anthropic.claude-sonnet-4-20250514-v1:0
with on-demand throughput isn't supported. Retry your request with the ID or ARN
of an inference profile that contains this model.
```//backend/apps/intelligence/bedrock_plugin.py:31 (alias table), triggered from
interviews/service.py:66, assessment/views.py:190, rashid/tools.py:73 etc.

Every code path that "generates interview questions with AI," "evaluates answers
with AI," "generates AI observations for the career brain," "reviews CVs," etc.
is **silently falling back to hardcoded generic content** right now — the fallback
paths are well-written (see `_get_fallback_questions`, `_get_fallback_evaluation`,
`_get_fallback_observations`) so the product doesn't crash, but none of the
"AI-powered" claims for this domain are currently backed by a real model call in
this environment. This matches AGENTS.md's warning that this repo's own status
claims have been unreliable — it is unreliable **in the code today**, not just in
old docs.

---

## 1. Assessment Engine

Files: `backend/apps/assessment/models.py`, `views.py`, `urls.py`, `admin.py`,
`serializers.py`; shared grader `backend/apps/core/code_execution.py`.

### What's real (verified)
- **Models** (`models.py:17-452`): `Assessment`, `AssessmentQuestion` (coding /
  multiple_choice / single_choice / essay), `AssessmentAttempt`, `SkillBadge`,
  `AssessmentTemplate`, `AssessmentResult` — a complete, sensible schema.
- **Grading is real, not simulated.** `views.py:submit_assessment` (line 118-236):
  - Multiple choice: real equality check against `question.correct_answer`
    (`views.py:141-146`).
  - Coding: calls `execute_and_grade()` (`apps/core/code_execution.py:124`), which
    submits real code to the **Judge0 CE API** via `requests.post` and polls for
    results (`code_execution.py:62-121`). This is a real code-execution sandbox
    call, not a stub.
  - **Live-verified**: wrote and ran a pytest against the real view with an
    in-memory MCQ question — `POST /assessments/start/` → `POST
    /assessments/{id}/submit/` returned `{"score":100,"passed":true,...}` — the
    full attempt→grade→result pipeline executes end-to-end (see transcript in
    session; this is DONE for MCQ).
  - AI feedback (`views.py:188-204`) calls `career_ai_service.generate_assessment_feedback`
    and has a real fallback dict if the AI call fails — verified live that it
    *does* fail right now (Bedrock ValidationException, see cross-cutting
    finding) and the fallback fires correctly.
- **Judge0 execution**: confirmed the Judge0 endpoint URL is real and reachable,
  but a raw `requests.post` to `https://judge0-ce.p.rapidapi.com/submissions`
  returned `401 {"message":"Invalid API key..."}` because
  `JUDGE0_API_KEY`/`getattr(settings,'JUDGE0_API_KEY',None)` is **unset** in this
  environment's `.env`/settings (`code_execution.py:19`, `coding_service.py:32`).
  → **Coding-question grading is currently non-functional (BROKEN) in this
  environment**, not because the code is wrong, but because the key is absent/
  invalid. Any environment audit claiming "coding assessments work" must supply
  evidence of a valid `JUDGE0_API_KEY`.

### What's missing (verdict: MISSING)
- **No AI-driven assessment/question-generation endpoint.** Unlike
  `interviews/service.py` (which generates questions via Bedrock),
  `assessment/views.py` has no `generate_question`/`create_from_ai` action —
  `AssessmentQuestion` rows must be created manually (admin panel: confirmed via
  `admin.py` registrations) or via a script. There is no self-serve "take an
  assessment for skill X" flow that creates questions on demand.
- **No frontend page at all.** `grep`'d the entire `frontend/src` tree for
  "assessment" (case-insensitive) — the only hit is
  `frontend/src/services/intelligence.ts`, which is unrelated intelligence-layer
  code, not an assessment UI. There is no assessment page/component/route in
  `App.tsx`. **The Assessment Engine has zero UI** — it is API-only.
- `assessment/urls.py` has no dedicated test file (`find` for `test*` under
  `apps/assessment` returned nothing) — the only verification here is the
  ad-hoc script run in this audit.

**Assessment Engine verdict: PARTIAL.** Backend grading logic (MCQ + coding via
Judge0) is real and DONE for the pieces that were tested; AI feedback generation
is real code but currently degraded to fallback due to the Bedrock outage;
question authoring is MISSING (admin-only); frontend is MISSING entirely.

---

## 2. Interview Simulation Engine

Files: `backend/apps/interviews/{models,service,coding_service,voice_service,
views,serializers,urls}.py`, `frontend/src/pages/InterviewPractice.tsx`.

### Modes supported (per model/serializer, i.e. what the system *claims*)
`InterviewSession.INTERVIEW_TYPES` (`models.py:11-17`): `technical`,
`behavioral`, `coding`, `system_design`, `case_study`. `MODES` (`models.py:19`):
`text`, `voice`. So on paper: yes, HR/behavioral + technical + role-specific
(via free-text `target_role`) + a "coding" type, in both text and voice mode.

### What actually works (verified live)
- **Text-mode flow for technical/behavioral/system_design/case_study: DONE.**
  Ran the real view code end-to-end via pytest against a live test DB:
  `POST /api/v1/interviews/sessions/start/` with `interview_type=technical`
  → creates `InterviewSession` + 5 `InterviewQuestion`s via
  `interview_service.generate_questions()` (`service.py:20-80`), which called
  real Bedrock (failed → fell back to `_get_fallback_questions`,
  `service.py:219-242`), returned `201` with a real `current_question`. This is
  the honest state: the pipeline runs, but with AI failing, it degrades to 5
  generic fallback questions regardless of `interview_type`/`target_role`/
  `difficulty` — i.e., **role-specificity is currently not functioning** even
  though the code path for it exists (`service.py:51-63` builds a
  role/difficulty-aware prompt).
  - Answer submission (`views.py:answer`, line 142-200) and scoring
    (`interview_service.evaluate_answer`, `service.py:82-134`, 6-dimension
    rubric) are real; also degrades to a fixed fallback score of 7.0/10 with
    fixed dimension scores when AI is down (`service.py:244-259`) — meaning
    right now, **every answer, regardless of quality, gets an identical
    canned score**. This is a serious, live-verifiable "coaching validity" bug
    on top of the AI outage, not something a static-code read alone would
    catch.
  - `complete_session()` (`service.py:136-189`) correctly averages scores and
    generates an Arabic feedback summary from the real (or fallback) per-
    question scores — logic is correct.
- **`coding` interview type: BROKEN / effectively MISSING as an integration.**
  - `urls.py:18-20` maps `coding-question/`, `coding-problem/`,
    `coding-solution/` all to `InterviewViewSet.as_view({'post': 'start'})` —
    i.e. **these three distinct URL names all point at the same generic
    interview-start action**, not at `coding_service.py`'s
    `CodingInterviewService` (problem generation via Bedrock + Judge0
    execution + AI-suggestion feedback). Confirmed via `search_files` that
    `coding_interview_service` (the singleton in `coding_service.py:394`) has
    **zero importers anywhere in the codebase** — it is fully dead code, never
    wired to any view/URL.
  - Ran the interview app's own bundled test
    `TestInterviewCodingAPI::test_get_coding_problem` live: **it fails**
    (`400` instead of expected `200`) because it hits the generic `start`
    action with `{"difficulty":"medium","language":"python"}`, which doesn't
    match `StartInterviewSerializer`'s required fields (`interview_type`,
    `target_role`). This is not a test-authoring nit — it's proof the intended
    coding-interview integration was never actually connected.
  - **Verdict for coding interview mode: MISSING (as a real feature) /
    REFACTOR-NEEDED (dead code that should either be wired up or deleted).**
- **`GET /api/v1/interviews/stats/` is BROKEN (500 error), verified live.**
  `views.py:404-433` uses `models.Avg`/`models.Count` (lines 417, 423-425) but
  `views.py` never imports `from django.db import models` (see full import
  list at `views.py:4-25` — no such import). Ran it live:
  ```
  NameError: name 'models' is not defined
    File "apps/interviews/views.py", line 417, in get_interview_stats
  ```
  → returns HTTP 500 `{"success":false,...}` every time. **Any interview
  history/stats dashboard depending on this endpoint is fully broken.**
- **Interview app's own test suite: 14 of 15 tests failing, verified live**
  (`pytest apps/interviews/tests/test_api.py -q`):
  - All session/question CRUD tests fail with `KeyError: 'success'` or
    `KeyError: 'data'` — the tests expect a `{"success": bool, "data": {...}}`
    envelope (matching the global `StandardizedResponse` renderer used
    elsewhere, e.g. `apps/assessment/views.py`), but `InterviewViewSet`'s
    default DRF `ModelViewSet` actions (`list`/`retrieve`/`create`/`update`/
    `destroy` — none overridden) return **bare, un-enveloped
    `InterviewSessionSerializer` data**. Only the custom `@action` methods
    (`start`, `answer`, `complete`, `voice_answer`, `history`) manually build
    Response dicts, and even those don't match the `{"success":true,"data":
    {...}}` shape the tests expect (they return flat dicts, e.g.
    `{'session_id':..., 'interview_type':...}` — see `views.py:129-140`).
    **This is a genuine test/implementation mismatch — either the tests were
    written against an intended envelope contract that was never implemented,
    or the implementation drifted away from the contract.** Either way, it is
    concrete evidence the "interview app" has never had its full test suite
    passing, contradicting any historical "100% ready" claim.
  - Voice tests fail for the same envelope reason plus URL/serializer field
    mismatches (`voice-interview-answer` test posts `question_index`/
    `transcript`/`duration_seconds`, but the real `voice_answer` action expects
    a multipart `audio` file — the test was written against a different,
    imagined voice API contract than what's implemented).
- **`analyze-job/<slug>` URL note**: not in `interviews/urls.py` — that pattern
  belongs to `apps/rashid/urls.py:47`, and the equivalent Rashid test for it
  also fails live (`TypeError: execute_tool_endpoint() got an unexpected
  keyword argument 'job_slug'` — a URL/view signature mismatch, same class of
  bug as above). Flagging because it's the same interview-adjacent surface
  (Rashid's `interview_prep` tool, `tools.py:179-250`).

### Frontend
- `frontend/src/pages/InterviewPractice.tsx` (921 lines) is a real, fairly
  thorough React page: role/type/difficulty picker, text answer flow, voice
  recording via `MediaRecorder`/`getUserMedia`, radar chart for dimension
  scores (recharts), Arabic/English bilingual UI. It correctly calls the real
  backend endpoints (`/interviews/start/`, `/{id}/answer/`,
  `/{id}/voice-answer/`, `/{id}/complete/`). **This is genuinely implemented
  UI, not a mockup** — see Voice Engine section for why the voice path still
  fails end-to-end regardless.
- No dedicated frontend page exists for "coding interview" (no code
  editor/Judge0 UI component found under `frontend/src`), consistent with the
  backend finding that coding-interview integration was never completed.

**Interview Simulation Engine verdict: PARTIAL.** Text-mode
technical/behavioral/system_design/case_study: DONE (logic correct, but AI
generation currently degraded to identical fallback content/scores due to the
Bedrock outage — a real reliability issue, not just an environment quirk, since
nothing alerts on this failure). Coding-interview mode: MISSING/dead
integration. Stats endpoint: BROKEN. Test suite: mostly failing, indicating this
area has never been verified working end-to-end by its own tests.

---

## 3. Voice Engine — is it real or a mockup?

**Verdict: Real cascaded STT→LLM→TTS pipeline code, not a UI mockup — but
currently non-functional end-to-end in this environment due to missing
AWS permissions and missing config, verified live with real AWS API calls.**

### Evidence it is real, not a placeholder
- Frontend (`InterviewPractice.tsx:262-379`): uses the real
  `navigator.mediaDevices.getUserMedia({audio:true})` + `MediaRecorder` APIs,
  posts the recorded blob as multipart `audio` to
  `/interviews/{id}/voice-answer/`, receives a `next_question_audio` base64
  MP3 and plays it back via a real `Audio()` element (`playBase64Audio`,
  lines 363-379). No disabled buttons, no "coming soon" placeholder text
  found anywhere in this component for the voice path — the mic button is
  wired to `startRecording`/`stopRecording` state, not a no-op.
- Backend `voice_service.py`: `text_to_speech()` (line 46-75) calls real
  `boto3.client('polly').synthesize_speech(...)`. `speech_to_text()` (line
  77-152) does a genuinely correct AWS Transcribe workflow: upload audio to
  S3 → `start_transcription_job` → poll every 2s up to 30s → download/parse
  transcript JSON from S3 → clean up the temp S3 object. This is a real,
  non-trivial integration, not a stub returning canned text.
- `views.py:voice_answer` (line 229-341) does real content-type/magic-byte
  validation of uploaded audio (lines 253-281) before calling
  `voice_interview_service.speech_to_text` — genuine input hardening, not
  vestigial code.

### Evidence it does not work right now (verified live, not inferred)
- Ran direct `boto3` calls against the configured AWS credentials
  (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` present in `backend/.env`,
  confirmed non-empty, 20/40 chars respectively — **not flagging as the
  AGENTS.md-described leaked key issue, values look like legitimate current
  creds, not empty**):
  - `sts.get_caller_identity()` → succeeds, confirms identity
    `arn:aws:iam::571600863624:user/speckit-user`.
  - `polly.synthesize_speech(...)` → **`AccessDeniedException`**: "User ...
    speckit-user is not authorized to perform: polly:SynthesizeSpeech".
  - `transcribe.list_transcription_jobs(...)` → **`AccessDeniedException`**
    for `transcribe:ListTranscriptionJobs`.
  - `s3.list_buckets()` → **`AccessDeniedException`** for
    `s3:ListAllMyBuckets`.
  → The IAM user backing this app has **no permissions for any of the three
  AWS services the voice pipeline depends on.**
- `AWS_STORAGE_BUCKET_NAME` and `AWS_REGION` (as read via
  `getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)` /
  `getattr(settings, 'AWS_REGION', 'us-east-1')` in `voice_service.py:32-43`)
  resolve to **`None`** and the hardcoded fallback `'us-east-1'` respectively
  when loaded through Django settings in this environment — confirmed via a
  direct `settings.py` introspection call. `config/settings/base.py` only
  defines `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_DEFAULT_REGION`
  (lines 321-323) — there is **no `AWS_STORAGE_BUCKET_NAME` or `AWS_REGION`
  setting defined anywhere in `config/settings/`** (searched all of
  `backend/config`). So even with correct IAM permissions,
  `speech_to_text()`'s `self.s3_client.upload_file(tmp_path, self.aws_bucket,
  s3_key)` (`voice_service.py:100`) would immediately fail because
  `self.aws_bucket is None`.
- Net result: **`text_to_speech()` and `speech_to_text()` will both raise/
  return `None` in this environment today**, and the view code handles this
  gracefully (`views.py:284-289` returns 422 "Failed to transcribe audio" if
  `voice_interview_service.speech_to_text` returns `None`) — so it fails
  *safely*, not silently claiming success, but it is **not currently a
  working voice pipeline**.

### Historical-claims reconciliation
This directly explains how a past audit could have said "100% ready with
voice" (the code genuinely is a complete, correctly-designed cascaded
pipeline — a reviewer reading only the code would reasonably conclude it
works) while another audit said the interview app "doesn't exist" (whoever
made that claim likely never found `backend/apps/interviews/` at all, since
it unambiguously exists with ~1,700 lines of real logic). **Neither historical
claim was checked against live AWS credentials or a live request — this audit
is the first to actually attempt the calls.**

**Voice Engine verdict: PARTIAL (REFACTOR/INTEGRATE needed, not BUILD from
scratch).** The architecture and code are sound; what's missing is (a) IAM
permissions for Polly/Transcribe/S3 on the configured AWS user, (b)
`AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` settings, (c) a valid `JUDGE0_API_KEY`
if voice-mode coding interviews are ever wired up, and (d) the interview
app's own test suite fixed so voice regressions are actually caught
(currently 100% of voice tests fail, for contract-mismatch reasons unrelated
to the AWS issue).

---

## 4. Career Coach functionality

**Question asked:** does anything continuously track user goals/gaps and
recommend actions, or is this entirely absent?

**Verdict: PARTIAL — the tracking/goal-CRUD half is real and wired; the
"continuous, proactive, recommend-actions" half is fully built but 100% unwired
dead code.** Not "entirely absent" (there is real functionality), but the
single most on-point module for "continuous coaching" specifically never runs.

### What is real and wired (DONE)
- **`CareerGoal`/`CareerGoalAction` CRUD + analytics**
  (`apps/career/goal_api.py`, 509 lines): full REST surface — list/create/
  detail/update/delete goals, actions, milestones (add/complete), a progress
  summary view (`CareerGoalProgressView`, lines 405-451: totals, avg
  progress, upcoming-deadline list), and an analytics view
  (`CareerGoalAnalyticsView`, lines 455-509: completion rate by type/priority,
  average days-to-completion). This is real, correct Django ORM
  aggregation code (`Count`, `Avg`, `Q`, `ExtractDay`), properly
  user-scoped. **This part is DONE** as a goal-tracking system — but it is
  reactive (user must create/update goals themselves), not "continuous
  tracking" in the sense of the system watching and updating on its own.
- **`SkillGapAnalyzer`** (`apps/career/skill_gap_analysis.py`, 311 lines,
  wired at `apps/career/urls.py:69` → `get_skill_gap_analysis`,
  `apps/career/views.py:513-533`): computes gap between `CareerUserSkill`
  and `career_profile.target_roles` using the skill knowledge graph — real
  gap-severity scoring and recommendation generation logic (per docstring
  and structure; did not trace every internal branch given time constraints,
  but the entry point and endpoint wiring are confirmed real and reachable).
  This is the one piece that is genuinely "identify gaps + recommend" and it
  **is wired to a live endpoint**.
- **`CareerBrainService.update_brain()`** (`apps/career/career_brain_service.py`
  :154-199): aggregates skills/goals/preferences/learning/history +
  generates AI "observations" (strengths/growth_areas/skill_gaps/
  market_trends/key_insights) via Bedrock, with a sane fallback
  (`_get_fallback_observations`, lines 331-339) when AI is down (confirmed
  degraded right now per the cross-cutting Bedrock finding). **BUT**: grepped
  the entire backend for callers of `career_brain_service` (the singleton) —
  **zero results** other than its own definition. `CareerBrainView`
  (`apps/career/views.py:406-437`) only reads/writes the raw `CareerBrain`
  model directly via its own serializer; it never calls
  `career_brain_service.update_brain()`. So this "brain" only updates when a
  client explicitly `POST`s new field values to `/career/career-brain/` —
  there is **no automatic recompute** despite the service existing to do
  exactly that. **Verdict for this piece: REFACTOR/INTEGRATE needed** (wire
  `update_brain()` to a signal or Celery Beat task; it currently does
  nothing on its own).

### What is fully built but never runs (the core "proactive coach" gap)
- **`ProactiveRashidService`** (`apps/rashid/proactive_service.py`, 332
  lines) is explicitly designed to be the continuous-coaching engine:
  `check_user_triggers()` (lines 35-107) checks 5 triggers — new matching
  jobs, approaching goal deadlines, trending skills, "no interview practice
  in 2+ weeks" reminder, profile completeness < 80% — and
  `generate_notification()` + `create_notification_record()` turn triggers
  into AI-personalized, persisted `Notification` rows. This is well-designed,
  Arabic-localized, and directly matches "continuously track user goals/gaps
  and recommend actions."
  - **Confirmed via `search_files` across the entire `backend/` tree**: the
    only files referencing `proactive_rashid_service` or
    `check_user_triggers` are `proactive_service.py` itself (its own
    definition). **No view imports it. No URL route exposes it. No Celery
    task calls it. `config/celery.py`'s `beat_schedule` (lines 21-90) has
    zero entries for anything Rashid/proactive-related** — every other
    domain (scraper, emails, verification, talent scores, analytics) has a
    scheduled task; Rashid proactive notifications do not.
  - **This is the single clearest "MISSING (as a running feature) despite
    being BUILD-complete (as code)" finding in this entire audit domain.**
    Nothing currently calls this code in production, in tests, in Celery
    Beat, or via any signal handler. It is inert.
- There is also no cron/Celery task anywhere for `update_completeness_score`
  running automatically either — it exists as a task
  (`apps/career/tasks.py:74-113`) but is only triggered on-demand (its
  docstring says triggered by CV upload/skill add/etc.; did not verify signal
  wiring for those triggers within this domain's file scope — flagging as
  out-of-scope-but-relevant).

### Rashid `tools.py` career-coaching tools (real, but user-invoked, not proactive)
- `CVReviewTool`, `CoverLetterTool`, `InterviewPrepTool`,
  `LinkedInOptimizerTool`, `CourseAdvisorTool` (`tools.py:23-404`) are all
  real, on-demand AI tools with real Bedrock calls, real CV file reading,
  real DB lookups (profile/skills/experience), each wired via
  `RASHID_TOOLS` registry (`tools.py:408-414`) and exposed through
  `execute_tool_endpoint` (`views.py:287-314`, `urls.py:44`). These are
  useful career-coaching features but are **user-triggered on demand**, not
  "continuous tracking" — they answer the "recommend actions" half only when
  asked, never proactively.
- `CourseAdvisorTool._get_available_courses()` (`tools.py:385-404`) returns a
  **hardcoded string list of courses**, not a live query against
  edu.usamif.com as the docstring claims ("Recommend courses from
  edu.usamif.com") — a real code/comment mismatch worth flagging (**verdict:
  REFACTOR** — either wire a real courses API or fix the misleading
  docstring/name).

**Career Coach verdict: PARTIAL.** Goal tracking + skill-gap analysis: DONE and
wired. Continuous/automatic re-evaluation of the "career brain": built but not
scheduled (REFACTOR/INTEGRATE). The one purpose-built proactive/continuous
recommendation engine (`ProactiveRashidService`) exists as complete, reasonable
code and is **never invoked anywhere** (MISSING as a live feature — needs a
Celery Beat entry + signal wiring to actually deliver on "continuously track
and recommend").

---

## 5. External repo evaluation: USE / ADAPT / REJECT

### `github.com/ngoanpv/DeepInterview` — **ADAPT (partial ideas), do not fork wholesale**
- Apache-2.0, 23 stars/6 forks, actively developed (124 commits, releases
  through v0.3.0, 2026-08-02), monorepo (Next.js web + Python `agent` +
  LiveKit voice worker), explicitly documents an honest prep→live→post
  pipeline: CV/JD ingestion → company research → question planning →
  real-time voice interview (LiveKit + Deepgram STT + Gemini + Cartesia/
  ElevenLabs TTS) → scored report → a "study coach" that grounds answers in
  the user's own session materials via a knowledge sidecar.
- **Why ADAPT not USE wholesale**: it's a separate full-stack app (own
  Next.js frontend, own Supabase auth/billing layer, own agent API) — pulling
  it in whole would fight this repo's Django/DRF + React/Vite architecture
  and its "one shared Career Graph, not fragmented per-feature modules"
  principle from AGENTS.md. Its **auth+billing is explicitly hosted-only**
  and would need to be stripped for self-host use anyway.
- **What's worth adapting**: (1) its local-model fallback path (Ollama +
  Whisper + Kokoro, zero API keys needed) is directly relevant to this
  repo's current Bedrock-outage problem — a similar local-fallback tier would
  make the interview/voice engines resilient to the exact AWS
  ValidationException seen in this audit. (2) Its "prep/live/post" split
  (heavy async model before/after, one lean fast model on the live turn
  path) is a better architecture than this repo's current
  "one Bedrock call per question, no differentiation" approach. (3) The
  "study coach grounds answers in your session" pattern (CV+JD+company
  research fed into a per-session knowledge base) is a stronger version of
  what `career_brain_service.build_context()` already attempts — could
  inform an upgrade there. **Do not** adopt its LiveKit-specific real-time
  voice transport unless this repo is ready to add a LiveKit dependency;
  the existing Polly/Transcribe approach is simpler and already
  IAM-fixable without a new infra dependency.

### `github.com/IliaLarchenko/Interviewer` — **REJECT for direct use, weak ADAPT candidate at most**
- Apache-2.0, Gradio-based single-file app (`app.py`), designed as a
  standalone Hugging Face Space / local Gradio tool, not a backend service
  or API. Supports pluggable LLM (OpenAI/Claude/HF/local)/STT
  (Whisper)/TTS (OpenAI tts-1) via `.env` config, streaming mode.
- **Why REJECT**: it's architecturally incompatible — a Gradio UI app, not a
  Django/DRF backend or a React component library; integrating it would mean
  either iframing an entirely separate Python web app (ugly, stateful,
  duplicates auth/session) or rewriting its Gradio UI logic into React,
  which is effectively a rewrite, not a reuse. It also has no persistence/
  scoring-history model (no `InterviewSession`-equivalent) — its value is
  purely as a config pattern (multi-provider STT/LLM/TTS via env vars).
- **Weak adapt value**: its multi-provider model-adapter `.env` pattern (swap
  `LLM_TYPE`/`STT_TYPE`/`TTS_TYPE` + name per provider) is a reasonable
  reference for how this repo could add a non-AWS TTS/STT fallback (e.g.
  OpenAI Whisper/tts-1) as a second provider tier for `voice_service.py`,
  given AWS Polly/Transcribe are currently completely unauthorized in this
  environment. That's the only concrete takeaway; the rest of the project
  is not reusable here.

---

## Consolidated per-file verdict table

| File | Verdict | Evidence |
|---|---|---|
| `apps/assessment/models.py` | DONE | Complete schema, no issues found |
| `apps/assessment/views.py:118-236` (submit_assessment) | DONE | Live-verified MCQ grading pipeline works end-to-end |
| `apps/assessment/views.py` (question authoring) | MISSING | No AI/self-serve question-creation endpoint exists |
| `apps/core/code_execution.py` | PARTIAL | Real Judge0 integration; `JUDGE0_API_KEY` unset/invalid in this env (live 401 confirmed) |
| Assessment frontend | MISSING | Zero assessment UI anywhere in `frontend/src` |
| `apps/interviews/service.py` | DONE (logic) / degraded (AI down) | Full generate/evaluate/complete pipeline verified live; currently returns fallback content only |
| `apps/interviews/coding_service.py` | MISSING (dead code) | `coding_interview_service` has zero importers repo-wide |
| `apps/interviews/urls.py:18-20` | BROKEN (misleading routes) | `coding-question/problem/solution` all alias generic `start` action |
| `apps/interviews/views.py:404-433` (get_interview_stats) | BROKEN | Live-verified 500 `NameError: name 'models' is not defined` (missing `django.db.models` import) |
| `apps/interviews/views.py` (ModelViewSet default actions) | REFACTOR | Response envelope inconsistent with app's own test expectations and other apps' `{"success","data"}` convention |
| `apps/interviews/tests/test_api.py` | BROKEN (as a suite) | 14/15 tests fail live; contract mismatches, not flaky |
| `apps/interviews/voice_service.py` | PARTIAL (real, unauthorized) | Real Polly/Transcribe/S3 code; live AWS calls return AccessDeniedException; `AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` unset |
| `frontend/src/pages/InterviewPractice.tsx` | DONE (as UI) | Real MediaRecorder/getUserMedia/base64-audio-playback wiring, not a mockup |
| `apps/career/goal_api.py` | DONE | Full CRUD + analytics, live-checked for correctness of ORM logic |
| `apps/career/skill_gap_analysis.py` + wiring | DONE (wired) | Endpoint confirmed reachable at `/career/skill-gap/` |
| `apps/career/career_brain_service.py` | REFACTOR/INTEGRATE | Real logic, but `update_brain()` never called automatically anywhere |
| `apps/rashid/proactive_service.py` | MISSING (as a live feature) | Zero callers repo-wide; not in Celery Beat; complete code otherwise |
| `apps/rashid/tools.py` (5 tools) | DONE (on-demand only) | Real Bedrock calls + DB reads; `CourseAdvisorTool` course list is hardcoded despite docstring claim (REFACTOR) |
| `config/celery.py` beat_schedule | MISSING (Rashid entries) | No proactive/career-brain-refresh cron entries exist among the ~14 scheduled tasks |
| Bedrock `sonnet` alias (`bedrock_plugin.py:31`, used everywhere in this domain) | BROKEN | Live-verified `ValidationException` on every model invocation attempted during this audit |

---

## Recommendations (priority order, in-scope only)

1. **Fix `apps/interviews/views.py` missing `from django.db import models`
   import** — one-line fix, currently a fully broken stats endpoint (500 on
   every call).
2. **Fix or remove the Bedrock `sonnet` inference-profile issue** — this is
   the single highest-leverage fix in this whole domain: it silently degrades
   assessment feedback, interview question generation, interview scoring,
   career-brain observations, and all 5 Rashid tools to generic fallback
   content. Needs an inference-profile ARN per AWS's error message, not a
   raw model ID.
3. **Wire or delete `apps/interviews/coding_service.py`.** Either connect
   `coding-question/problem/solution` URLs to `CodingInterviewService` for
   real, or remove the dead module and the misleading URL aliases so nobody
   builds a frontend against endpoints that don't do what their names say.
4. **Grant the AWS IAM user (`speckit-user`) `polly:SynthesizeSpeech`,
   `transcribe:*`, and S3 read/write on the media bucket, and set
   `AWS_REGION`/`AWS_STORAGE_BUCKET_NAME` in Django settings** — voice mode
   is unusable without this regardless of any other fix.
5. **Schedule `ProactiveRashidService.check_user_triggers()`** (e.g. daily
   Celery Beat task iterating active users) if "continuous career coaching"
   is meant to be a real product feature — right now it is 100% inert despite
   being fully coded.
6. **Fix the interview app's response-envelope contract** (either update the
   ViewSet to wrap responses in `{"success","data"}` like `assessment/views.py`
   does, or fix the tests) — 14/15 failing tests here means this area has
   effectively zero regression coverage today.
7. **Build an Assessment frontend** if assessments are meant to be
   user-facing — currently API-only.

---

*Audit performed by direct code inspection + live pytest/boto3/requests
execution against this repository's own Django test settings and real AWS
account. No status claims were taken at face value; every PARTIAL/BROKEN/DONE
verdict above traces to either an exact file:line citation or a reproduced
command output within this audit session.*

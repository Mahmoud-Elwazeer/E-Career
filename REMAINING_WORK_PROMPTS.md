# Remaining Work — Cline Prompts
## E-Career Platform — August 7, 2026

Each phase below contains ready-to-paste prompts for Cline. Execute them in order.

---

## PHASE A: Critical Configuration (30 minutes)

### Prompt A1: Typesense & Qdrant API Keys
```
On the production server at /var/www/usam/backend/.env, add the following environment variables:

TYPESENSE_API_KEY=<your-actual-typesense-key>
QDRANT_API_KEY=<your-actual-qdrant-key>

Then restart the service:
sudo systemctl restart usam.service
```
> ⚠️ This is manual — you need to get the actual keys from your Typesense and Qdrant instances.

---

## PHASE B: ESCO & Skills Data Import (12 hours)

### Prompt B1: ESCO Dataset Import Command
```
In the E-Career Django project (backend/), create a management command at backend/apps/skills/management/commands/import_esco.py that:

1. Downloads the ESCO skills CSV from https://ec.europa.eu/esco/portal/api (or loads from a local file path argument)
2. Parses the CSV which has columns: conceptUri, preferredLabel, altLabels, description, skillType, reuseLevel
3. Creates/updates Skill model instances in apps/skills/models.py (the model already exists with fields: id, name, name_ar, description, esco_uri, skill_type, category)
4. Maps skillType to our category field
5. Handles duplicates by esco_uri (update if exists)
6. Logs progress every 1000 records
7. Supports --file argument for local CSV and --limit for testing

Run with: python manage.py import_esco --file /path/to/esco_skills.csv

The Skill model is in backend/apps/skills/models.py. Check the existing model fields before creating the command.
```

### Prompt B2: O*NET Dataset Import
```
In the E-Career Django project (backend/), create a management command at backend/apps/skills/management/commands/import_onet.py that:

1. Loads O*NET occupation data from a local file (argument --file)
2. O*NET data has columns: O*NET-SOC Code, Title, Description
3. Creates Occupation model instances (create the model in apps/skills/models.py if it doesn't exist):
   - Fields: id (UUID), onet_code, title, title_ar, description, category
4. Also import the O*NET skills-to-occupation mapping file (--skills-file argument)
5. Create a SkillOccupationLink model (skill FK, occupation FK, importance, level)
6. Handle duplicates by onet_code

The skills app is at backend/apps/skills/. Check existing models first.
```

### Prompt B3: ESCO-O*NET Mapping
```
In the E-Career Django project, create a management command at backend/apps/skills/management/commands/map_esco_onet.py that:

1. For each O*NET skill, find the closest ESCO skill by name similarity (using difflib.SequenceMatcher or Levenshtein)
2. Create/update a mapping table: EscoOnetMapping (esco_skill FK, onet_occupation FK, confidence_score float)
3. Only create mappings where confidence > 0.8
4. Log statistics: total mapped, average confidence, unmapped count
5. Support --threshold argument to adjust confidence cutoff

This links our ESCO skills taxonomy with O*NET occupations for career path recommendations.
```

---

## PHASE C: Embeddings & Semantic Search (12 hours)

### Prompt C1: Generate Job Embeddings
```
In the E-Career Django project, create a management command at backend/apps/vectors/management/commands/generate_job_embeddings.py that:

1. Fetches all active jobs from apps/jobs/models.py (Job model, status='active')
2. For each job, creates an embedding text: "{title} {company_name} {description} {skills}" 
3. Uses the existing Cohere embed plugin at backend/apps/vectors/cohere_plugin.py (or check backend/apps/search/ for the embedding service)
4. Stores embeddings in Qdrant using the existing plugin at backend/apps/vectors/qdrant_plugin.py
5. Collection name: "jobs"
6. Payload includes: job_id, title, company_name, location, salary_min, salary_max
7. Processes in batches of 100 to avoid memory issues
8. Supports --batch-size and --limit arguments
9. Logs progress and handles errors gracefully (skip failed jobs, continue)

Check the existing Qdrant plugin and Cohere plugin code first to understand the API.
```

### Prompt C2: Generate User Profile Embeddings
```
In the E-Career Django project, create a management command at backend/apps/vectors/management/commands/generate_user_embeddings.py that:

1. Fetches all users who have a career_profile (from apps/career/models.py CareerProfile)
2. For each user, creates embedding text from their profile: "{skills} {experience} {education} {interests} {target_roles}"
3. Uses the existing embedding service (check backend/apps/vectors/ or backend/apps/search/)
4. Stores in Qdrant collection "users"
5. Payload: user_id, name, skills list, experience_years
6. Batch processing with progress logging
7. Also create a Celery task at backend/apps/vectors/tasks.py that regenerates a single user's embedding (called when profile updates)

Check the existing Qdrant and Cohere plugins first.
```

### Prompt C3: Semantic Search Endpoint
```
In the E-Career Django project, create a semantic search API endpoint:

1. Add to backend/apps/search/views.py (or create backend/apps/vectors/views.py):
   - GET /api/v1/search/semantic/?q=<query>&limit=20
   - Takes natural language query, generates embedding, searches Qdrant "jobs" collection
   - Returns ranked job results with similarity scores
   - Supports filters: location, salary_min, salary_max, employment_type
   
2. Add a hybrid search endpoint:
   - GET /api/v1/search/hybrid/?q=<query>&limit=20
   - Combines Typesense keyword search (weight 0.3) + Qdrant semantic search (weight 0.7)
   - Returns merged, deduplicated, re-ranked results

3. Add a "Similar Jobs" endpoint:
   - GET /api/v1/jobs/<id>/similar/?limit=5
   - Gets the job's embedding from Qdrant, finds nearest neighbors
   - Excludes the source job

4. Register URLs in the appropriate urls.py
5. Add appropriate serializers
6. Require authentication for all endpoints

Check existing search views and Qdrant plugin for patterns.
```

---

## PHASE D: GDPR Compliance (12 hours)

### Prompt D1: GDPR Data Export
```
In the E-Career Django project, create GDPR data export functionality:

1. Create backend/apps/core/gdpr.py with:
   - class GDPRExportService:
     - export_user_data(user_id) -> dict: collects ALL user data across all apps
     - Includes: profile, career data, saved jobs, applications, interview sessions, notifications, events, AI conversations
     - Returns a structured dict that can be serialized to JSON
     
2. Create a Celery task at backend/apps/core/tasks.py:
   - task: generate_gdpr_export(user_id)
   - Generates the export, saves as JSON file to media/gdpr_exports/{user_id}_{timestamp}.json
   - Sends email notification when ready with download link
   - Auto-deletes the file after 7 days

3. Create API endpoint:
   - POST /api/v1/core/gdpr/export/ — requests export (rate limited: 1 per day)
   - GET /api/v1/core/gdpr/export/status/ — check if export is ready
   - GET /api/v1/core/gdpr/export/download/ — download the export file

4. Register in backend/apps/core/urls.py
5. Add rate limiting (use the existing rate_limiting middleware pattern)

Check all models across apps to ensure complete data collection: accounts, users, career, jobs, rashid, interviews, notifications, resume, events, analytics.
```

### Prompt D2: GDPR Data Deletion
```
In the E-Career Django project, create GDPR data deletion (right to be forgotten):

1. Add to backend/apps/core/gdpr.py:
   - class GDPRDeletionService:
     - delete_user_data(user_id, confirmation_token) -> dict
     - Deletes ALL user data across all apps in correct order (respecting FK constraints)
     - Anonymizes data that must be retained for legal reasons (e.g., completed transactions)
     - Returns summary of what was deleted
     
   - Deletion order:
     a. AI conversations and messages (rashid)
     b. Interview sessions and questions
     c. Notifications and preferences
     d. Resume data and exports
     e. Career goals, actions, milestones
     f. Career profile, skills, learning history
     g. Saved jobs, applications, alerts
     h. Events and analytics
     i. User profile
     j. Finally: User account (anonymize email to deleted_{uuid}@deleted.local)

2. Create API endpoints:
   - POST /api/v1/core/gdpr/delete/request/ — sends confirmation email with token
   - POST /api/v1/core/gdpr/delete/confirm/ — with token, executes deletion
   - Requires password re-confirmation
   - 72-hour cooling off period before actual deletion

3. Create Celery task for the actual deletion (runs after cooling off)
4. Log all GDPR actions for audit trail (keep log even after deletion)

Check all models to ensure nothing is missed. Use Django's on_delete CASCADE where possible.
```

---

## PHASE E: CV Parsing Pipeline (8 hours)

### Prompt E1: CV Parser Service
```
In the E-Career Django project, create a CV parsing pipeline:

1. Install dependencies: add pdfplumber, python-docx, and docling to backend/requirements/base.txt

2. Create backend/apps/career/cv_parser.py:
   - class CVParserService:
     - parse_pdf(file_path) -> dict: uses pdfplumber for text extraction
     - parse_docx(file_path) -> dict: uses python-docx
     - parse_image(file_path) -> dict: uses docling for OCR
     - extract_structured_data(raw_text) -> dict:
       Uses AWS Bedrock Claude to extract:
       {
         "name": str,
         "email": str,
         "phone": str,
         "summary": str,
         "experience": [{"title", "company", "start_date", "end_date", "description"}],
         "education": [{"degree", "institution", "year"}],
         "skills": [str],
         "languages": [str],
         "certifications": [str]
       }
     - map_skills_to_esco(skills: list[str]) -> list[dict]:
       Matches extracted skill names to ESCO skills in the database using fuzzy matching

3. Create API endpoint:
   - POST /api/v1/career/cv/upload/ — accepts PDF/DOCX file upload
   - Parses the file, extracts data, maps skills
   - Updates the user's CareerProfile.cv_parsed_data
   - Updates CareerUserSkill records from extracted skills
   - Returns the structured extraction

4. Create Celery task for async processing (large files)
5. Add file size limit (10MB) and type validation

The CareerProfile model is in backend/apps/career/models.py with fields cv_file and cv_parsed_data (JSONField).
The Bedrock client is in backend/apps/rashid/ — check how it calls Claude.
```

---

## PHASE F: Testing (10 hours)

### Prompt F1: Core API Tests
```
In the E-Career Django project, create comprehensive API tests:

1. Create backend/apps/jobs/tests/test_api.py:
   - Test job list endpoint (pagination, filtering)
   - Test job detail endpoint
   - Test job search
   - Test saved jobs CRUD
   - Test unauthenticated access returns 401

2. Create backend/apps/accounts/tests/test_auth.py:
   - Test registration
   - Test login (JWT token returned)
   - Test token refresh
   - Test password reset flow
   - Test invalid credentials

3. Create backend/apps/career/tests/test_api.py:
   - Test career profile CRUD
   - Test talent score calculation
   - Test career goals CRUD
   - Test goal actions and milestones
   - Test profile completeness
   - Test skill gap analysis

4. Create backend/apps/interviews/tests/test_api.py:
   - Test start interview session
   - Test submit answer
   - Test get session results
   - Test list sessions

5. Create backend/apps/rashid/tests/test_api.py:
   - Test create conversation
   - Test send message (mock Bedrock response)
   - Test get conversations list
   - Test get messages

Use Django REST Framework's APITestCase. Create a base test class with user setup (create test user, get JWT token). Mock external services (Bedrock, Typesense, Qdrant).

Run with: python manage.py test
```

### Prompt F2: Frontend Tests
```
In the E-Career frontend (frontend/), set up and create tests:

1. Install: npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

2. Add to vite.config.ts:
   test: {
     globals: true,
     environment: 'jsdom',
     setupFiles: './src/test/setup.ts',
   }

3. Create frontend/src/test/setup.ts with testing-library setup

4. Create tests for critical pages:
   - src/pages/__tests__/Jobs.test.tsx — renders job list, handles loading state
   - src/pages/__tests__/Login.test.tsx — renders form, handles submit
   - src/hooks/__tests__/use-auth.test.tsx — login/logout flow
   - src/components/__tests__/RashidWidget.test.tsx — renders widget

5. Add test script to package.json: "test": "vitest"

Mock API calls with MSW or simple jest.mock. Focus on rendering without crashes and basic user interactions.
```

---

## PHASE G: Daily Liveness & Scrapers (15 hours)

### Prompt G1: Job Liveness Checks
```
In the E-Career Django project, create automated job liveness checking:

1. Create backend/apps/verification/tasks.py:
   - @shared_task daily_liveness_check():
     - Gets all active jobs older than 7 days
     - For each job, sends HEAD request to source_url
     - If 404 or connection error: mark job as "expired" (status='expired')
     - If redirect to generic careers page: mark as "likely_expired"
     - If 200: update last_verified_at timestamp
     - Process in batches of 50 with 1-second delay between batches
     - Log results: total checked, expired, still active

2. Create backend/apps/verification/tasks.py:
   - @shared_task weekly_reverification():
     - Re-verifies all "active" jobs
     - Updates legitimacy_score based on response
     - Sends notification if many jobs from one source are dead

3. Register tasks in Celery Beat schedule (backend/config/settings/base.py or celery.py):
   - daily_liveness_check: runs daily at 3:00 AM UTC
   - weekly_reverification: runs every Sunday at 2:00 AM UTC

Check the existing Job model for the status field and source_url field.
Check how Celery Beat is configured in the project (look at config/celery.py and CELERY_BEAT_SCHEDULE).
```

### Prompt G2: SmartRecruiters Scraper
```
In the E-Career Django project, create a SmartRecruiters ATS scraper:

1. Create backend/apps/scraper/scrapers/smartrecruiters.py:
   - class SmartRecruitersScraper:
     - Base URL pattern: https://careers.smartrecruiters.com/{company_name}
     - API endpoint: https://api.smartrecruiters.com/v1/companies/{id}/postings
     - parse_job_listing(data) -> dict matching Job model fields
     - scrape_company(company_slug) -> list[dict]
     - Maps fields: title, location, description, department, experience_level

2. Create backend/apps/scraper/scrapers/workable.py:
   - class WorkableScraper:
     - Base URL pattern: https://apply.workable.com/j/{job_id}
     - API: https://{company}.workable.com/spi/v3/jobs
     - parse_job_listing(data) -> dict
     - scrape_company(company_subdomain) -> list[dict]

3. Add scraper registration in backend/apps/scraper/ (check existing scraper patterns)
4. Create Celery tasks for each scraper
5. Add to CELERY_BEAT_SCHEDULE for daily runs

Check the existing scraper app structure first — there should be a base scraper class or pattern to follow.
```

---

## PHASE H: Employer AI Features (14 hours)

### Prompt H1: AI Candidate Ranking
```
In the E-Career Django project, create AI-powered candidate ranking for employers:

1. Create backend/apps/employers/ranking_service.py:
   - class CandidateRankingService:
     - rank_candidates(job_id, candidate_ids) -> list[dict]:
       - Gets job requirements (skills, experience, education)
       - Gets each candidate's profile (skills, experience, career score)
       - Uses AWS Bedrock Claude to generate a ranking with explanations
       - Returns: [{user_id, rank, score, match_reasons, gaps}]
     
     - generate_shortlist(job_id, max_candidates=10) -> list[dict]:
       - Auto-selects top candidates based on:
         a. Skill match percentage
         b. Experience relevance
         c. Location match
         d. Salary expectations alignment
       - Returns ranked shortlist with AI explanations

2. Create API endpoints in backend/apps/employers/views.py:
   - POST /api/v1/employers/jobs/<job_id>/rank/ — rank specific candidates
   - GET /api/v1/employers/jobs/<job_id>/shortlist/ — auto-generate shortlist
   - GET /api/v1/employers/jobs/<job_id>/compare/?candidates=id1,id2,id3 — side-by-side comparison

3. Add serializers and URL routes
4. Only accessible to employer users who own the job posting

Check existing employer models in backend/apps/employers/models.py and the Bedrock client usage in backend/apps/rashid/.
```

---

## PHASE I: Enhanced Rashid AI (8 hours)

### Prompt I1: Career Brain Integration
```
In the E-Career Django project, enhance Rashid AI with Career Brain context:

1. The CareerBrain model already exists in backend/apps/career/models.py. Create backend/apps/career/career_brain_service.py:
   - class CareerBrainService:
     - build_context(user_id) -> str:
       Collects user's full career context into a prompt-ready string:
       - Current role and experience
       - Skills (with proficiency levels)
       - Career goals and progress
       - Recent job searches and saves
       - Interview performance trends
       - Skill gaps identified
       - Market trends relevant to their field
     
     - update_brain(user_id):
       Updates the CareerBrain model with latest aggregated data
       Called by event consumers when user data changes

2. Integrate into Rashid's prompt in backend/apps/rashid/ (find where the system prompt is built):
   - Before sending to Bedrock, prepend the Career Brain context
   - This makes Rashid aware of the user's full career situation
   - Rashid can now proactively suggest: "I noticed you haven't worked on your goal X in 2 weeks"

3. Create a Celery task that updates Career Brain nightly for all active users

Check how Rashid builds prompts (look at backend/apps/rashid/service.py or similar) and the CareerBrain model fields.
```

### Prompt I2: Rashid Proactive Notifications
```
In the E-Career Django project, add proactive notifications from Rashid:

1. Create backend/apps/rashid/proactive_service.py:
   - class ProactiveRashidService:
     - check_user_triggers(user_id) -> list[dict]:
       Checks for notification-worthy events:
       - New jobs matching their saved searches (daily)
       - Career goal deadlines approaching (3 days before)
       - Skills trending in their target industry
       - Interview practice reminder (if none in 2 weeks)
       - Profile completeness < 80% reminder
       
     - generate_notification(user_id, trigger_type, context) -> str:
       Uses Bedrock Claude to generate a personalized, friendly notification message
       in Rashid's character voice

2. Create Celery task:
   - @shared_task check_proactive_triggers():
     Runs daily, checks all active users, creates notifications
   
3. Create notifications via the existing notifications app (apps/notifications/):
   - notification_type = "rashid_proactive"
   - Include the AI-generated message
   - Link to relevant page (job, goal, interview, etc.)

4. Register in Celery Beat: daily at 9:00 AM UTC

Check existing notification models and the Rashid service for patterns.
```

---

## PHASE J: Recommendations Engine (10 hours)

### Prompt J1: LightFM Recommendations
```
In the E-Career Django project, create a job recommendation engine using LightFM:

1. Add lightfm and scipy to backend/requirements/base.txt

2. Create backend/apps/intelligence/recommendation_service.py:
   - class RecommendationService:
     - build_interaction_matrix():
       Creates user-item interaction matrix from:
       - Job views (weight 1)
       - Job saves (weight 3)  
       - Job applications (weight 5)
       - Job dismissals (weight -2)
       Data from events app (apps/events/models.py)
     
     - build_item_features():
       Job features: location, industry, experience_level, skills, salary_range
     
     - build_user_features():
       User features: skills, experience_years, location, preferences
     
     - train_model():
       Trains LightFM hybrid model (collaborative + content-based)
       Saves model to media/models/lightfm_latest.pkl
     
     - get_recommendations(user_id, n=20) -> list[dict]:
       Returns top N job recommendations with scores
       Filters out already-seen jobs

3. Create Celery task:
   - @shared_task nightly_model_training():
     Retrains the model every night at 1:00 AM UTC

4. Create API endpoint:
   - GET /api/v1/recommendations/ — returns personalized job recommendations
   - GET /api/v1/recommendations/similar-users/ — "people like you applied to..."

5. Register in Celery Beat schedule

Check the events app for interaction tracking and existing recommendation views.
```

---

## PHASE K: Voice & Coding Interviews (30 hours)

### Prompt K1: Voice Interview Setup
```
In the E-Career Django project, add voice interview capability:

1. Add dependencies to requirements: boto3 (already there for Bedrock), websockets

2. Create backend/apps/interviews/voice_service.py:
   - class VoiceInterviewService:
     - text_to_speech(text, language='en') -> bytes:
       Uses AWS Polly to convert interviewer questions to audio
       Voice: "Matthew" for English, "Zeina" for Arabic
     
     - speech_to_text(audio_bytes, language='en') -> str:
       Uses AWS Transcribe (streaming) to convert user audio to text
     
     - process_voice_answer(session_id, audio_bytes):
       1. Transcribe audio to text
       2. Feed to existing interview evaluation service
       3. Generate next question
       4. Convert to speech
       5. Return: {transcript, evaluation, next_question_audio_url}

3. Create API endpoints:
   - POST /api/v1/interviews/<session_id>/voice/answer/ — upload audio, get response
   - GET /api/v1/interviews/<session_id>/voice/question/ — get current question as audio

4. Update InterviewSession model to support mode='voice'

5. Frontend: Create frontend/src/components/interview/VoiceRecorder.tsx:
   - Uses MediaRecorder API to capture microphone
   - Sends audio chunks to backend
   - Plays back AI interviewer audio responses
   - Visual waveform indicator

Check AWS credentials in .env and existing Bedrock client for AWS SDK patterns.
```

### Prompt K2: Coding Interview with Judge0
```
In the E-Career Django project, add coding interview capability:

1. Add docker service for Judge0 in docker-compose.yml (or use hosted Judge0 API)

2. Create backend/apps/interviews/coding_service.py:
   - class CodingInterviewService:
     - generate_problem(difficulty, topic, language) -> dict:
       Uses Bedrock Claude to generate a coding problem with:
       {title, description, examples, constraints, test_cases, starter_code}
     
     - execute_code(code, language, test_cases) -> dict:
       Submits to Judge0 API for execution
       Returns: {passed, failed, output, errors, execution_time, memory}
     
     - evaluate_solution(problem, code, test_results) -> dict:
       AI evaluation of code quality:
       {score, correctness, efficiency, style, suggestions}

3. Create API endpoints:
   - POST /api/v1/interviews/coding/start/ — generate a coding problem
   - POST /api/v1/interviews/coding/run/ — execute code against test cases
   - POST /api/v1/interviews/coding/submit/ — final submission with evaluation

4. Frontend: Add Monaco Editor to InterviewPractice page:
   - npm install @monaco-editor/react
   - Language selector (Python, JavaScript, Java, C++)
   - Run button, Submit button
   - Test case results panel
   - AI feedback panel

Update the existing InterviewPractice.tsx page to add a "Coding" tab alongside the text interview.
```

---

## 📋 EXECUTION ORDER

| Order | Phase | Effort | Priority |
|-------|-------|--------|----------|
| 1 | A: API Keys Config | 30min | 🔴 Critical |
| 2 | B: ESCO/Skills Import | 12h | 🔴 High |
| 3 | C: Embeddings & Search | 12h | 🔴 High |
| 4 | D: GDPR Compliance | 12h | 🔴 High |
| 5 | F: Testing | 10h | 🔴 High |
| 6 | E: CV Parsing | 8h | 🟡 Medium |
| 7 | G: Liveness & Scrapers | 15h | 🟡 Medium |
| 8 | H: Employer AI | 14h | 🟡 Medium |
| 9 | I: Enhanced Rashid | 8h | 🟡 Medium |
| 10 | J: Recommendations | 10h | 🟡 Medium |
| 11 | K: Voice & Coding | 30h | 🟢 Low |

**Total: ~131 hours across 11 phases**

---

## ⚙️ IMPORTANT CONTEXT FOR CLINE

Before starting any prompt, Cline should know:
- Django project is at: `backend/` with `config/` for settings
- Frontend is at: `frontend/` (React + TypeScript + Vite)
- Python 3.10 on production server
- AWS Bedrock Claude Sonnet for AI features
- Typesense for keyword search
- Qdrant for vector search
- Redis for caching and Celery broker
- PostgreSQL database
- Celery + Celery Beat for async tasks
- All apps follow the pattern: models.py, views.py, serializers.py, urls.py, tasks.py
- Authentication: JWT via rest_framework_simplejwt
- API prefix: /api/v1/
- Frontend uses: shadcn/ui, TailwindCSS, React Query, React Router v6

# D2 Audit — CV/Resume Engine + Skills/Knowledge Graph

**Scope:** Read-only code audit of `backend/apps/profiles`, `backend/apps/resume`,
`backend/apps/career` (CV parsing/tailoring pieces), `backend/apps/skills`, plus the
frontend resume/profile UI. No code was modified. Per AGENTS.md instructions,
findings are based on direct code inspection, not on the ~100 historical
`*_SUMMARY.md`/`*_COMPLETE.md` docs (which are archive-only and known to
contradict each other/the code).

**Headline finding:** There are **three parallel, disconnected CV-parsing
implementations** (`apps.profiles.cv_parser.CVParser`,
`apps.career.cv_parser.CVParserService`, and prompt logic duplicated again in
`apps.intelligence.career_ai.CareerAIService.parse_cv`) and **two parallel,
disconnected resume-persistence models** (`CareerProfile.cv_parsed_data` JSON
blob vs. the separate `apps.resume.Resume` structured-fields model). This is
exactly the "re-fragmenting into disconnected per-feature modules" anti-pattern
AGENTS.md calls out for `career`/`skills`/`rashid` — it has also happened
inside the CV subsystem itself.

---

## 1. Resume/CV Engine

### 1.1 Upload
- **DONE** — `apps/profiles/views.py:83-100` `ProfileViewSet.upload_cv` (POST
  `/api/v1/profile/upload_cv/`) and `apps/career/cv_parser_views.py:43-167`
  `cv_upload` (POST `/api/v1/career/cv/upload/`) are **two independent upload
  endpoints** writing to the same `CareerProfile.cv_file`/`cv_parsed_data`
  fields via different code paths. Both exist, both are wired into urls.py
  (`apps/profiles/urls.py:14`, `apps/career/urls.py:72`), neither references
  the other. **REFACTOR** — collapse into one canonical upload path; current
  state is a maintenance/consistency hazard (e.g. malware scanning differs
  slightly between the two — see 1.2).
- File validation: extension allow-list + 10MB cap enforced in both
  `apps/profiles/cv_parser.py:273-274` (`CVParser.SUPPORTED_FORMATS`,
  `MAX_FILE_SIZE`) and `apps/career/cv_parser_views.py:26-29`
  (`ALLOWED_EXTENSIONS`, `MAX_FILE_SIZE`) — duplicated constants, values match
  today but nothing keeps them in sync. **PARTIAL**.

### 1.2 Malware scanning / security
- **DONE** on the `apps.profiles` upload path: `serializers.py:153-171`
  (`CVUploadSerializer.validate_cv_file`) calls `upload_validator.validate()`
  and `scan_stream_for_malware()` before accepting the file.
- **DONE** on the `apps.career` upload path too:
  `cv_parser_views.py:61-91` calls `upload_validator.validate()` and
  `scan_file_for_malware()`. Good — both paths are covered, just duplicated
  (see 1.1).

### 1.3 Parsing / text extraction (PDF, DOCX, OCR)
- **DONE, but triplicated.**
  - `apps/profiles/cv_parser.py:1-406` — plugin-based `CVParser` with
    `DoclingParserPlugin` (line 50), `PdfplumberParserPlugin` (line 104),
    `EasyOCRParserPlugin` (line 136, does real OCR for scanned/image CVs via
    `easyocr` + `pdf2image`), `DocxParserPlugin` (line 191), `TxtParserPlugin`
    (line 226). This is the most complete implementation — genuine
    OCR fallback for scanned/image resumes, Docling→pdfplumber fallback chain.
  - `apps/career/cv_parser.py:24-177` — a **second**, simpler
    `CVParserService` with `parse_pdf` (pdfplumber only, line 47),
    `parse_docx` (python-docx, line 92), `parse_image` (line 142 — calls
    `docling.DocumentConverter`, **not EasyOCR**; Docling does not do OCR on
    plain images without config, so scanned-image CVs uploaded via
    `/api/v1/career/cv/upload/` likely extract poor/no text — **BROKEN** for
    that specific path vs. the profiles path which has real OCR).
  - Neither module imports the other; `EasyOCRParserPlugin` (real OCR) is only
    reachable via the profiles endpoint.
  - **REFACTOR** — merge into a single parser service; today OCR quality
    depends entirely on which of the two upload endpoints the frontend
    happens to call.
- Dependencies actually installed: `docling==2.31.0`, `pdfplumber==0.11.0`,
  `python-docx==1.1.0` present in `backend/requirements.txt:47-49`.
  **`easyocr` and `pdf2image` are NOT in requirements.txt** — grep of the file
  found no matches for either package. **BROKEN** — `EasyOCRParserPlugin`
  (`apps/profiles/cv_parser.py:136-184`) will hit its `except ImportError`
  branch (`logger.warning("EasyOCR not installed"); return ""`) in any
  environment built strictly from `requirements.txt`, silently returning empty
  text for scanned/image CVs instead of OCR-ing them. Verify with:
  `pip show easyocr pdf2image` inside the backend venv, or
  `grep -i easyocr backend/requirements.txt` (currently no output).
- `xhtml2pdf` (used by the resume PDF exporter, see 1.7) is also **not** in
  `requirements.txt` — same silent-fallback risk on PDF export.

### 1.4 Structured extraction (skills/experience/education/projects/certs/achievements)
- **DONE (AI-based, with fallback)** — three near-identical Claude prompt
  schemas exist:
  - `apps/career/cv_parser.py:179-233` (`extract_structured_data`) — its own
    JSON schema (name/email/phone/summary/experience/education/skills flat
    list/languages/certifications). **No "projects" or "achievements"
    fields** in this schema.
  - `apps/intelligence/career_ai.py:52-115` (`CareerAIService.parse_cv`) — a
    **different, richer** schema that DOES include `projects` (with
    technologies/url) and splits skills into
    technical/languages/soft_skills, plus `personal.linkedin`/`portfolio`.
  - `apps/profiles/serializers.py:191-201` (`CVUploadSerializer.save`) is the
    one that actually calls `apps.intelligence.career_ai.career_ai_service`
    (the richer schema) — so the *profiles* upload path gets projects,
    the *career* upload path (`cv_parser_views.py:109`, calling
    `apps/career/cv_parser.py:extract_structured_data`) does **not** extract
    projects or achievements at all. **PARTIAL/INTEGRATE** — no single
    canonical extraction schema; "achievements" as a distinct field is
    **MISSING** everywhere (folded into free-text `description` only).
  - Regex/keyword fallback exists for when Bedrock is unavailable:
    `apps/career/cv_parser.py:265-319` (`_fallback_extract_structured_data`) —
    email/phone regex + a fixed ~30-word skill keyword list. Reasonable
    degrade path, but very shallow (no experience/education fallback
    extraction at all — those stay empty lists if AI is down).
- Skill→ESCO mapping: **DONE**, via fuzzy string matching
  (`difflib.SequenceMatcher`) in `apps/career/cv_parser.py:321-371`
  (`map_skills_to_esco`), confidence threshold 0.7. This runs an O(N×M)
  loop (N extracted skills × up to 1000 ESCO skills, line 342) per upload —
  **fine for occasional CV uploads, would not scale to bulk/batch use.**
- `CareerUserSkill` upsert from parsed skills: **DONE** —
  `apps/career/cv_parser.py:373-410` (`update_user_skills`), writes
  `source='cv_extraction'`, `verified=False`, fixed `proficiency='intermediate'`
  regardless of actual seniority signal in the CV (**PARTIAL** — proficiency
  inference is a no-op constant, not derived from years/context).

### 1.5 ATS analysis / compatibility scoring
- **MISSING.** Repo-wide search for `ats_score`, `ats_analysis`,
  `ATSAnalysis`, `ats_optimiz*`, and case-insensitive `\bats\b` inside
  `backend/` and `frontend/src/` returned **zero real matches** (only
  incidental substring hits in unrelated files like `github_service.py`,
  `admin.py` — none are actual ATS-compatibility features). There is no
  keyword-density check, no formatting/parseability score, no
  "will-this-survive-an-ATS-parser" feature anywhere in the codebase despite
  this being a standard resume-tool feature and implied by the task's ask.
  **BUILD** from scratch if wanted.

### 1.6 Quality scoring
- **DONE, but scoped to "profile completeness," not "resume/CV quality."**
  Three independent completeness calculators exist, all measuring
  profile-field-fill-rate, not CV writing/content quality:
  - `apps/profiles/views.py:102-152` (`ProfileViewSet.completion`) — inline
    weighted dict (cv/skills/experience/education/preferences/portfolio/
    languages, sums to 100).
  - `apps/profiles/serializers.py:76-99` (`get_completion_percentage`) —
    a **second, slightly different** weighting of the same fields, duplicated
    logic that can silently drift from the view's version.
  - `apps/career/completeness_calculator.py:1-379`
    (`ProfileCompletenessCalculator`) — the most sophisticated version, 7
    weighted dimensions (basic_info/summary/experience/education/skills/
    external_signals/preferences), each with its own sub-scoring function
    and returns recommendations. This is the best of the three but is
    **not used by** the two profiles-app scorers above — three scoring
    systems compute three different "completion %" numbers for the same user
    depending which endpoint the frontend calls.
  - **REFACTOR** — pick one (`career/completeness_calculator.py` is the most
    complete) and delete the other two ad-hoc versions.
  - True CV *quality* scoring (grammar, action-verb usage, quantified
    achievements, length/density heuristics, ATS-readability) is
    **MISSING** — nothing in `apps/resume` or `apps/career` evaluates the
    actual written content quality of a CV, only whether fields are filled.

### 1.7 Job-specific optimization / CV tailoring
- **PARTIAL** — `apps/career/cv_tailor_service.py:1-37`
  (`CVTailorService.analyze`) is real: pulls user skills vs. job skills,
  computes `missing_skills` and a naive `match_score`
  (`len(intersection)/len(job_skills)`), and asks Bedrock for 3-5 bullet
  suggestions (keywords to add, skills to emphasize, experience to highlight).
  Wired to `POST /api/v1/career/cv-tailor/<job_id>/`
  (`apps/career/urls.py:85`, `views_cv_tailor.py:9-14`). This is a real,
  working feature — but it only returns *suggestions as text*, it does not
  rewrite/generate a tailored CV variant, and there is no persistence of the
  suggestion or before/after diff.
- **Bug found**: `apps/career/cv_tailor_service.py:7` reads
  `user.career_profile.career_user_skills` but the actual model field
  (`apps/career/models.py:305-316`, `CareerUserSkill.user` FK) has
  `related_name='career_userskills'` (no underscore between `user` and
  `skill`), and the *other* usage on line 267 of the same models.py
  (`self.career_userskill_set.filter(...)`) uses the Django default reverse
  accessor name (singular model name + `_set`) because that FK relationship
  has no explicit `related_name` at all in that spot. Three different
  spellings (`career_user_skills`, `career_userskills`,
  `career_userskill_set`) are used across the codebase to reach the same
  relationship — **BROKEN**: `cv_tailor_service.py:7`'s
  `user.career_profile.career_user_skills` will raise
  `AttributeError`/`FieldError` at runtime (the actual related_name is
  `career_userskills`, not `career_user_skills`) unless Django's related
  manager silently falls back — it will not; this is a real bug that breaks
  `cv_tailor_suggestions` whenever `hasattr(user, 'career_profile')` is True
  and skills are looked up. Verify: `grep -n "career_user_skills\b"
  backend/apps/career/cv_tailor_service.py` vs.
  `grep -n "related_name='career_userskills'" backend/apps/career/models.py`.
  **Fix suggestion (not applied — audit only):** change line 7 to
  `user.career_profile.career_userskills.all()`.

### 1.8 Multi-version CVs
- **MISSING/PARTIAL, ambiguous by design.** There is no explicit
  "CV version" or "resume variant per job" model. What exists instead:
  - `CareerProfile` (`apps/career/models.py:21`) holds exactly **one**
    `cv_file`/`cv_parsed_data` per user (OneToOne with User, line 29) — so the
    "canonical CV" concept is singular.
  - `apps.resume.Resume` (`apps/resume/models.py:73-158`) is a separate model
    that supports **multiple resumes per user** (`ForeignKey` to user, line
    80, `related_name='resumes'`) with full structured fields
    (personal_info/summary/experience/education/skills/projects/
    certifications/languages/interests, lines 100-135) and a
    `ResumeTemplate` FK for styling. This is genuinely multi-version-capable
    — a user can create N `Resume` rows.
  - **But these two models are entirely disconnected.** `Resume` is not
    populated from `CareerProfile.cv_parsed_data` — a user who uploads a CV
    (populating `CareerProfile`) gets nothing pre-filled in the Resume
    Builder; they'd have to re-enter everything manually (confirmed:
    `ResumeBuilder.tsx:213-235`'s `handleImportFromCV` only pulls from
    `/api/v1/career/cv/status/`'s `cv_parsed_data` on-demand button click —
    it is a one-way, manual, non-persistent import action, not a live link).
  - **INTEGRATE** — genuine multi-version support exists in `apps.resume`,
    but it needs to be connected to the CV-parsing pipeline (auto-seed a
    first `Resume` from parsed CV data) to be useful as "multi-version CV
    management" rather than "resume builder that starts from a blank form."

### 1.9 Resume Builder (UI)
- **DONE (functional)** — `frontend/src/pages/ResumeBuilder.tsx` (877 lines):
  tabbed editor (personal/experience/education/skills/projects/certs/
  languages), live preview (`ResumePreview.tsx`), autosave
  (`scheduleAutoSave`, referenced around line 111/195), create/update/delete
  mutations against `apps.resume` endpoints (lines 122-150), template
  selection, and the CV-import button (line 292, `handleImportFromCV`).
  This is a real, wired-up feature — not a stub.
- **Bug found:** `ResumeBuilder.tsx:24` sets `const API_BASE =
  '/api/v1/resume'` and calls its own local `apiFetch` (lines 34-38) that does
  **not** use the shared `services/client.ts` (`apiRequest`) that the rest of
  the app uses for auth-token-refresh handling — AGENTS.md explicitly flags
  "duplicate-API-client bug (`services/client.ts` vs `services/api.ts`)" as a
  documented recurring pattern in this repo; `ResumeBuilder.tsx` is a third
  instance of it (a page-local `apiFetch` with manual
  `localStorage.getItem('access_token')`, line 27) — note this reads a
  **different localStorage key** (`access_token`) than `client.ts` uses
  (`usam_access`, `client.ts:8`). If both are live, a user logged in via the
  main app (which sets `usam_access`) will have `ResumeBuilder.tsx`'s
  `apiFetch` send **no Authorization header at all** on every resume
  API call (falsy token → `getAuthHeaders()` returns headers without
  `Authorization`, `ResumeBuilder.tsx:26-32`), silently hitting the
  `permission_classes=[IsAuthenticated]` 401 wall. **BROKEN** — confirmed by
  code inspection; would need a live request to fully confirm but the
  key-name mismatch is unambiguous in source. Verify:
  `grep -n "localStorage.getItem" frontend/src/pages/ResumeBuilder.tsx
  frontend/src/services/client.ts`.

### 1.10 PDF/DOCX export
- **PARTIAL/BROKEN.** `apps/resume/export_service.py:1-69`
  (`ResumeExportService`):
  - `export_html` (line 40) — **DONE**, renders Django template.
  - `export_json` (line 43) — **DONE**.
  - `export_pdf` (line 26) — **PARTIAL**: uses `xhtml2pdf.pisa` which is
    **not in requirements.txt** (confirmed via grep, see 1.3); on
    `ImportError` it **silently falls back to returning raw HTML bytes with
    no format conversion** (line 36-38: `return html.encode('utf-8')`) while
    the view still serves it with `content_type='application/pdf'` and a
    `.pdf` filename (`apps/resume/views.py:254-256`) — **users would download
    a file named `something.pdf` that is actually raw HTML**, a real
    functional bug if `xhtml2pdf` isn't installed in the deployed
    environment. Verify: `pip show xhtml2pdf` in the backend venv;
    `grep -i xhtml2pdf backend/requirements.txt` (no output today).
  - **DOCX export is advertised but not implemented — BROKEN.**
    `ResumeExportRequestSerializer.FORMAT_CHOICES`
    (`apps/resume/serializers.py:183-188`) and `ResumeExport.FORMAT_CHOICES`
    (`apps/resume/models.py:176-181`) both list `'docx'` as a valid format,
    and the frontend export UI would reasonably let a user pick it — but
    `apps/resume/views.py:export_resume` (lines 250-268) only branches on
    `'pdf'`, `'html'`, `'json'`. If `export_format == 'docx'`, none of the
    `if/elif` branches match, execution falls through to the
    "Record the export" block (`ResumeExport.objects.create(..., format='docx',
    status='completed', ...)`, lines 270-276) and returns
    `{'success': True, 'message': 'Export as docx complete'}`
    (line 278) **without ever generating or returning any file**. This is a
    confirmed silent-failure bug: the API reports success and logs a
    completed export record for a format that produces no output.
    Verify: `sed -n '233,278p' backend/apps/resume/views.py` — no `elif
    export_format == 'docx'` branch exists.
  - Only one export template exists on disk: `find` of
    `apps/resume/templates/resume/export/` returned only `modern.html`.
    `ResumeExportService.TEMPLATES` (lines 19-24) declares `professional`,
    `creative`, `minimalist` templates too, all of which will hit the
    `except Exception: return render_to_string('resume/export/modern.html', ...)`
    fallback (line 65-66) — i.e. **every export renders the same "modern"
    layout regardless of selected template**, silently. **BROKEN**
    (templates advertised in code/model choices but 3 of 4 don't exist on
    disk).

### 1.11 Resume templates data
- **PARTIAL.** `ResumeTemplate` model exists with rich fields (category,
  preview_image, premium flag, rating) but there is **no seed/fixture
  command** for it anywhere under `apps/resume/` (confirmed: no `*seed*` or
  `*fixture*` files found). `GET /api/v1/resume/templates/` will return an
  empty list on a fresh DB unless templates are inserted manually via admin.
  **BUILD** a seed command, or **MISSING** data pipeline.

---

## 2. Skills / Knowledge Graph

### 2.1 Unified skill taxonomy
- **DONE, well-built.** `apps/skills/models.py:15-131` (`Skill`) — ESCO-based
  taxonomy with `esco_uri` (unique), `onet_element_id` cross-reference,
  `type` (technical/soft/language/tool/framework/methodology), hierarchical
  `parent` self-FK with `level` depth, Arabic translation field (`name_ar`),
  and a JSON `embedding` field for semantic similarity. This is a real,
  properly normalized taxonomy — not a flat tag list.
- Import pipeline: **DONE** — `management/commands/import_esco.py` (312
  lines, real CSV parsing with `--dry-run`/`--limit`), `import_onet.py`,
  `map_esco_onet.py`, `seed_skills.py` (a ~30-category hardcoded fallback
  taxonomy for environments without the real ESCO/O*NET CSVs, confirmed at
  `seed_skills.py:1-40`). **generate_arabic_translations.py** uses Claude
  Haiku for i18n, cost-estimated in `apps/skills/README.md:75-78`.
  **Caveat — whether the import has actually been RUN against a live DB
  (i.e., whether `skills_skill` table is populated) could not be verified
  from code alone; this requires a live DB check** (`python manage.py shell
  -c "from apps.skills.models import Skill; print(Skill.objects.count())"`)
  — do not assume populated without running it.

### 2.2 User↔Skill relationship
- **DONE** — `CareerUserSkill` (`apps/career/models.py:297-372`): M2M via
  explicit through-model with `proficiency` (beginner→expert),
  `years_experience`, `verified` bool, `verification_source`,
  `source` (cv_extraction/self_reported/assessment/github/inferred), and a
  `confidence` float. This is a solid, evidence-aware user-skill edge — not
  a flat string list. (Separately, `CareerProfile.skills`
  (`apps/career/models.py:111-114`) is a **duplicate flat JSON list** of the
  same information for "quick access" — two sources of truth for a user's
  skills, one relational + verified, one denormalized JSON; they are kept in
  sync manually by application code in several places, e.g.
  `serializers.py:238-247`, which is a drift risk. **PARTIAL/REFACTOR**.)

### 2.3 Skill↔Evidence relationship
- **PARTIAL, fragmented.** Two separate models both claim this role and are
  not connected to each other or to `CareerUserSkill`:
  - `apps/resume/models.py:290-378` (`SkillVerification`) — has
    `verification_method` (assessment/github/project/endorsement/
    certification/cv), `evidence_url`, `evidence_text`, `score`, `level`,
    `expires_at`. This is a proper "skill + evidence" model.
  - `CareerUserSkill.verification_source`/`.source`/`.confidence`
    (`apps/career/models.py:336-363`) captures similar evidence-provenance
    info but as flat CharFields, not linked to `SkillVerification` records.
  - No FK exists between `SkillVerification` and `CareerUserSkill` or
    `Skill` (`SkillVerification.skill_name` is a plain CharField, line 305,
    not a FK to `apps.skills.models.Skill`) — so evidence recorded via one
    path is invisible to graph queries or gap-analysis run against the other.
  - **REFACTOR/INTEGRATE** — these should be one Evidence model FK'd to both
    `Skill` and `CareerUserSkill`.

### 2.4 Skill↔Job relationship
- **DONE** — `JobSkill` (`apps/skills/models.py:349-409`): FK to `Job` and
  `Skill`, `importance` (1-5), `level`, `source` (ai/manual/import).
  Extraction pipeline is real: `apps/skills/extraction.py:1-377`
  (`SkillExtractor`) — Claude-based extraction with MD5-hashed description
  caching (7-day TTL, line 32/68), ESCO fuzzy-mapping (`_find_esco_skill`,
  line 253), keyword-fallback extraction (`_fallback_extraction`, line
  161-223) when Bedrock is down. Management command
  `extract_skills_from_jobs.py` exists to batch-run this. **DONE.**

### 2.5 Skill↔Role/Occupation relationship
- **DONE** — `Occupation` (`apps/skills/models.py:196-257`, ESCO/O*NET
  hierarchy) and `OccupationSkill` (259-298, importance 1-5 + level 1-7 from
  O*NET). Real, queryable.

### 2.6 Skill↔Industry relationship
- **MISSING.** No `Industry` model exists anywhere in the codebase (grep for
  `class Industry` returned zero matches repo-wide). Occupations/skills are
  not tagged by industry/sector at all. **BUILD** if industry-level
  filtering/analytics is wanted.

### 2.7 Occupation↔CareerPath relationship
- **DONE** — `CareerPath` (`apps/skills/models.py:301-346`): from/to
  Occupation FKs, `typical_years`, `probability`, `required_skills_delta`
  JSON. Queried via `SkillGraph.get_career_paths`
  (`apps/skills/graph.py:191-202`) and exposed at
  `GET /api/v1/skills/occupations/<id>/career-paths/`
  (`apps/skills/graph_urls.py`→`graph_views.py:112-127`, also duplicated as
  `apps/skills/views.py:297-327` `CareerPathsFromOccupationView` — **two
  endpoints for the same query, one in graph_views.py one in views.py,
  REFACTOR to dedupe**).

### 2.8 Skill↔LearningResource relationship
- **PARTIAL/MISSING.** `CareerLearning` (`apps/career/models.py:375-433`)
  tracks a user's completed courses (title/platform/skills_gained JSON/
  completed_at/certificate_url) — this is "user's learning history," not a
  "LearningResource" catalog entity with its own model that skills/gaps could
  recommend *from*. There is no `LearningResource` model, no catalog of
  courses/certifications tied to specific `Skill` rows for recommendation
  purposes. `SkillGapAnalyzer._generate_recommendations`
  (`apps/career/skill_gap_analysis.py:223-269`) returns **generic hardcoded
  action strings** ("Take online courses on platforms like Coursera or
  Udemy", line 241) — not references to any actual learning-resource
  records or real course data. **MISSING** the LearningResource entity;
  what exists is a recommendation stub with placeholder text.

### 2.9 Skill↔Company relationship
- **MISSING** as a direct edge. Company↔Skill only exists transitively via
  Company→Job→JobSkill (no direct `CompanySkill` or "skills this company
  values" aggregate model/view). Not necessarily a gap (transitive query is
  fine functionally) but there's no materialized/cached view for
  "top skills at Company X" — would require an ad-hoc JOIN through Job today.
  **PARTIAL** (queryable but not modeled or optimized as first-class).

### 2.10 Graph query engine
- **DONE, but README overstates it — verify before trusting.**
  `apps/skills/graph.py:1-202` (`SkillGraph`) implements **real recursive-CTE
  SQL** (`WITH RECURSIVE`, lines 34-68, 119-146) directly against the
  `skills_relationship` adjacency table — `find_related_skills`,
  `get_skill_distance` (bounded 5-hop BFS), `find_skill_path`,
  `get_skill_hierarchy` (parent-chain walk), `get_occupation_skills`,
  `get_career_paths`. This is a working, dependency-free graph engine.
  **However**, `apps/skills/README.md:80-108, 124-222` describes an **Apache
  AGE** graph-database architecture (`setup_age_graph` management command,
  `ag_catalog`, `create_graph('skills_graph')`) as if it's the primary
  storage — but `graph.py`'s actual `SkillGraph` class **never touches AGE
  at all**; every method queries plain PostgreSQL tables via
  `django.db.connection` + recursive CTEs. The AGE setup command exists
  (`setup_age_graph.py`) and can create the extension/graph, but nothing in
  `graph.py`, `graph_views.py`, or `skill_gap_analysis.py` reads from or
  writes to it. **This is a doc/code mismatch exactly matching the AGENTS.md
  warning "don't assume README/roadmap docs reflect current code"** — AGE is
  either vestigial/half-migrated-away-from, or was never actually wired in
  despite the README's confident "✅ Completed" checklist (`README.md:239-241`
  claims Task 1.25/1.26 "Install Apache AGE extension" / "Create AGE graph"
  are done, but the query layer doesn't use it). Tests confirm this too:
  `apps/skills/tests/test_graph_queries.py:106` skips two tests entirely on
  SQLite via `_skip_on_sqlite` with the comment "Raw SQL UUID handling
  requires PostgreSQL" — no AGE-specific test exists at all.
  Verify live: `python manage.py shell -c "from django.db import connection;
  cursor=connection.cursor(); cursor.execute(\"SELECT extversion FROM
  pg_extension WHERE extname='age'\"); print(cursor.fetchone())"` — if this
  errors/returns None on the deployed DB, AGE was never actually installed
  and the README's "Completed" claim for that section is false.
- Two sets of near-identical graph API views exist:
  `apps/skills/graph_views.py` (Related/Path/Distance/Hierarchy/
  OccupationSkills/CareerPaths views, mounted via `graph_urls.py`) **and**
  `apps/skills/views.py:118-165` (`RelatedSkillsView`, a *different*
  implementation using plain `SkillRelationship.objects.filter()` ORM
  queries instead of `SkillGraph`). Both are routed
  (`skills/urls.py:29` and `skills/urls.py:43→graph_urls.py`) — likely
  colliding/ambiguous route resolution for "related skills." **REFACTOR** —
  dedupe into one implementation.

### 2.11 Skill Gap Analysis
- **DONE (real feature)** — `apps/career/skill_gap_analysis.py:1-312`
  (`SkillGapAnalyzer`): per-target-role gap scoring (missing/required ratio),
  severity buckets (low/medium/high/critical), calls `SkillGraph` for related
  skills to suggest (line 208-221), and generates category-grouped
  recommendations. Exposed at `GET /api/v1/career/skill-gap/`
  (`career/urls.py:69`). Falls back to a **hardcoded 4-role skill dict**
  (`_get_required_skills`, lines 163-184: software engineer/data
  scientist/product manager/ux designer only) when no matching `Occupation`
  row exists in DB — reasonable degrade but very narrow coverage.

### 2.12 Career Brain (cross-cutting context aggregator)
- **DONE** — `apps/career/career_brain_service.py:1-380`
  (`CareerBrainService`): aggregates skills/goals/preferences/learning/
  history-summary/AI-observations into `CareerBrain` model
  (`apps/career/models.py:599-...`), used to build Arabic-language context
  strings for Rashid AI prompts (`build_context`, lines 36-152). This is a
  genuine "one shared intelligence layer" component in the spirit of
  AGENTS.md's stated architecture goal — a partial realization of the Career
  Graph vision, though its `_generate_ai_observations` (lines 279-329) is
  Bedrock-dependent with a static 5-line fallback (`_get_fallback_observations`,
  lines 331-339) when AI is unavailable.

---

## 3. Cross-cutting architecture concerns (Career Graph fragmentation)

Per AGENTS.md's explicit warning about `career`/`skills`/`rashid` apps
drifting into separate schemas: this audit found concrete instances **inside**
the CV/skills domain itself, not just across apps:

1. **Skills stored in 3 places per user**: `CareerProfile.skills` (flat JSON
   list), `CareerUserSkill` (relational, verified/evidence-aware — the
   "correct" one), and `CareerBrain.skills` (a third JSON dict rebuilt from
   `CareerUserSkill` by `career_brain_service.py:201-214`). Three
   representations of the same fact, synced by hand in application code.
2. **CV parsing logic triplicated** (profiles/cv_parser.py,
   career/cv_parser.py, intelligence/career_ai.py) with three different
   output JSON schemas.
3. **Profile completeness scored 3 different ways** (see 1.6).
4. **Evidence for skill claims split across `SkillVerification` and
   `CareerUserSkill`** with no FK linking them (see 2.3).
5. **Two upload endpoints, two export-related-skills views, two
   career-paths-from-occupation views** — the "duplicate API surface" pattern
   AGENTS.md flags for frontend `client.ts`/`api.ts` recurs on the backend
   for CV/skills routes too.

**Recommendation for a follow-up engineering task (not executed — audit
only):** consolidate around `apps.career.models.CareerProfile` +
`CareerUserSkill` + `apps.skills` taxonomy as the single source of truth;
delete/redirect the `apps.profiles` duplicate upload path and the
`apps.career.cv_parser.CVParserService` duplicate parser; make `apps.resume`
`Resume` rows derive from `CareerProfile.cv_parsed_data` on creation instead
of starting blank.

---

## 4. External repo evaluation — `magic-resume` (JOYCEQL)

**URL:** https://github.com/JOYCEQL/magic-resume
**Verdict: REJECT** (do not adopt/integrate).

Reasons:
1. **License is commercially unusable for this product.** README states
   Apache 2.0 with an explicit carve-out: "**Commercial License Required**:
   ... Any organization or individual that provides it as a service
   (SaaS/PaaS, etc.) to the public for profit ... must obtain a commercial
   license, regardless of whether the source code has been modified." Since
   E-Career (jobs.usamif.com) is exactly a for-profit SaaS offering a resume
   builder to the public, adopting this code would require a paid commercial
   license from the author — a real legal/cost blocker, not just a
   preference.
2. **Tech stack mismatch.** It's a TanStack Start + Framer Motion +
   Zustand + Tiptap frontend-only app with **local-storage persistence** (no
   backend, no auth, no multi-user data model) — this repo's Resume Builder
   is already a React/Vite + Django-REST-backed multi-user system with
   templates, exports, and skill verification tied to a real user account.
   Integrating magic-resume's frontend would mean replacing a working,
   already-integrated builder with an incompatible framework
   (TanStack Start vs. this repo's Vite/React Router setup) for no functional
   gain.
3. **No parsing/ATS/skills-graph capability at all.** magic-resume is purely
   an editor + PDF export (its own roadmap lists "Import PDF" as a *future*
   item, not present today) — it does not solve any of this repo's actual
   gaps (ATS scoring, OCR, skill taxonomy, multi-source parsing). There is
   nothing to reference-and-adapt architecturally beyond "yet another
   React resume form," which this repo already has.

**Even for REFERENCE-only purposes** (not adoption): its "auto one page" and
theme/animation polish (Framer Motion transitions) are visually nicer than
the current plain shadcn/ui-based `ResumeBuilder.tsx`, but that's a UI-polish
idea, not something requiring the external repo's code.

## 5. Alternative OSS resume parser/builder projects (quick web_search)

- **Reactive Resume** (github.com/AmruthPillai/reactive-resume, ~41.7k
  stars, MIT license) — full-stack resume builder (React/Nest, self-hosted
  Docker Compose, headless-Chromium PDF export, public share links, MCP/API
  support). **Verdict: REFERENCE.** MIT license means no legal blocker (unlike
  magic-resume), and its architecture (separate "printer" microservice for
  headless-Chromium PDF generation) is a genuinely useful pattern to
  reference for fixing this repo's fragile `xhtml2pdf`-with-silent-HTML-
  fallback PDF export (section 1.10) — swapping to a headless-browser PDF
  renderer would fix both the missing-dependency risk and probably render
  more faithful PDFs than xhtml2pdf's limited CSS support. Not a drop-in
  replacement (different stack) but worth studying its PDF pipeline.
- **pyresparser** (github.com/OmkarPathak/pyresparser, ~959 stars,
  spaCy/NLTK-based) — classic rule+NER resume parser (name/email/phone/
  skills/education/experience from PDF/DOCX). **Verdict: REFERENCE only.**
  Unmaintained-feeling (old spaCy API surface, no ATS/skills-graph feature),
  but its skill/entity-extraction *approach* (NER over free text) could be a
  cheap non-AI fallback layer to strengthen this repo's very shallow regex
  fallback (`apps/career/cv_parser.py:265-319`) for when Bedrock is
  unavailable — currently that fallback only extracts email/phone/~30
  keyword skills with zero experience/education parsing.
- **magicalapi/resume-parser-python** and similar "AI resume parser API"
  wrapper projects surfaced in search results are thin wrappers around
  paid third-party APIs (not real open implementations) — **Verdict:
  REJECT**, no code value, would reintroduce a paid-vendor dependency this
  repo has deliberately avoided by using Bedrock/Claude directly.

---

## 6. Suggested verification commands (not run — read-only audit)

```bash
# Confirm ESCO/O*NET data actually loaded
python manage.py shell -c "from apps.skills.models import Skill, Occupation; print(Skill.objects.count(), Occupation.objects.count())"

# Confirm AGE extension status on the real DB
python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute(\"SELECT extversion FROM pg_extension WHERE extname='age'\"); print(c.fetchone())"

# Confirm easyocr/xhtml2pdf actually installed in the deployed venv
pip show easyocr pdf2image xhtml2pdf 2>&1 | grep -i "warning\|not found\|Name:"

# Confirm ResumeTemplate table is non-empty
python manage.py shell -c "from apps.resume.models import ResumeTemplate; print(ResumeTemplate.objects.count())"

# Reproduce the cv_tailor_service related_name bug
python manage.py shell -c "from apps.career.models import CareerProfile; cp = CareerProfile.objects.first(); print(hasattr(cp, 'career_user_skills'), hasattr(cp, 'career_userskills'))"
```

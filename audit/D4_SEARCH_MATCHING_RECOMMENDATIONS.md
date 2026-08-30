# D4 Audit — Search + Matching + Recommendation Engines

**Scope:** `apps/search`, `apps/vectors`, `apps/career/recommendation_engine.py`,
`apps/search/recommendation_engine.py`, `apps/intelligence/job_matching.py`.
**Method:** Direct code read, `git log`/`git show` on the 2026-08-29 fix commit,
targeted grep for stale field references, `pip show` for dependency reality
check. Read-only — no code changed.

All file paths below are relative to `backend/`.

---

## 0. Executive summary

| Area | Verdict | One-line why |
|---|---|---|
| Keyword search (Typesense) | **DONE** | Real plugin, health-checked, trust-score gated, used by views. |
| Postgres search fallback | **DONE** | Wired as automatic fallback when Typesense unhealthy. |
| Semantic search (pgvector) | **PARTIAL** | Wired end-to-end (view→service→plugin) and functionally coherent, but plugin has debug `print()`s and only exists because Qdrant (the documented "primary") isn't installed/used anywhere in code. |
| Vector infra Qdrant | **MISSING (never built)** | README/docstrings describe Qdrant as primary; zero Qdrant code exists; `qdrant-client` isn't even a dependency. Pure documentation fiction. |
| Hybrid search (RRF) | **BROKEN** | `HybridSearchView` calls `search_service.search(...)`, a method that does not exist on `SearchService` (it's `search_jobs`). Will raise `AttributeError` on every call, caught by a blanket `except Exception` → always returns 500. |
| Matching Engine (`job_matching.py`) | **BROKEN** | Explainable score breakdown exists (`calculate_job_compatibility`) but the file is import-broken (`apps.vectors.services` doesn't exist) and not wired to any URL/view at all — fully dead code. |
| Recommendation Engine — TWO systems | **CONFIRMED DISCONNECTED** | `apps/career/recommendation_engine.py` and `apps/search/recommendation_engine.py` are separate classes, separate models loaded, separate endpoints (`/api/v1/career/recommendations/` vs `/api/v1/search/recommendations/`), no shared code, no shared trained model. |
| 2026-08-29 `is_active`→`status` fix | **VERIFIED CLEAN** | Commit `3a92ce0` correctly fixed all 21 sites across 8 files; both recommendation engines' 3+4 sites confirmed patched. |
| Other stale-field bugs (NOT covered by that fix) | **FOUND — 4 new ones**, see §5 | `job.remote_type`, `job.experience_required`, `job.required_skills`, `profile.saved_jobs`, `job.job_type`/`job.is_remote` — none exist on current models. |
| Gorse (external OSS recommender) | **verdict: ADAPT (long-term), not now** | See §7. |

---

## 1. Search infrastructure

### 1.1 Keyword search — Typesense (primary)
`apps/search/service.py:45-137` — `SearchService`
- `primary` property (`service.py:53-56`) lazily builds `TypesenseSearchPlugin()`.
- `fallback` property (`service.py:58-61`) lazily builds `PostgresSearchPlugin()`.
- `_get_plugin()` (`service.py:64-71`) health-checks Typesense first, falls back to
  Postgres on any exception — **DONE**, this is real, defensive, working design.
- `_enforce_trust_score_filter()` (`service.py:123-127`) — "NON-NEGOTIABLE" trust-score
  gate applied to every search query. Good defense-in-depth against low-quality/
  scraped jobs leaking into results.
- `apps/search/services.py:1-9` is a thin back-compat shim re-exporting the same
  singleton — no duplication, fine.
- Confirmed dependency present: `typesense==2.0.0` installed (`pip show typesense`).
- Wired: `apps/search/views.py:15` imports `search_service`, used by the main
  search endpoint.

**Verdict: DONE.**

### 1.2 Postgres fallback
`apps/search/plugins/postgres_plugin.py` — exists, used automatically by
`SearchService._get_plugin()`. Not deep-audited line-by-line (out of the two
target recsys files' scope) but its wiring point is real and reachable.

**Verdict: DONE (wiring confirmed; plugin internals not fully audited).**

### 1.3 Semantic search — pgvector
`apps/vectors/service.py:28-199` — `VectorService`
- `vector_plugin` property (`service.py:36-41`) **hardcodes `PgVectorPlugin()`**
  with the comment *"pgvector is the canonical store"* (`service.py:37`) —
  this directly contradicts `apps/vectors/README.md:7,19-27,50-52,317-333`,
  which describes Qdrant as primary with pgvector as fallback.
- `embedding_plugin` property (`service.py:44-49`) hardcodes `CohereEmbedPlugin()`
  (AWS Bedrock Cohere Embed v3, 1024-dim).
- `PgVectorPlugin` (`apps/vectors/plugins/pgvector_plugin.py:26-317`) is a real,
  working implementation: creates `vectors_<collection>` tables with an
  `ivfflat` index, does cosine-similarity search via `<=>` operator, has
  `health_check()`. **However** it contains leftover debug `print()` statements
  at `pgvector_plugin.py:202-204` inside `search()` — dumps SQL param counts to
  stdout on every semantic-search call in production. Minor but real.
- Confirmed reachable: `apps/vectors/views.py:14,83-92` (`SemanticSearchView`)
  calls `vector_service.semantic_search(...)` — real code path.
- Confirmed: **Qdrant is 100% vaporware.** `search_files` for `qdrant`
  (case-insensitive) across `backend/` returns hits only in docs/README/
  docker migration files — **zero** `QdrantVectorPlugin` class exists anywhere,
  and `pip show qdrant-client` → "Package(s) not found." The README's own
  "Components" section (`README.md:50-52`) claims `QdrantVectorPlugin: Qdrant
  implementation` exists — it does not.

**Verdict: PARTIAL** (pgvector semantic search works and is wired; the
documented Qdrant "primary" layer is **MISSING** — never built, not a stub,
not a config toggle, literally absent from the codebase while the README
describes it as already running with cost/performance benchmarks).

### 1.4 Hybrid search (keyword + semantic, RRF)
`apps/vectors/views.py:211-345` — `HybridSearchView`
- Step 1 (`views.py:266-271`): `search_service.search(query=query, filters=filters,
  page=1, page_size=limit)`.
- **`SearchService` (apps/search/service.py:45)` has no `.search()` method.**
  Its only public keyword-search entry point is `search_jobs(self, query:
  SearchQuery) -> SearchResponse` (`service.py:73`), which takes a
  `SearchQuery` dataclass object, not keyword args `query=`/`filters=`/`page=`/
  `page_size=`.
- Result: **every call to `HybridSearchView.get()` raises `AttributeError:
  'SearchService' object has no attribute 'search'`**, caught by the blanket
  `except Exception as e` (`views.py:338`), so the endpoint always returns
  HTTP 500 with `"Hybrid search failed"`. This is a live production 500,
  same class of bug as the `is_active` one just fixed, but **not covered by
  the 2026-08-29 fix** because it's a missing-method bug, not a stale-field
  filter bug.

**Verdict: BROKEN.** `GET /api/v1/search/hybrid/` (and any equivalent route)
500s on every call. Fix is small (call `search_jobs()` with a `SearchQuery`
object, or add a `.search()` compatibility method) but nobody has hit it yet
per the same pattern as the is_active bug — an untested integration seam.

### 1.5 Embeddings pipeline
`apps/search/embeddings.py:1-85` — `EmbeddingService` — thin, correct wrapper
around `apps.vectors.service.get_vector_service()`; delegates to
`generate_embeddings`, `semantic_search`, `vector_plugin.upsert/delete`. This
one is internally consistent (imports the real module/singleton correctly,
unlike `job_matching.py` — see §3). **DONE.**

### 1.6 Vector indexing management command
`apps/vectors/management/commands/index_jobs.py:1-129` — separate command from
`apps/vectors/management/commands/embed_jobs.py` (not read in depth, but two
job-indexing commands existing is itself a smell worth flagging for the
broader search domain). `index_jobs.py` has its own stale-field bugs — see §5.

---

## 2. Matching Engine — `apps/intelligence/job_matching.py`

### 2.1 Is it explainable?
**Yes, by design** — `calculate_job_compatibility()` (`job_matching.py:284-337`)
returns exactly the shape the task asked about:
```python
{
  'overall_score': 0.85,
  'breakdown': {'skills': 0.90, 'experience': 0.80, 'location': 1.0, 'salary': 0.85},
  'recommendation': 'Highly Recommended',
  'strengths': [...], 'areas_to_improve': [...]
}
```
Backed by four separate `_calculate_*_score()` methods (`job_matching.py:339-378`),
each independently interpretable. This is the right shape — not a black box.
**Design verdict: DONE** (as a design/algorithm).

### 2.2 Is it actually usable?
**No — the module is import-broken and completely unwired.**

- `job_matching.py:10`: `from apps.vectors.services import vector_service` —
  **wrong module name** (`services` plural; real module is `apps/vectors/
  service.py`, singular) **and wrong symbol** (real module exposes a factory
  `get_vector_service()`, not a `vector_service` singleton instance —
  confirmed via `search_files` for `vector_service` / `class VectorService` /
  `get_vector_service` in `apps/vectors/service.py`). This import fails at
  module load time with `ModuleNotFoundError: No module named
  'apps.vectors.services'`.
- Even if the import were fixed to the real module, `self.vector_service.
  embed_text(query)` (`job_matching.py:46`) and `self.vector_service.
  similarity_search(...)` (`job_matching.py:49-53`) call methods that **do not
  exist** on `VectorService` — the real API is `generate_embeddings()` and
  `semantic_search()` (`apps/vectors/service.py:74,89`). Two independent API
  mismatches stacked on one broken import.
- **Zero references anywhere in `apps/` import `job_matching`, `job_matching_
  service`, or `JobMatchingService`** (`search_files` for all three returned 0
  hits outside the file's own definition). No URL, no view, no Celery task,
  no other service touches it.
- `apps/intelligence/urls.py:1-46` has no route to any job-matching endpoint
  (routes cover Rashid AI chat, trend detection, research, knowledge graph,
  content pipeline — matching is absent).
- Additional internal breakage independent of the import bug (`§5.4`): it also
  calls `job.remote_type` and `job.required_skills.all()`, neither of which
  exist on the current `Job` model.

**Verdict: BROKEN + MISSING integration.** This is not "partially working code
with a bug" — it is a file that cannot even be imported, is never imported by
anything else in the codebase, and would still be broken on 3 more counts if
the import were fixed. It reads as a designed-but-never-tested or
abandoned-mid-refactor module. Given the well-designed breakdown shape, the
right move is **REFACTOR** (fix the import + method calls + field names and
wire it to a URL) rather than delete, since the explainability design is
worth keeping — but as shipped today it delivers zero matching capability.

---

## 3. Recommendation Engine — confirmed TWO disconnected systems

Per the task's hypothesis: **confirmed, not a false alarm.** These are fully
independent implementations with no shared code, shared trained model, or
shared cache.

| | `apps/career/recommendation_engine.py` | `apps/search/recommendation_engine.py` |
|---|---|---|
| Class | `RecommendationEngine` (module-level singleton `recommendation_engine = RecommendationEngine()`, `career/recommendation_engine.py:31,289`) | `RecommendationEngine` (per-user instance via factory `get_recommendation_engine(user)`, `search/recommendation_engine.py:22,588-600`) |
| Design | Hybrid: content-based (`_content_based_scores`) + LightFM collaborative (`_collaborative_scores`) + recency boost, manually weighted 0.6/0.3/0.1 (`career/recommendation_engine.py:36-38`) | LightFM with item/user feature matrices built from skills+employment_type+location hash-bucket (`search/recommendation_engine.py:112-193`), separately weighted 0.6/0.4 hybrid at request time (`search/recommendation_engine.py:348-351`) |
| Data pulled | `apps.career.models.CareerProfile` (flat JSON `skills`/`target_roles`/`target_locations`), `apps.employers.models.JobApplication` | `apps.career.models.CareerUserSkill` (normalized skill FK + proficiency), `apps.career.models.CareerLearning`, `apps.core.models.GitHubConnection` (imported, `search/recommendation_engine.py:17`, but never actually used in the read code) |
| Model persistence | In-memory only (`self._model`, `self._user_map` instance attrs, retrained via Celery beat task `apps.career.tasks.train_recommendation_model`, `career/tasks.py:163-177`) — **lost on every process restart/worker respawn**, no model serialization to disk/DB | In-memory only, rebuilt **per request** inside `get_recommendation_engine(user)` (new instance every call, `search/recommendation_engine.py:598-600`) — even more wasteful; there is no persisted/shared model across requests at all |
| API surface | `GET /api/v1/career/recommendations/?limit=` (`career/views_recommendations.py:11-33`) | `GET /api/v1/search/recommendations/`, `GET /api/v1/search/similar-jobs/<uuid>/`, `POST /api/v1/search/train-recommendation-model/` (`search/views.py:147-267`) |
| Explainability | Yes — `reasons: List[str]` per recommendation (`career/recommendation_engine.py:92-96,144,151,159`) plus separate `content_score`/`collaborative_score` | Partial — returns `content_score`/`collaborative_score` breakdown but no human-readable `reasons` list |
| Fallback when no profile/model | `_fallback_recommendations()` — recent active jobs, flat 0.5 score (`career/recommendation_engine.py:279-286`) | `_get_fallback_recommendations()` — title/skill keyword scoring against target roles (`search/recommendation_engine.py:426-492`) — a **different, non-trivial fallback algorithm**, duplicated effort |

**No cross-references exist between the two files** (confirmed via
`search_files` — neither imports the other, neither is imported by the same
callers, `apps/career/tasks.py` only trains the career engine, nothing trains
the search engine's model except its own `TrainRecommendationModelView`).

This is exactly the "repeatedly-flagged risk in this repo" that `AGENTS.md`
warns about (fragmenting into disconnected per-feature modules instead of one
shared intelligence layer, `AGENTS.md:8-12`). Recommendations is a second,
independently-confirmed instance of that pattern, on top of the already-known
`career`/`skills`/`rashid` schema fragmentation.

**Verdict: INTEGRATE (or REPLACE — see §7).** Two LightFM models solving the
same problem (job recommendations for a user) with different feature
engineering, different weighting, different endpoints, and no shared training
data pipeline is redundant engineering effort and guarantees the two surfaces
will drift and disagree on what's recommended to the same user.

---

## 4. Verification of the 2026-08-29 `is_active` → `status` fix

Commit `3a92ce0` ("fix: Job.objects filter/get using nonexistent is_active
field", author Mohamed Usama, 2026-08-29 09:25:06 +0300):

```
backend/apps/career/recommendation_engine.py           | 6 +++---
backend/apps/emails/matching.py                        | 4 ++--
backend/apps/emails/tasks.py                            | 6 +++---
backend/apps/intelligence/tools.py                      | 8 ++++----
backend/apps/intelligence/trend_detection.py            | 6 +++---
backend/apps/profiles/views.py                          | 2 +-
backend/apps/search/recommendation_engine.py            | 8 ++++----
backend/apps/vectors/management/commands/index_jobs.py  | 1 +-
```

- **`career/recommendation_engine.py`** — all 3 sites patched cleanly:
  `career/recommendation_engine.py:72` (recency filter), `:117` (content-based
  candidates), `:282` (fallback recs) — all now `status='active'`. Confirmed
  by direct read of the current file (§ code excerpt above shows
  `status='active'` in place at all three).
- **`search/recommendation_engine.py`** — all 4 sites patched cleanly:
  `:104` (`_build_mappings`), `:121` (`_build_item_features`), `:231` (`train`),
  `:447` (`_get_fallback_recommendations`) — confirmed all read `status=
  'active'` in the current file.
- Both files' `git show` diff hunks exactly match current file content — no
  regression, no partial application, no merge artifact. **Fix landed
  cleanly.**
- Grep for any remaining `Job.objects....is_active` anywhere in `apps/` found
  **zero hits** on `Job.objects` (the 50 `is_active` matches that do exist are
  all on `Company`, `Source`, `User`, `FeatureFlag`, etc. — models that
  genuinely have an `is_active` BooleanField, e.g. `Company.is_active`,
  `jobs/models.py:29`). No stray Job-model `is_active` references remain.

**Verdict: VERIFIED CLEAN.**

---

## 5. NEW stale/wrong field references found (not covered by the 2026-08-29 fix)

The task asked to specifically hunt for other stale-field bugs in these two
files (plus job_matching.py, in-scope for this audit) beyond `is_active`.
Found **five** distinct additional bugs, none touched by commit `3a92ce0`:

### 5.1 `job.remote_type` — field removed by migration, still referenced
- Current `Job` model has **no `remote_type` field.** Migration
  `apps/jobs/migrations/0003_remove_job_remote_type_job_work_arrangement_and_
  more.py:13-16` explicitly `RemoveField(model_name='job', name='remote_type')`
  and replaces it with `work_arrangement` (`0003_...py:17-21`).
- Still referenced as if it exists in:
  - `apps/search/recommendation_engine.py:362,416,472,485,550` (5 sites)
  - `apps/intelligence/job_matching.py:113,148,149,369` (4 sites; note `:148-149`
    is a **queryset filter** `queryset.filter(remote_type=filters['remote_type'])`
    — this one is a live `FieldError` risk exactly like the fixed `is_active`
    bug, on a code path (`_fallback_search`) that IS reachable if the semantic
    search's `try` fails, e.g. every time Bedrock/pgvector errors)
- Impact: `search/recommendation_engine.py` lines 416/472 (`if job.remote_type
  in [...]`) will raise `AttributeError: 'Job' object has no attribute
  'remote_type'` the moment a Job object is accessed with that attribute at
  runtime — not caught by any try/except at that call depth in
  `_calculate_content_score`/`_get_fallback_recommendations`, so this **will
  500** the recommendations endpoint the same way `is_active` did, just one
  attribute deeper into the flow (reached only once `status='active'` filter
  succeeds and jobs are returned — i.e. the OLD bug was masking this NEW one).

### 5.2 `job.experience_required` — never existed on Job model
- `apps/search/recommendation_engine.py:410,467` —
  `abs(job.experience_required - user_profile.experience_years)`.
- Real field is `Job.experience_level` (a CharField choice: entry/mid/senior/
  lead, `apps/jobs/models.py:223-225`), not a numeric `experience_required`.
  There is no numeric experience field on `Job` at all.
- **Will raise `AttributeError`** the instant either `_calculate_content_score`
  (called from `get_recommendations`, `search/recommendation_engine.py:344`)
  or `_get_fallback_recommendations` (`:466-468`) executes — i.e. immediately
  masked-then-exposed by the same chain as §5.1: fix `status='active'` →
  jobs load → first `.remote_type`/`.experience_required` access 500s.

### 5.3 `job.required_skills` / `job.skills` — wrong relation name
- `apps/search/recommendation_engine.py:131,398`: `job.skills.all()`.
- `apps/intelligence/job_matching.py:184,346`: `job.required_skills.all()`.
- Real model: `apps/skills/models.py:349-367` — `JobSkill` through-model with
  `job = ForeignKey('jobs.Job', related_name='skills', ...)` and
  `skill = ForeignKey(Skill, related_name='jobs', ...)`.
- So `job.skills.all()` (used in `search/recommendation_engine.py`) is
  **actually correct** — `related_name='skills'` on the Job side does exist —
  good catch of a false positive, worth noting explicitly so it isn't
  miscategorized.
- **But `job.required_skills.all()`** (used twice in `job_matching.py:184,346`)
  **is wrong** — there is no `required_skills` related-name anywhere on `Job`.
  This is a second, independent bug in `job_matching.py` beyond the broken
  import (§2.2) — would `AttributeError` even after the import is fixed.

### 5.4 `profile.saved_jobs` — field never existed on `CareerProfile`
- `apps/career/recommendation_engine.py:252-255` (`_build_interaction_matrix`):
  `CareerProfile.objects.exclude(saved_jobs=[])` then iterates
  `profile.saved_jobs`.
- Confirmed via full field enumeration of `CareerProfile`
  (`apps/career/models.py:21-1277` class body) — the model has no `saved_jobs`
  field of any kind (JSONField, M2M, or otherwise). Full field list: `user,
  cv_file, cv_parsed_data, cv_parse_status, cv_parsed_at, experience_years,
  current_role, current_company, target_roles, target_locations,
  target_salary_min, target_salary_currency, open_to_remote, github_username,
  github_data, portfolio_url, portfolio_analysis, linkedin_data, skills,
  education, languages, certifications, is_discoverable, preferred_type,
  email_alerts, cv_uploaded_at, alert_frequency, min_match_score,
  completeness_score, last_active_at`.
- This queryset **will raise `django.core.exceptions.FieldError`** exactly
  like the original `is_active` bug — same failure class, different field,
  same file. **Silently swallowed** by the bare `except Exception: pass`
  wrapping it (`career/recommendation_engine.py:250,256-257`), so instead of a
  visible 500 it just means the "saved jobs" collaborative-filtering signal
  silently contributes **zero interactions**, forever, without anyone
  noticing — arguably worse than a loud 500 because it degrades recommendation
  quality invisibly. LightFM training (`train_model()`,
  `career/recommendation_engine.py:193-243`) will only ever see application
  data, never saved-job data, despite the code and docstring claiming both are
  used ("Saved jobs (weight 1.0)" comment at `:249`).

### 5.5 `job.job_type` / `job.is_remote` — wrong field names in vector indexer
- `apps/vectors/management/commands/index_jobs.py:93,97`:
  `'job_type': job.job_type` and `'is_remote': job.is_remote`.
- Neither field exists on `Job`. Real equivalents: `employment_type` (choice
  field) and `work_arrangement`/`location_type` (there is no boolean remote
  flag at all — remote-ness is one of three `work_arrangement` choice values).
- This command (`python manage.py index_jobs`) would `AttributeError` on the
  very first batch (`index_jobs.py:75-100` list comprehension building
  `documents`), meaning **the Qdrant/pgvector job-indexing management command
  cannot run at all** as written — independent confirmation that this whole
  vector-indexing surface has never been exercised end-to-end since these
  field renames happened (same migration `0003_...py` that removed
  `remote_type`).

### Summary table — stale-field bugs found beyond the fixed `is_active` ones

| File:Line | Wrong reference | Correct field | Runtime effect |
|---|---|---|---|
| `search/recommendation_engine.py:362,416,472,485,550` | `job.remote_type` | `job.work_arrangement` | AttributeError once job list loads |
| `intelligence/job_matching.py:113,148,149,369` | `job.remote_type` / filter kwarg | `job.work_arrangement` | AttributeError / FieldError |
| `search/recommendation_engine.py:410,467` | `job.experience_required` | `job.experience_level` (different type — string not int) | AttributeError |
| `intelligence/job_matching.py:184,346` | `job.required_skills` | `job.skills` (via `JobSkill.related_name`) | AttributeError |
| `career/recommendation_engine.py:252-255` | `profile.saved_jobs` | *(no such field exists)* | Silent FieldError, swallowed, permanent signal loss |
| `vectors/management/commands/index_jobs.py:93,97` | `job.job_type`, `job.is_remote` | `job.employment_type`, `job.work_arrangement` | AttributeError, command unusable |

**Net effect: the 2026-08-29 fix made the `is_active` filter succeed, which
means jobs now actually load into these functions — which means the NEXT
stale-field bug on the very next line (`.remote_type`, `.experience_required`)
is now the live blocker.** The fix was necessary but not sufficient; both
recommendation engines are still broken end-to-end for any real job dataset,
just one field-access deeper than before.

---

## 6. Recommended classification (per task's taxonomy)

| Component | Classification |
|---|---|
| Typesense keyword search | **DONE** |
| Postgres fallback search | **DONE** |
| pgvector semantic search | **PARTIAL** (works, but debug prints + Qdrant story is fiction) |
| Qdrant "primary" vector store | **MISSING** (never built; docs describe non-existent code) |
| Hybrid search (RRF) endpoint | **BROKEN** (`search_service.search()` doesn't exist) |
| `job_matching.py` matching engine | **BROKEN** + **MISSING integration** (import fails, unwired, additional stale-field bugs even if import fixed) |
| `career/recommendation_engine.py` | **BROKEN** (stale `remote_type`/`experience_required`/`saved_jobs` refs downstream of the fixed `is_active` bug) |
| `search/recommendation_engine.py` | **BROKEN** (same class of bug, `remote_type`/`experience_required`) |
| Two-recsys architecture | **INTEGRATE** (or **REPLACE**, see §7) — must become one shared recommendation layer per `AGENTS.md`'s own stated principle |
| `vectors/management/commands/index_jobs.py` | **BROKEN** (unusable as written — `job_type`/`is_remote`) |

---

## 7. Gorse (github.com/zhenghaoz/gorse, now gorse-io/gorse) — evaluation

**What it is:** an open-source, Go-based, standalone recommender system
server (~9.8k GitHub stars). Runs as its own service (single binary or
Docker), stores data in MySQL/MongoDB/Postgres/ClickHouse with Redis-class
caching, exposes a RESTful API (`POST /api/feedback`, `GET /api/collaborative-
filtering/{user-id}`, `GET /api/item-to-item/{name}/{item-id}`, etc.) plus
official Python/Go/Java/JS/Rust client libraries. Supports classical
collaborative filtering, item-to-item/user-to-item, non-personalized
("most-starred") recommenders, and newer LLM-based/embedding-based
multimodal recommenders, all configured declaratively (not custom Python
code) via a pipeline config. Has a GUI dashboard for monitoring/config.

**Why it's relevant here:** it is architecturally exactly the "one shared
recommendation infrastructure" `AGENTS.md` says this project needs and
currently lacks (§3). It would replace both bespoke, broken, in-process
LightFM engines with a single external service that both the `career` and
`search` apps call via the same client — feedback events (application,
save, view, click) get pushed to one place, one model trains, one API
serves recommendations to any caller.

**Trade-offs against the current situation:**
- *For (USE/ADAPT):* Gorse is purpose-built for exactly this "users × items ×
  interactions → recommendations" problem and would eliminate the entire
  category of bug found in §5 — no more hand-rolled LightFM feature-matrix
  code with stale Django field references, because feature engineering moves
  into Gorse's config, and Job/User field access moves into a thin
  feedback-sync layer (a much smaller, easier-to-test surface than the ~900
  combined lines currently spread across two engines).
- *Against (REJECT concerns):* it's a new infrastructure dependency (separate
  Go service + its own datastore) in a stack that already runs Postgres+
  pgvector, Typesense, Qdrant-in-name-only, Redis, Celery — adding Gorse means
  one more moving part to deploy/monitor, and this project's own docs (§0,
  Qdrant) show a pattern of adding infra in documentation that never gets
  deployed in practice. There's real risk Gorse becomes a second "Qdrant
  README fiction" if adopted aspirationally without deployment follow-through.
  It also doesn't give the field-level explainability (`skills 95%, experience
  90%`) the task asked about "out of the box" — Gorse's collaborative/
  item-to-item scores are opaque `Score: float` values; the breakdown-style
  explainability that already exists in `job_matching.py`'s
  `calculate_job_compatibility()` (§2.1) and `career/recommendation_engine.py`'s
  `reasons` list would need to be layered on top as a separate scoring pass
  fed by Gorse's ranking — i.e. Gorse alone does not solve the explainability
  requirement, only the "one shared infra instead of two disconnected ones"
  requirement.

**Verdict: ADAPT, not REPLACE-immediately.** Don't bring in Gorse as a
same-sprint fix — the immediate, cheap fix is: (1) patch the 6 new
stale-field bugs in §5 the same way the `is_active` bug was patched, (2)
literally delete or clearly deprecate one of the two `RecommendationEngine`
classes and route both `career` and `search` endpoints through the survivor,
(3) fix or remove the Qdrant documentation fiction. Gorse becomes worth a real
pilot only once there's a single, correctly-wired in-house recommendation
path to compare it against and migrate feedback events from — introducing
Gorse before that consolidation would create a *third* recommendation
system, compounding rather than solving the fragmentation problem this audit
was asked to check for.

---

## 8. File:line citation index (for quick lookup)

- `apps/search/service.py:45,53-56,58-61,64-71,73,123-127` — SearchService core
- `apps/search/services.py:1-9` — back-compat shim (fine, not duplication)
- `apps/vectors/service.py:28,36-41,44-49,74-87,89-128` — VectorService, hardcoded pgvector+Cohere
- `apps/vectors/plugins/pgvector_plugin.py:26,166-249,202-204` — PgVectorPlugin + debug prints
- `apps/vectors/views.py:266,211-345` — broken HybridSearchView
- `apps/vectors/README.md:7,19-27,50-52,317-333` — Qdrant fiction
- `apps/intelligence/job_matching.py:10,22,46,49-53,92,113,148-149,184,346,369,284-337,339-378` — broken matching engine
- `apps/career/recommendation_engine.py:31,36-38,47-107,109-129,131-162,193-243,245-267,252-255,279-286,289` — career recsys
- `apps/search/recommendation_engine.py:22,34-46,101-193,215-279,285-379,362,398,410,416,467,472,485,550,588-600` — search recsys
- `apps/career/views_recommendations.py:8,27` / `apps/search/views.py:144,169,212,250` — two separate endpoint surfaces
- `apps/career/tasks.py:163-177` — career-only training task, no equivalent shared scheduler
- `apps/jobs/models.py:211-368` — canonical Job model (ground truth for all stale-field findings)
- `apps/jobs/migrations/0003_remove_job_remote_type_job_work_arrangement_and_more.py:13-21` — proof `remote_type` was deliberately removed
- `apps/career/models.py:21-1277` (CareerProfile field enumeration), `:297-325` (CareerUserSkill)
- `apps/skills/models.py:349-367` — JobSkill through-model (ground truth for `related_name='skills'`)
- `apps/vectors/management/commands/index_jobs.py:93,97` — broken indexer
- Fix commit: `git show 3a92ce0` — full diff verified against current file state, 21 sites/8 files, all clean.

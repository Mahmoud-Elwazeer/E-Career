# PROMPT — E-Career Phase 1: Foundational/Architectural Consolidation

You are a senior backend/full-stack engineer working in the E-Career repo at
`M:\job already web for jobs\E-Career` (Django/DRF backend in `backend/`,
React/Vite frontend in `frontend/`).

## Prerequisite

**Phase 0 must be complete and verified before starting this.** Read
`M:\job already web for jobs\E-Career\audit\PHASE_0_COMPLETION_REPORT.md`
first — if it doesn't exist or shows unresolved critical bugs, stop and
flag that instead of proceeding.

## Before touching anything

1. Read `AGENTS.md` in full.
2. Read `MASTER_IMPLEMENTATION_PLAN.md` in full — sections 2 (Engine
   Status Table) and 3 (Cross-Cutting Patterns) are directly relevant to
   every item below. Items below are 1.1–1.16 from its "Phase 1" table.
3. This phase is about **consolidation, not new features**. The repeated
   theme across all 10 source audits is "duplicated/parallel implementations,
   disconnected" — your job is to pick ONE canonical implementation per
   pair/triple and retire the others, preserving all functionality that
   actually works today. Do NOT delete something without confirming (via
   grep for import/call sites) that nothing still depends on it.
4. Never touch `.env` or secrets.
5. This is bigger, riskier surgery than Phase 0 — write/run tests before
   and after each consolidation. Commit each item separately.

## Scope: these 16 items only

**1.1** — `CareerBrain` (`apps/career/models.py:599-905`) is a well-designed
"single source of truth" model whose only sync method (`update_from_profile()`)
has zero call sites anywhere in the codebase — fully dead code. Decide its
fate: EITHER (a) wire it in — fire it via a Django signal or Celery task
whenever `CareerProfile`, `CareerUserSkill`, `JobApplication`, or
`InterviewSession` are created/updated, so it actually becomes the
aggregation layer it was designed to be, OR (b) formally retire it (remove
the dead code, document why in a commit message) if the team decides
per-model queries are sufficient. Recommend (a) given AGENTS.md's explicit
"Career Graph" architectural bet — but flag this decision to the user
rather than assuming.

**1.2** — Consolidate the 3 CV parsers into one canonical parser + schema:
`apps/profiles/cv_parser.py`, `apps/career/cv_parser.py`,
`apps/intelligence/career_ai.py` (its CV-parsing portion). Read all 3 in
full, compare their extraction schemas, pick the most complete/correct one
as canonical (likely whichever is most actively used — check call sites),
migrate all callers to it, delete the other two's CV-parsing logic (keep
anything in `career_ai.py` that isn't CV-parsing-specific).

**1.3** — Consolidate the 2 CV upload endpoints into one:
`apps/profiles/views.py:83-100` and `apps/career/cv_parser_views.py:43-167`.
Pick one canonical URL/view, update frontend call sites to use only that
one, remove the other (or make it redirect/delegate to the canonical one if
external clients might still hit the old URL).

**1.4** — Consolidate the 3 profile-completeness calculators into one; the
audit recommends keeping `apps/career/completeness_calculator.py` as
canonical — verify this is indeed the most complete/correct implementation
first, then migrate all callers to it and remove the other two.

**1.5** — `apps/intelligence/job_matching.py` and
`apps/employers/ranking_service.py` are both well-designed but have zero
callers (dead code). For each: either fix its known bugs (see Phase 0 items
0.9 for job_matching.py's stale fields) and wire it into a real endpoint, OR
delete it if a decision is made not to use it. Do not leave dead-but-broken
modules sitting unresolved — that's the exact anti-pattern this phase exists
to fix.

**1.6** — Merge the two recommendation engines
(`apps/career/recommendation_engine.py` and
`apps/search/recommendation_engine.py`) into one. Compare both
implementations, pick the better-designed one as base (or write a new one
combining both LightFM setups' strengths), migrate the `career` and
`search` app endpoints that currently call each one to use the single
survivor, delete the loser.

**1.7** — There are 3 separate anti-aggregator blocklists in the
direct-apply-verification code. Unify them into the existing-but-currently-
unused admin models `BlockedDomain`/`ApprovedATS`
(`apps/verification/models.py:91-181`) so the blocklist becomes
admin-editable instead of hardcoded in 3 places. Update every verification
check to read from these models instead of hardcoded lists.

**1.8** — Build the 9-state Job Quality Engine field that `AGENTS.md`
specifies (Active / Probably active / Needs verification / Expired /
Archived / Broken / Duplicate / Rejected / Direct-source verified) — this
currently doesn't exist anywhere as a single field; state is scattered
across 3 uncoordinated fields (`Job.status`, `Job.is_expired`,
`VerificationResult.status`). Add a new field (e.g.
`Job.quality_state` with a `choices=` of the 9 states), migrate the 3
existing sources of truth into it via a data migration, and update every
place that currently checks the 3 old fields to check the new one instead
(keep the old fields if other code still needs them, or deprecate
cleanly).

**1.9** — Deprecate `apps.users.UserProfile` (`apps/users/models.py:112-183`)
for real — schema-level, not just a Python import alias. First, fix the
data-loss bug: `min_match_score` was silently dropped during the original
consolidation migration
(`apps/career/migrations/0004_migrate_userprofile_data.py`) and needs a
follow-up data migration to recover/migrate it for any pre-consolidation
users where it's still recoverable. Then plan the actual table
deprecation (mark model as legacy, stop writes, eventual removal) — check
git history/AGENTS.md for whether "preserve existing code" constraints
apply before doing a destructive schema change; if in doubt, do the data
migration but leave final table removal as a follow-up decision for the
user.

**1.10** — Reconcile the 3 skill representations: `CareerProfile.skills`
(flat list), `CareerUserSkill` (structured model,
`apps/career/models.py:111-114,297-372`), and `CareerBrain.skills`
(`career_brain_service.py:201-214`). Pick `CareerUserSkill` as the
canonical structured source (it's the richer model per the audit), migrate
all write paths to update it, and make `CareerProfile.skills` /
`CareerBrain.skills` either derived read-only views of it or removed.

**1.11** — AI model routing: force every AI call site through
`apps/intelligence/model_router.py`'s `select_model()` — currently it has
exactly 1 caller while 4+ other locations hardcode model IDs directly
(`bedrock_plugin.py:29-32`, `agent.py:39-49`, and others found by Phase 0's
grep in item 0.9-adjacent work). Also: build `MODEL_ALIASES` dynamically
from `list_foundation_models()` (a real AWS Bedrock API call) instead of a
hardcoded dict, per `AGENTS.md`'s explicit requirement that the router
should discover available models from the account, not hardcode a list.
Delete the second, redundant alias table in `agent.py`.

**1.12** — Point the in-app notification READ path (whatever the frontend
actually queries) at `apps.notifications.UserNotification`
(`apps/notifications/models.py:97`) — this is the model real backend events
(new application, interview started, etc.) actually write to. Currently the
frontend reads `apps.users.Notification` (`apps/users/models.py:75`), which
nothing in production writes to, so the in-app bell/list always renders
empty for real users. Retire `apps.users.Notification` once the read path
is migrated (check for any other readers first).

**1.13** — Consolidate the 3 Rashid tool registries: `RASHID_TOOLS`
(wherever defined in `apps/rashid/tools.py`), `ToolRegistry`
(`apps/intelligence/tools.py`), and `agent.py`'s `@agent.tool` decorators
(`apps/intelligence/agent.py`) into ONE registry. Then — this is the bigger
part — migrate the live chat path (WebSocket/REST, in `apps/rashid/service.py`)
away from raw prompt concatenation onto the real tool-calling
`apps/intelligence/agent.py` implementation, which already correctly calls
`SearchService`, `SkillGapService`, `RecommendationEngine`, etc. This is the
single highest-value fix for making Rashid an actual "platform intelligence
layer" instead of a chatbot with duplicated inline business logic.

**1.14** — Collapse the two navbar/layout system pairs
(`components/Navbar.tsx` + `AppLayout` vs `components/AuthNavbar.tsx` +
`Layout`) into one canonical pair. Determine which pages use which wrapper
currently, migrate all pages to the single survivor, delete the other.

**1.15** — Add client-side role gates. Currently `components/RequireAuth.tsx:4-15`
has zero role awareness — any authenticated user can render the shell of
`/admin*` and `/app/employer/*` routes (the backend still correctly blocks
the actual data calls, but the UX is a broken-shell experience instead of a
clean redirect). Add `RequireRole`/`RequireAdmin`/`RequireEmployer` wrapper
components and apply them to the relevant routes in `App.tsx`.

**1.16** — Reconcile the `source_url` vs `direct_apply_url` vs
`source_raw_url` field semantics on the `Job` model — pick which one is
canonical for "the URL to verify/re-check", update the recurring
verification Celery Beat tasks (`apps/verification/tasks.py:38-39,48-49`,
which currently check the wrong field per Phase 0/D3 findings) to check the
correct one consistently. Cross-reference `apps/jobs/models.py:231,250-255`.

## When done

Write a completion report to
`M:\job already web for jobs\E-Career\audit\PHASE_1_COMPLETION_REPORT.md`
in the same format as Phase 0's report: per-item status, what changed,
verification method, anything you couldn't complete or flagged for human
decision (especially 1.1 and 1.9, which have judgment calls baked in).

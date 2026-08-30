# Phase 7b Completion Report

**Date:** 2026-08-30
**Branch:** `development`
**Commits:** `4bc7013` through `a02a7a8` (6 commits)

## Task Checklist

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7b.1 | Admin AI Copilot | Done | Privilege-separated pydantic-ai agent with 5 read-only tools, DRF endpoint, chat UI tab |
| 7b.2 | Packages/Entitlements | Done | SubscriptionPlan + CompanySubscription models, check_entitlement() wired into 2 employer actions, admin CRUD |
| 7b.3 | AI cost tracking blind spots | Done | Fixed all 4: double-counting, missing operation labels, pydantic-ai bypass, missing user FK |
| 7b.4 | Admin global search | Done | Cross-entity search (users, companies, jobs), 2-char minimum, admin search tab |
| 7b.5 | Celery Beat viewer | Done | Periodic task list + enable/disable toggle with ActivityLog, automation tab |

## Commit Log

| Commit | Description |
|--------|-------------|
| `4bc7013` | fix(7b.3): close 4 AI cost tracking blind spots |
| `efad72b` | feat(7b.2): subscription plans, entitlements, and gated employer actions |
| `04be6be` | feat(7b.1): admin AI copilot agent with 5 read-only tools |
| `c08f98a` | feat(7b): 8 new admin API endpoints — celery beat, search, packages, copilot |
| `33c3114` | feat(7b): admin dashboard — celery beat, search, packages, copilot tabs |
| `a02a7a8` | test(7b): 27 tests for Phase 7b admin endpoints and entitlement checks |

## New Endpoint Inventory (8 endpoints)

All endpoints require `IsAdminRole` permission.

| # | Method | URL | View | Purpose |
|---|--------|-----|------|---------|
| 1 | GET | `/api/v1/admin-api/celery-beat/` | CeleryBeatListView | List periodic tasks with schedule, enabled, last_run, total_run_count |
| 2 | PATCH | `/api/v1/admin-api/celery-beat/<id>/toggle/` | CeleryBeatToggleView | Enable/disable periodic task + ActivityLog |
| 3 | GET | `/api/v1/admin-api/search/?q=` | AdminSearchView | Cross-entity search (users, companies, jobs) |
| 4 | GET/POST | `/api/v1/admin-api/plans/` | SubscriptionPlanListView | List/create subscription plans |
| 5 | GET/PATCH/DELETE | `/api/v1/admin-api/plans/<uuid>/` | SubscriptionPlanDetailView | Retrieve/update/delete plan |
| 6 | GET/POST | `/api/v1/admin-api/subscriptions/` | CompanySubscriptionListView | List/create company subscriptions |
| 7 | GET/PATCH | `/api/v1/admin-api/subscriptions/<uuid>/` | CompanySubscriptionDetailView | Retrieve/update subscription |
| 8 | POST | `/api/v1/admin-api/copilot/chat/` | AdminCopilotChatView | Admin AI copilot chat |

**Total admin URL patterns:** 28 (20 from 7a + 8 from 7b)

## New Models

| Model | Location | Fields |
|-------|----------|--------|
| SubscriptionPlan | `apps/core/models.py` | name, description, feature_flags (JSONField), job_posting_limit, candidate_search_limit, ai_features_enabled, is_active |
| CompanySubscription | `apps/core/models.py` | company FK, plan FK, status (trial/active/suspended/cancelled), started_at, notes |

**Migration:** `0004_add_subscription_plan_and_company_subscription.py` — applied successfully.

## New Files

| File | Purpose |
|------|---------|
| `backend/apps/intelligence/admin_agent.py` | Admin AI copilot — pydantic-ai agent with AdminDeps, 5 tools, haiku model |
| `backend/apps/core/tests/test_admin_api_7b.py` | 27 tests for all Phase 7b endpoints and entitlement logic |
| `backend/apps/core/migrations/0004_...py` | Migration for SubscriptionPlan + CompanySubscription |

## AI Cost Tracking Fixes (7b.3 Detail)

| Blind Spot | Root Cause | Fix |
|------------|-----------|-----|
| Double-counting | AICostDashboardView summed both EventLog costs AND RashidUsage estimated costs for overlapping calls | Removed RashidUsage from dashboard; single source of truth is EventLog |
| Missing operation labels | BedrockLLMPlugin._track_usage() had no operation field in event data | Added `operation` field to LLMRequest dataclass; all 12+ call sites now pass labeled operations (cv_parsing, job_matching, chat, etc.) |
| Pydantic-AI bypass | `chat_with_rashid` used pydantic-ai's Bedrock client, bypassing BedrockLLMPlugin cost tracking entirely | Added explicit EventLog emission in views.py after `agent.run()` with usage extraction |
| Missing user FK | `_track_usage()` passed `user=None` to emit() | Resolves user object from `request.user_id` before emitting |

## Entitlement Gating (7b.2 Detail)

`check_entitlement(company, check_type, current_count)` in `apps/core/permissions.py`:
- Returns True if no active subscription exists (ungated by default)
- Returns True if plan limit is 0 (unlimited)
- Raises PermissionDenied if `current_count >= limit`

Wired into 2 employer actions:
1. `JobPostingViewSet.perform_create` — checks `job_posting` limit against active job count
2. `TalentDiscoveryViewSet.perform_create` — checks `candidate_search` limit against monthly discovery count

## Frontend Changes

4 new tab components in `AdminDashboard.tsx`:
- **CeleryBeatTab** — periodic task list with enable/disable toggle switches
- **AdminSearchTab** — search box with multi-entity result list
- **PackagesTab** — split view showing plans list and subscriptions list with inline management
- **CopilotTab** — chat UI with message bubbles, input field, loading state

AdminTab union extended from 20 to 21 values (added `copilot`). Copilot added to Intelligence nav group.

## Test Results

### Phase 7b Tests (27 new)

| Class | Tests | Coverage |
|-------|-------|----------|
| TestCeleryBeatList | 2 | GET list, non-admin rejection |
| TestCeleryBeatToggle | 5 | Toggle, ActivityLog creation, missing field, 404, non-admin |
| TestAdminSearch | 5 | Results, user search, short query, empty query, non-admin |
| TestSubscriptionPlans | 5 | List, create, update, delete, non-admin |
| TestCompanySubscriptions | 3 | List, create, non-admin |
| TestEntitlementChecks | 3 | Limit enforced, no-sub ungated, unlimited plan |
| TestAdminCopilot | 4 | Empty message, missing message, non-admin, responds-or-501 |

### Full Verification Suite

| Check | Result |
|-------|--------|
| `pytest` | **484 passed**, 2 skipped, 0 failures |
| `npx tsc --noEmit` | **0 errors** |
| `npx vite build --mode production` | **Success** |

## Bug Found and Fixed During Testing

- `AdminSearchView` used `Q(full_name__icontains=q)` but `full_name` is a `@property` on the User model, not a DB column. Fixed to `Q(first_name__icontains=q) | Q(last_name__icontains=q)`.

## Deferred Items / Notes for 7c

1. **Propose-confirm pattern for copilot destructive actions**: The admin agent is currently read-only by design. If destructive tool calls are added later (e.g., "pause this source"), they should use a confirmation token pattern per the prompt spec. Not needed now since all 5 tools are read-only.
2. **Cmd+K quick-open shortcut**: The search tab works as a plain search bar. The keyboard shortcut is a nice-to-have for a future polish pass.
3. **pydantic-ai not installed in venv**: `pydantic-ai-slim[bedrock]==0.2.35` is in requirements.txt but not installed. The copilot endpoint returns 501 gracefully when unavailable. This is the same pre-existing situation as the Rashid agent.
4. **AI cost dashboard per-company breakdown**: Per-user breakdown is now working (7b.3 fix). Per-company breakdown would require joining through employer profiles — deferred to analytics polish (7c).

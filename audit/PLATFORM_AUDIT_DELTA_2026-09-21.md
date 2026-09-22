# Platform Audit Delta & Redesign Execution — 2026-09-21

Autonomous audit of every route against the design system + backend wiring,
followed by systematic batch execution. Green gate (typecheck + build + lint 0
errors) held after every batch.

## Method
- Enumerated all routes from `App.tsx`; classified each page by shell usage
  (Layout/AppShell), header pattern (PageHeader vs ad-hoc), token adherence,
  backend wiring, and intelligence surfacing.
- Cross-checked frontend against real backend endpoints (services + Django urls)
  to find capability that exists but isn't exposed.

## Delta — what was found and done

### CORRECT (preserved, not touched)
Dashboard, CoverLetters, EmployerDashboard, CareerGraph, landing (Index/Hero),
navigation (AuthNavbar/PublicNavMenu mega-menus), JobDetail, Companies,
SkillsExplorer (chamber header intentional), Settings, Notifications.

### WRONG / WEAK → FIXED

**TalentScore.tsx — fully rebuilt (was the worst offender).**
- Was: raw `container` + hardcoded `<h1>`, loading/error unshelled (chrome
  flicker), `DIMENSION_CONFIG` + charts hardcoded hex (broken in dark/night),
  manual `useState`+`Promise.all`, `any` types, English-only, and it *discarded*
  the rich backend intelligence (per-dimension grade/confidence/trend/evidence/
  explanation, `ai_confidence`, `last_calculated_at`, `score_history`); action
  rows looked clickable but were dead.
- Now: `page-shell` + `PageHeader`; AppShell-wrapped loading (skeleton) + error;
  React Query (3 queries + recalc mutation); **theme-aware charts** via a
  `cssVar()` helper reading `--primary/--border/--muted-foreground/--card`;
  chamber overall-score card with grade + AI confidence + last-updated;
  **strengths-vs-gaps** framing; **per-dimension drill-down** surfacing real
  grade/trend/evidence/explanation/confidence; real `score_history` line chart;
  **deep-linked** recommended actions (each routes to the page that fixes it);
  full i18n. Added token helpers to `services/scores.ts`
  (`gradeToken`/`trendTokenText`/`priorityToken`).

**ProfilePage.tsx — dead field fixed.** `min_salary` was held in state with no
input (silent dead field). Added a real salary Input + currency select + Switch
(replacing a native checkbox) for remote preference.

**Recommendations.tsx — build error fixed.** Removed a **duplicate
`import { useState }`** (would have failed a clean build). Converted to
`AppShell` + `PageHeader` + `StatCard`; kept its already-good match-reasons /
factor-breakdown surfacing.

**ResumeBuilder.tsx — weak empty states redesigned** (the ones the user saw as
"broken"): editor empty state now has an icon tile, context-aware heading
("Build your first resume" vs "Select a resume"), and Create / Import-from-CV
CTAs; the preview empty state is a proper dashed resume-sheet placeholder.

**TalentSearch.tsx — tokenized + shell-aligned.** Score bars used hardcoded hex
(dark-mode broken) → semantic token classes. Ad-hoc header → `page-shell` +
`PageHeader`. Candidate ranking intelligence (knockout, evidence, per-dimension
scores) was already good — preserved.

**JobPostingForm.tsx / SalaryInsights.tsx — header alignment** to the
design-system heading scale.

### MISCONNECTED / MISSING backend capability → EXPOSED (frontend-only, no
backend changes)

**Admin decision-support alerts.** `GET /admin-api/alerts/`
(`DecisionSupportAlertsView`) was fully built but had no consumer. Added
`AdminAlertsBanner` (new component) shown globally atop the admin console —
surfaces AI cost spikes, stale scrapers, cache failures, missing Celery workers,
overdue GDPR. Added `fetchAdminAlerts` to `services/admin.ts`.

**Scraper run controls.** `POST /admin-api/sources/{uuid}/control/`
(`SourceControlView`, start/stop/pause/run_now) was built but unused. Wired
Run-now + Pause/Resume buttons into `AdminSourcesManager`. Added `controlSource`.

## STILL OPEN (needs a BACKEND change — deliberately NOT done autonomously)
Per the "no backend endpoints without care" rule, these are flagged, not built:
- **P0 — BlockedDomain / ApprovedATS management.** Governs the direct-apply moat.
  Has NO REST endpoint (Django-admin only) → needs a new `admin-api` CRUD pair
  before a frontend screen can exist.
- **P1** — GDPR export/delete action buttons (endpoints exist), plan/subscription
  PATCH editing, intelligence marketing tabs (market-gaps/content-opportunities/
  industry-breakdown/location-insights/admin-trends), richer System Health from
  `apps/monitoring`, company timeline parity, CSV template download, AI
  model-routing panel.
- Admin per-tab **URL routing** (tabs are local state; not deep-linkable) and
  replacing the `Object.entries` key-dump tabs with purpose-built layouts.

## Verification
After each batch and at the end: `tsc --noEmit` clean, `vite build` exit 0,
`eslint` 0 errors (palette-drift guard still reports only 1 — the intentional
shadcn toast destructive variant). No new raw-palette classes introduced.

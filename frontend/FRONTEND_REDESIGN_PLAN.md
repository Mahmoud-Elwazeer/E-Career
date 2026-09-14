# E-Career Frontend Redesign & Improvement Plan

**Status:** Proposal for review — no destructive changes until approved.
**Branch:** `frontend-renewal-2026-09` (off `development`, uncommitted).
**Approach:** Audit → Plan → Preserve → Refactor → Redesign → Integrate → Improve → Test.
**Non-negotiable:** Do not break backend APIs, auth, routes, data, or working flows.

---

## 0. How this plan uses the provided design resources

The repo is **already built on the right foundation**: `shadcn/ui` = **Radix UI** primitives + Tailwind, with the components **owned** in `src/components/ui/` (verified: `accordion.tsx` imports `@radix-ui/react-accordion`, ~50 owned UI components exist). This is precisely the "owned component foundation" model. Therefore:

| Resource | Decision | Rationale |
|---|---|---|
| **Radix UI** | **Keep as foundation** (already in use via shadcn) | Every primitive already wraps Radix. No new dependency. |
| **Magic UI / Aceternity UI** | **Adapt selected components into owned files** (landing only) | MIT, copy-paste. Port: animated grid/bento, marquee (trust logos), number ticker, spotlight/beam background, animated gradient. Used ONLY on marketing surfaces. |
| **Stripe Design, Apple HIG** | **Principles only** | Hierarchy, spacing rhythm, restraint. No code. |
| **Material (MUI), Fluent, Carbon, Polaris, Base Web** | **Pattern reference only — NOT installed** | Full competing systems; installing conflicts with Tailwind/shadcn and fragments the UI. Borrow UX patterns (Polaris tables/empty-states, Carbon dense data, Fluent command bars, Stripe pricing) reimplemented in our system. |
| **Ark UI / Park UI / Ariakit** | **Not adopted as dependencies** | Alternative headless models; mixing with Radix creates two a11y systems. Would require re-owning every primitive with no net gain. |

**Guiding rule:** own our components, adapt useful patterns, avoid dependency lock-in, keep ONE coherent system. Marketing pages are expressive; dashboards stay fast, dense, and calm.

---

## 1. Current-state audit (verified against code)

### Architecture
- **Stack:** React 18 + Vite 5 + TS, React Router 6, TanStack Query 5, Tailwind 3, shadcn/Radix, framer-motion 12, i18next (EN/AR + RTL), recharts.
- **Entry/shell:** `App.tsx` (providers + routes, now code-split), `components/Layout.tsx` → `AuthNavbar` + `Footer` + `PageTransition`.
- **State:** TanStack Query for server state; `use-auth`, `use-theme` contexts; localStorage tokens. **No Redux — keep it that way.**
- **API:** `services/client.ts` `apiRequest()` — versioned base, JWT auto-refresh, envelope unwrap. Domain services in `services/*`.
- **Design tokens:** `index.css` defines light/dark/**night** themes, surface/status/sidebar tokens, radius/shadow/motion scales, RTL. `motion-tokens.ts` centralizes durations/eases/presets.

### What already works (PRESERVE)
- Auth (login/register/reset/refresh), route guards (`RequireAuth`/`RequireAdmin`/`RequireEmployer`).
- Jobs browse/detail/save/apply; Saved; Alerts; Applications.
- Profile CRUD + CV upload; Resume builder (CRUD + export); Recommendations; TalentScore.
- Employer: dashboard, register, post-job, talent-search; Rasheed chat + widget; Interviews; Coding; Assessments; Salary; Notifications + preferences; Admin console; Settings.
- i18n EN/AR, three themes, motion library, ~50 shadcn components.

### Fixed already this session (baseline for redesign)
- Green gate: **lint 0 errors, 25/25 tests, tsc clean, build OK**.
- Logo installed + `Logo` component (theme-inverting).
- Jobs error/retry + debounce; JobCard date hardening.
- EmployerDashboard + ProfilePage + Settings rewritten to tokens/shell/bilingual with real states.
- Token migration across ~20 pages; shells unified via `AppShell`; RashidMiniChat tokenized.
- Code splitting: entry bundle 1.34 MB → 475 kB.
- Shared primitives added: `AppShell`, `PageHeader`, `StatCard`.

### Remaining problems to solve in this overhaul
1. **Landing page** is dense/single-file and not a strong conversion experience.
2. **Navbar** is functional but flat — no mega-menus, weak candidate/employer separation, secondary items hidden on desktop.
3. **Visual consistency**: type scale/spacing rhythm inconsistent; cards/tables/forms vary per page.
4. **Data viz** (recharts) unstyled to tokens; heavy (374 kB) and eager on TalentScore.
5. **AI UI** (Rasheed states, streaming, activity) lacks a consistent visual language.
6. **Missing/rough states**: many pages still lack skeletons, standardized empty/error/success.
7. **Accessibility**: focus management in menus/dialogs, contrast in all 3 themes, keyboard flows need a pass.
8. **`any`-heavy services** (201 lint warnings) — type debt, not blocking.
9. **Duplicate/parallel** notification + assistant surfaces; onboarding split.
10. **Admin** is one monolithic file with local-state tabs (no deep-linking).

---

## 2. Design system (the single source of truth)

### 2.1 Color system (keep brand teal `#0A3836`)
- Preserve existing HSL token model in `index.css` (light/dark/night). Brand teal stays `--primary`.
- Add semantic intent tokens already present: success/warning/info/destructive + location-type badges.
- Deliverable: `DESIGN_TOKENS.md` documenting every token + usage rules; audit contrast to WCAG AA in all three themes; adjust `--muted-foreground` where AA fails.
- **Rule:** never hard-code palette classes (`bg-blue-600`). Always tokens. Add an ESLint guard (custom rule or `no-restricted-syntax`) to prevent regressions.

### 2.2 Typography
- Keep Poppins (Latin) + Noto Sans Arabic (RTL). Formalize the scale already in `index.css` (`text-display` … `text-overline`).
- Add responsive clamp() sizing for display/heading on landing. Define line-length limits (`max-w-prose`) for body.
- Deliverable: `Typography` reference in Storybook-style page `/__ui` (dev-only) or the plan doc.

### 2.3 Spacing & layout
- Standardize on an 4px base scale (Tailwind default) with page rhythm tokens: `.page-shell`, `.page-header`, section spacing utilities (already added).
- Container widths: content `max-w-7xl`, prose `max-w-3xl`, forms `max-w-2xl`, editor full-bleed.
- Grid system for dashboards: 12-col responsive; card grids `sm:2 / lg:3 / xl:4`.

### 2.4 Elevation, radius, motion
- Shadows/radii/blur already tokenized — document tiers (flat / raised / overlay / modal).
- Motion: reuse `MOTION` tokens. **Landing = expressive; app = ≤200ms, reduced-motion respected.**

---

## 3. Component library plan (own + adapt)

Legend: **Keep** (exists, good) · **Enhance** (exists, upgrade) · **New** (build, owned) · **Adapt** (port pattern from a kit).

| Category | Plan | Notes |
|---|---|---|
| Buttons | Enhance | Add `xl`/`pill` sizes, loading state prop, icon slots; keep variants. |
| Cards | Enhance | `surface-card` variants: flat/interactive/stat/feature; consistent padding. |
| Forms | Enhance | Standardize with `react-hook-form` + `zod` (already deps); shared `Field`, error/help text, async validation states. |
| Inputs | Keep/Enhance | Add search input, tag/chip input (owned), file dropzone (from Profile), OTP (exists). |
| Dropdowns/Menus | Keep (Radix) | Add mega-menu + nav dropdown components. |
| Modals/Dialogs | Keep (Radix) | Standard `Modal` wrapper w/ transitions, focus trap, sizes. |
| Tables | New (owned) | `DataTable` on `@tanstack/react-table` (already dep): sort, filter, paginate, empty/loading, row actions. Adapt **Polaris/Carbon** data patterns. |
| Tabs | Keep (Radix) | Add URL-synced tabs variant for Admin/Profile. |
| Navigation | Rebuild | Mega-menu navbar (see §5). |
| Sidebars | Enhance | `sidebar.tsx` exists; use for Admin + Employer console shells. |
| Notifications | Enhance | One toast system (sonner) + notification center; kill duplication. |
| Empty states | Enhance | `EmptyState` exists; standardize illustration + action; adapt Polaris. |
| Loading states | New | `Skeleton` variants per surface (card/table/list/detail); route `Suspense` fallback per area. |
| Error states | New | `ErrorState` (retry) + route `ErrorBoundary` per area. |
| Success states | New | Inline success + toast + confetti (landing/onboarding only). |
| Badges | Enhance | Status/quality/match-score/verification badges with tokens. |
| Tooltips | Keep (Radix) | Consistent delay/placement; RTL-aware. |
| Search | New | Global command palette (`cmdk` — already dep) + page search inputs. |
| Filters | New | `FilterBar` + `FilterSheet` (mobile); active-filter chips (exists in Jobs). |
| Pagination | Enhance | Windowed pagination (added in Jobs) → shared component. |
| Data viz | Enhance | Token-themed recharts wrappers: `RadarCard`, `TrendChart`, `BarStat`, `Sparkline`; lazy-load. |
| AI UI | New | `AiActivity` (thinking/typing/streaming), `AiMessage`, `AiSuggestionChip`, `RasheedAvatar` states, streaming cursor. |
| Profile | Enhance | Completion ring, section cards, skill chips, CV status. |
| Job | Enhance | `JobCard` (done), `JobDetailHeader`, `DirectApplyBadge` (exists), `MatchScoreCard` (exists). |
| Talent Pool | Enhance | Candidate card, pool board, add-to-pool, consent badge. |
| Matching | Enhance | `MatchBreakdownModal` (exists) → `MatchRadar` + factor bars. |
| Recommendation | Enhance | Reco card w/ reason chips + match ring. |
| Interview | Enhance | Question runner, voice recorder UI, timeline, feedback report. |
| Dashboard | New | `StatCard` (done) + `DashboardGrid`, `ActivityFeed`, `QuickActions`. |
| Admin | Rebuild | Console shell + URL-routed sections (split monolith). |
| Pricing/packages | New | `PricingTable`, `PlanCard`, feature matrix, billing toggle. Adapt **Stripe**. |

---

## 4. Landing page redesign (marketing surface — expressive)

Full experience, not recolor. Sections, in order:
1. **Hero** — animated gradient/spotlight background (adapted Aceternity), clear H1 value prop, primary CTA (Find jobs) + secondary (For employers), live search, product visual/character.
2. **Trust strip** — real sources/stats only; marquee of source logos.
3. **Value proposition** — 3-pillar: Candidates · Employers · AI (Rasheed).
4. **Feature bento grid** (adapted Magic UI) — Direct-apply verification, Matching, Talent Pool, CV/Career tools.
5. **AI capabilities** — Rasheed demo card w/ animated activity states.
6. **Candidate experience** — workflow (Search → Match → Apply → Interview → Grow).
7. **Employer experience** — post → screen → talent pool → hire.
8. **Interview capabilities** — simulator preview.
9. **Career development** — TalentScore/skills growth.
10. **Trust/verification** — anti-aggregator moat explained.
11. **Platform workflow** — animated step diagram.
12. **Statistics** — CountUp, only real data from `use-landing-data`.
13. **Pricing** — plan cards (if plans API present; else "contact").
14. **Testimonials** — ONLY if real data exists; otherwise omit.
15. **FAQ** — accordion (Radix, exists).
16. **Final CTA** — strong close, dual CTAs.
17. **Footer** — redesigned, grouped links, logo, language/theme.

Animation budget: scroll reveals, parallax hero, number tickers, hover lifts — all `prefers-reduced-motion` safe.

---

## 5. Navbar redesign

- **Public navbar:** logo, mega-menu triggers (Product, For Candidates, For Employers, Pricing, About), Sign in, primary CTA. Hover → contextual mega-menus (grouped feature links + preview). Radix NavigationMenu (owned `navigation-menu.tsx` exists).
- **App navbar (candidate):** primary (Jobs, Rasheed, Resume, Interviews, For You), secondary in a grouped menu; notification bell; user menu.
- **App navbar (employer):** Dashboard, Post Job, Talent Search, Candidates, Analytics; clear separation.
- **Admin:** console sidebar shell (not top nav).
- Active states, smooth transitions, full mobile sheet with grouped sections, RTL-correct. Not over-built.

---

## 6. Page-by-page plan (every route)

**Public/Marketing:** Landing (rebuild §4), About (enhance), Login/Register (redesign split layout + trust panel), ResetPassword (align), ApiDocs (token pass).
**Onboarding:** unify into one server-backed flow; progress UI; skip/resume.
**Candidate:** Profile (done — polish), Career Identity/TalentScore (token viz + actions), CV Builder (keep editor, polish top bar + templates), Cover Letter (align), Job discovery (done — polish filters), Job detail (redesign header/apply), Search (global palette + results), Recommendations (reco cards + reasons), Matching (radar + factors), Applications (timeline/status), Saved, Alerts.
**Interviews:** simulation runner redesign (voice UI, progress, feedback report), Coding (editor polish), Assessments (quiz UI polish).
**Rasheed:** full chat page + widget consistent AI language; streaming/activity states.
**Notifications:** center + preferences (dedupe), consistent.
**Settings:** done — polish.
**Pricing:** new page + plan cards.
**Employer:** Company pages, Dashboard (done — polish + analytics), Job management (list + form), Candidate management (table + pipeline), Screening, Matching, Interview management, Analytics (charts).
**Admin:** split monolith into console shell + URL-routed sections (overview, jobs, companies, sources, users, GDPR, AI costs, feature flags, plans, copilot). Keep all existing endpoints.

Each page must ship: loading (skeleton), empty, error (retry), success feedback, responsive (320→1440+), RTL, keyboard/focus, tokens only.

---

## 7. Cross-cutting improvements
- **A11y:** focus-visible everywhere, focus trap/restore in overlays, aria labels on icon buttons, AA contrast in 3 themes, keyboard nav, `prefers-reduced-motion`.
- **Performance:** keep route code-split; lazy recharts; image `loading`/`fetchpriority`; memoize heavy lists; bundle budget (entry < 500 kB).
- **i18n/RTL:** migrate remaining hard-coded EN strings to keys progressively; logical props (`ms/me/ps/pe/start/end`).
- **Type safety:** replace `any` in services incrementally with response models (reduce 201 warnings).
- **Guardrails:** ESLint rule blocking raw palette classes; keep green gate (lint/test/build) after each phase.

---

## 8. Execution phases (each ends green: lint+test+build)

- **Phase A — Design system core:** tokens doc, type/spacing formalization, enhance Button/Card/Badge/Input/Form/Skeleton/EmptyState/ErrorState, add DataTable/FilterBar/Modal/Pagination/AiActivity. Dev-only `/__ui` gallery.
- **Phase B — Navigation & shells:** mega-menu navbar, footer, PublicShell/AppShell/EmployerShell/AdminShell, mobile nav.
- **Phase C — Landing:** full rebuild (§4) with adapted marketing components.
- **Phase D — Candidate pages:** profile, jobs, job detail, search, recommendations, matching, applications, CV/cover letter, TalentScore.
- **Phase E — Interviews & Rasheed:** simulator, coding, assessments, AI chat/widget.
- **Phase F — Employer + Pricing:** dashboard, job mgmt, candidate mgmt/screening, analytics, company pages, pricing.
- **Phase G — Admin:** console shell + URL-routed sections.
- **Phase H — Cross-cutting:** a11y pass, RTL sweep, perf, type-debt reduction, final verification.

## 9. Safety protocol
- No backend/API/route/contract changes. UI-only.
- Reuse first; refactor when needed; replace only with clear reason (documented per page).
- After each phase: `npm run lint && npm test && npm run build` must pass; manual smoke of touched flows.
- No commits/pushes without your go-ahead. Work stays on `frontend-renewal-2026-09`.
- Adapted kit code lands as **owned files** in `src/components/` (no runtime dep added beyond what's needed).

---

## 10. What I will NOT do
- Not install MUI/Fluent/Carbon/Polaris/Base Web/Ark/Ariakit as dependencies.
- Not rebuild from zero. Not touch backend. Not add testimonials/fake stats.
- Not over-animate dashboards.

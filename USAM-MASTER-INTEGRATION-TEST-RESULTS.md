# USAM Master Integration — Test Results

Scope: the feature-discovery and stable-linking work described in
`USAM-MASTER-FEATURE-LINKS.md`. This document distinguishes what was
actually verified, by what method, from what still needs a real browser
pass against the live production domain.

## What was built

- `frontend/src/lib/return-url.ts` — `sanitizeReturnTo()` / `readNextParam()`,
  the open-redirect guard for the login return-destination mechanism.
- `frontend/src/lib/role-routing.ts` — `postAuthDestination()` now runs every
  `from`/`next` value through `sanitizeReturnTo()` before using it.
- `frontend/src/pages/Login.tsx` — reads `?next=` as a second source for the
  post-login destination (alongside the existing `location.state.from`),
  so an external site can deep-link through login with a plain `<a href>`.
- `frontend/src/components/RequireAuth.tsx` / `RequireRole.tsx` — now
  preserve the query string (not just the path) when redirecting an
  unauthenticated visitor to `/login`.
- `frontend/src/data/feature-catalog.json` + `.ts` — the single canonical
  list of every major feature (33 entries), each with a real route, access
  requirement, bilingual name/description, category, and related features.
- `frontend/src/pages/Features.tsx` (`/features`) — new public discovery
  page rendering the full catalog, filterable by audience, with safe
  gated-login links for anonymous visitors.
- `frontend/src/pages/AdminDashboard.tsx` — the active admin section is now
  driven by `?tab=` instead of local-only `useState`, so every admin screen
  has a stable, bookmarkable, refreshable URL. Added a sidebar link to the
  previously-unlinked `/admin/finance` page.
- Navigation wiring: `/features` added to `PublicNavMenu` (desktop mega
  menu), `AuthNavbar` (both authenticated states' secondary menu + mobile
  sheet), `Footer` (Company column), and a homepage CTA on `Index.tsx`.
- `frontend/index.html` — corrected the canonical URL from the stale
  `https://usam.jobs` to the real production domain `https://jobs.usamif.com`
  (matches `robots.txt`, `deploy/nginx.conf`, and deployment docs).
- `frontend/scripts/generate-usam-master-catalogue.mjs` — regenerates both
  integration catalogue files from the single JSON source of truth.

## Automated checks (actually run, this session)

| Check | Command | Result |
|---|---|---|
| TypeScript compile | `npx tsc --noEmit` | ✅ Pass, zero errors |
| Unit/component tests | `npx vitest run` | ✅ 62/62 passed (8 test files) |
| Production build | `npm run build` | ✅ Succeeds; `Features` page produced its own lazy chunk (`Features-*.js`, ~19 kB / ~6.75 kB gzip) |
| Catalogue generation | `npm run generate:master-catalogue` | ✅ Produced `USAM-MASTER-FEATURE-LINKS.md` + `.json` from 33 entries, no errors |
| Django system check | `manage.py check` | ✅ Clean (3 pre-existing deprecation warnings unrelated to this change; backend was not modified) |

New/changed tests added as part of this work:
- `frontend/src/lib/__tests__/return-url.test.ts` (14 tests) — open-redirect
  protection: absolute URLs, protocol-relative URLs, backslash tricks,
  embedded schemes, control characters, and the valid-path/valid-query cases.
- `frontend/src/__tests__/role-routing.test.ts` (+2 tests) — confirms
  `postAuthDestination` rejects an external URL passed as `from` for both
  the individual and employer role paths.
- `frontend/src/pages/__tests__/Login.test.tsx` (+2 tests) — confirms the
  login flow accepts a safe `?next=` and silently discards an unsafe one
  (no crash, no destructive toast).
- `frontend/src/pages/__tests__/AdminDashboard.test.tsx` (4 new tests) —
  confirms `?tab=` deep-linking: defaults to overview with no param, opens
  directly into the named section, falls back to overview for an unknown
  tab value instead of rendering blank, and that clicking a sidebar item
  updates the active section.

## HTTP-level checks against a local dev server (NOT a browser test)

Ran `npm run dev` (Vite, `localhost:8080`) and issued `curl` requests. This
confirms the SPA shell and routing table serve a `200` for each path — it
does **not** confirm the React component renders correctly, that data
fetching succeeds, or that visual/interactive behavior is correct, since
curl does not execute JavaScript.

| Route | HTTP status |
|---|---|
| `/` | 200 |
| `/features` | 200 |
| `/for-individuals` | 200 |
| `/for-businesses` | 200 |
| `/pricing` | 200 |
| `/about` | 200 |
| `/login` | 200 |
| `/login?next=%2Fapp%2Fjobs` | 200 |
| `/api-docs` | 200 |
| `/app/jobs` | 200 |
| `/admin` | 200 |
| `/admin?tab=rashid` | 200 |
| `/nonexistent-route-xyz` | 200 (SPA shell serves; the `NotFound` component renders client-side) |

## What was NOT tested (explicitly unfinished verification)

No browser-automation tool was available in this environment, so the
following were **not** verified and must be checked manually (or with
Playwright/Cypress/manual QA) before relying on them for the live Master
integration:

1. **Visual/interactive correctness** of `/features` — filter buttons,
   card layout at mobile/tablet widths, RTL mirroring of the breadcrumb
   arrow and card icons, dark/night theme contrast.
2. **Real login round-trip** — an actual sign-in using a real account,
   confirming the browser lands on the exact `next`/`from` destination
   post-authentication (unit tests cover the destination-resolution logic
   in isolation, not the full browser navigation).
3. **Permission-boundary UI** — an employer-only or admin-only route
   rendering the correct "wrong role" redirect in a live session (covered
   by existing `RequireRole` logic + its own prior test coverage, not
   re-verified end-to-end here).
4. **Production domain checks** — none of the `https://jobs.usamif.com`
   URLs in the generated catalogue were actually requested over the
   network. They are correct per the canonical/robots.txt/nginx config
   references found during the audit, but a live check (e.g. an actual
   `curl https://jobs.usamif.com/features`) was not performed as part of
   this change.
5. **Cross-browser/screen-reader behavior** for the new page (keyboard
   focus order, screen reader announcement of the filter buttons'
   `aria-pressed` state).

## Known pre-existing issues flagged (not fixed — out of scope)

- `frontend/public/sitemap.xml` is a stale, hand-written file with fake
  job IDs (`j1`...`j20`, `c1`...`c8`) and the old `usam.jobs` domain. It is
  served as a static file and does not match the real `Job`/`Company` data
  or the real route shapes (`/app/jobs/:id`, not `/jobs/:id`). A real
  sitemap generator exists server-side (`backend/apps/jobs/sitemaps.py`,
  already correctly scoped to `Job.objects.visible()`) but nothing wires
  it to replace the static file at deploy time. Flagging for a separate
  fix — regenerating/removing this file was outside the scope of the
  feature-linking directive.
- `CodingPractice` (`/app/coding-practice`) is intentionally excluded from
  the main individual-features navigation (a documented, deliberate
  decision tied to a future USAM Education migration) but the route and
  catalog entry are both live — included in the catalogue with a note.
- `TalentPools` requires a `talent_pool` entitlement server-side and
  renders a locked state without it; the catalogue entry documents this
  as a note rather than a different `status`, since the route itself is
  fully live for entitled employers.

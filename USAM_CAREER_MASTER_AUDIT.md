# USAM Career — Product Audit for the USAM Master Ecosystem Landing Page

> Audit only. No code was modified to produce this. Findings are grounded in the
> actual E-Career (USAM Career / Jobs) codebase. Items that could not be verified
> from code are explicitly marked _(unverified)_. Forward-looking ideas are under
> **RECOMMENDATIONS**.

---

## 1. Project Overview

| Field | Value |
|---|---|
| Project name | **E-Career** (product brand: **USAM Career / USAM Jobs**) |
| Product purpose | Global direct-employer job discovery + career intelligence platform (find verified roles from original employer sources, understand them, become qualified for them) |
| Production URL | `https://jobs.usamif.com` |
| Platform code (financial namespace) | `C` (Career) — siblings: `E` Education, `F` Freelancing, `K` Kids |
| Frontend framework | React 18 + Vite 5 + TypeScript |
| UI system | Tailwind CSS + shadcn/ui (Radix primitives) + framer-motion |
| Routing | react-router-dom v6 (lazy/code-split routes) |
| Data fetching | @tanstack/react-query |
| Backend framework | Django + Django REST Framework |
| Async / realtime | Celery (workers + beat), Django Channels + Daphne (WebSocket) |
| Database | PostgreSQL (with pgvector; Typesense/Qdrant referenced for search/vectors) |
| Authentication | JWT (SimpleJWT) + django-allauth (Google OAuth scaffolded, hidden in UI) |
| AI integrations | AWS Bedrock model routing (Rasheed assistant, matching, CV/interview AI) |
| Payments | **Native `apps.payments`**: double-entry ledger + provider abstraction; Stripe adapter (real, hosted checkout); AlexBank adapter scaffolded (awaiting credentials) |
| Secrets | AWS Secrets Manager helper (env fallback) |
| Storage | AWS S3 (boto3 present) _(bucket usage unverified in this audit)_ |
| Deployment | AWS EC2 (Ubuntu), nginx serving `frontend/dist`, gunicorn service `usam.service`, Celery worker/beat services |
| Environments | `config/settings/{base,development,production,test}.py` |

**Shared with other USAM products:** the financial platform namespace (`C/E/F/K`)
is explicitly multi-product; the transaction/reference system, ledger, and
provider abstraction in `apps.payments` are designed to be shared across USAM
products. Everything else is Career-specific.

---

## 2. Page / Route Inventory

> Source of truth: `frontend/src/App.tsx`.

### Public routes
| Path | Page | Status | Expose on Master? |
|---|---|---|---|
| `/` | Landing (hero, audience switcher, features, Rasheed) | Implemented | Yes (product entry) |
| `/for-individuals` | Individual audience page | Implemented | Yes (deep link) |
| `/for-businesses` | Employer audience page | Implemented | Yes (deep link) |
| `/about` | About (mission/graph/AI/verified) | Implemented | Optional |
| `/contact` | Contact (mailto form + channels) | Implemented | Optional |
| `/pricing` | Pricing | Implemented | Yes |
| `/login` | Login/Register (+ account-type selector) | Implemented | Yes (auth entry) |
| `/reset-password` | Password reset | Implemented | No |
| `/api-docs` | API docs | Implemented (not guarded) | No |

### Authenticated — individual (`RequireAuth`)
`/app/dashboard`, `/app/jobs`, `/app/jobs/:id`, `/app/companies`, `/app/companies/:id`,
`/app/career-graph`, `/app/skills`, `/app/profile`, `/app/career`, `/app/talent-score`,
`/app/saved`, `/app/alerts`, `/app/recommendations`, `/app/rashid`, `/app/interviews`,
`/app/resume`, `/app/cover-letters`, `/app/applications`, `/app/salary`, `/app/assessments`,
`/app/coding-practice` (route kept; removed from nav — migrating to Education),
`/app/notifications`, `/app/notification-preferences`, `/app/settings`,
`/app/billing` (packages + checkout + transaction history).

### Authenticated — employer (`RequireEmployer`)
`/app/employer/dashboard`, `/app/employer/register`, `/app/employer/post-job`,
`/app/employer/jobs/:id/edit`, `/app/employer/talent-search`.

### Admin (`RequireAdmin`, role = `admin`)
`/admin` (AdminDashboard — many tabs), `/admin/intelligence`, `/admin/finance`
(Financial Control Center).

### Django admin (server-rendered, `is_staff`)
`/admin/` on the backend — raw model control (users, jobs, sources, packages,
ledger, etc.). Separate from the React `/admin`.

### Legacy aliases
`/jobs`, `/jobs/:id`, `/companies/:id`, `/profile`, `/saved`, `/alerts` (RequireAuth).

---

## 3. Feature Inventory (user-facing)

| Feature | What it does | Access | Main route | Status |
|---|---|---|---|---|
| Job discovery/search | Search verified jobs, filters (mode, industry, seniority, salary, etc.) | public browse / auth for detail | `/app/jobs` | Implemented (data depends on ingestion) |
| Job detail + direct apply | Full job view, apply routes to employer/ATS source | auth | `/app/jobs/:id` | Implemented |
| Saved jobs | Save/track jobs | auth | `/app/saved` | Implemented |
| Job alerts | Saved-search alerts | auth | `/app/alerts` | Implemented |
| Recommendations | Personalized matches w/ reasons | auth | `/app/recommendations` | Implemented |
| Rasheed AI coach | Chat, CV/interview/cover-letter help | public (curated) + auth (LLM) | `/app/rashid` + global companion | Implemented |
| Resume/CV builder | Build/export ATS CV | auth | `/app/resume` | Implemented |
| Cover letters | Generate/manage cover letters (job-scoped) | auth | `/app/cover-letters` | Implemented |
| Interview practice | AI voice/coding interview prep | auth | `/app/interviews` | Implemented |
| Talent Score | Employability scoring | auth | `/app/talent-score` | Implemented |
| Career Graph | Skills/gaps/growth paths | auth | `/app/career-graph` | Implemented |
| Skills Explorer | Skills taxonomy browse | auth | `/app/skills` | Implemented |
| Salary insights | Salary benchmarking | auth | `/app/salary` | Implemented |
| Assessments | Skill assessments + badges | auth | `/app/assessments` | Implemented |
| Applications tracking | Track applications | auth | `/app/applications` | Implemented |
| Profile / Career Identity | Candidate profile | auth | `/app/profile` | Implemented |
| Notifications (+prefs) | In-app notifications | auth | `/app/notifications` | Implemented |
| Billing & plans | Buy packages, transaction history | auth | `/app/billing` | Implemented (Stripe key needed for live paid) |
| Employer: post/manage jobs | Create/edit jobs | employer | `/app/employer/post-job` | Implemented |
| Employer: talent search | Search candidate pool | employer | `/app/employer/talent-search` | Implemented |
| Employer dashboard | Hiring overview | employer | `/app/employer/dashboard` | Implemented |
| Admin dashboard | Jobs/verification/sources/users/companies/talent/packages/matching/AI tabs | admin | `/admin` | Implemented (blocked by global render crash — see §15) |
| Admin finance | Revenue/reconciliation/transactions | admin | `/admin/finance` | Implemented |
| Coding practice | Coding challenges | auth | `/app/coding-practice` | Implemented; removed from Career nav (Education-bound) |

---

## 4. User Types / Roles

Backend role field `AppUser.role` = `user | employer | admin`. Employer org
modelled via `Company` + `EmployerProfile` + `EmployerTeamMember`
(owner/admin/recruiter/hiring_manager/viewer).

| Role | Entry | Dashboard | Notes |
|---|---|---|---|
| Individual (`user`) | `/login` (account type "Individual") | `/app/dashboard` | Full candidate feature set |
| Employer (`employer`) | `/login` → "Company" → `/app/employer/register` | `/app/employer/dashboard` | Billing scoped to Company |
| Admin (`admin`) | `/login` → `/admin` | React `/admin` + Django `/admin/` | Needs `is_staff` for Django admin |
| Team roles | via `EmployerTeamMember` | employer surfaces | owner/admin/recruiter/hiring_manager/viewer |

---

## 5. Key User Journeys

- **Visitor → job seeker:** `/` → For Individuals → `/login` (Individual) → `/app/dashboard` → build profile/CV → recommendations → apply direct.
- **Visitor → employer:** `/` → For Businesses → `/login` (Company) → `/app/employer/register` (attach company) → `/app/employer/dashboard` → post job / talent search.
- **Purchase:** `/app/billing` → pick package → checkout (Stripe hosted / free instant) → webhook → ledger + entitlement → transaction history.
- **Rasheed:** any page → floating companion → chat (public curated or authed LLM) → deep-link to feature.

---

## 6. Navigation Audit

- **Public navbar** (`PublicNavMenu`): "For Individuals" mega-menu, "For Employers" mega-menu (both with "Explore all" → audience pages), Pricing, About, Contact. Logged-out desktop.
- **Audience switcher** (landing + link mode): Individuals / Businesses / Governments("Soon", disabled).
- **Authenticated navbar** (`AuthNavbar`): individual vs employer arrays swap on `role==='employer'`. Individual primary: Home/Jobs/Rasheed/Resume/Interviews/For You; secondary dropdown incl. Billing, Settings. Employer primary: Dashboard/Post Job/Talent Search; secondary: Browse Jobs, Billing & Plans, Settings.
- **Footer**: For Individuals / For Employers / Company (Pricing, About, Contact, API Docs).
- **Gaps/notes:** admin nav to `/admin/finance` not surfaced in main nav (reached by URL); Governments intentionally disabled; Coding Practice intentionally removed from Career nav.

---

## 7. Design System

**Source of truth:** `frontend/src/index.css` (CSS custom properties per theme:
`:root` light, `.dark`, `.night`) + `frontend/tailwind.config.ts` + `frontend/src/lib/motion-tokens.ts`.

- **Brand color:** teal — `--primary: 178 72% 13%` (#0A3836) in light. Signal/accent amber. Warm-paper light background (`40 30% 97%`). Dark/night themes use a **brand green** hue family (~183/184) with green-tinted surfaces + subtle green glow (not blue-gray, not neon).
- **Semantic tokens:** `--background, --foreground, --card, --primary, --secondary, --accent, --muted, --border, --ring, --success, --warning, --info, --destructive, --signal`, sidebar tokens, location-badge tokens, shadow scale, `--shadow-glow`.
- **Typography:** display serif (Fraunces) for headings/wordmark; sans body. Utility classes: `text-display-serif`, `text-heading-2/3`, `text-body`, `text-caption`, `eyebrow-mono`.
- **Components (shadcn/ui):** `frontend/src/components/ui/*` — button, card, input, label, textarea, badge, tabs, dropdown-menu, navigation-menu, sheet, tooltip, sonner (toast), etc.
- **Motion:** `frontend/src/components/motion/*` — PageTransition, RouteTransition, ScrollReveal, StaggerContainer/Item, AnimatedCard, TextReveal. Reduced-motion aware.
- **Visual language:** rounded cards (`card-premium`, `card-accent-top`), `icon-tile`, `chamber chamber-grid` hero, `glow-blob`, `hero-gradient`, `signal-dot`, `press-feedback`. RTL-aware throughout.
- **ESLint palette guard:** blocks raw Tailwind palette classes to keep tokens consistent.

---

## 8. Brand Assets

| Asset | Path |
|---|---|
| Brand wordmark (SVG, vector-traced real logo) | `frontend/src/components/Logo.tsx` (`BRAND_PATH`) |
| Logo SVG file (favicon/meta) | `frontend/public/logo.svg` |
| Logo PNGs (master 1920×1080) | `frontend/public/logo.png`, `logo-usam.png`, `logo-dark.png` |
| Favicon | `frontend/public/favicon.ico` + `<link rel=icon svg>` in `index.html` |
| OG image | `frontend/public/og-image.png` |
| Rasheed hero character (animated SVG) | `frontend/src/components/rashid/RasheedScene.tsx` |
| Rasheed avatar (round, expression states) | `frontend/src/components/rashid/RasheedAvatar.tsx` |
| Rasheed 3D (opt-in, GLB pipeline) | `frontend/src/components/rashid/RasheedAvatar3D.tsx` (+ `Rasheed3DOrFallback.tsx`) |
| Master brand PNG (source) | `C:\Users\moham\Pictures\Logo.png` (local, not in repo) |

Fonts: Fraunces (display) + sans, loaded via the app's font setup _(exact loader unverified in this audit)_.

---

## 9. AI Features

| AI | Purpose | Where | Endpoint | Provider | Status |
|---|---|---|---|---|---|
| **Rasheed chat** | Career coaching, CV/interview/cover-letter | `/app/rashid` + global `RasheedCompanion` | `POST /api/v1/intelligence/rashid/chat/` (+ `apps/rashid` tools, WebSocket `/ws/rashid/`) | AWS Bedrock (routed) | Implemented |
| Rasheed tools | analyze job / cover letter / interview prep / cv review / career path | Job detail + companion (`rashid:open-tool` event) | `apps/rashid` tool endpoints | Bedrock | Implemented |
| Matching / recommendations | Scored job matches w/ reasons | `/app/recommendations` | `apps/search` recommendation engine, `apps/intelligence` | Bedrock/embeddings | Implemented |
| Interview simulation | AI mock interviews (+ coding) | `/app/interviews`, `/app/coding-practice` | `apps/interviews` | Bedrock | Implemented |
| CV analysis / skills extraction | Parse CV, map skills | resume/profile | `apps/career`, `apps/resume` | Bedrock | Implemented |
| Talent Score | Employability scoring | `/app/talent-score` | `apps/career` | model + rules | Implemented |

- **Public vs authed:** the global companion answers anonymous visitors with curated responses; authenticated users get the real LLM.
- **Model routing:** AWS Bedrock, intended to discover models dynamically for quality-per-cost (per project guidance).

---

## 10. AI Guide / Character — "Rasheed"

- **Name/role:** Rasheed, the AI career coach (sole AI character — there is no "Masar").
- **Visual identity:** modern geometric assistant — smart-glasses visor with glowing teal eyes, support headset with pulsing mic light, brand-teal palette. Consistent across hero (`RasheedScene`), round avatar (`RasheedAvatar`), and chat.
- **Presence:** global floating companion on **every** page (public + authed), route-aware proactive nudges; a dedicated chat page at `/app/rashid`.
- **Can:** explain platform, summarize jobs, review CV, prep interviews, draft cover letters, guide onboarding, hand off to features via events.
- **Cannot (by design):** unrestricted financial authority; sensitive financial actions require explicit auth/confirmation.
- **Assets:** `frontend/src/components/rashid/` (`RasheedScene.tsx`, `RasheedAvatar.tsx`, `RasheedCompanion.tsx`, `rasheed-state.tsx`, 3D pipeline files).

---

## 11. API / Route Map (selected, no secrets)

Base: `/api/v1`. Envelope: `{success, data, message, errors}` (unwrapped by client).

| Method | Path | Purpose | Auth | Role |
|---|---|---|---|---|
| POST | `/auth/register/`, `/auth/login/` | Auth | No | — |
| GET | `/users/me/` | Current user | Yes | any |
| GET | `/jobs/` | List jobs (quality-gated) | No | — |
| GET | `/jobs/<slug>/` | Job detail | No | — |
| POST | `/jobs/<slug>/ask-rashid/` | Rasheed on a job | Yes | user |
| POST | `/intelligence/rashid/chat/` | Rasheed chat | Yes | user |
| GET | `/career/recommendations/` | Recommendations | Yes | user |
| GET/POST | `/resume/resumes/` … `/resume/export/` | Resume CRUD/export | Yes | user |
| GET/POST | `/career/cover-letters/`, `/career/cover-letter/<uuid>/detail/` | Cover letters | Yes | user |
| POST | `/employer/register/` | Attach employer profile | Yes | user→employer |
| GET | `/payments/packages/` | Sellable packages | No | — |
| POST | `/payments/checkout/` | Create order + checkout | Yes | any |
| GET | `/payments/orders/<ref>/` | Order status (owner) | Yes | owner |
| GET | `/payments/transactions/` | User financial history | Yes | any |
| POST | `/payments/webhooks/<provider>/` | Provider webhook (signed, idempotent) | No (signature) | — |
| GET | `/payments/admin/overview\|ledger\|reconciliation\|transactions\|audit` | Financial control center | Yes | admin |
| GET/POST | `/admin-api/plans/`, `/subscriptions/`, `/talent-pools/`, `/companies/`, `/celery-beat/<id>/toggle/` | Admin control | Yes | admin |

---

## 12. Data Model (key entities)

- **Identity/org:** `User(role)`, `Company`, `EmployerProfile`, `EmployerTeamMember(role)`.
- **Jobs:** `Job` (quality_state, direct_apply_url, apply_url_verified, ats_platform, source), `Source` (ats_platform, schedule_cron), `Company`, `Tag`.
- **Verification:** `VerificationResult`, `BlockedDomain` (aggregators), `ApprovedATS` (allow-list).
- **Career:** `CareerProfile`, `TalentScore`, `InterviewSession`, `CoverLetter`, `CareerGoal`, `OnboardingProgress`.
- **Resume:** `Resume` (uuid-keyed), `ResumeTemplate`, `ResumeExport`.
- **Entitlements:** `SubscriptionPlan` (limits/flags), `CompanySubscription` (org-scoped lifecycle).
- **Payments (`apps.payments`):** `Package` → `SubscriptionPlan`, `Coupon`, `Order`, `Payment`(+`PaymentAttempt`, state machine), `Invoice`/`InvoiceItem`, `Refund`, `WebhookEvent`, `FinancialAuditLog`; **Ledger:** `LedgerAccount`, `LedgerTransaction`, `LedgerEntry`, `IdempotencyKey` (balances derived, not stored).

---

## 13. Analytics / Tracking

- Backend structured logging + monitoring service (`apps.core.monitoring_service`), admin click/search/conversion analytics (`AdminDashboard` AnalyticsTab), Sentry SDK present. Financial analytics from real ledger/orders (`apps/payments/analytics.py`).
- **RECOMMENDATIONS (not built):** cross-product funnel events for the Master Page (product_card_view, product_choose, redirect_to_product), unified attribution across C/E/F/K.

---

## 14. Mobile / Responsive

- Tailwind breakpoints (`sm/md/lg/xl`). Mobile nav via `Sheet` in `AuthNavbar`; RTL-aware. Hero/cards/switcher responsive. _(No systematic mobile QA performed in this audit; treat mobile polish as unverified.)_

---

## 15. Current Problems

**CRITICAL**
- **Global React render crash** reported on production ("Something went wrong" on every route). Not reproduced by static analysis or the 23 passing frontend tests; needs the live **browser console error** to pinpoint. Blocks all React pages incl. `/admin`. Django admin (`/admin/` backend) is unaffected (server-rendered).
- **Admin access:** app admin requires `role='admin'`; Django admin requires `is_staff/is_superuser`. A test account was not staff (login rejected) — must be promoted.

**HIGH**
- Job volume low until ingestion runs (`seed_approved_ats`, `setup_sources --purge-aggregators`, `run_scrapers`); scraping not auto-scheduled (no PeriodicTask rows / scheduler mismatch).
- Paid checkout needs `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` in secrets to go live (free plan works now).

**MEDIUM**
- Duplicate scrape code paths (`orchestrator.py` vs `tasks.py`); some ATS connectors (icims/oracle/sap) not wired; `workday` is a stub.
- AlexBank adapter scaffolded (raises until real contract/creds).

**LOW**
- Legacy route aliases retained; Coding Practice route retained but de-navigated; server disk was near-full earlier (now ~76%).

---

## 16. Master Landing Page Readiness

- **Product identity:** USAM Career — verified direct-employer job discovery + career intelligence.
- **Core promise:** find real opportunities from original employer sources, understand them, and become qualified for them.
- **Target audiences:** individuals/job seekers/professionals; companies/employers; (governments — planned).
- **Main features to present:** verified job search, Rasheed AI coach, CV/resume builder, interview prep, recommendations, Talent Score, employer hiring suite.
- **AI to present:** **Rasheed** (career + hiring AI coach).
- **Entry points / deep links from Master Page:**
  - Career product home → `https://jobs.usamif.com/`
  - Individuals → `/for-individuals`
  - Businesses → `/for-businesses`
  - Pricing → `/pricing`
  - Rasheed (post-login) → `/app/rashid`
  - Jobs → `/app/jobs`
  - Sign in / up → `/login`

---

## 17. Master Page Content Data (JSON)

```json
{
  "product": "USAM Career",
  "tagline": "Find verified jobs from real employers — and become qualified for them.",
  "description": "A global direct-employer job discovery and career intelligence platform. Verified roles from original employer sources, an AI career coach (Rasheed), CV and interview tools, recommendations, and an employer hiring suite.",
  "targetUsers": ["Job seekers", "Professionals", "Students & graduates", "Employers / companies", "Recruiters"],
  "coreOutcomes": [
    "Discover verified, direct-apply jobs",
    "Build an ATS-ready CV and cover letters",
    "Prepare for interviews with AI",
    "Get scored, explained job matches",
    "Hire faster with candidate search & talent pools"
  ],
  "features": ["Verified job search", "Direct-apply", "Rasheed AI coach", "Resume builder", "Cover letters", "Interview practice", "Recommendations", "Talent Score", "Career Graph", "Skills Explorer", "Salary insights", "Assessments", "Employer job management", "Talent search", "Billing & packages"],
  "aiAgents": [
    {"name": "Rasheed", "role": "Career + hiring AI coach", "prelogin": true, "postlogin": true, "route": "/app/rashid"}
  ],
  "importantRoutes": ["/", "/for-individuals", "/for-businesses", "/pricing", "/login", "/app/dashboard", "/app/jobs", "/app/rashid", "/app/employer/dashboard", "/admin", "/admin/finance"],
  "deepLinks": [
    {"label": "For Individuals", "route": "/for-individuals"},
    {"label": "For Businesses", "route": "/for-businesses"},
    {"label": "Jobs", "route": "/app/jobs"},
    {"label": "Rasheed AI", "route": "/app/rashid"},
    {"label": "Pricing", "route": "/pricing"}
  ],
  "brandColors": [
    {"name": "primary", "value": "hsl(178 72% 13%)", "hex": "#0A3836"},
    {"name": "dark-surface", "value": "hsl(183 26% 9%)"},
    {"name": "signal-amber", "approx": "#F2B44C"}
  ],
  "brandAssets": ["frontend/public/logo.svg", "frontend/public/logo.png", "frontend/public/og-image.png", "frontend/src/components/Logo.tsx", "frontend/src/components/rashid/RasheedScene.tsx"],
  "navigation": ["For Individuals", "For Employers", "Pricing", "About", "Contact"],
  "userRoles": ["user", "employer", "admin"],
  "integrations": ["AWS Bedrock (AI)", "Stripe (payments)", "AlexBank (scaffolded)", "AWS Secrets Manager", "PostgreSQL/pgvector", "Typesense/Qdrant", "Celery/Channels", "Sentry"],
  "platformCode": "C"
}
```

---

## 18. File Map

| Area | Path |
|---|---|
| Frontend root | `frontend/` |
| App routes | `frontend/src/App.tsx` |
| Pages | `frontend/src/pages/*` |
| UI components | `frontend/src/components/ui/*` |
| Motion | `frontend/src/components/motion/*` |
| Rasheed / AI character | `frontend/src/components/rashid/*` |
| Navbar / nav | `frontend/src/components/AuthNavbar.tsx`, `PublicNavMenu.tsx`, `Footer.tsx` |
| Logo / brand | `frontend/src/components/Logo.tsx`, `frontend/public/logo.svg` |
| Design tokens | `frontend/src/index.css`, `frontend/tailwind.config.ts`, `frontend/src/lib/motion-tokens.ts` |
| API client | `frontend/src/services/client.ts` |
| Billing UI/service | `frontend/src/pages/Billing.tsx`, `AdminFinance.tsx`, `frontend/src/services/billing.ts`, `adminFinance.ts` |
| Role routing | `frontend/src/lib/role-routing.ts` |
| Backend root | `backend/` |
| Settings | `backend/config/settings/*` |
| URL root | `backend/config/urls.py` |
| Jobs | `backend/apps/jobs/*` |
| Scraper (ingestion) | `backend/apps/scraper/*` (orchestrator, `ats/` connectors) |
| Verification (moat) | `backend/apps/verification/*` |
| Career / AI | `backend/apps/career/*`, `backend/apps/intelligence/*`, `backend/apps/rashid/*` |
| Resume / interviews | `backend/apps/resume/*`, `backend/apps/interviews/*` |
| Employers | `backend/apps/employers/*` |
| Entitlements | `backend/apps/core/models.py` (SubscriptionPlan, CompanySubscription) |
| **Payments / financial core** | `backend/apps/payments/*` (models, `models_ledger.py`, `ledger.py`, `providers/`, `services.py`, `analytics.py`, `admin_views.py`, `secrets.py`) |
| Prior audits | `audit/PHASE0_INGESTION_AUDIT.md`, `audit/FINANCIAL_AND_ROLE_AUDIT.md`, `audit/PRACTICE_ENGINE_MIGRATION_TO_EDUCATION.md` |

---

## RECOMMENDATIONS (not existing functionality)

- Master Page should deep-link into product features (routes above), not just the homepage.
- Add cross-product analytics events for choose→redirect attribution across C/E/F/K.
- Resolve the global React crash (needs live console error) before featuring `/admin` externally.
- Run the ingestion runbook so Career shows real job volume before the Master launch.
- A shared USAM identity/SSO across products would let the Master Page pass an authenticated session into Career (not currently implemented).

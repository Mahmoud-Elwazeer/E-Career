# E-Career (USAM Jobs) — Frontend Redesign Research & Design Plan

**Date:** 2026-09-21
**Status:** Research and planning deliverable — NOT an implementation. Per explicit
instruction, no page rebuild starts until this plan is reviewed and approved.
**Scope of this document:** Phases 1–5 of the requested process (audit, reference
research, design direction, design system, motion system) plus the full "REQUIRED
OUTPUT" checklist. Phases 6–15 (actual page-by-page rebuild) are sequenced at the
end as the next step, not executed here.

**Sources used:** direct reads of the live codebase (frontend + backend), the
existing `frontend/FRONTEND_REDESIGN_PLAN.md` and `RASHEED_3D_ASSET_SPEC.md`,
the most recent code-verified audit (`audit/CODE_VERIFIED_RECONCILIATION_2026-09-10.md`),
the 14 style-reference documents in `C:\Users\moham\Desktop\designs`, and targeted
web research on motion tooling and ATS/career-platform UX patterns. `C:\Users\moham\Desktop\jooob`
was checked and is empty — nothing to incorporate from it.

---

## 0. The single most important finding before anything else

**A serious, code-verified redesign plan already exists in this repo** at
`frontend/FRONTEND_REDESIGN_PLAN.md`, on an uncommitted branch `frontend-renewal-2026-09`.
It independently arrives at almost the same conclusions this document does: keep
shadcn/Radix, don't add a competing UI kit, rebuild the landing page and navbar,
formalize the existing token system, fix inconsistent shells, add missing loading/
error/empty states. Some of its "fixed already this session" claims (code splitting,
EmployerDashboard/ProfilePage/Settings rewrites, lint/test/build green) were verified
as real by the independent `CODE_VERIFIED_RECONCILIATION_2026-09-10.md` audit.

**Decision: this new plan supersedes and consolidates the old one rather than
duplicating it.** Where they agree, that's confirmation. Where they differ, this
document reconciles using the newer reconciliation audit's findings (which actually
ran tests/build/lint, not just read source) and the Desktop design references,
which the old plan didn't have access to. Section 12 below tracks every point of
difference explicitly.

---

## 1. Current frontend assessment

**Stack (verified, healthy, no conflicts):** React 18.3 + Vite 5 + TypeScript 5.8,
React Router 6, TanStack Query 5 for server state (no Redux — correct, keep it that
way), Tailwind 3 with a real HSL-token design system, shadcn/ui on Radix primitives
(~50 owned components), framer-motion 12, i18next EN/AR with RTL support, recharts
for data viz, react-hook-form + zod for forms, three.js/@react-three/fiber/drei for
the Rasheed 3D fallback path.

**API client:** Single source of truth, `services/client.ts`. The historically
documented `client.ts` vs `api.ts` duplicate-client bug that broke Recommendations
**is fixed in the code that exists today** — there is no `services/api.ts`
anywhere in the tree. However, `frontend/HTTP_CLIENT_MIGRATION.md` still describes
migrating to a hypothetical axios-based `lib/api.ts` that was never built and never
will be needed; it actively contradicts current code and should be deleted. The
same bug pattern has re-emerged in two isolated spots instead: `InterviewPractice.tsx`
and (per the reconciliation audit) other ad hoc `fetch()` calls that bypass the
shared client's JWT auto-refresh. `axios` is also still listed in `package.json`
dependencies despite zero usage anywhere in the codebase — dead weight from the
same abandoned migration.

**Design tokens already exist and are good:** `index.css` defines light/dark/night
themes as HSL CSS variables, a brand teal (`#0A3836`), a warm paper background
instead of cold gray, a single amber signal accent, full type/spacing/radius/shadow/
motion scales, and `prefers-reduced-motion` handling with a View Transition API
theme switch already implemented. This is a materially better starting point than
"redesign from zero" — the problem is inconsistent **application** of these tokens,
not their absence.

**Routing:** ~30 pages under `/app/*`, code-split via `lazy()` (only Index/Login/
Jobs/JobDetail/NotFound eager-load), guarded by `RequireAuth`/`RequireAdmin`/
`RequireEmployer`. A few legacy duplicate routes (`/jobs`, `/profile`, etc. outside
`/app/*`) exist and should be cleaned up, not multiplied further.

**No dedicated "Dashboard" page exists.** Post-login, users land on `/app/jobs`,
which serves as a de facto home screen. This is a real product gap (not a bug) that
the redesign should address — see §9.

---

## 2. Current landing page assessment

`pages/Index.tsx` composes ~15 sections: Hero → QuickFilters → Featured jobs
carousel → How It Works → Feature bento grid → Career Tracks (hardcoded fake
numbers, flagged) → Categories grid → Company Spotlight → Saved Jobs Teaser →
Stats Strip → "Why USAM" → FAQ → Employer CTA → Final CTA. Heavy, consistent use
of framer-motion (`whileInView`, staggered reveals, `useReducedMotion` guards
throughout — accessibility here is already good). No Lottie/GSAP/Rive currently.

**Real problems, not cosmetic ones:**
- It's a monolithic single file with 15 sections and no clear narrative arc — too
  much density, not enough breathing room, per both the old plan's own audit and
  visual-density concerns in the user's brief.
- `CareerTracks.tsx` shows **hardcoded, static salary/count figures** captioned
  "real counts load from API on jobs page" — this is exactly the kind of
  fabricated-looking data the user's brief explicitly forbids. Fix: either wire it
  to real data or remove the specific numbers and keep only real category links.
- The product is described through generic feature cards more than *demonstrated*.
  There's no interactive product preview, no live "watch Rasheed find you a job"
  flow, no real workflow animation — despite the backend and Rasheed system being
  real enough to actually demonstrate live.
- Section order doesn't yet follow a strict "what/who/why/how" comprehension arc —
  it's reasonably good but has redundant CTA moments (employer CTA + final CTA
  both present, plus scattered mid-page CTAs) that dilute rather than reinforce.

## 3. Current navigation assessment

`AuthNavbar.tsx` is a single navbar component branching on auth/role state — no
separate header file, which is a maintainable pattern, not a smell. For
unauthenticated users it already renders a genuine mega-menu (Radix
`NavigationMenu`) with "For Individuals" and "For Employers" dropdowns, each with
a featured panel and multi-column feature grids. This is materially better than
"flat navbar" — the old plan's claim that "navbar has no mega-menu" is **stale**;
the reconciliation-audit-adjacent read of the actual component shows mega-menus
already exist for the public state.

**Real gaps:**
- **No third "Government" audience segment exists anywhere** — the user's brief
  repeatedly asks for Individual/Business/Government structure, but the product
  as built is strictly individual vs. employer. This needs a product decision, not
  just a design one (see §9 open question).
- Authenticated nav is flat pills, not mega-menu — secondary items (Applications,
  Saved Jobs, Companies, Talent Score, Career Graph, Skills Explorer, Alerts,
  Salary, Assessments, Notifications, Settings) are buried in a user dropdown menu,
  effectively hidden from casual discovery. This is the real "important capabilities
  are hidden" problem the brief warns against, just in the logged-in state rather
  than the logged-out one.
- Naming drift: UI says "Rasheed," code/backend says "Rashid" throughout. Cosmetic
  but should be resolved once, platform-wide, as part of the redesign.

## 4. Current Rasheed assessment

This needed the deepest look, and the finding is more nuanced than "static PNG" —
**it's already not a static image**, but it is fragmented and under-realized:

- **Live system:** `RasheedAvatar` (hand-authored SVG, 4 expression states, breathing/
  blink idle animation via Framer Motion) + `RasheedScene` (half-body SVG with a
  "device" whose screen cycles through product moments) + `RasheedCompanion`
  (global floating widget, mounted on every route, route-aware proactive nudges,
  real LLM-backed chat for authenticated users, canned keyword answers for
  anonymous users). None of this is a PNG. It's SVG + Framer Motion, thoughtfully
  built, with an explicit code comment that it's designed to read as "a competent
  HR professional rather than a cartoon mascot" — a good instinct for this domain.
- **A real 3D upgrade path already exists in code** (`Rasheed3DOrFallback.tsx`,
  three.js/R3F, `RASHEED_3D_ASSET_SPEC.md` with a full production brief: GLB ≤10MB,
  Mixamo skeleton, 24 ARKit morphs + 15 visemes for lip-sync, 9 named animation
  clips) — but **no actual `.glb` asset has been produced**, so it always falls
  back to the SVG scene. This is a content/asset gap, not a code gap.
- **A second, dead character system exists in parallel**: `RashidWidget` +
  `RashidCharacter` (6 pose components: bust/wave/thinking/presenting/celebrating/
  listening) with richer tool-routing (CV review, cover letter, interview prep,
  LinkedIn optimizer, course advisor, job analysis, career path) — but it is
  **not mounted anywhere in `App.tsx`**. `AskRashidButton.tsx` (used on Job Detail
  pages) dispatches browser events intended for this dead widget, so "Ask Rasheed
  about this job" **currently does nothing** in the live app. This is a genuine
  functional gap the redesign must close — either revive and merge the richer
  tool-routing into the live `RasheedCompanion`, or delete the dead code, not both.
- **Backend has two competing chat code paths**: `apps/rashid/service.py` and
  `apps/intelligence/agent.py`, with `RasheedCompanion` actually calling the
  `intelligence` one. This is exactly the "career/skills/rashid fragmenting into
  disconnected modules" risk your AGENTS.md flags, manifesting inside Rasheed
  specifically.

## 5. Current design-system assessment

Genuinely strong foundation, inconsistently applied. `index.css` + `tailwind.config.ts`
already define a token system most products would spend a redesign phase building.
The `CODE_VERIFIED_RECONCILIATION_2026-09-10.md` audit's most important finding
for this whole exercise: **Profile, Employer Dashboard, TalentScore, SalaryInsights,
Recommendations, and other "legacy" pages hardcode their own palettes and controls
instead of using the token system**, and **multiple application shells coexist**
(`Layout`+`AuthNavbar` vs. pages that mount `AuthNavbar` directly vs. Profile/
Employer Dashboard bypassing both vs. Admin's own separate shell) — so different
routes render different headers/spacing/transitions. This — not a missing design
language — is the actual root cause of "doesn't feel like one product."

Also confirmed: i18next/RTL are wired at the infrastructure level but **no
component anywhere calls `useTranslation()`/`t()`** — bilingual copy is done via
inline `isAr ? "..." : "..."` ternaries scattered per-component. This works but
isn't real i18n and will not scale; it's a maintenance debt worth flagging even
though it's out of pure-visual scope.

## 6. Current motion/animation assessment

Framer Motion is already the sole animation library, used well and consistently
(reduced-motion guards are present almost everywhere it matters — better than most
production codebases). No GSAP, no Rive, no Lottie, no Spline currently installed
or needed for anything shipped today. The landing page in particular already has a
mature motion vocabulary (`ScrollReveal`, `StaggerContainer`, `StaggerItem`,
`AnimatedCard`, `TextReveal`, `CountUp`, `PageTransition` in `components/motion/`).
The gap is not "no motion system" — it's that motion isn't yet applied with the
same rigor on internal app pages (dashboards, tables, forms) as it is on the
landing page, and Rasheed's animation is siloed in SVG/Framer rather than a real
character rig.

## 7. Page-by-page assessment (individual + employer journeys)

Full detail is in the audit sub-agent findings; condensed table below. "Broken"
means a concrete, reproducible defect with a root cause identified; "Gap" means
missing UI for an existing backend capability; "Real/working" means verified UI +
API wiring both check out.

| Page | Status | Root cause if broken |
|---|---|---|
| Auth (login/register/reset) | Real/working | — |
| Onboarding | Real/working, minor: double-mounted in `Index.tsx` and `App.tsx` | Non-fatal error swallowing |
| Dashboard | **Missing entirely** | No page exists; Jobs list serves as fallback home |
| Profile | Real/working, bypasses shared shell | Hardcoded styles instead of tokens |
| CV/Resume Builder | Real editor + real CRUD + real autosave. **Export button is broken** | `client.ts`'s `apiRequest` calls `res.text()` on a binary PDF/DOCX response, corrupting it; frontend never creates a Blob/download; user sees a fake "Export ready" toast and gets nothing |
| Cover Letter | **Frontend gap** — backend fully built (`career/cover-letter*` routes), zero frontend UI | Never built, not broken |
| Skills / Assessments | Real/working | — |
| Jobs listing / detail | Real/working, most mature service in the app | — |
| Recommendations / Matching | Real/working, one stray duplicate import (cosmetic) | — |
| Applications tracking | **Broken** | Calls `GET /applications/`, which doesn't exist; real endpoint is `GET /users/me/applications/`; 404 is swallowed by react-query into an empty state — users with real applications see "no applications" |
| Interview Simulation | Real, substantial feature, isolated API-client drift | Hand-rolled `fetch()` bypasses shared client's 401 auto-refresh |
| Employer Dashboard | Real/working | — |
| Job posting / management | Real/working; edit route exists in the component but isn't wired into the router | Router gap, not a component bug |
| Talent Search / ranking | Real/working | — |
| Employer analytics / billing / interview scheduling | **Does not exist** | Never built — this is scope the user's brief assumes exists ("employer analytics," "interview management") that isn't in the product today |

**On the user's specific flagged claim ("CV/Resume page is visually empty, buttons
don't work"):** verified false as a blanket statement — the editor is real,
autosave works, most buttons work. The specific true defect is the export feature,
plus the fact that a brand-new user with zero resumes sees a legitimate-but-easy-
to-miss empty state that can *look* like a broken/empty page if the "New Resume"
CTA isn't prominent enough. Both are real, fixable, narrowly-scoped issues — not
evidence the page needs to be rebuilt from scratch.

## 8. Broken/incomplete functionality — consolidated priority list

Carried forward from the reconciliation audit plus this session's findings,
ordered by user impact:

1. **Applications page 404** — wrong endpoint, silently empty for real users. (P0)
2. **Resume export produces nothing** — binary response mishandled by generic
   client. (P0)
3. **"Ask Rasheed about this job" does nothing** — event dispatched, no listener
   mounted. (P0, functional — directly relevant to the Rasheed rebuild)
4. **Employer dashboard links to two unrouted paths** (`/app/employer/jobs`,
   `/app/employer/applications`). (P0)
5. **Settings notification/public-profile toggles have no persistence.** (P0)
6. **Interview Practice bypasses shared client** — session-expiry mid-interview
   hard-fails instead of refreshing. (P1)
7. **No Dashboard/home page** — product gap. (P1, becomes part of navigation
   rebuild since it changes what "logged in home" means)
8. **Cover Letter has no frontend** — backend ready, unused. (P1, net-new page,
   not a redesign of an existing one)
9. **Job posting edit route not wired into router** despite component support.
   (P2)
10. **`HTTP_CLIENT_MIGRATION.md` and unused `axios` dependency** — stale docs/dead
    dependency that could mislead future work. (P2, cleanup)
11. **BlockedDomain allowlist is empty** — the direct-apply-only enforcement
    mechanism is fully built (ingestion-time + employer-posting-time gates both
    exist) but the LinkedIn/Indeed/ZipRecruiter/Monster domains were never seeded
    into the database, so the block doesn't fire yet in practice. **This is a
    backend data-seeding task, not a frontend one, but it materially affects the
    "verified direct-apply" trust story the landing page is supposed to sell** —
    flagging here so it isn't lost. (P1, backend, outside this redesign's
    execution scope but should be raised to whoever owns backend/ops)

None of these require backend architecture changes — they're either a wrong URL,
a missing frontend page for an existing endpoint, an unwired route, or (for #11) a
data-seeding gap. This confirms the user's instruction to "not destroy the backend"
is easy to honor: nothing found here needs backend rework, only frontend fixes and
one admin data-entry task.

---

## 9. Open product questions before design work proceeds

These aren't design decisions — they need a product answer first, because they
change what gets built:

1. **Government audience.** The brief asks for an Individual/Business/Government
   navigation structure repeatedly, but no government-specific feature, page, or
   backend model exists anywhere in the product today. Before designing a
   "Government" nav section, we need to know: is this a real near-term feature
   (e.g., public-sector job categories, government employer accounts, compliance
   reporting) or should the navigation stay two-sided (Individual/Employer) as it
   is today? Building UI for a third audience with no underlying feature would
   violate the brief's own "do not invent unnecessary features" rule. **Recommend:
   keep nav two-sided unless you confirm a government-specific feature set
   exists or is planned.**
2. **Employer analytics, billing, and interview-scheduling pages** are assumed by
   the brief's page list but don't exist in the product. Are these in scope to
   *build new* (not redesign), or should the redesign only cover what exists
   today plus the specific fixes in §8? **Recommend: treat as backlog/Phase-2
   scope, not part of the visual redesign** — building three new employer
   feature areas is a product build, not a UI rebuild, and mixing the two will
   blow up the timeline and risk.
3. **Rasheed 3D asset.** The `.glb` character model doesn't exist. Producing one
   (via Character Creator 4 + Headshot 3, a freelance 3D artist, or similar,
   per `RASHEED_3D_ASSET_SPEC.md`'s own ranked recommendation) is a content
   commission with its own timeline and cost, separate from code work. **Recommend:
   proceed with the SVG/Framer Motion character system now (it's already good),
   treat the 3D upgrade as a parallel, independent content track that plugs in
   later without blocking anything** — this is exactly what the existing fallback
   architecture was built to allow.

---

## 10. Reference research

### 10.1 Desktop design references (`C:\Users\moham\Desktop\designs`, 14 style docs)

These are structured style-reference documents (color tokens, type scales,
component notes) for 14 different products/sites, not screenshots. Assessed for
relevance to an HR/career/AI platform:

**Directly relevant, informing the recommended direction below:**
- **Apple** — restraint, one functional accent color, typography carrying
  hierarchy over decoration, near-white canvas with generous space. Relevant
  principle: chrome recedes, content and product leads.
- **Increase** (fintech/banking) — navy-and-paper institutional palette with
  chartreuse/mint used only as "voltage," monospace companion for data/numbers,
  near-black filled buttons projecting gravitas over enthusiasm. Directly
  analogous to what a career/HR platform needs: trustworthy, not flashy.
- **Linear** — near-black canvas, one electric accent used sparingly, hairline
  borders instead of shadows, 400–510 weight band (no heavy bold), precision-
  machined component geometry. Relevant for the *app/dashboard* surfaces
  specifically (jobs table, employer console, admin) more than marketing pages.
- **Subframe** — monochrome workbench, one serif used only as editorial
  punctuation against a systematic sans, flat bordered surfaces over shadows,
  generous vertical rhythm. Relevant for a calm, confident marketing tone without
  going cold.
- **Hyperstudio** — obsidian canvas carved out by light, hairline structure, a
  single white pill for primary actions, no shadows. Relevant for a dark-mode/
  night-theme treatment given the product already ships a "night" theme.

**Reviewed but not directly relevant** (too decorative/extreme for HR/career
domain trust requirements, noted only so the research is complete): the
brutalist-editorial "AI for Business" reference (oversized uppercase condensed
type, near-neon yellow — too aggressive for a platform mediating job applications
and personal data), the lipstick-magenta magazine reference, the sticker-pastel
"Slush" reference, the high-fashion-editorial "Branding" reference, the
storybook-illustration "MindMarket" reference, the type-foundry "Dylanbrouwer"
reference, and the warm-broadsheet "Wispr Flow" reference (charming but its
serif-at-120px editorial voice doesn't fit dense data screens like Talent Search
or Admin).

**Synthesis, not adoption of any single one:** none of these should be copied
wholesale — per the brief's own instruction. The useful common thread across the
relevant subset is: *one disciplined accent color, real typographic hierarchy
instead of decoration, flat/bordered surfaces over heavy shadows, and restraint on
marketing pages paired with density/precision on data pages.* This validates
rather than replaces the token system already in `index.css` (warm paper canvas,
brand teal, single amber signal) — the existing palette choice is already in the
right family (Increase/Apple-adjacent), it just needs consistent enforcement.

### 10.2 External references

**SaaS/product design (Linear, Notion, Stripe, Vercel, Attio):** consistent
pattern of dense-but-calm dashboards, generous use of monospace for data/IDs,
and marketing pages that demonstrate the product live rather than describing it
in cards — directly supports the brief's "landing page should show the actual
product" requirement.

**AI product references (ChatGPT, Claude, Perplexity, Cursor):** the common
pattern is a calm, low-chrome chat surface with clear state indication (thinking/
typing/streaming) rather than a cartoonish assistant. This supports the existing
instinct in `RasheedAvatar`'s own code comment — "read as a competent HR
professional, not a cartoon mascot" — rather than pushing toward a Duolingo-style
mascot, which would clash with the platform's trust-and-verification positioning.

**Career/recruitment/ATS references (researched: Ashby, Greenhouse, Lever,
LinkedIn, Indeed):** 2026 industry commentary consistently frames Ashby as the
"modern UX + analytics" benchmark and Greenhouse as the "structured hiring,
enterprise-grade" benchmark, with Lever positioned for CRM-style recruiting
workflows. For the **employer-side** surfaces specifically (Talent Search,
future Candidate management/Analytics), Ashby's data-dense-but-clean table and
filter patterns are the more relevant reference than any consumer job board —
this platform's employer console is closer to an ATS than to Indeed/LinkedIn's
consumer browse experience. For the **candidate-side** discovery surfaces,
LinkedIn/Indeed's job-card and filter patterns remain the right familiar mental
model, which the existing `Jobs.tsx`/`JobCard` already roughly follows.

---

## 11. Recommended design direction

**Personality: "Verified professional intelligence."** Not a cartoon AI product,
not a cold enterprise tool, not a maximalist editorial brand. The platform's real
differentiator per its own architecture (direct-apply verification, Career Graph,
Job Quality Engine, an actually-LLM-backed career coach) is *trustworthy
intelligence*, and the visual language should say that before any copy does.

**Concretely, this means keeping and formalizing what's already there rather than
replacing it:**
- **Keep the brand teal (`#0A3836`) and warm paper background** — this combination
  already sits in the same family as the Increase/Apple-adjacent references
  identified as most relevant, and changing the core brand color at this stage
  would be change-for-change's-sake, which the brief explicitly forbids.
  Consolidate every hardcoded per-page color into these tokens.
- **Keep the single amber signal accent, used sparingly** — matches the "voltage"
  principle from Increase/Linear: one accent that means "pay attention here,"
  not decoration.
- **Marketing surfaces (landing, pricing, about) get more visual confidence**:
  larger type moments, live product demonstrations, scroll storytelling —
  informed by Apple/Subframe restraint, not brutalist maximalism.
- **App/dashboard surfaces (Jobs, Profile, Employer console, Admin) get Linear-
  style density and calm**: hairline borders over heavy shadows, tighter
  vertical rhythm, monospace for scores/IDs/dates (the token system already has
  `font-mono-data` — use it consistently for Talent Score numbers, match
  percentages, application IDs).
- **Rasheed stays a professional SVG/Framer character for now**, refined and
  consolidated into one system (see §12), with the 3D upgrade as a separate,
  non-blocking content track.

## 12. Reconciliation with the existing `FRONTEND_REDESIGN_PLAN.md`

| Topic | Old plan said | This audit found | Resolution |
|---|---|---|---|
| Navbar mega-menu | "Navbar is flat, no mega-menus" | Public navbar already has real mega-menus; only the *authenticated* nav is flat | Old claim is stale for logged-out state; scope the navbar work to the authenticated nav + secondary-item discoverability instead of rebuilding from scratch |
| API client | Describes migrating to axios `lib/api.ts` | Never executed; current `services/client.ts` (fetch-based) is the sole, correct client | Delete `HTTP_CLIENT_MIGRATION.md`, remove unused `axios` dependency |
| Design tokens | "Formalize the scale" | Scale already fully formalized in `index.css`; the real problem is non-adoption on ~6 legacy pages | Reframe Phase A from "build tokens" to "enforce tokens + add the ESLint guard against raw palette classes the old plan already proposed" |
| Landing page | "Rebuild, 17 sections" | Confirmed dense/monolithic; `CareerTracks` has fabricated-looking static numbers | Adopt old plan's rebuild intent, but explicitly fix the fake-numbers issue and reduce section count/redundant CTAs |
| Rasheed | Not deeply assessed | Two parallel systems, one dead; "Ask Rasheed" button non-functional; 3D path built but assetless | New, more specific finding — old plan's "keep Rasheed chat+widget" line was too coarse; this needs an explicit unify-or-delete decision (§14) |
| Dashboard | Not mentioned as missing | No Dashboard page exists at all | New finding; add to page-by-page scope |
| Cover Letter | Not mentioned | Backend ready, zero frontend | New finding; add as net-new page, not a "redesign" |
| Applications bug | Not mentioned | Wrong endpoint, silent 404 | New, concrete P0 bug from the newer reconciliation audit |

The old plan's **process discipline is sound and should be kept as-is**: phased
execution (A→H) gated on lint+test+build green after each phase, no backend/API
contract changes, no commits without go-ahead, owned-file adaptation instead of
new UI-kit dependencies. This document doesn't replace that discipline — it
corrects the factual inputs feeding it and adds the specific bugs/gaps found here.

## 13. Dependencies

**Reuse (already installed, suffices for everything scoped here):**
framer-motion (all UI/landing motion), Radix/shadcn (all components), TanStack
Query (data), react-hook-form + zod (forms), recharts (charts, needs token-
styling + lazy-loading, not replacement), lucide-react (icons, see below),
three.js/@react-three/fiber/drei (Rasheed 3D path, already correctly gated
behind an asset-presence check).

**Remove:**
- `axios` — zero usages, leftover from an abandoned migration plan.
- `frontend/HTTP_CLIENT_MIGRATION.md` — describes a plan that was never executed
  and now contradicts the real code; delete or rewrite to reflect reality.
- The dead `RashidWidget`/`RashidCharacter` pose system — **only after** the
  decision in §14 is made (delete outright, or port its tool-routing logic into
  the live `RasheedCompanion` first, then delete the old files).

**New dependencies proposed: none required for the visual/motion redesign
itself.** Framer Motion already covers every animation need identified in this
audit (component transitions, scroll reveals, stagger, layout animations,
reduced-motion). This directly satisfies the brief's "no dependency mess" mandate
— the existing stack is sufficient.

**Conditionally justified, not proposed yet:**
- **GSAP** — only if a specific landing-page section genuinely needs a scrubbed,
  multi-element scroll timeline that Framer Motion's `useScroll`/`useTransform`
  can't express cleanly (e.g., a complex pinned scroll-story sequence). Framer
  Motion's own scroll API is already used for the Stats Strip's scroll-progress
  underline, so most needs are already covered. Recommend: attempt in Framer
  Motion first; only reach for GSAP if a named section genuinely needs it, and
  scope it to that one section as an owned utility, not a platform-wide addition.
- **Rive** — only if/when a real interactive Rasheed character rig is
  commissioned (see §14/§9.3). Not justified today since there's no rig to drive.
  If commissioned, Rive is the right choice over Lottie (state-machine/input-
  driven, not just timeline playback) and over raw three.js/GLB for anything that
  doesn't need true 3D — cheaper to produce, easier to art-direct expressions.

**Icon system:** already consistently `lucide-react` throughout — keep it, no
change needed. The brief's instruction to "choose a coherent icon system" is
already satisfied; this is a non-issue, not a gap.

## 14. Rasheed architecture decision required

Two options, both technically clean, need a product call before implementation:

**Option A — Consolidate into the live system.** Port the tool-routing logic
(CV review, cover letter, interview prep, LinkedIn optimizer, course advisor, job
analysis, career path) from the dead `RashidWidget` into `RasheedCompanion`, wire
`AskRashidButton`'s dispatched events to it, delete `RashidWidget`/`RashidCharacter`/
`RashidBubble`/`RashidMiniChat`/`RashidOnboarding`/`ToolSelector` once the useful
logic is ported. Net effect: one character, one widget, richer capabilities,
smaller codebase.

**Option B — Delete the dead system outright**, keep `RasheedCompanion` exactly
as it is, and separately decide whether "Ask Rasheed about this job" becomes a
simple deep-link into the existing `/app/rashid` chat page (passing job context)
instead of an inline tool panel. Simpler, less work, slightly less capable.

**Recommendation: Option A.** The tool-routing concept (job-specific CV review,
cover letter generation launched from context) is genuinely valuable product
surface that already has backend support (`apps/rashid/tools.py`) and a half-
built frontend — finishing it is cheaper than losing it, and it directly serves
the brief's requirement that Rasheed "help users discover features" and
"proactively communicate when appropriate."

Either way, the backend fragmentation (`apps/rashid/service.py` vs
`apps/intelligence/agent.py` both implementing "chat with Rashid") should be
flagged to backend ownership as a follow-up — it's outside this frontend
redesign's execution boundary (per the "don't touch backend" safety protocol)
but will keep causing drift if left alone.

## 15. Motion system architecture

No new library. Formalize what exists:
- `motion-tokens.ts` (already defines durations/eases/presets) becomes the single
  source every component motion must reference — no ad hoc `transition={{duration: 0.4}}`
  literals scattered in components.
- Marketing pages: expressive tier — scroll reveals, stagger, hero parallax,
  number tickers, already largely built in `components/motion/`.
- App/dashboard pages: restrained tier — ≤200ms, layout animations for list
  reordering/tab switches, no scroll storytelling. This tier is currently under-
  applied on internal pages relative to landing; formalizing the two-tier system
  explicitly (and documenting which tier each surface belongs to) is the actual
  gap, not missing tooling.
- `prefers-reduced-motion` handling is already broadly correct — audit for the
  handful of internal-page animations added outside the `components/motion/`
  primitives to confirm they inherit the same guard.

## 16. Risks

- **Scope creep risk is the largest single risk here.** The user's brief describes
  employer analytics, billing, and interview-scheduling pages that don't exist.
  Building those is a feature build, not a redesign, and conflating the two will
  make "is this done" unanswerable. Mitigated by explicitly carving them out in
  §9.2 as a separate backlog decision.
- **Rasheed consolidation (§14) touches a currently-functional live widget.**
  Must be done carefully with the tool-porting done first and tested before any
  deletion, to avoid regressing the one part of the character system that
  currently works end-to-end.
- **Token-adoption cleanup on legacy pages (Profile, Employer Dashboard,
  TalentScore, SalaryInsights, Recommendations)** touches pages already confirmed
  working — risk is introducing visual regressions while removing hardcoded
  styles. Mitigate with the old plan's own discipline: one page at a time, green
  gate (lint+test+build) after each.
- **BlockedDomain seeding (§8.11)** is a backend/data task adjacent to this
  redesign's trust-and-verification story on the landing page ("verified direct-
  apply," "no middleman"). If the landing page's trust claims get more prominent
  in the redesign (per the brief's request to *demonstrate* verification), it
  becomes more important that the claim is actually enforced in production data,
  not just in code. Flag to backend/ops owner; do not let the frontend redesign
  silently imply a guarantee that isn't yet data-complete.

## 17. Performance considerations

Already tracked well by the old plan and confirmed by the reconciliation audit:
entry bundle already reduced 1.34MB → 475kB via code-splitting; recharts (374kB)
still eager-loads on TalentScore and should move to lazy-load; production build
currently succeeds. Nothing found in this audit changes these numbers or adds new
performance risk, provided no new heavy dependency (a second animation library, a
UI kit) is introduced — which this plan explicitly avoids.

---

## 18. Implementation plan (sequencing for Phases 6 onward)

This is the proposed order for actual implementation, once this plan is approved.
Each phase ends green (lint + test + build) before the next starts, per the
existing plan's own safety protocol, which this document adopts unchanged.

1. **Fix the concrete P0/P1 bugs first** (§8, items 1–6) — these are small,
   isolated, high-value, and de-risk everything else by removing "is this broken
   or is it the redesign's fault" ambiguity during the visual work.
2. **Design system enforcement pass** — consolidate hardcoded per-page styles
   into existing tokens on the ~6 flagged legacy pages; add the ESLint guard
   against raw palette classes; unify the shell fragmentation (`Layout` vs.
   direct `AuthNavbar` mounts vs. bypassed shells) into one consistent shell.
3. **Navigation rebuild** — keep the existing public mega-menu structure (it
   already works), rebuild the authenticated nav for better secondary-item
   discoverability, resolve the Rasheed/Rashid naming drift platform-wide.
4. **Rasheed consolidation** (§14, Option A) — port tool-routing, wire
   `AskRashidButton`, then remove dead code.
5. **Landing page rebuild** — restructure section order/count, fix the
   `CareerTracks` fabricated-numbers issue, add at least one real interactive
   product demonstration (e.g., a live-feeling search-to-match-to-apply sequence
   using real component states, not new fake data).
6. **Core candidate journey polish** — Dashboard (new), Profile, CV/Resume
   (fix export, polish empty state), Applications (fix endpoint), Cover Letter
   (new page against existing backend), Jobs/Recommendations (polish only, both
   already solid).
7. **Employer journey polish** — Dashboard, Job posting (wire edit route),
   Talent Search — polish only; explicitly defer analytics/billing/interview-
   scheduling to the backlog decision in §9.2.
8. **Cross-cutting pass** — accessibility (focus management, contrast in all 3
   themes, keyboard nav), responsive sweep, motion-tier consistency check,
   final platform-wide visual QA.

---

## Summary for review

The product is in materially better shape than the brief assumes: the design
token system, the API client, the mega-menu navbar, and the Rasheed character are
all already real, already reasonably good, and already partially aligned with
what's being asked for. The actual work is: fix five or six concrete, narrowly-
scoped bugs; enforce the existing design system on the handful of pages that
don't use it yet; consolidate Rasheed into one system instead of two; rebuild the
landing page's structure and remove its one fabricated-data issue; add the two
genuinely missing pages (Dashboard, Cover Letter); and make an explicit,
scoped-out decision about the employer features the brief assumes exist but
don't. Nothing here requires new dependencies, new animation libraries, or
backend changes.

Waiting on your decisions for:
- §9.1 — Government audience: build nav for it, or keep two-sided?
- §9.2 — Employer analytics/billing/interview-scheduling: in scope now, or backlog?
- §14 — Rasheed: consolidate (Option A, recommended) or simplify (Option B)?
- Separately, and not blocking the above: the live AWS key and Google OAuth
  secret found in `backend/.env` should be rotated — flagging again here since
  it's a standing security item, not part of the redesign itself.

# E-Career (USAM) — Design System

The single source of truth for the platform's visual language. Everything here is
already implemented in `src/index.css`, `tailwind.config.ts`, and
`src/lib/motion-tokens.ts`. This document explains **what the tokens are, what
they mean, and the rules for using them** so the system stays coherent as pages
are built and refactored.

**Golden rule:** never hard-code a raw Tailwind palette class (`bg-gray-100`,
`text-blue-600`, `border-red-500`, `dark:text-gray-400`, …). Always use a
semantic token. An ESLint rule warns on violations. The token system is the only
thing that themes correctly across light / dark / night and RTL.

---

## 1. Design direction

**"Verified professional intelligence."** A career + hiring operating system that
must read as *trustworthy* first. The visual language is Apple/Increase/Linear-
adjacent restraint — warm paper canvas, one disciplined brand color, one signal
accent, typographic hierarchy over decoration, hairline borders over heavy
shadows. Marketing surfaces are expressive; app/dashboard surfaces are dense and
calm.

## 2. Color system

All colors are HSL CSS variables with three themes (`:root` light, `.dark`,
`.night`). Consume them through the Tailwind semantic names below — never the raw
`hsl(var(--…))` and never a palette number.

| Role | Token / Tailwind class | Meaning |
|---|---|---|
| Brand | `primary`, `primary-hover`, `primary-muted`, `primary-deep` | Brand teal `#0A3836`. Primary actions, active states, "chamber" sections. |
| Signal | `signal`, `signal-foreground` | Single warm amber accent. "Pay attention here" — live dots, key highlights, verification. Used sparingly, never decoration. |
| Canvas | `background`, `foreground` | Warm paper `#F8F6F1` + warm near-black ink. |
| Surfaces | `card`, `surface-1/2/3`, `surface-elevated`, `popover` | Layered surfaces. `surface-2` = card wash, `surface-3` = teal-tinted. |
| Secondary | `secondary`, `accent`, `muted` (+ `-foreground`) | Soft teal mist / neutral fills. `muted-foreground` = secondary text. |
| Status | `success`, `warning`, `info`, `destructive` (+ `-foreground`) | Semantic status only. **Use these instead of green/yellow/blue/red palette classes.** |
| Location | `.location-remote`, `.location-hybrid`, `.location-onsite` | Job location-type badges (bg/text/border baked in). |
| Structure | `border`, `border-subtle`, `input`, `ring` | Warm hairlines + focus ring. |
| Sidebar | `sidebar`, `sidebar-*` | Admin/employer console shells. |

**Palette-class → token cheatsheet** (for refactoring drift):

| Don't write | Write instead |
|---|---|
| `text-gray-400`, `dark:text-gray-400` | `text-muted-foreground` |
| `text-gray-500/600/700` | `text-muted-foreground` or `text-foreground` |
| `bg-gray-50/100` | `bg-muted` or `bg-surface-2` |
| `border-gray-200/700`, `dark:border-gray-700` | `border-border` |
| `text-red-500/600`, `border-red-500` | `text-destructive`, `border-destructive` |
| `text-green-500/600`, `bg-green-500/5` | `text-success`, `bg-success/5` |
| `text-yellow-500`, `border-yellow-500/30` | `text-warning` (or `text-signal`), `border-warning/30` |
| `text-blue-600`, `bg-blue-600` | `text-info` or `text-primary`, `bg-primary` |
| `text-purple-*`, `border-purple-600` | `text-primary` / `border-primary` (no purple in this system) |
| `bg-amber-50 dark:bg-amber-950` | `bg-warning/10` (+ `text-warning` for text) |
| `text-emerald-500` | `text-success` |

## 3. Typography

Three families, loaded once in `index.css`:

- **Poppins** — UI workhorse. Body, nav, buttons, labels, tables, forms. Body
  weight 400, headings 500.
- **Fraunces** (editorial serif) — the signature voice for hero + section
  headers. Opt in via `.font-display`, `.text-display-serif`, `.text-hero-serif`,
  or `.serif-accent` (a single italic serif word inside a sans line).
- **JetBrains Mono** — data/stats/labels only. `.font-mono-data`, `.eyebrow-mono`.
  Use for scores, match %, IDs, counts.

**Type scale utilities** (use these, don't invent `text-[42px]`):
`text-display`, `text-heading-1/2/3`, `text-body-lg`, `text-body`,
`text-caption`, `text-overline`, plus serif `text-display-serif` / `text-hero-serif`.

Arabic: same Poppins stack falls back to Noto Sans Arabic; all layout uses
logical properties (`ps-/pe-/ms-/me-/start/end`) so RTL is automatic.

## 4. Spacing, grid, radius, shadow

- **Spacing:** Tailwind 4px base scale. Page rhythm via `.page-shell` (container +
  vertical padding), `.section-y` (marketing section rhythm).
- **Containers:** content `max-w-7xl` (via `container`), prose `max-w-3xl`, forms
  `max-w-2xl`.
- **Radius:** `rounded-xs → rounded-2xl → rounded-full` (token-backed).
- **Elevation:** `shadow-xs → shadow-xl` + `shadow-glow`. Prefer hairline borders
  over heavy shadows on app surfaces; reserve `shadow-lg/xl` for overlays and
  marketing lift.

## 5. Component primitives (composable CSS classes)

Built in `index.css @layer components`. Reuse these before writing bespoke markup:

- **Page structure:** `.page-shell`, `.page-header`, `.page-title` (serif +
  accent bar), `.page-subtitle`, `.section-heading`.
- **Surfaces:** `.surface-card`, `.surface-card-interactive`, `.paper-card`,
  `.paper-card-interactive`, `.card-premium`, `.card-accent-top`.
- **Marketing/hero:** `.hero-gradient`, `.hero-grid`, `.chamber`, `.chamber-grid`,
  `.glow-blob`, `.glass-panel`, `.section-band`, `.text-gradient-brand`.
- **Bits:** `.eyebrow` / `.eyebrow-mono`, `.pill-tag` / `.pill-tag-signal`,
  `.signal-dot`, `.icon-tile`, `.stat-tile` / `.stat-value` / `.stat-label`.
- **Interaction:** `.hover-scale`, `.press-feedback`, `.link-underline`, `.glass`.

Shared React primitives: `AppShell`, `PageHeader`, `StatCard`, `EmptyState`,
`Skeletons`, plus the full shadcn/ui set in `src/components/ui/`.

## 6. Motion system (two tiers)

Single library: **Framer Motion** (already installed). No GSAP/Lottie/Rive today
(see the redesign plan for when they'd be justified). Tokens live in
`src/lib/motion-tokens.ts` (`MOTION`) and mirror the CSS motion variables.

- **Tier 1 — Marketing (expressive):** scroll reveals, stagger, hero parallax,
  number tickers, hover lift. Use the `components/motion/` primitives
  (`ScrollReveal`, `StaggerContainer`, `StaggerItem`, `AnimatedCard`,
  `TextReveal`, `CountUp`, `PageTransition`).
- **Tier 2 — App/dashboard (restrained):** ≤200ms, layout animations for list/tab
  changes, no scroll storytelling. Keep dashboards calm.

**Rules:** reference `MOTION` tokens instead of inline `{duration: 0.4}` literals;
every motion must respect `prefers-reduced-motion` (the `components/motion/`
primitives and `index.css` already guard this globally).

## 7. Icons

**lucide-react**, exclusively. Consistent stroke/size. Do not mix icon libraries.

## 8. Rasheed (character)

One character system: `RasheedAvatar` (SVG, 4 expression states) + `RasheedScene`
(half-body presenter) + `RasheedCompanion` (global assistant widget), driven by
the semantic `rasheed-state` store (idle/greeting/talking/thinking/…). A 3D GLB
path (`Rasheed3DOrFallback`, three.js) exists and auto-activates if/when a
validated `rasheed.glb` asset is added — until then the animated SVG is the live
character. Any component can open/drive Rasheed via the `rashid:open` /
`rashid:open-tool` window events. Do not introduce a second character
implementation.

## 9. Themes & RTL

Three themes via a root class (`.dark`, `.night`); light is default. Theme switch
uses the View Transition API with a reduced-motion fallback. All three are
first-class — anything you build must look correct in all three, which is exactly
why raw palette classes are forbidden (they only define one or two shades).

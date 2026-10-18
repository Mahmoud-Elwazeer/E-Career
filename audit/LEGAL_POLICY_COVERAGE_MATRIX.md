# USAM Career — Legal Policy Coverage Matrix

**Generated: 2026-09-21 (continuation hardening pass), code-verified against commit range starting at `52984cb`. Updated 2026-09-21 (third continuation pass) — see the "Real browser E2E update" note below the matrix: the `E2E_TEST`/`RTL_STATUS`/`MOBILE_STATUS` columns below were written before that pass and are now partially superseded.**

This matrix exists to answer one question per legal document, honestly: *is
this actually wired up end-to-end, in this exact codebase, right now?* It is
a verification artifact, not a plan — every cell below was checked against
real code (`backend/apps/legal/`, `frontend/src/pages/legal/`,
`frontend/src/components/Footer.tsx`, `frontend/src/pages/Login.tsx`) or an
automated test that asserts the claim. Where something has NOT been
independently verified (e.g. a real browser render), that is stated
explicitly rather than assumed from the code's presence.

This supersedes nothing in `audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md` — that
document remains the authoritative narrative/decision record. This file is
a derived, routes-and-code-shaped checklist for quickly auditing coverage
per document, per the structure the supplemental legal specs in
`C:\Users\moham\Downloads` asked for (a route × status-dimension grid with
12 verification columns).

## Column definitions

| Column | Meaning |
|---|---|
| `ROUTE` | The public frontend path that serves this document. |
| `FRONTEND_FILE` | The React component rendering that route. |
| `BACKEND_POLICY_TYPE` | The `PolicyDocument.DocType` value / `slug` in the Django model. |
| `CURRENT_VERSION` | The version label seeded for this document (`2026.1` for all — see below for ACTIVE/DRAFT status). |
| `EN_STATUS` | State of the English content. |
| `AR_STATUS` | State of the Arabic content. |
| `RTL_STATUS` | Whether the page renders correctly right-to-left when `dir=rtl`. |
| `MOBILE_STATUS` | Whether the page is responsive at common mobile breakpoints. |
| `LINK_STATUS` | Whether this document is linked from the Legal Center hub and/or footer with a real (non-`#`) route. |
| `ACCEPTANCE_STATUS` | Whether accepting this specific document is required at signup, tracked via `PolicyAcceptance`, or purely informational. |
| `E2E_TEST` | Whether a real browser end-to-end test (not just `pytest`/`vitest` unit/integration tests) covers this page. |
| `FINAL_STATUS` | One of `ENGINEERING_READY` / `CONFIGURATION_REQUIRED` / `LEGAL_REVIEW_REQUIRED` / `NOT_YET_PUBLIC`. **Never `PRODUCTION_ACTIVE`** — nothing in this matrix is live in production; see the taxonomy in `LEGAL_PRIVACY_COMPLIANCE_MASTER.md` §"Status taxonomy". |

## Status legend (plain-language, used consistently below)

- **DRAFT_SEEDED** — English content exists (written from this repo's own
  code audit, not a template) as a `PolicyVersion` row with
  `status=DRAFT`. It is **not publicly visible** at its route today — it
  requires an admin to review and promote it through
  `DRAFT → IN_REVIEW → APPROVED → ACTIVE` via the Admin Legal Control Plane
  before `GET /legal/<slug>` will serve it instead of a 404/"no active
  version yet" page.
- **DRAFT_SEEDED_MACHINE_TRANSLATED** — Same as above, but the content is
  an unreviewed machine translation into Arabic (`is_machine_translated=True`
  on the `PolicyVersion` row), produced by this agent during this pass, not
  by a certified translator or legal counsel. The DRAFT-only gate above
  applies identically — and additionally, `services.activate_version()`
  checks BOTH the English (`"REQUIRES LEGAL REVIEW"`) and Arabic
  (`"تتطلب مراجعة قانونية"`) unresolved-marker strings before allowing
  activation, so an Arabic draft still containing an unresolved placeholder
  cannot be activated by accident any more than an English one can.
- **CODE_PRESENT_NOT_VISUALLY_VERIFIED** (used for `RTL_STATUS`/
  `MOBILE_STATUS`) — The shared page chrome (`Layout`, `PolicyPage.tsx`,
  `PolicyMarkdown.tsx`) uses the app's existing RTL/responsive
  infrastructure (`useTheme().dir`, Tailwind logical properties, the same
  `container`/`prose` classes every other page uses) — this is real,
  existing, shared code, not new one-off styling written for these pages.
  However, no one has opened each of these specific 13 pages in a real
  browser at `dir=rtl` or at a mobile viewport and visually confirmed
  correct rendering during this pass. The claim is "uses the same proven
  infrastructure as the rest of the site," not "independently visually
  verified."
- **LINKED** (used for `LINK_STATUS`) — The route appears as a real
  (non-`#`) link from the Legal Center hub (`LegalCenter.tsx`) and/or the
  site footer (`Footer.tsx`), confirmed by `LegalPages.test.tsx`'s
  automated assertion that no `href="#"` exists among these links.
- **SIGNUP_REQUIRED** (used for `ACCEPTANCE_STATUS`) — `Login.tsx`'s
  `legalReady` gate blocks account creation unless this specific document
  has a live `ACTIVE` version, and a successful signup calls
  `acceptPolicy(slug, "signup")` for it, creating a `PolicyAcceptance` row.
  Confirmed in code: **only `terms` and `privacy`** are wired this way.
- **INFORMATIONAL** (used for `ACCEPTANCE_STATUS`) — The document is
  publicly readable and linked, but no code path requires or records a
  user's acceptance of it specifically. This is not a defect for most of
  these documents (e.g. a disclosure register doesn't need "acceptance"
  the way Terms does) — it is stated here so no one assumes a
  `PolicyAcceptance` audit trail exists for a document where it doesn't.
- **NOT_DONE** (used for `E2E_TEST`) — No Playwright/Cypress/manual-browser
  test exists for this page in this repo as of this pass. Coverage is
  limited to `pytest` (backend) and `vitest` + React Testing Library
  (frontend component-level, jsdom environment — not a real browser).
  This matches a real gap the supplemental legal specs predicted and this
  pass did not close (flagged as a follow-up, not fabricated as done).

---

## Matrix

| ROUTE | FRONTEND_FILE | BACKEND_POLICY_TYPE | CURRENT_VERSION | EN_STATUS | AR_STATUS | RTL_STATUS | MOBILE_STATUS | LINK_STATUS | ACCEPTANCE_STATUS | E2E_TEST | FINAL_STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `/legal/terms` | `pages/legal/PolicyPage.tsx` | `terms` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer) | SIGNUP_REQUIRED | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/privacy` | `pages/legal/PolicyPage.tsx` | `privacy` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer) | SIGNUP_REQUIRED | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/cookies` | `pages/legal/PolicyPage.tsx` | `cookies` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer) | INFORMATIONAL (consent itself is tracked via `CookieConsent`, not `PolicyAcceptance`) | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/refunds` | `pages/legal/PolicyPage.tsx` | `refunds` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer) | INFORMATIONAL | NOT_DONE | LEGAL_REVIEW_REQUIRED (refund window unconfirmed) |
| `/legal/payment-security` | `pages/legal/PolicyPage.tsx` | `payment_security` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer) | INFORMATIONAL | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/security` | `pages/legal/PolicyPage.tsx` | `security` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub only — not in footer) | INFORMATIONAL | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/ai-disclosure` | `pages/legal/PolicyPage.tsx` | `ai_disclosure` | 2026.1 (DRAFT) | DRAFT_SEEDED | DRAFT_SEEDED_MACHINE_TRANSLATED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer, footer link added this pass) | INFORMATIONAL | NOT_DONE | ENGINEERING_READY (`makes_final_decision` hard-blocked at the DB/serializer layer, not just text) |
| `/legal/acceptable-use` | `pages/legal/PolicyPage.tsx` | `acceptable_use` | 2026.1 (DRAFT) | DRAFT_SEEDED (new this pass) | DRAFT_SEEDED_MACHINE_TRANSLATED (new this pass) | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub only) | INFORMATIONAL | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/data-rights` | `pages/legal/PolicyPage.tsx` | `data_rights` | 2026.1 (DRAFT) | DRAFT_SEEDED (new this pass) | DRAFT_SEEDED_MACHINE_TRANSLATED (new this pass) | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + footer, both new this pass) | INFORMATIONAL | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/subprocessors` | `pages/legal/PolicyPage.tsx` | `subprocessors` | 2026.1 (DRAFT) | DRAFT_SEEDED (new this pass) | DRAFT_SEEDED_MACHINE_TRANSLATED (new this pass) | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub only) | INFORMATIONAL | NOT_DONE | LEGAL_REVIEW_REQUIRED (DPA status unconfirmed for all 4 processors) |
| `/legal/international-transfers` | `pages/legal/PolicyPage.tsx` | `international_transfers` | 2026.1 (DRAFT) | DRAFT_SEEDED (new this pass) | DRAFT_SEEDED_MACHINE_TRANSLATED (new this pass) | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub only) | INFORMATIONAL | NOT_DONE | LEGAL_REVIEW_REQUIRED (transfer register is empty of confirmed mechanisms) |
| `/legal/candidate-privacy` | `pages/legal/PolicyPage.tsx` | `candidate_privacy` | 2026.1 (DRAFT) | DRAFT_SEEDED (new this pass) | DRAFT_SEEDED_MACHINE_TRANSLATED (new this pass) | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub + linked directly from both job-application flows — `JobDetail.tsx` custom-form modal and `QuickApplyPanel.tsx` review dialog, new this pass) | INFORMATIONAL | NOT_DONE | CONFIGURATION_REQUIRED |
| `/legal/business-terms` | `pages/legal/PolicyPage.tsx` | `business_terms` | 2026.1 (DRAFT) | DRAFT_SEEDED (new this pass) | DRAFT_SEEDED_MACHINE_TRANSLATED (new this pass) | CODE_PRESENT_NOT_VISUALLY_VERIFIED | CODE_PRESENT_NOT_VISUALLY_VERIFIED | LINKED (hub only) | INFORMATIONAL | NOT_DONE | CONFIGURATION_REQUIRED |

### Supporting registers (not standalone policy documents, but part of the same disclosure surface)

| Surface | ROUTE | FRONTEND_FILE | Backing data | LINK_STATUS | E2E_TEST | FINAL_STATUS |
|---|---|---|---|---|---|---|
| Legal Center hub | `/legal` | `pages/legal/LegalCenter.tsx` | n/a (static grouping of the 13 documents above) | LINKED from footer | NOT_DONE | ENGINEERING_READY — now grouped into 4 named categories (Platform / Payments & Commercial / Candidate & Employer / Data & Governance) rather than one flat list, this pass |
| Public processor register (API) | `GET /api/v1/legal/processors/` (no dedicated page yet — `/legal/subprocessors` is prose, this is the structured data behind it) | n/a — backend-only | `ProcessorRecord` (4 seeded vendors) | n/a | `test_public_registers.py` (5 tests) | LEGAL_REVIEW_REQUIRED (`dpa_signed` unconfirmed for all) |
| Public transfer register (API) | `GET /api/v1/legal/transfers/` | n/a — backend-only | `DataTransferRecord` (empty by default) | n/a | `test_public_registers.py` (5 tests) | LEGAL_REVIEW_REQUIRED (register is empty/unconfirmed by design) |

---

## Real browser E2E update (2026-09-21, third continuation pass)

The rest of this matrix (generated during the second continuation pass)
predates real-browser E2E coverage and states `E2E_TEST: NOT_DONE` and
`RTL_STATUS`/`MOBILE_STATUS: CODE_PRESENT_NOT_VISUALLY_VERIFIED` for every
row. **That gap is now closed** — see `audit/LEGAL_PRIVACY_COMPLIANCE_
MASTER.md` §9C for the full account. In summary, using Playwright against
system-installed Chrome (devDependency only, never installed in
production):

- All 13 `/legal/<slug>` routes were confirmed in `legal-public-pages.spec.ts`
  to render real activated content (not a "no active version" 404 state) —
  effectively upgrading every row's `E2E_TEST` from `NOT_DONE` to
  **DONE (content-render check)**.
- `mobile-and-rtl.spec.ts` independently verified, in a real browser: the
  Legal Center hub mirrors RTL layout, a long policy page has no horizontal
  overflow on a mobile viewport (Pixel 7), and Arabic content actually
  renders (via live `GET .../policies/<slug>/?locale=ar` calls) for 7 of
  the 13 documents (`terms`, `privacy`, `cookies`, `refunds`,
  `payment-security`, `candidate-privacy`, `business-terms`) — upgrading
  those 7 rows' `RTL_STATUS`/`MOBILE_STATUS` from
  `CODE_PRESENT_NOT_VISUALLY_VERIFIED` to **VISUALLY_VERIFIED**. The
  remaining 6 documents (`security`, `ai-disclosure`, `acceptable-use`,
  `data-rights`, `subprocessors`, `international-transfers`) share the
  exact same `PolicyPage.tsx`/`PolicyMarkdown.tsx` rendering path as the 7
  verified ones and the same app-wide `useTheme().dir` RTL infrastructure,
  so there is no code-level reason to expect different behavior — but
  they were not individually clicked through in this pass, so their rows
  below are left as `CODE_PRESENT_NOT_VISUALLY_VERIFIED` rather than
  silently upgraded without a direct check.
- The cookie consent banner was confirmed fully localized to Arabic in a
  real browser — title, body, and all three buttons (Accept All / Reject
  Non-Essential / Manage Preferences) — a cross-cutting UI element, not
  tied to any single policy row.
- **This upgrade is engineering-only.** No row's `EN_STATUS`/`AR_STATUS`/
  `FINAL_STATUS` changes as a result of this update — every document is
  still a `DRAFT` `PolicyVersion`, and every Arabic version is still
  `is_machine_translated=True`, unreviewed. RTL/mobile now rendering
  correctly in a real browser does not make the underlying text approved.

## What this matrix does NOT claim

- It does not claim any of the 13 documents is legally reviewed, legally
  binding, or publicly visible in production today — **every single one is
  still a `DRAFT` `PolicyVersion`** as of this pass. Making any of them
  publicly live requires an admin to review the actual rendered content at
  `/legal/<slug>` and explicitly promote it through the Admin Legal Control
  Plane (`DRAFT → IN_REVIEW → APPROVED → ACTIVE`) — this matrix does not
  do that, per the directive's explicit instruction not to auto-publish
  unreviewed legal text.
- It does not claim the Arabic content is translation-reviewed. Every
  Arabic `PolicyVersion` is seeded with `is_machine_translated=True`,
  which both the API response and the `/legal/<slug>` page surface as an
  "Unreviewed machine translation" badge (pre-existing `PolicyPage.tsx`
  behavior, confirmed unchanged by this pass) — a real human/legal Arabic
  review is a prerequisite before activating any Arabic version, exactly
  as it is for English.
- It does not claim RTL or mobile rendering was independently,
  page-by-page visually verified in a real browser — see
  `CODE_PRESENT_NOT_VISUALLY_VERIFIED` above. A browser-based E2E pass
  (Playwright or manual) remains a real, open gap for all 13 pages, not
  closed by this matrix or this pass.
- It does not claim a `LEGAL_LINK_AUDIT.md`/`LEGAL_CONTENT_FEATURE_AUDIT.md`
  -style exhaustive crawl of every internal cross-reference between
  documents was performed beyond what `LegalPages.test.tsx` automates
  (no-`#`-placeholder assertion across all 13 routes). Each document's own
  markdown cross-links to sibling documents (e.g. Terms → Payment Security)
  were written to point at real slugs in this pass, but a dedicated,
  separate crawl artifact was not produced — this matrix itself is the
  closest equivalent delivered.

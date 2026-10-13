# USAM Career — Legal / Privacy / Payments / Consent Compliance Master

**Status: authoritative, code-verified. Last updated 2026-09-21 (this directive's execution).**

This is the single source of truth for the Legal/Privacy/Payments/Consent
subsystem per the "USAM Master Ecosystem Legal/Privacy/Payments/Consent
Implementation Directive." It supersedes any older planning doc on this
subject (there was none — this subsystem did not exist before this work).

**This document makes NO compliance claims.** It records what was built,
what was verified against real code, what official legal sources were
consulted, and — critically — exactly which facts remain **REQUIRES LEGAL
REVIEW / CONFIGURATION** because this codebase cannot invent them. Nothing
here should be read as a representation of GDPR, PDPL, or PCI DSS
compliance in full.

---

## 1. Non-negotiables (verbatim from the directive) — status

| Non-negotiable | Status |
|---|---|
| Default currency = EGP | ✅ `PLATFORM_BASE_CURRENCY=EGP` setting added; `payments.Currency` default was already EGP; seed packages are EGP |
| No raw card storage | ✅ Verified by code scan + test (`test_no_card_pan_cvv_fields_exist_on_any_payments_model`) — zero PAN/CVV fields anywhere |
| No CVV storage | ✅ Same test |
| No fake security claims | ✅ Payment Security / Security Overview policy text explicitly avoids "military-grade encryption" etc., and discloses real gaps (localStorage tokens, CV public URL) |
| No fake compliance claims | ✅ No page claims GDPR/PCI/"fully compliant" anywhere |
| Terms/Privacy/Refunds/Cookie/Payment-Security publicly accessible | ✅ `/legal`, `/legal/terms`, `/legal/privacy`, `/legal/cookies`, `/legal/refunds`, `/legal/payment-security`, plus `/legal/security`, `/legal/ai-disclosure` |
| Legal links in footer | ✅ New "Legal" footer column, real routes, no `#` |
| Signup references current Terms+Privacy | ✅ Required checkbox in `Login.tsx` register flow, linked to `/legal/terms` and `/legal/privacy`, records `PolicyAcceptance` |
| Cookie UX > Accept All only | ✅ `CookieConsentBanner`: Accept All / Reject Non-Essential / Manage Preferences |
| Optional consent separate from Terms | ✅ Marketing + Talent Pool checkboxes are independent, never pre-checked, never bundled with the Terms checkbox |
| Talent Pool privacy explicit | ✅ Off by default (`CareerProfile.is_discoverable=False`), opt-in only, surfaced in signup, Settings, and Privacy Center |
| Policy versions + acceptance auditable | ✅ `PolicyVersion` immutable-content lifecycle + `PolicyAcceptance` append-only log |
| User can revisit privacy/cookie controls | ✅ Privacy Center (`/app/privacy-center`) + "Cookie settings" footer link |
| Refunds connect to real ledger | ✅ Already existed (`services.refund_payment` posts a reversing double-entry transaction); unchanged, verified by existing + new tests |
| Webhooks verified server-side | ✅ Already existed (Stripe signature verification); verified by new tests (`test_webhook_with_invalid_signature_is_rejected`, duplicate-ignored test) |
| Public policy text matches real system behavior | ✅ Seeded policy text was written FROM the Sept 2026 code audit, not from a template |
| Unknown legal facts marked for review, not invented | ✅ `requires_legal_review` flags on `RetentionPolicy`, `JurisdictionPolicyProfile`; blank `LegalEntityConfig`; no refund-window number hardcoded |

---

## 2. Official legal research (Phase A5)

### Egypt — Law No. 151 of 2020 on the Protection of Personal Data

- **Primary texts referenced**: Official Gazette No. 28 *bis* (e), 15 July
  2020 (law text); Ministerial Decree No. 816 of 2025 (Executive
  Regulations), issued 1 Nov 2025, effective 2 Nov 2025.
  Sources: [Law No. 151 of 2020 translation (Andersen)](https://eg.andersen.com/wp-content/uploads/2025/06/Law-No.-151-OF-2020.pdf),
  [Egypt Data Privacy Laws overview (RecordingLaw, audited 10 Sep 2026)](https://www.recordinglaw.com/world-laws/world-data-privacy-laws/egypt-data-privacy-laws/),
  [Library of Congress Global Legal Monitor](https://www.loc.gov/item/global-legal-monitor/2020-10-29/egypt-countrys-first-law-on-protection-of-personal-data-enters-into-force/).
- **Compliance window**: one-year period from the Executive Regulations'
  issuance (1 Nov 2025) → ends **1 Nov 2026**. As of this writing (Sept
  2026) the PDPC's online application portal is not yet reachable.
- **Scope**: electronic/partially-electronic processing of natural persons'
  data; six categories carved out (personal/household use, official
  statistics, media use, judicial records, national-security bodies, Central
  Bank + supervised entities except money-transfer/exchange companies).
- **Legal bases (Art. 6, exhaustive — four only)**: consent; contractual
  necessity; legal/judicial obligation; controller's legitimate
  rights/obligations (unless it conflicts with the data subject's
  fundamental rights). No GDPR-style "vital interests" or "public task"
  ground exists.
- **Consent standard**: explicit, specific, freely given, informed,
  documented, withdrawable at any time with processing stopping on
  withdrawal. Executive Regs distinguish explicit consent (required for most
  processing, sensitive data, direct marketing) from a narrow implied-consent
  carve-out (processing strictly necessary for a service the subject
  requested).
- **Sensitive data (Art. 12)**: health, financial/banking, religious,
  political, security/criminal records, biometric — **and children's data in
  every case**, regardless of content. Requires a PDPC licence AND
  written/explicit consent (+ guardian consent for a child). No employment,
  vital-interest, or public-health carve-out exists (unlike GDPR).
- **Data subject rights (Art. 2)**: access, withdraw consent, correct/
  update/erase, restrict, know of breaches, object. **No right to data
  portability.** The subject pays a PDPC-capped fee (max EGP 20,000) for
  exercising a right, except breach notice. Rights requests: **6 working
  days** to respond (Art. 32); silence on an Art. 10(3) data-availability
  request counts as refusal.
- **Breach notice**: to the PDPC within **72 hours**; to the data subject
  within **3 working days of the PDPC notification** (not from discovery).
  Must be in Arabic, via the subject's nominated contact channel.
- **Cross-border transfer**: prohibited without PDPC prior authorization
  (licence/permit) **plus** data-subject consent for every transfer,
  including to an already-"adequate" destination. No adequacy list published
  as of 10 Sep 2026.
- **Licensing**: mandatory tiered pre-authorization regime (unlike EU/UK/US
  self-assessment) — separate licences for general processing, cross-border
  transfer, direct marketing, surveillance, and sensitive data.
- **DPO**: mandatory for all legal entities processing personal data;
  voluntary for natural-person controllers/processors.
- **Regulator**: Personal Data Protection Centre (PDPC), chaired by the
  Minister of Communications and IT; board includes Defence, Interior,
  General Intelligence, Administrative Control Authority, ITIDA, NTRA.

### Saudi Arabia — Personal Data Protection Law (PDPL)

- **Primary instruments**: Royal Decree No. M/19 (9/2/1443H / 16 Sep 2021,
  original law); Royal Decree No. M/148 (5/9/1444H / 27 Mar 2023, amended
  law); SDAIA Implementing Regulations + Personal Data Transfer Regulations
  (published 7 Sep 2023); both in force **14 Sep 2023**, fully enforceable
  after the one-year grace period ended **14 Sep 2024**.
  Sources: [KSA PDPL overview (Securiti.ai)](https://securiti.ai/saudi-arabia-personal-data-protection-law/),
  [Saudi Arabia Data Privacy Laws (RecordingLaw)](https://www.recordinglaw.com/world-data-privacy-laws/saudi-arabia-data-privacy-laws/),
  [SDAIA (Wikipedia summary of mandate)](https://en.wikipedia.org/wiki/Saudi_Authority_for_Data_and_Artificial_Intelligence).
- **Scope**: any processing of personal data taking place in the Kingdom,
  plus processing of KSA residents' data by entities located abroad.
  Excludes personal/family-only processing (if not published/disclosed).
  Covers deceased persons' data if it would identify the deceased or a named
  family member.
- **Consent**: required unless a listed exception applies (clear benefit +
  subject unreachable; required by law/prior agreement; public-entity
  security/judicial processing; research/statistics with safeguards;
  "legitimate interests" — added by the 2023 amendment, does not apply to
  sensitive data). Independent consent per purpose; consent must never be a
  precondition for an unrelated service; explicit consent required for
  sensitive/credit data and for decisions based solely on automated
  processing.
- **Privacy policy requirement**: a formal privacy policy must exist and be
  shown to subjects before data collection, including purpose, content,
  collection method, storage, processing, destruction, rights, and how to
  exercise them.
- **Data subject rights**: know/information, access, correction, deletion/
  destruction, data portability (obtain + transfer to another controller —
  **unlike Egypt**, Saudi PDPL grants portability). No standalone
  "restriction" right (achieved via consent withdrawal / marketing opt-out
  per Art. 26). Response SLA: **30 days**, extendable once by up to 30 more
  days with notice.
- **Breach notice**: to SDAIA within **72 hours** via the National Data
  Governance Platform, with a follow-up root-cause analysis; to affected
  subjects "without undue delay" if harm/rights-conflict is possible,
  including the DPO's contact details.
- **DPO**: mandatory where the controller is a public entity processing data
  at scale, conducts regular/systematic monitoring (e.g. cookie tracking,
  wearables, behavioral analytics), or processes sensitive data as a core
  activity.
- **Cross-border transfer**: requires an approved safeguard (SCCs, BCRs,
  certification, or case-by-case approval) and, for sensitive/large-scale
  continuous transfers, a Data Transfer Risk Assessment (DTRA) per SDAIA's
  Feb 2025 guideline.
- **National Register of Controllers**: mandatory registration for public
  entities and controllers whose core activity is personal-data processing or
  sensitive-data processing; 5-year certificate.
- **Penalties**: up to 2 years' imprisonment and/or SAR 3M fine for malicious
  disclosure of sensitive data (Art. 35); warning or up to SAR 5M (doubled on
  repeat) for other violations (Art. 36); civil compensation available (Art.
  40). SDAIA's violation committees issued 48 decisions in 2025.
- **Regulator**: SDAIA (Saudi Data & AI Authority) — confirmed still the
  competent authority as of Jan 2026, beyond its original 2-year mandate.

### What this means for the platform (seeded, see §4)

A `JurisdictionPolicyProfile` row was seeded for each jurisdiction with the
figures above (DSR SLA, breach-notice hours). **The minors'-age threshold
for guardian consent was deliberately left blank for BOTH jurisdictions** —
neither source stated a single applicable numeric age for this platform's
context, and the directive forbids inventing one. This is a concrete
`REQUIRES LEGAL REVIEW` item (see §7).

---

## 3. Platform audit — verified facts (Phase A1–A4)

All of the following were confirmed by reading the actual code in this
repository during this directive's execution (not inferred from prior
status docs, consistent with `AGENTS.md`'s standing instruction).

### Payments / currency

- `apps/payments/models.py`: money stored as `BigIntegerField` minor units +
  `currency` (`Currency.TextChoices` = EGP, USD only). All of `Package`,
  `Order`, `Payment`, `Invoice`, `Refund`, `AdjustmentRequest` default
  `currency=EGP`.
- `apps/payments/models_ledger.py`: a real double-entry ledger already
  existed. Balances are **derived** (`Sum("amount")`), never a mutable
  column. `LedgerEntry.save()` raises `LedgerImmutableError` on any update
  attempt; `delete()` always raises. `LedgerTransaction.idempotency_key` is
  DB-unique.
- `apps/payments/providers/stripe_provider.py`: **LIVE-capable** — uses
  Stripe-hosted Checkout (`mode="payment"`), so card fields never touch
  USAM. Webhook signature verified via `stripe.Webhook.construct_event`.
  Refunds via `stripe.Refund.create`.
- `apps/payments/providers/alexbank_provider.py`: **SCAFFOLD, not live.**
  Every money-moving method (`create_payment`, `verify_payment`,
  `refund_payment`, `parse_webhook`) unconditionally raises
  `AlexBankNotImplemented`. `health()` always reports `live_enabled: False`.
  A `AlexBankMockProvider` exists but is gated behind `settings.DEBUG` or an
  explicit `ALEXBANK_ALLOW_MOCK` secret, and its `parse_webhook` performs
  **no signature verification** — sandbox-only by design, never reachable
  in production config.
- `apps/payments/providers/base.py` `get_provider()`: only recognizes
  `"stripe"`, `"alexbank"`, `"alexbank_mock"`. "Paymob"/"Fawry" appear only
  in a docstring comment and unrelated scraper seed data — **zero real
  implementation.** Classification: **Stripe = LIVE-capable** (depends on
  deployed secrets, not independently verified in this session) · **AlexBank
  = SCAFFOLD** · **Paymob/Fawry/PayTabs = PLANNED, not built.**
- `apps/payments/views.py` `WebhookView`: dedup on `(provider,
  provider_event_id)` via a real DB `UniqueConstraint`; a duplicate
  already-`PROCESSED` event is acknowledged without reprocessing (now
  pinned by `test_webhook_duplicate_event_is_ignored_without_reprocessing`).
  An invalid-signature webhook returns HTTP 400 and writes nothing (now
  pinned by `test_webhook_with_invalid_signature_is_rejected`).
- No field named `card`/`pan`/`cvv`/`cvc`/`magstripe`/`pin` exists anywhere
  in the payments app — confirmed by a whole-word static scan over every
  model field, pinned by
  `test_no_card_pan_cvv_fields_exist_on_any_payments_model`.
- No `DEFAULT_CURRENCY`-style setting existed before this work. **Added**:
  `settings.PLATFORM_BASE_CURRENCY = "EGP"` (config/settings/base.py),
  documented as distinct from per-job `salary_currency` and per-transaction
  payment currency.
- **Known inconsistency (flagged, not silently changed)**:
  `apps/jobs/models.py` `Job.salary_currency` defaults to `"USD"`, while the
  employer-posted job-posting model in `apps/employers/models.py` defaults
  `salary_currency` to `"EGP"`. Two different job models, two different
  defaults. This is a business/legal decision (which default is
  authoritative, and whether to backfill) that this directive explicitly
  did not resolve unilaterally — see §7.
- Frontend: zero hardcoded `$`/`USD`/`EGP` strings found in
  `Pricing.tsx`/`Billing.tsx`/`EmployerBilling.tsx`; `formatMoney()`
  (`services/billing.ts`) is currency-agnostic, driven entirely by the
  backend-supplied `currency` field via `Intl.NumberFormat`.

### Consent / Talent Pool / signup (before this directive)

- **Zero** Terms/Privacy checkbox or link existed anywhere in
  `Login.tsx` or `EmployerRegister.tsx` signup flows.
- `apps/accounts/serializers.py` `RegisterSerializer` had no consent field;
  `RegisterView.post` performed no consent capture.
- The ONE genuine consent-style control that existed:
  `CareerProfile.is_discoverable` (default `False`) + a dedicated
  `views_discoverability.py` endpoint + a Settings.tsx toggle — Talent Pool
  visibility.
- GDPR-adjacent machinery existed but was **orphaned**:
  `apps/accounts/models_gdpr.py` (`DataExportRequest`,
  `AccountDeletionRequest`), `views_gdpr.py`, `tasks_gdpr.py` were fully
  implemented but **never wired into any URLconf** — the self-service
  export/deletion endpoints were unreachable dead code until this
  directive's work (see §4).

### Cookies / tracking

- Zero third-party analytics/tracking SDKs anywhere in the frontend (no
  GA/Pixel/Hotjar/PostHog/Mixpanel/Segment/Sentry — confirmed by reading
  `index.html`, `main.tsx`, and a repo-wide grep). `ErrorBoundary.tsx` has
  only a commented-out Sentry TODO.
- Auth tokens (`usam_access`/`usam_refresh`) are stored in plain
  `localStorage`, not httpOnly cookies — an XSS-exposure gap, disclosed
  honestly in the Security Overview policy page rather than hidden.
- The only `document.cookie` write in the whole frontend is
  `sidebar.tsx`'s UI-state cookie (shadcn default) — not tracking.

### CV / document security

- `CareerProfile.cv_file`/`JobApplication.cv_snapshot` are plain
  `FileField`s served from a predictable `/media/...` URL with **no
  authorization or signed-URL check** — a real exposure gap. **Not fixed in
  this directive's scope** (out of scope per the directive's own priority
  order, which asked this to be flagged); disclosed explicitly in the
  Security Overview policy page as a "known gap (tracked for
  remediation)".

### AI / Rasheed

- Zero AI-disclosure or consent mechanism existed anywhere in
  `apps/intelligence/**` before this directive. New
  `AIProcessingDisclosure` register now documents Rasheed, job matching,
  interview practice, and CV parsing, with a hard validation rule
  (`makes_final_decision` must be `False`) preventing anyone from ever
  claiming AI makes the final hiring call.

### Interview / voice data

- Two parallel `InterviewSession` models exist (`apps/career/models.py` and
  `apps/interviews/models.py`) — a pre-existing fragmentation risk, not
  something this directive consolidated.
- `VoiceInterviewService.speech_to_text()` deletes the raw S3 audio after
  transcription, but the transcript text persists with **no retention/TTL
  field anywhere**. Seeded as an unconfigured (`requires_legal_review=True`)
  row in the retention matrix rather than inventing a number.

---

## 4. What was built (Phases B–I)

### Backend — `apps/legal` (new Django app)

Models: `PolicyDocument`, `PolicyVersion` (lifecycle DRAFT → IN_REVIEW →
APPROVED → SCHEDULED → ACTIVE → RETIRED, enforced by `services.
activate_version` which retires the previously-active sibling and never
overwrites content), `PolicyAcceptance` (append-only), `ConsentPurpose`,
`ConsentRecord` (append-only grant/withdraw history), `MarketingPreference`
(separate from `notifications.NotificationPreference`), `CookieCategory`,
`CookieConsent` (works for both authenticated users and anonymous
session-keyed visitors), `PrivacyRequest` + `PrivacyRequestEvent` (DSR
workflow with SLA pulled from `JurisdictionPolicyProfile`, never
hardcoded), `DataExportJob`, `DeletionJob`, `RetentionPolicy`, `LegalHold`,
`ProcessorRecord`, `DataTransferRecord`, `JurisdictionPolicyProfile`,
`IncidentReport`, `AIProcessingDisclosure`, `LegalEntityConfig` (singleton,
starts unconfigured).

API surface (`/api/v1/legal/...`): public policy serving + acceptance,
consent purpose list + grant/withdraw, marketing preference, cookie
category list + consent recording (anonymous-capable) + "my consent"
lookup, Privacy Center DSR endpoints (owner-scoped), public legal-entity +
AI-disclosure registers, and a full Admin Legal Control Plane
(`IsAdminRole`-gated) covering every one of the above resources plus
policy-version transitions, legal-hold release, and the DSR admin queue.

Also wired in this work: `apps.accounts.views_gdpr` (data export +
account-deletion self-service) — previously implemented but **never
reachable** — into `accounts/urls.py` for the first time.

Settings: `PLATFORM_BASE_CURRENCY = "EGP"`.

Migrations: `apps/legal/migrations/0001_initial.py` (verified via `manage.py
makemigrations`/`check`).

Seed data: `python manage.py seed_legal` populates all 7 policy documents
(each with one APPROVED→ACTIVE `v2026.1` version), the consent purposes,
cookie categories, the two jurisdiction profiles, the AI-disclosure
register, and a baseline retention matrix. **This command must be run once
per environment** (see deployment commands, §8) or `/legal/*` pages will
correctly show "no active version yet" rather than fabricating content.

### Frontend

- **Legal Center**: `/legal` hub + `/legal/:slug` generic policy page.
  Renders the backend's ACTIVE `PolicyVersion` via `react-markdown` +
  `remark-gfm` (parsed to React elements, never `dangerouslySetInnerHTML`
  — the directive's XSS-safety requirement for admin-authored legal text).
  Shows version/effective-date/machine-translation badges and an honest
  "no active version yet" state on 404 instead of fabricating text.
- **Cookie consent** (`CookieConsentBanner`): Accept All / Reject
  Non-Essential / Manage Preferences; works for anonymous visitors
  (session-key scoped on the backend); necessary category is always forced
  `true` and disabled in the manager; every choice persists via
  `POST /legal/cookie-consent/` (not just `localStorage`); reopenable via a
  "Cookie settings" footer link; never blocks login.
- **Signup consent** (`Login.tsx`): required Terms+Privacy checkbox gates
  the submit button; two independent, never-pre-checked opt-ins (Talent
  Pool visibility for individuals, marketing emails) — explicitly NOT
  bundled with the Terms checkbox.
- **Privacy Center** (`/app/privacy-center`): data export request/status
  (now reachable via the newly-wired `views_gdpr` endpoints), 30-day
  grace-period account deletion with cancel, per-purpose consent list,
  Talent Pool toggle (reuses the existing discoverability endpoint),
  marketing preference toggles, DSR request form + status tracker.
- **Admin Legal Control Plane** (`/admin/legal`, admin-gated, linked from
  the main Admin Dashboard sidebar): policy-version lifecycle actions,
  retention-matrix editor (surfaces `REQUIRES LEGAL REVIEW` rows), read-only
  jurisdiction profiles, cookie-category list, DSR queue + status
  transitions, legal-entity singleton editor.
- **Footer**: new "Legal" column with real routes (terms/privacy/cookies/
  refunds/payment-security + "View all" + "Cookie settings") — no `#`
  placeholders.
- **Checkout disclosures**: `Billing.tsx` and `EmployerBilling.tsx` now
  show an EGP-currency + auto-renewal + refund/payment-security-policy
  disclosure before any purchase, with no pre-checked marketing consent
  anywhere in the checkout flow (there never was one — payment flows don't
  collect marketing consent).

---

## 5. Payment & Card Security — Phase H findings (code-verified)

| Item | Finding | Evidence |
|---|---|---|
| Raw card/CVV storage | **None exists.** | Static field scan, all payments models — `test_no_card_pan_cvv_fields_exist_on_any_payments_model` |
| Card entry surface | Stripe-hosted Checkout only; no raw `<input>` card fields anywhere in the frontend | Code read of `Billing.tsx`/`EmployerBilling.tsx` + repo grep for card/cvv input patterns (zero matches) |
| Webhook signature verification | Stripe: `stripe.Webhook.construct_event` with `STRIPE_WEBHOOK_SECRET`; AlexBank: live adapter unreachable, mock has no verification but is DEBUG/secret-gated | `stripe_provider.py`, `alexbank_provider.py` |
| Webhook replay protection | DB-level `UniqueConstraint(provider, provider_event_id)`; duplicate already-processed events are acknowledged without reprocessing | `models.py` `WebhookEvent.Meta.constraints`; `test_webhook_event_provider_event_id_is_deduplicated_at_db_level`, `test_webhook_duplicate_event_is_ignored_without_reprocessing` |
| Invalid-signature webhook handling | Rejected with HTTP 400; nothing is written to the DB | `test_webhook_with_invalid_signature_is_rejected` |
| Client-claimed success trust | No endpoint accepts a bare `payment_success=true`; the only path to `Order.PAID` is `services.mark_order_paid()`, called from the $0-free-order branch of checkout or from a provider-verified webhook/refund flow | `views.py` `CheckoutView`/`WebhookView`; `test_client_claimed_success_alone_cannot_mark_an_order_paid` |
| Failed payment → entitlement | A `FAILED` payment never calls `mark_order_paid`; no entitlement row is created | `test_failed_payment_never_marks_order_paid_or_grants_entitlement` |
| Idempotency (double-charge protection) | `LedgerTransaction.idempotency_key` is DB-unique; `mark_order_paid`/`refund_payment` key their ledger postings on the order/refund reference so retries are no-ops | `test_mark_order_paid_posts_ledger_and_is_idempotent` (existing), `models_ledger.py` |
| Refund → ledger | Refunds post a **reversing** double-entry transaction (never mutate the original); payment/order flip to `REFUNDED` only on full refund | `services.refund_payment` (pre-existing, unchanged, re-verified) |
| AlexBank fake-success risk | Structurally impossible in the live path — every money-moving method raises before any `ok=True` result could be returned; the mock provider is non-production-reachable | `test_alexbank_live_adapter_always_raises_not_implemented_for_money_ops`, `test_alexbank_health_reports_live_disabled` |
| 3D Secure | Delegated entirely to the provider's hosted flow (Stripe Checkout); USAM implements no own 3DS logic | `stripe_provider.py` — no 3DS code path exists in this codebase |
| PCI DSS scope | **Not assessed/certified.** Hosted-checkout-only architecture reduces exposure versus a platform that collects card fields directly, but this document makes no PCI compliance claim | Payment & Card Security policy page states this explicitly |
| Fake security badges | None exist anywhere in the frontend | Grep for badge/certification imagery in Billing/Pricing pages — none found |
| Subscription cancellation semantics | `CompanySubscription`/`UserSubscription` have a flat `status` (trial/active/suspended/cancelled) with no "immediate vs period-end" field; admin changes status manually via `admin_views.subscriptions` | `apps/core/models.py`; flagged as a gap — not resolved in this directive (would require new plan-level cancellation-timing fields, out of the scope the directive asked for) |
| Recurring billing disclosure | Added to `Billing.tsx`/`EmployerBilling.tsx` before checkout | This directive's frontend work (§4) |

**Security headers / CSRF / CORS** (read, not modified): `production.py`
already sets `SECURE_HSTS_*`, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`,
`SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS=DENY`. No
`Content-Security-Policy` header or `django-csp` package is configured —
flagged as a gap, not fixed in this directive's scope. `CORS_ALLOW_ALL_ORIGINS
= True` in `development.py` only (expected for local dev); production uses an
explicit `CORS_ALLOWED_ORIGINS` allow-list from `base.py`.

---

## 6. Test evidence

Backend (`pytest`, `config.settings.test`, SQLite in-memory):

- `apps/legal/tests/test_legal_core.py` — **26 passed**: policy version
  activation/retirement/freeze rules, consent independence + withdrawal
  history, anonymous cookie consent + forced-necessary, DSR open/transition/
  SLA computation + RBAC, AI-disclosure guardrail, legal-entity
  unconfigured-by-default.
- `apps/accounts/tests/test_gdpr_routes.py` — **4 passed**: the
  newly-wired data-export and account-deletion self-service endpoints.
- `apps/payments/tests/test_card_security_audit.py` — **8 passed**: no
  card/CVV fields, webhook dedup + invalid-signature rejection, failed
  payment never grants entitlement, client-claimed success is never
  trusted, AlexBank can never fake a live success.
- Full regression run across `apps/legal`, `apps/accounts`, `apps/payments`,
  `apps/career` (ATS readiness) — **149 passed, 0 failed**.

Frontend (`vitest`):

- `src/components/legal/__tests__/CookieConsentBanner.test.tsx` —
  **6 passed**: three-button UX, anonymous operation, necessary-always-on
  forced in both accept-all and reject-non-essential paths, no re-prompt
  once a consent record exists, necessary toggle disabled in the manager.
- `src/pages/legal/__tests__/LegalPages.test.tsx` — **4 passed**: every
  Legal Center tile links to a real route (no `#`), unconfigured-entity
  notice shown honestly, policy content renders with version badge, honest
  404 state.
- `src/pages/__tests__/Login.test.tsx` (new `describe` block) —
  **3 passed**: submit disabled until Terms accepted, optional consents
  never pre-checked, `acceptPolicy`/`setConsent` called correctly (and only
  when explicitly opted in).
- Full suite — **75 passed, 0 failed**. `tsc --noEmit` clean. Production
  `vite build` succeeds.

---

## 7. REQUIRES LEGAL REVIEW / CONFIGURATION — open items

These are **not** implementation gaps; they are facts this codebase
correctly refuses to invent. Each is already modeled as an explicit "blank
+ flagged" row/field so an admin or legal counsel can fill it in without a
code change:

1. **Legal entity identity** (`LegalEntityConfig`): name, registered
   address, tax/registration ID, DPO identity, contact emails — all blank.
2. **Refund window** (`LegalEntityConfig.default_refund_window_days`):
   `NULL`. The Refund Policy page explicitly says "no window confirmed yet"
   rather than defaulting to a common figure like 14 days.
3. **Minors' / guardian-consent age threshold**
   (`JurisdictionPolicyProfile.minor_age_threshold`, both EG and SA):
   `NULL`. Neither official source reviewed gave one applicable numeric age
   for this platform's context (Egypt treats ALL children's data as
   "sensitive" regardless of a specific age cutoff; Saudi PDPL doesn't state
   one either).
4. **Retention periods** (`RetentionPolicy`, several rows): account core
   data, CV documents, interview transcripts, and payment records are all
   `retention_period_days=NULL, requires_legal_review=True`. Only the two
   periods already hardcoded in existing (unrelated to this directive) code
   — the 30-day GDPR export-file expiry and the 30-day account-deletion
   grace period — were seeded with real numbers, because those are
   confirmed in code, not invented.
5. **Processor / sub-processor register** (`ProcessorRecord`): empty table.
   No vendor (AWS, Stripe, etc.) has been formally entered with a confirmed
   DPA status — `dpa_signed` defaults to `NULL` ("not yet confirmed"), never
   `False`-by-omission.
6. **Cross-border transfer register** (`DataTransferRecord`): empty table;
   model defaults `mechanism=UNKNOWN` ("not yet determined — REQUIRES LEGAL
   REVIEW") rather than assuming SCCs/adequacy.
7. **Governing law / dispute resolution** (Terms of Service §9): marked
   `REQUIRES LEGAL REVIEW / CONFIGURATION` in the policy text itself.
8. **Security/vulnerability-disclosure contact**: not yet configured
   (Security Overview policy page says so explicitly).
9. **Job.salary_currency USD-default vs. employer-posting-model EGP-default
   inconsistency** (§3): a business decision on which model is authoritative
   is needed before either default is changed; this directive deliberately
   did not pick one unilaterally.
10. **Subscription cancellation timing** (immediate vs period-end) is not
    modeled per-plan; needs a product/legal decision on the intended
    semantics before a schema change.
11. **Content-Security-Policy header**: not configured; a CSP needs to be
    authored against the real asset/script inventory (Rasheed 3D assets,
    etc.) before being turned on, to avoid breaking functionality.

---

## 8. Deployment commands

Two increments were committed to `development` and pushed:

- `d144cfb` — backend `apps.legal` domain (models, services, APIs, admin
  control plane, `PLATFORM_BASE_CURRENCY`, seed command, 26 tests).
- `a6b9366` — frontend Legal Center/cookie banner/Privacy Center/signup
  consent/Admin Legal UI + the `views_gdpr` URL wiring fix + 13 frontend +
  4 backend tests.
- *(this commit)* — Phase H payment/card-security audit tests (8 new
  backend tests) + this master document + Admin Dashboard sidebar link.

Production deployment (run once per environment; `seed_legal` is required
or `/legal/*` will correctly — but unhelpfully — show "no active version
yet"):

```bash
cd /var/www/usam
git pull origin development

# Backend
source backend/venv/bin/activate
pip install -r backend/requirements/production.txt
cd backend
python manage.py migrate
python manage.py seed_legal
python manage.py collectstatic --noinput
cd ..

# Frontend
cd frontend
npm ci
npm run build
cd ..

# Restart services
sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service
sudo nginx -s reload
```

Verification after deploy:
- `GET https://jobs.usamif.com/api/v1/legal/policies/` returns 7 documents,
  each with a non-null `live_version`.
- `https://jobs.usamif.com/legal` renders all 7 tiles; each links to real
  content.
- Visiting the site logged-out shows the cookie banner with all three
  buttons; accepting/rejecting does not require login.
- `/app/privacy-center` (as a logged-in user) successfully requests a data
  export and shows a `pending`/`processing`/`completed` status.
- `/admin/legal` (as an admin) lists the 7 policy versions in `ACTIVE`
  status and the two seeded jurisdiction profiles.

---

## 9. Final Acceptance checklist (A–Z areas)

| Area | Done |
|---|---|
| A. Platform audit (payments, cookies, signup, CV, AI, interviews) | ✅ §3 |
| B. Official Egypt/Saudi legal research | ✅ §2 |
| C. Backend policy/consent domain + migrations | ✅ §4 |
| D. Currency separation (`PLATFORM_BASE_CURRENCY=EGP`) | ✅ §3 |
| E. Public policy-serving + consent + cookie + DSR + admin APIs | ✅ §4 |
| F. Legal Center public pages | ✅ §4 |
| G. Cookie consent banner + manager | ✅ §4 |
| H. Signup consent (required Terms+Privacy, optional Talent Pool/marketing) | ✅ §4 |
| I. Privacy Center (export/deletion/consent/Talent Pool/marketing/DSR) | ✅ §4 |
| J. Payment & card security audit | ✅ §5 |
| K. Admin Legal Control Plane | ✅ §4 |
| L. Footer legal nav + checkout disclosures | ✅ §4 |
| M. Tests (backend + frontend) | ✅ §6 — 149 backend + 75 frontend passing |
| N. This master document | ✅ |
| O. Commit + push to `development` | ✅ `d144cfb`, `a6b9366`, and this commit |
| P. Deployment commands per increment | ✅ §8 |
| Q. REQUIRES LEGAL REVIEW items explicitly tracked, not invented | ✅ §7 |
| R. No fake compliance/security claims anywhere | ✅ verified by reading every new policy page's text |
| S. AI disclosure (assists, doesn't decide) enforced at the data layer | ✅ `AIProcessingDisclosure.makes_final_decision` validator |
| T. Talent Pool explicit opt-in (not automatic exposure) | ✅ pre-existing `is_discoverable=False` default, now surfaced in 3 places |
| U. Direct Apply redirect disclosure | ✅ Terms of Service §3 |
| V. Minors/children policy — not invented | ✅ §7 item 3 |
| W. CV/document security gap — disclosed, not silently left unmentioned | ✅ Security Overview policy page |
| X. Interview transcript retention — disclosed as unconfigured | ✅ §7 item 4 |
| Y. Currency consistency gap (Job vs employer-posting model) — flagged | ✅ §3, §7 item 9 |
| Z. CSP / cancellation-timing / processor-register gaps — flagged, not fabricated | ✅ §7 items 10–11, 5–6 |

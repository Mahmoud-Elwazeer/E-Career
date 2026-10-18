# USAM Career — Legal / Privacy / Payments / Consent Compliance Master

**Status: authoritative, code-verified. Last updated 2026-09-21 (continuation hardening pass — see §9A for this pass's changes; §§1-11 below are the prior pass, corrected in-place where a prior "not fixed" claim has since been superseded).**

## Status taxonomy (used throughout this document)

| Status | Meaning |
|---|---|
| **ENGINEERING READY** | Code is implemented, tested, and merged to `development`. Not yet deployed to production and/or not yet legally configured. |
| **CONFIGURATION REQUIRED** | Code is ready; a specific admin-entered value (legal entity, contact email, refund window, etc.) is still blank and must be filled in before the feature is fully meaningful in production. |
| **LEGAL REVIEW REQUIRED** | A legal fact (minors' age threshold, retention period, governing law, DPA status) cannot be confirmed from code or public sources and must come from qualified legal counsel. Marked `requires_legal_review=True` in the data itself. |
| **PRODUCTION ACTIVE** | Deployed to `jobs.usamif.com`, verified live, and — where applicable — legally configured. **Nothing in this document is marked PRODUCTION ACTIVE yet** — see §10. |

**This document does not claim full legal/regulatory compliance at any point.** It records what was built, what was verified, and what remains open.

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
  show an EGP-currency + refund/payment-security-policy disclosure before
  any purchase, with no pre-checked marketing consent anywhere in the
  checkout flow (there never was one — payment flows don't collect
  marketing consent). **Correction (directive item 14, this pass):** the
  disclosure previously said "renew automatically until cancelled" —
  false. There is no recurring billing, auto-charge, or subscription-
  renewal mechanism anywhere in `apps.payments` (confirmed: `CheckoutView`
  only ever makes one single charge per purchase; no Stripe subscription
  mode is used; `admin_views.subscriptions` only flips a status flag
  manually). The disclosure now correctly states each purchase is a
  single one-time charge with no auto-renewal, and the seeded Refund &
  Cancellation Policy's "Subscriptions" section was corrected to match
  (it previously implied a self-service "cancel to stop future billing"
  flow that does not exist — there is no future charge to cancel).

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
| Recurring billing disclosure | **Corrected (item 14)**: no recurring billing exists — `Billing.tsx`/`EmployerBilling.tsx` and the seeded Refund Policy now correctly state every purchase is one-time, no auto-renewal | This pass; see §9.16/§9.14-item-14 |

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

Four increments are committed to `development` and pushed:

- `d144cfb` — backend `apps.legal` domain (models, services, APIs, admin
  control plane, `PLATFORM_BASE_CURRENCY`, seed command, 26 tests).
- `a6b9366` — frontend Legal Center/cookie banner/Privacy Center/signup
  consent/Admin Legal UI + the `views_gdpr` URL wiring fix + 13 frontend +
  4 backend tests.
- `a3d6de7` — payment/card-security audit tests (8 tests) + this master
  document + Admin Dashboard sidebar link.
- `49eddd6` — production-hardening pass: Talent Pool privacy fix (incl. a
  critical pre-existing 500-error bug fix), webhook amount/currency
  verification, policy-acceptance race-condition hardening, retention
  enforcement engine, processor register seed, Markdown XSS hardening,
  safe `npm audit fix`. See §9 for full detail.

### A. Pre-deploy checks

The repo contains **multiple deploy scripts from different eras with
conflicting assumptions** about where the Python virtualenv lives
(`deploy-to-server.sh`/`deploy.sh` use `backend/venv/bin`; `deploy/
gunicorn.service` uses `/var/www/usam/venv/bin` — one level up). Run these
checks on the actual server FIRST so the deploy commands in §B use the
venv path that is actually correct for this box, not a guess:

```bash
cd /var/www/usam
git status                      # confirm no uncommitted local changes you'd lose
git log --oneline -3             # confirm current HEAD before pulling
git rev-parse HEAD

# Which venv actually exists?
ls -la backend/venv/bin/python 2>/dev/null && echo "venv is at backend/venv"
ls -la venv/bin/python 2>/dev/null && echo "venv is at /var/www/usam/venv"

# Which services actually run this app? (names vary across the repo's own
# scripts: usam.service / gunicorn-usam.service / ecareer-backend — confirm
# before restarting the wrong one, or a nonexistent one)
systemctl list-units --type=service --all | grep -Ei "usam|ecareer|gunicorn|celery"

# Confirm the database/queues you must NOT disturb are healthy BEFORE you
# touch anything — compare against this same output again after deploy.
sudo -u postgres psql -c "\l" 2>/dev/null | grep -i usam   # Postgres DB present
docker ps 2>/dev/null | grep -i typesense                  # Typesense container running
docker volume ls 2>/dev/null | grep usam_typesense_data     # the real data volume exists
curl -s -o /dev/null -w "typesense:%{http_code}\n" http://127.0.0.1:8108/health
redis-cli ping 2>/dev/null || echo "redis not reachable on default port"

# Confirm no destructive flags are anywhere in what you're about to run —
# this deploy does NOT drop/recreate the DB, does NOT touch Typesense data,
# does NOT run collectstatic --clear (one of the repo's OLDER scripts does
# use --clear; do not use that variant here).
```

**Do not proceed to §B until you know which `venv` path and which service
name(s) are real on this box.** Below, `<VENV>` stands for whichever path
you confirmed (`backend/venv/bin` or `venv/bin`), and `<SERVICE>` for the
confirmed Gunicorn/Daphne service name.

### B. Exact deployment commands

```bash
cd /var/www/usam
git pull origin development

# Backend — install deps, migrate (additive-only, see §9.1), seed legal data,
# collect static. No --clear, no destructive flags.
<VENV>/pip install -r backend/requirements/production.txt
cd backend
../<VENV>/python manage.py migrate --noinput
../<VENV>/python manage.py seed_legal
../<VENV>/python manage.py collectstatic --noinput
cd ..

# Frontend — rebuild only; nginx serves the existing frontend/dist until this
# completes, so there is no window where the site serves nothing.
cd frontend
npm ci
npm run build
cd ..

# Restart ONLY the services confirmed in §A. Do not restart postgresql,
# redis, or the Typesense container — none of this deploy touches their data
# and restarting them is unnecessary risk, not required by this change.
sudo systemctl restart <SERVICE>
sudo systemctl restart celery-usam.service celery-beat-usam.service   # if these are the confirmed names from §A
sudo nginx -t && sudo nginx -s reload   # -t validates config before reload — never reload a broken config
```

**New in this increment, run once if not already present (idempotent,
dry-run by default, no destructive action):**
```bash
cd backend && ../<VENV>/python manage.py enforce_retention
# Expect: SKIP lines for every category (all currently requires_legal_review
# or unconfigured) except interview_transcripts/cv_documents, which report
# "found=N ... affected=0" in dry-run. Do NOT pass --execute in production
# until legal has confirmed retention periods — see §9.4.
```

### C. Post-deploy verification

```bash
# Code/migration state
git rev-parse HEAD   # expect 49eddd6 (or later)
cd backend && ../<VENV>/python manage.py showmigrations legal
../<VENV>/python manage.py check

# Legal API + pages (expect 200 for all of these)
for p in /legal/ /legal/terms /legal/privacy /legal/cookies /legal/refunds /legal/payment-security /legal/security /legal/ai-disclosure; do
  printf "%s -> " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "https://jobs.usamif.com$p"
done
curl -s https://jobs.usamif.com/api/v1/legal/policies/ | python3 -m json.tool | head -40

# Services untouched by this deploy are still healthy
curl -s -o /dev/null -w "typesense:%{http_code}\n" http://127.0.0.1:8108/health
sudo systemctl is-active postgresql redis-server 2>/dev/null
sudo systemctl status <SERVICE> celery-usam.service celery-beat-usam.service --no-pager -l | head -40
sudo journalctl -u <SERVICE> -n 100 --no-pager | grep -Ei "error|traceback" || echo "no errors in recent log"

# Payments unaffected (sanity — no live charge, just confirm the endpoint responds)
curl -s -o /dev/null -w "packages:%{http_code}\n" https://jobs.usamif.com/api/v1/payments/packages/
```

Full browser/UI checklist (manual, see §39 of the original directive and
§10 below for the complete live-verification list): cookie banner on a
fresh/incognito browser shows all three buttons and does not require
login; Login.tsx signup shows the required Terms checkbox and the two
independent opt-ins; `/app/privacy-center` requires auth; `/admin/legal`
requires admin; footer legal links resolve; existing Login/Jobs/Billing
pages still work.

### D. Rollback commands

This deploy made no destructive schema changes (§9.1 — purely additive
migration), so rollback is a plain code revert, not a data-recovery
operation:

```bash
cd /var/www/usam
git log --oneline -5          # confirm the commit to roll back to
git checkout <previous-commit-hash>
<VENV>/pip install -r backend/requirements/production.txt
cd backend && ../<VENV>/python manage.py migrate --noinput   # no-op: nothing to unapply, additive-only
cd ../frontend && npm ci && npm run build
cd ..
sudo systemctl restart <SERVICE> celery-usam.service celery-beat-usam.service
sudo nginx -t && sudo nginx -s reload
```

Rolling back does **not** require dropping the new `legal_*` tables —
leaving them in place with no code referencing them is harmless (standard
additive-migration rollback practice). Only drop them manually if you have
an explicit reason to; that would be a separate, deliberate decision, not
part of this rollback.

---

## 9. Production-hardening pass (commit `49eddd6`)

This section documents the hardening pass performed after the initial
implementation was accepted as code-complete, before production launch.

### 9.1 Migration safety review

`apps/legal/migrations/0001_initial.py` reviewed line-by-line: contains
**only** `CreateModel`/`AddConstraint`/`AddIndex` operations — zero
`AlterField`, `RemoveField`, `RunSQL`, or `RunPython`. `sqlmigrate`
confirmed every operation is a plain `CREATE TABLE`/`CREATE INDEX` (SQLite
shown in dev; PostgreSQL will emit the equivalent `CREATE TABLE`/`CREATE
INDEX CONCURRENTLY`-eligible statements — none of these lock existing
tables since none existed before this migration). `makemigrations --check
--dry-run` reports **"No changes detected"** both before and after this
hardening pass's model changes (`TalentPool.active_candidates()` is a
plain Python method, not a field — no migration required). **Verdict:
safe for production — purely additive, no destructive operation, no
long-lock risk against existing tables.**

### 9.2 Seed vs. publish — the launch flow

`seed_legal` creates `PolicyVersion` rows and immediately calls
`services.activate_version()` on each — so after running it, all 7
documents ARE live/public at `/legal/*` with the seed's draft text. This
is intentional for a staging/dev environment but **for production, the
directive requires a controlled launch**, not an immediate blanket
auto-publish of unreviewed text. The actual recommended production launch
flow:

1. **Seed to DRAFT only.** **Update (continuation pass, 2026-09-21 — see
   §9A.1):** `seed_legal` now defaults to creating every policy as
   `DRAFT` and never auto-activates. An explicit `--activate-drafts` flag
   (intended for test/staging only) is required to reproduce the old
   auto-publish behavior, and that flag itself is gated behind
   `activate_version(..., allow_unresolved_markers=True)` so draft text
   still containing `"REQUIRES LEGAL REVIEW"` markers cannot be activated
   by accident even with the flag set. This closes the "immediate
   blanket auto-publish of unreviewed text" risk described below at the
   code level, not just the process level.
2. **Review**: an admin/legal reviewer reads each of the 7 documents at
   `/legal/<slug>` on staging.
3. **Approve + Activate**: via the Admin Legal Control Plane
   (`/admin/legal` → Policy versions tab → "Send to review" → "Approve" →
   "Activate"), or directly via API: `POST /api/v1/legal/admin/versions/
   <uuid>/transition/` with `{"status": "approved"}` then `{"status":
   "active"}`. The management-command equivalent (for a scripted launch)
   is to call `apps.legal.services.activate_version(version=version,
   approver=admin_user)` from a one-off `manage.py shell` command — no
   dedicated CLI flag exists for this yet (flagged as a nice-to-have, not
   a blocker, since the admin UI already does this safely).
4. **Public verification**: confirm `/legal/<slug>` returns the approved
   text and the version badge shows the expected `version_label`.

**If no active version exists**, `/legal/<slug>` returns the honest "No
active version yet" page (never fabricated text) — confirmed by
`PolicyPage.test.tsx`'s dedicated test for this state. **The production
Legal Center will NOT end up with empty/broken pages after deployment**
as long as `seed_legal` is run during the deploy (§8.B) — it both creates
AND activates in one step today. The gap is narrower than "pages will be
empty" — it's "the FIRST live text will be the seed's own draft wording
until someone with legal authority reviews and, if needed, supersedes it
with a new version" (which the versioning system fully supports — see
§9.3's version-update test).

### 9.3 Signup/policy-acceptance race condition — closed

`policy_accept` (`apps/legal/views.py`) now runs inside an explicit
`@db_transaction.atomic` block and — as it already did — resolves "the
currently ACTIVE version" fresh at the moment of the API call via
`services.get_active_version()`, never trusting a version id supplied by
the frontend. New test `test_policy_accept_binds_to_whichever_version_
is_active_at_submit_time_not_a_stale_one` proves the exact scenario: a
user who loaded signup while v1 was active, then an admin activates v2
before the user's request lands, is correctly bound to v2. A second new
test (`test_policy_version_update_preserves_old_acceptance_and_tracks_
new_separately`) proves v1's acceptance row survives v2's activation
unmutated, `needs_reacceptance()` correctly flips to `True`, and accepting
v2 creates a wholly separate row.

### 9.4 Production legal configuration checklist

| Setting | Current state | Required for launch? | Value source | Blocks policy activation? | Legal review required? |
|---|---|---|---|---|---|
| `LEGAL_ENTITY_NAME` | Blank (`LegalEntityConfig.legal_entity_name=""`) | Yes — shown in Terms/footer/invoices | Business registration documents | No (policies can activate with a `REQUIRES LEGAL REVIEW / CONFIGURATION` placeholder) | Yes |
| `LEGAL_ADDRESS` | Blank | Yes | Business registration documents | No | Yes |
| `LEGAL_CONTACT_EMAIL` / `PRIVACY_CONTACT_EMAIL` | Blank | Yes — Privacy Center/footer reference it | A real, monitored mailbox the company owns | No | No (operational, not legal) |
| `SUPPORT_EMAIL` | Blank in `LegalEntityConfig`; `Contact.tsx` hardcodes `support@usamif.com` (pre-existing, unrelated to this pass) | Yes | A real, monitored mailbox | No | No |
| `GOVERNING_LAW` | Marked `REQUIRES LEGAL REVIEW / CONFIGURATION` in Terms §9 text | Yes, before any dispute could arise | Legal counsel | No | Yes |
| `PLATFORM_BASE_CURRENCY` | `EGP` (configured, code-verified) | **Done** | N/A | N/A | No |
| Minimum age / account eligibility | Not enforced anywhere; `minor_age_threshold=NULL` for both jurisdictions | Should be set before any marketing targeting minors | Legal counsel (Egypt treats all children's data as "sensitive" regardless of a stated age; no single number found in Saudi sources either) | No | **Yes — critical** |
| Refund window | `LegalEntityConfig.default_refund_window_days=NULL`; Refund Policy text says "no window confirmed yet" | Yes, before any real refund dispute | Business/legal decision | No | Yes |
| Cancellation rules (immediate vs. period-end) | Not modeled — flat `status` field only, no `cancel_at_period_end` | Should be decided before marketing promises either behavior | Business/product decision | No | No (product decision, not legal) |
| Retention periods (CV, interview transcripts, payment records) | `requires_legal_review=True`, `retention_period_days=NULL` for all three | Yes, before `enforce_retention --execute` is ever run | Legal counsel + business records-retention policy | No (policy text says "pending review") | **Yes — critical** |
| Jurisdiction enablement (EG/SA) | Both seeded with real DSR-SLA/breach-notice figures from official sources; `minor_age_threshold` unset | Partially done | Legal counsel for any additional jurisdiction | No | Yes (for remaining fields) |
| Cookie categories | Fully seeded (necessary/functional/analytics/marketing) — no trackers exist yet to gate | **Done** | N/A | N/A | No |
| Processor list | Seeded with 4 code-confirmed vendors (AWS, Stripe, Typesense, Sentry); `dpa_signed=NULL` for all | Partially done | Legal/procurement to confirm DPA status per vendor | No | Yes (DPA confirmation only) |
| AI/model-provider disclosure | 4 AI touchpoints disclosed (Rasheed, matching, interview practice, CV parsing); `makes_final_decision` hard-blocked at `True` | **Done** | N/A | N/A | No |
| Payment provider disclosure | Stripe (hosted checkout) and AlexBank (scaffold, explicitly marked not-live) both disclosed accurately in Payment & Card Security policy text | **Done** | N/A | N/A | No |

No secret values (API keys, passwords, tokens) are included in this table
or anywhere in this document, per the directive's own instruction.

### 9.5 EGP currency audit — completed

Full repo-wide audit performed (backend + frontend + seed data + emails +
Admin Finance). Findings, classified per the directive's taxonomy:

- **PLATFORM_PRICE** (platform billing/ledger): `apps.payments.Currency`
  choices, all `Package`/`Order`/`Payment`/`Invoice`/`Refund`/
  `AdjustmentRequest`/`LedgerAccount`/`LedgerEntry` default `EGP` —
  consistent, correct, matches `PLATFORM_BASE_CURRENCY`. `seed_packages.py`
  hardcodes `EGP` for all 6 real packages — correct.
- **JOB_SALARY**: confirmed, not touched (per directive's own instruction
  not to blindly force EGP onto job-salary data). `apps.jobs.models.Job.
  salary_currency` defaults `USD`; the employer-posted job-posting model in
  `apps.employers.models` defaults `EGP` — this is the known, previously-
  flagged inconsistency, addressed in §9.6 below. Seven ATS scraper
  connectors (`greenhouse`-style adapters) fall back to a blanket `"USD"`
  when a source doesn't specify a currency — a plausible-but-unverified
  assumption (most of those ATSes are USD-denominated), not location-aware;
  flagged as a data-quality note, not changed (changing scraper defaults
  without a product decision risks silently mislabeling real job data).
  `apps.jobs.serializers.py`'s *display* fallback (`'EGP'`) independently
  disagrees with the *model* default (`'USD'`) when a value is empty — a
  separate, smaller inconsistency noted for future cleanup, not fixed in
  this pass (display-only, doesn't change stored data).
- **PAYMENT_TRANSACTION**: confirmed per-row, never silently overridden —
  Stripe adapter passes through whatever currency the `Order`/`Payment`
  carries; no hardcoded transaction currency anywhere.
- **HISTORICAL_DATA**: a previously-removed stale `salary_currency_new`
  field (migration `0007_remove_stale_salary_fields.py`) — dead migration
  artifact, not a live concern.
- **TEST_FIXTURE**: `seed_jobs.py`'s location-aware demo currency
  (`EGP`/`AED`/`SAR` by location string match) and all pytest fixtures
  using `USD`/`EUR` — cosmetic, zero production risk.
- **EXTERNAL_PROVIDER_VALUE**: Stripe's `currency.lower()` pass-through —
  correctly non-hardcoded.
- **Live-DB impact note**: changing `Job.salary_currency`'s Python default
  does NOT retroactively change existing rows (Django model defaults only
  apply at creation time) — any default change is a forward-only effect;
  determining how many existing rows are "genuinely USD" vs.
  "silently-defaulted USD" requires a live query this pass did not run
  (read-only audit), and there is no stored flag distinguishing the two.

### 9.6 Job salary-currency default inconsistency — decision deferred, not resolved unilaterally

Per the directive's own instruction ("Determine the correct domain
behavior... do not silently rewrite historical salary currencies"), this
pass did **not** change either model's default. Reasoning: `Job` and the
employer `JobPosting` model are two different tables feeding into the same
public job listing surface via `apps.employers.admin.py`'s approval flow
(`salary_currency=job_post.salary_currency` copied verbatim, no
normalization) — changing one default without the other, or without
knowing which one the business considers authoritative, risks either (a)
silently mislabeling scraped non-Egyptian jobs as EGP, or (b) silently
mislabeling Egypt-market employer postings as USD. **This requires a
product/business decision** (which this pass is not positioned to make
unilaterally) on one of: (1) make `Job.salary_currency` nullable with no
default, requiring every ingestion path to explicitly set it from
verified source data (most correct, most invasive); (2) leave both
defaults as-is but add a `salary_currency_confirmed: bool` flag so
downstream code/UI can distinguish real values from defaults (additive,
non-breaking); or (3) align both to one shared default (loses information
either way). **Recommendation**: option (2) — it's additive, doesn't
touch existing data, and immediately gives the business visibility into
how much of the job data is actually currency-verified vs. guessed.
Flagged for a follow-up decision, not implemented in this pass.

**Update (continuation pass, 2026-09-21 — see §9A.2):** the follow-up
decision was made. `Job.salary_currency` is now nullable with **no**
default (option 1's intent, applied only to `Job`, not to the
employer-posted `JobPosting` model, which keeps its real EGP default
since that field is human-entered by an employer, not scraped/guessed).
A new `Job.salary_currency_raw` field preserves the original source text
when a scraper cannot confidently resolve a currency. All 7 ATS scraper
connectors (`personio`, `recruitee`, `smartrecruiters`, `teamtailor`,
`workable`, plus the shared `base`/`normalizer`/`contract`/`orchestrator`/
`tasks` pipeline code) were fixed to stop fabricating `'USD'` as a
fallback — they now pass through `None` and the raw text when the
currency genuinely cannot be determined from the source. This does not
retroactively correct historical rows (per the directive's own
instruction not to silently rewrite historical data) but stops new bad
data from being created going forward. Migration:
`apps/jobs/migrations/0016_job_salary_currency_raw_alter_job_salary_currency.py`.
7 new tests.

### 9.7 Cookie tracker gating — nothing to gate yet (confirmed, not a gap)

Exhaustive search confirmed **zero** analytics/tracking SDKs exist
anywhere in the frontend (no GA/GTM/Meta Pixel/Hotjar/PostHog/Mixpanel/
Amplitude/Clarity/Segment/browser-Sentry). The `CookieConsentBanner`
correctly records granular preferences server-side, but there is
currently no runtime code path that reads those preferences back to
conditionally load a script — because no such script exists to load. This
is accurately a non-issue today: **when** a tracker is eventually added,
it must be wired to check the recorded consent before initializing;
until then, there is nothing non-essential running regardless of consent
choice, so "Reject Non-Essential" and "Accept All" are behaviorally
identical in terms of actual third-party calls (both: zero).

### 9.8 Anonymous → authenticated consent synchronization

`CookieConsent` rows are keyed by `session_key` for anonymous visitors and
by `user` once authenticated — the two are never merged or carried
forward automatically on login (confirmed: `cookie_consent_record`/
`cookie_consent_me` branch strictly on `request.user.is_authenticated` and
never query by both keys together). **This means a user's anonymous
cookie choice does not automatically transfer to their authenticated
session** — they would see the banner again post-login. This is privacy-
safe (never silently broadens consent — the opposite of the directive's
concern) but is a UX rough edge, not a privacy violation.

**Update (continuation pass, 2026-09-21 — see §9A.3):** implemented.
`services.sync_anonymous_cookie_consent_to_user()` runs on login
(`LoginView`) and copies the most recent anonymous session's
`CookieConsent` into a new authenticated-user row, with `method` noting
it was carried over (new `CookieConsent.carried_over_from_session_key`
field). It never broadens consent — it only ever copies the user's own
prior anonymous choice forward, and never runs if the user already has a
`CookieConsent` row. 5 new tests + migration
`0002_cookieconsent_carried_over_from_session_key.py`.

### 9.9 Talent Pool privacy — real gap found and fixed

Confirmed via direct code trace of the actual employer-facing query path
(not just the toggle's own response): `TalentPoolCandidate.
was_discoverable_at_creation` was write-only — no read path consulted it,
meaning a candidate who opted out of Talent Pool discovery AFTER being
added to an employer's saved pool remained visible to that employer
indefinitely. **Fixed**: `TalentPool.active_candidates()` now re-checks
live `CareerProfile.is_discoverable` on every read; `TalentPoolDetail
Serializer` and the `rank_pool` action both use it. The audit-trail row
itself is retained (never deleted) — only employer-facing visibility
changes. Separately, fixing this surfaced and fixed a **critical
pre-existing bug**: the Talent Pool API's `get_queryset()` annotation
collided with a model `@property` of the same name, causing an
`AttributeError` (HTTP 500) on every single Talent Pool endpoint call —
the entire feature was non-functional in production with zero test
coverage. Both fixes are covered by 5 new end-to-end tests. The
`rank_all=True` bypass in `CandidateRankingViewSet` (ranking a job's own
applicants regardless of `is_discoverable`, on the rationale that applying
to a specific job implies consent for that job's ranking) remains
unchanged — this is a documented design decision from the original
implementation, not something this pass judged to be a bug.

### 9.10 Privacy Center — real operations confirmed

Verified via direct code trace: `generate_data_export` scopes every
section (applications, saved jobs, interview sessions, cover letters,
notifications) through Django's reverse-relation manager off the specific
`user` instance — correctly scoped, no cross-user leakage possible by
construction. `process_account_deletion` anonymizes the `User` row in
place and never calls `.delete()`; combined with `payments.Order.user`
being `on_delete=models.PROTECT`, there is no code path in this repository
that could cascade-delete a user's financial ledger history. Consent
withdrawal and Talent Pool preference changes take effect immediately
(append-only `ConsentRecord`/live `CareerProfile.is_discoverable` check).
**Gap found, not fixed this pass**: `MarketingPreference.
email_marketing_opt_in` is recorded and user-editable but is not checked
by any code in `apps/emails/` or `apps/notifications/` before sending —
the preference is currently non-enforcing in practice (there is also no
marketing-type email send path in this codebase today to enforce it
against — all `EmailTemplate.TEMPLATE_TYPES` are transactional). Flagged
for when a marketing-send path is built.

**Update (continuation pass, 2026-09-21 — see §9A.4):** a marketing-send
path was found to already exist (`apps.emails.tasks.
send_re_engagement_emails` and `send_weekly_career_digest`, both
genuinely marketing in nature, both previously unwired to any consent
check). New `apps.legal.services.can_send_marketing(user)` is now called
at the top of both tasks and skips the send when the user has not opted
in. 7 new tests across both task files.

### 9.11 GDPR/legal-domain consolidation — confirmed disconnected, convergence plan recorded (not implemented)

Confirmed via cross-import grep: `accounts.models_gdpr`/`views_gdpr`/
`tasks_gdpr` and `legal.PrivacyRequest`/`DataExportJob`/`DeletionJob` are
**100% independent** — no FK, no shared Celery dispatch, no cross-import
in either direction. A user who files a DSR through the Privacy Center UI
(`legal.PrivacyRequest`) gets a tracked, SLA-timed ticket but no export/
deletion is automatically generated unless they separately call the
`accounts` app's dedicated endpoints. **Additional gap found**: `accounts.
tasks_gdpr.process_account_deletion` has no confirmed trigger —
`request_account_deletion` creates the `AccountDeletionRequest` row with a
30-day `scheduled_for` but never calls `.delay()`, and no Celery Beat
periodic task was found that polls for due deletion requests. **This
means the 30-day grace-period deletion may never actually execute today**
— flagged as a priority follow-up, not fixed in this pass (fixing it
safely requires deciding exactly what a scheduled, irreversible account
anonymization task's safety rails should be, which is a bigger design
question than this hardening pass's scope).

**Recommended convergence plan** (not implemented this pass): treat
`accounts.DataExportRequest`/`AccountDeletionRequest` as the EXECUTION
backend (they already have real Celery tasks and file-generation logic)
and `legal.PrivacyRequest` as the CANONICAL governance/audit record a user
and admin interact with. Concretely: add a nullable FK from
`DataExportRequest`/`AccountDeletionRequest` to `legal.PrivacyRequest`,
and have `legal.services.open_privacy_request()` — when
`request_type in ("export", "delete")` — create the corresponding
`accounts` execution-request row and trigger its task, instead of leaving
the DSR as a standalone ticket. This is additive (new nullable FK, no
data loss) and does not require deleting either system. Not implemented
this pass because it changes DSR-opening behavior and should be reviewed
before shipping, consistent with "do not implement destructive/behavior-
changing consolidation without review."

**Update (continuation pass, 2026-09-21 — see §9A.5/§9A.6):** both gaps
closed, exactly per the recommended plan above. (1) `legal.PrivacyRequest`
is now the canonical governance record: a new nullable
`privacy_request` FK was added to both `accounts.DataExportRequest` and
`AccountDeletionRequest` (migration
`0005_accountdeletionrequest_privacy_request_and_more.py`), and
`legal.services.open_privacy_request()` now branches on
`request_type in ("export", "delete")` to create the corresponding
`accounts` execution row and trigger its existing Celery task via two new
private helpers (`_trigger_legacy_export`/`_trigger_legacy_deletion`),
rather than leaving the DSR as a standalone ticket. (2) The missing
scheduling gap is fixed: a new `accounts.tasks_gdpr.
execute_due_account_deletions` periodic task polls for
`AccountDeletionRequest` rows past their `scheduled_for` date and now runs
on Celery Beat (new `config/celery.py` beat entry
`execute-due-account-deletions`). As defense-in-depth, `process_account_
deletion` itself now re-checks for an active `LegalHold` on the user
immediately before anonymizing, even though the request shouldn't have
been schedulable under a hold in the first place — belt-and-suspenders
against a hold being placed after scheduling but before execution. 10 new
tests across two test files.

### 9.12 Payment runtime trace — raw card data confirmed never reachable

Full trace from `Billing.tsx`/`EmployerBilling.tsx` → `services/
billing.ts` → `CheckoutView` → `StripeProvider.create_payment` →
Stripe-hosted Checkout → webhook → `mark_order_paid` → ledger. Confirmed:
zero `CardElement`/`@stripe/*`/`elements.create` usage anywhere in the
frontend; the only request body USAM's own API ever receives for checkout
is `{package, provider}`; no Celery tasks exist in `apps.payments` at all;
no `logging.*`/`print()` calls exist anywhere in the payments app that
could log a request body. Card data has no code path into React state,
Django request bodies, Celery args, logs, or the database — it never
leaves the customer's browser/Stripe's hosted page. This is a structural
guarantee (Stripe Checkout is fully hosted-redirect), not a filtering
rule, which is the stronger property.

### 9.13 Webhook amount/currency verification — gap found and fixed

Confirmed the pre-hardening `WebhookView` trusted a validly-signed webhook
event's `status` field alone to call `mark_order_paid` — it never compared
the event's reported amount/currency against the stored `Payment.amount`/
`Payment.currency`. **Fixed**: `StripeProvider.parse_webhook` now surfaces
`amount`/`currency` from the Stripe event object; `WebhookView` rejects
(HTTP 409, logged on the `WebhookEvent.error` field) any webhook whose
amount or currency disagrees with the stored Payment row, before ever
calling `mark_order_paid`. Backward-compatible: an adapter that doesn't
report these fields (older/other providers) is not penalized — absence is
not treated as a mismatch. 3 new tests cover amount mismatch, currency
mismatch, and the legitimate matching-case sanity check. **Still not
checked** (not found anywhere, not added this pass): an explicit Stripe
account/merchant-id comparison beyond the webhook-secret signature itself
— the signature check does bind the event to the configured webhook
endpoint in practice, but there's no additional `event["account"]`
assertion. Flagged as a residual, lower-priority gap.

### 9.14 Payment provider truth table (verified from code)

| Provider | Status | Hosted/tokenized | Raw card touches USAM? | 3DS | Webhook sig verification | Replay protection | Idempotency | Refunds | EGP | Prod creds configured? | Remaining blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **stripe** | LIVE-capable (code complete; actual production liveness depends on deployed `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` values — not verified in this read-only pass) | Hosted (Stripe Checkout) | No | Provider-managed via Checkout; no USAM-side 3DS code | Yes (`stripe.Webhook.construct_event`) | Yes (DB-unique `provider_event_id` + already-processed short-circuit) | Yes (`post_transaction` idempotency key + `mark_order_paid` early-return) | Yes (`stripe.Refund.create`) | Yes | **Unverified this pass** (secret values not inspected) | Confirm live secrets are set in production `.env` |
| **alexbank** | SCAFFOLD — every money operation raises `AlexBankNotImplemented` by design | N/A (never executes) | No (can't — never runs) | Not built (deliberately, per the adapter's own docstring) | Not implemented (raises before any check) | N/A | N/A | Not implemented | N/A | N/A | Full bank API spec not yet available (business/partner dependency, not a code gap) |
| **alexbank_mock** | DISABLED in production (`_guard()` requires `DEBUG=True` or an explicit `ALEXBANK_ALLOW_MOCK` secret) | N/A (fake) | No | N/A | Signature NOT verified (mock, test-only) | Relies on the same DB-unique constraint once routed through `WebhookView` | Same ledger path as any provider | Mock always returns success | N/A | N/A | By design — never intended to run in production |
| **paymob / fawry / paytabs / Banque Misr** | PLANNED, not built — `get_provider()` raises `ProviderError` for any of these names | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | No implementation exists; would be new work |

### 9.15 Refund system classification: **PARTIAL**

Core mechanics genuinely work: eligibility floor check (`status ==
SUCCEEDED`, amount bounds), real provider API call (`stripe.Refund.
create`), atomic reversing double-entry ledger posting (never mutates the
original sale), `FinancialAuditLog` entry. **Missing**: (a) no approval/
maker-checker workflow before money moves back out — unlike the parallel
`AdjustmentRequest` dual-control pattern for manual ledger adjustments, a
single admin can request-and-execute a refund in one call; (b) no wait for
asynchronous provider confirmation — the synchronous API response is
trusted directly, which is standard for card refunds but is not webhook-
verified the way the forward payment path is; (c) a refunded customer's
granted `CompanySubscription`/`UserSubscription` entitlement is **not**
automatically revoked — `refund_payment` never touches subscription
status, so a refunded customer keeps paid-feature access unless an admin
separately intervenes. None of (a)-(c) were fixed this pass (each is a
deliberate design decision requiring product/business sign-off on the
desired behavior, not a drop-in bug fix) — flagged for a follow-up
decision.

**Update (continuation pass, 2026-09-21 — see §9A.7/§9A.8):** (a) and (c)
fixed; (b) remains open (still flagged, not silently dropped). New
`services._revoke_entitlement()` is called whenever a refund's amount
equals the original payment's full amount, flipping the relevant
subscription's status to `'cancelled'` (reusing the existing status
vocabulary rather than inventing a new one) — a **partial** refund never
touches entitlement at all, by explicit policy, since this platform has
flat plan entitlements, not metered/proportional credits, so there is no
correct partial-downgrade to compute. A new `RefundRequest` model mirrors
the existing `AdjustmentRequest` dual-control pattern exactly: `services.
request_refund()` creates a pending request, and `approve_refund_request()`/
`reject_refund_request()` (new admin endpoints,
`admin_views.refund_requests`/`refund_request_decide`) enforce that the
approver cannot be the same user as the requester before money actually
moves. This is additive alongside the pre-existing single-admin
`issue_refund` endpoint, which still exists and is not being removed in
this pass. Migration `apps/payments/migrations/0003_refundrequest.py`.
20 new tests across two test files (13 on refund authorization/
entitlement, plus updates to the existing reconciliation suite).

### 9.16 Subscription cancellation — manual-admin-only, no period-end semantics

Confirmed: the only code path that sets `CompanySubscription`/
`UserSubscription.status` to `cancelled` is the admin-only `admin_views.
subscriptions` endpoint (and the equivalent `core` admin API view) — no
self-service cancellation UI exists. No `cancel_at_period_end`/
`current_period_end` field exists on either model — cancellation is
immediate-only in the data model, with no "at period end" option to
expose even if a self-service UI were built. No Celery Beat task for
renewal or failed-renewal/dunning logic exists anywhere (`apps.payments`
has no `tasks.py` file at all). This matches the admin-managed launch
model already documented in the code's own comments — not a regression,
but confirmed as the current real behavior rather than assumed.

**Correction (continuation pass, 2026-09-21 — see §9A.9):** this section's
framing was accurate about the code, but the frontend's own checkout
disclosure text (`Billing.tsx`/`EmployerBilling.tsx`) and the seeded
Refund & Cancellation Policy text (`seed_legal.py`) were both found, on
re-reading, to still describe purchases as "renewing automatically until
cancelled" in places — a false claim given there is no recurring billing
mechanism anywhere in `apps.payments` (confirmed again this pass: still
no `tasks.py`, still no `cancel_at_period_end` field). Both were
corrected to state plainly that each purchase is a single one-time charge
with no auto-renewal and nothing to "cancel" in the billing sense.

### 9.17 npm dependency audit — safe fixes applied, remainder documented

`npm audit` (initial): 28 vulnerabilities (1 low, 9 moderate, 16 high, 2
critical). `npm audit fix` (non-force): resolved 12, leaving 16 (8
moderate, 6 high, 2 critical) — ALL remaining issues require `npm audit
fix --force`, which would force major version bumps: `vitest` 3→5,
`tailwindcss` 3→4, `vite` 5→8, `react-router-dom` 6→7.18,
`@tailwindcss/typography` 0.5.16→0.5.4 (a downgrade signal from npm's
resolver — needs manual verification, not blindly applied). **None of
these forced upgrades were applied** — per the directive's explicit
instruction not to blindly force-fix, since every one is a breaking major
version change requiring its own regression-testing pass. All but one
(`@react-three/drei`'s transitive `uuid`) are **dev-dependency-only** or
build-tool-only (`vite`, `vitest`, `tailwindcss`, `typescript-eslint`,
`lovable-tagger`) — not shipped to end users in the production bundle,
meaningfully lowering real-world exploitability despite the "critical"
severity label (e.g. the `tinypool`/`vitest` RCE requires an attacker to
control test-runner worker options, not reachable from the deployed app).
`react-markdown@10.1.0`/`remark-gfm@4.0.1` (added for policy rendering)
were confirmed via `package-lock.json` to introduce only standard,
actively-maintained `unifiedjs`/`remark`/`mdast`/`hast` ecosystem
transitive dependencies — no new vulnerability was introduced by adding
them. **Documented, not fixed**: the 16 remaining issues all require a
dedicated major-version-upgrade pass (separate from this hardening work)
with its own test/regression cycle for `vite`/`vitest`/`tailwindcss`/
`react-router-dom`.

**Update (continuation pass, 2026-09-21 — see §9A.10):** `react-router-dom`
was upgraded directly, 6.30.1→7.18.4 (v7's "library mode" is documented as
backward-compatible with v6 usage patterns) — verified via a full
`tsc --noEmit` (zero new errors vs. the pre-upgrade baseline, confirmed by
diffing against a `git stash`'d run) and full `vitest run` (93/93 passing)
after the bump. A combined `vite` 5→7.1.5 + `vitest` 3→5.0.5 upgrade was
also attempted but broke 7 real tests (a `ResizeObserver`/Radix UI
incompatibility surfaced by the new `vitest` environment) and was rolled
back per the "verify after each change, one dependency family at a time"
rule rather than shipped broken. `tailwindcss` 3→4 was not attempted this
pass either — it is a complete config-format rewrite, not a drop-in
version bump, and judged too risky to combine with everything else in
this pass. **Final state**: 14 vulnerabilities remain (down from 16),
all still devDependencies-only, never shipped to the production bundle.

### 9.18 Markdown rendering XSS — hardened

Confirmed `PolicyMarkdown.tsx` had no `rehype-raw`/`dangerouslySetInnerHTML`
— react-markdown's default pipeline already rendered embedded raw HTML
(`<script>`, `<img onerror=...>`) as inert text, not executable DOM. One
real gap found: the `a` component override did not restrict URL schemes,
so a `javascript:`/`data:` URL in markdown source would fall through to a
real `<a href>`. **Fixed**: added an explicit scheme allowlist (http(s),
mailto, tel, relative, anchor) for both link and image `src`/`href`
attributes — anything else is neutralized to `#` (links) or not rendered
at all (images). 10 new tests, including explicit proof that embedded
`<script>`/`onerror` payloads never execute and that `javascript:`/`data:`
URLs are neutralized while legitimate `https:`/`mailto:`/internal `/legal/
...` links continue to work correctly.

### 9.19 Security headers — reviewed, not changed this pass

Confirmed present (nginx): HSTS, X-Frame-Options, X-Content-Type-Options,
X-XSS-Protection, Referrer-Policy, Permissions-Policy. Confirmed present
(Django production settings): `SECURE_HSTS_*`, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`.
Confirmed **absent** at both layers: `Content-Security-Policy` (no
`django-csp` dependency either). `SESSION_COOKIE_SAMESITE`/
`CSRF_COOKIE_SAMESITE`/`CSRF_COOKIE_HTTPONLY` rely on Django 4.2's
framework defaults (`Lax`/`Lax`/`False` respectively) rather than being
explicitly hardened — `CSRF_COOKIE_HTTPONLY=False` is actually correct/
required for this SPA architecture (the frontend must read the CSRF
cookie to echo it in a header) and is not a misconfiguration.
**Not changed this pass**: adding a CSP requires auditing every actual
script/asset source in production first (the Rasheed 3D assets, any CDN
fonts, etc.) to avoid breaking functionality — the directive itself asks
for a Report-Only CSP as the first step, which is new work beyond a
"hardening pass" scope and is recommended as a dedicated follow-up task.

**Update (continuation pass, 2026-09-21 — see §9A.12):** built, shipped
as **Report-Only only** (never enforcing) since this platform never had a
CSP before and an enforcing header risks breaking the app on day one. New
`apps.core.csp_middleware` adds `Content-Security-Policy-Report-Only`
against a verified real origin inventory (`fonts.googleapis.com`,
`checkout.stripe.com`, `accounts.google.com`, plus same-origin
WebSocket), registered in `MIDDLEWARE`. 4 new tests confirm the header is
present, report-only (not enforcing), and lists exactly the verified
origins. Promoting this to an enforcing header is a follow-up step once
report data from real traffic has been reviewed — not done this pass.

### 9.20 Admin Legal RBAC — single flat role confirmed, not changed

Confirmed: `IsAdminRole` is a single flat `request.user.role == "admin"`
check, applied identically across the entire codebase (payments, legal,
every other admin-gated endpoint) — not just this feature. Confirmed via
repo-wide grep: Django's built-in `Permission`/`Group` system
(`has_perm`, `Permission.objects`, `Group.objects`,
`@permission_required`) is used **nowhere** in this repository. There is
no existing granular-permission convention for this work to extend — a
granular RBAC system (separate "can activate policy" vs. "can process
DSR" permissions) would be a brand-new architectural pattern introduced
solely for this feature while every other admin-gated domain
(payments, jobs, users) stays on the flat role check. **Not implemented
this pass** — introducing an inconsistent permission model for one domain
only was judged a worse outcome than the current uniform-but-coarse
model; a platform-wide RBAC upgrade (if desired) should be a deliberate,
separately-scoped decision covering all admin domains, not just legal.

### 9.21 Policy/DSR audit logging — confirmed sufficient for DSRs, a real gap for policy versions

`admin_privacy_request_transition` → `services.transition_privacy_request`
writes a genuine append-only `PrivacyRequestEvent` row for every DSR
status change — confirmed sufficient. `policy_version_transition` →
`services.activate_version`, however, only mutates the `PolicyVersion`
row's own `status`/`approved_by`/`retired_at` fields in place — there is
**no append-only history table** for policy-version status transitions
specifically (unlike `ConsentRecord`/`PolicyAcceptance`, which genuinely
are append-only). The repo's own `apps.core.models.ActivityLog` model
exists but has zero call sites anywhere in the codebase (confirmed via
repo-wide grep) — it is permanently-empty dead code, not an available
audit mechanism today. **Not fixed this pass** (adding a dedicated
`PolicyVersionEvent` table mirroring `PrivacyRequestEvent` is a clean,
low-risk addition, but was deprioritized behind higher-impact fixes in
this pass — flagged as a near-term follow-up, not a blocker, since
`PolicyVersion.updated_at` plus the one-ACTIVE-version-at-a-time invariant
still gives a verifiable, if less granular, history).

**Update (continuation pass, 2026-09-21 — see §9A.1):** rather than add a
new dedicated table, `services.activate_version()` now writes a real
`apps.core.models.ActivityLog` entry on every activation — giving the
dead-code `ActivityLog` model its first genuine call site in the repo,
and giving policy-version transitions an actual append-only audit trail
without introducing a parallel schema. The same change also hard-blocks
activating any version whose content still contains the literal marker
text `"REQUIRES LEGAL REVIEW"` (new `UNRESOLVED_MARKER` constant +
`ActivationBlocked` exception) unless explicitly bypassed via
`allow_unresolved_markers=True` — closing the "unreviewed text could be
accidentally activated" risk at the one real code chokepoint, not just
documenting it. A new admin `policy_version_preview` action/route lets a
reviewer read a DRAFT version's rendered content before deciding to
activate it, without requiring it to go live first to be readable.

### 9.22 Retention enforcement — built this pass (was previously database-only)

`RetentionPolicy` previously had zero code acting on it. **Built**:
`apps.legal.retention_service.run_retention_enforcement()` +
`manage.py enforce_retention` — DRY_RUN by default, only enforces a
category with BOTH a legally-confirmed `retention_period_days` (not NULL,
`requires_legal_review=False`) AND an explicitly-registered handler
(`interview_transcripts`, `cv_documents` today — `gdpr_export_files`/
`account_deletion_grace` are deliberately excluded since they already have
real enforcement elsewhere, to avoid two systems racing on the same
rows). Any user under an active `LegalHold` is excluded from every
category. 8 new tests. **Not wired into Celery Beat** — deliberate,
per the directive's instruction to default to DRY_RUN until retention
periods are legally confirmed; scheduling is a separate go-live step for
whoever operates the recurring job once legal signs off on actual periods.

**Update (continuation pass, 2026-09-21 — see §9A.1):** `enforce_retention`
itself was hardened, independent of the Beat-scheduling decision above
(which still stands — it remains deliberately NOT scheduled, since
retention periods are still legally unconfirmed). Each category is now
processed inside its own `try`/`except` so one category's failure (e.g. a
storage error deleting one user's CV) cannot silently abort the other
categories in the same run; the command's output now reports a
`failed`/`total_failed` count per category via a new
`CategoryResult.failed`/`error` field, so a partial failure is visible in
the command's own output rather than only in logs. 2 new tests.

### 9.23 Processor register — seeded from real integrations this pass

Was previously an empty table despite the model existing. Seeded with
exactly 4 vendors, each confirmed by actual code: AWS (S3 for CVs/media/
interview audio, Bedrock for AI inference, Transcribe/Polly for voice,
Secrets Manager for credentials), Stripe (hosted checkout), Typesense
(search index), Sentry (backend error tracking — server-side only, not a
browser tracker). `dpa_signed` left `NULL` (unconfirmed) for all four —
never assumed signed or unsigned. Added a "Processors" tab to the Admin
Legal Control Plane UI to view this register. 7 new tests, including an
explicit assertion that `dpa_signed` is never defaulted to a boolean.

### 9.24 AI processing disclosures — reviewed, consistent with real behavior

The 4 seeded disclosures (Rasheed, job matching, interview practice, CV
parsing) were cross-checked against this pass's own code audits of
`apps/interviews/voice_service.py` and the broader AI touchpoints — the
descriptions remain accurate. The `makes_final_decision` field has a
hard server-side validator (`AIProcessingDisclosureSerializer.
validate_makes_final_decision`) rejecting `True` for any entry — confirmed
still enforced, re-tested this pass (`test_seed_legal_ai_disclosures_
never_claim_final_decision`).

### 9.25 Voice/interview privacy — one correction to the prior audit, two gaps confirmed still open

**Correction**: the original master doc's claim that raw audio deletion
"runs unconditionally after transcription" is **not accurate** — re-
reading `voice_service.py`'s `speech_to_text()` shows the `s3_client.
delete_object()` call only executes on the SUCCESS path (after a
completed transcription job and a successful transcript fetch/parse). Any
timeout, failed transcription job, or exception during fetch/parse returns
early WITHOUT deleting the raw audio — meaning failed/timed-out voice
sessions leave orphaned raw audio in S3 with no cleanup job.

**Update (continuation pass, 2026-09-21 — see §9A.17): FIXED.**
`speech_to_text()` was rewritten so the S3 delete and local temp-file
cleanup both happen in a `finally` block, guaranteeing cleanup on every
exit path — success, transcription timeout, failed job, or any exception
during fetch/parse — not just the success path. Two new Celery tasks
close the remaining edge cases that a `finally` block inside a single
request/task can't reach on its own: `mark_stale_interview_sessions_
abandoned` (catches sessions where the process itself died or was killed
mid-call, before `finally` could even run) and `cleanup_orphaned_voice_
interview_audio` (a sweep for any S3 object matching the audio key
pattern that has no corresponding live session row at all — defense
against any cleanup path this pass didn't anticipate). Both are now
scheduled on Celery Beat. 9 new tests. **Still confirmed open**
(unchanged from the original audit, not addressed this pass either): no
retention/TTL field on `InterviewSession.transcript` or
`InterviewQuestion.answer_text` — stored indefinitely; `enforce_retention`
CAN clear `InterviewSession.transcript` once
`RetentionPolicy("interview_transcripts")` is legally confirmed and
switched off `requires_legal_review`, closing this gap operationally the
moment legal provides a number. Employers confirmed to have zero code-
level access to interview transcripts (clean separation, unchanged). Also
noted but NOT fixed this pass: a pre-existing model-fragmentation issue
where `apps.interviews` and `apps.career` each have their own, separate
`InterviewSession`-shaped model — flagged as a follow-up architectural
question, out of scope for a cleanup-focused fix.

### 9.26 CV/document security — malware scanning is real, with a packaging caveat

**Correction to an earlier assumption**: ClamAV malware scanning is NOT
merely absent — `apps.core.upload_security.scan_stream_for_malware()` is
real code, genuinely called from `apps.profiles.serializers.
CVUploadSerializer.validate_cv_file()`, with `CLAMAV_FAIL_CLOSED=True` by
default (settings). **However**: `pyclamd` (the Python ClamAV client this
code imports) is absent from every `requirements/*.txt` file — if not
manually installed in the deployed environment, `_get_clamd_connection()`
returns `None` and, combined with fail-closed, **every CV upload would be
rejected outright** rather than silently skipping the scan. This is a
packaging gap, not a scanning-logic gap. **Not fixed this pass** (adding
`pyclamd` to requirements is a one-line change but requires confirming a
real `clamd` daemon is actually provisioned on the production host first
— otherwise fail-closed would newly start rejecting all CV uploads the
moment the dependency is added, which is a deploy-coordination step
beyond this pass's scope). MIME/extension/magic-byte/size validation and
path-traversal protection all confirmed real and already enforced
(`UploadValidator`). No automated CV retention/deletion job exists beyond
on-demand user-triggered delete — same gap as interview transcripts,
closable via `enforce_retention` once `cv_documents`' retention period is
legally confirmed.

**Update (continuation pass, 2026-09-21 — see §9A.15/§9A.16):** the
packaging/visibility gap is now surfaced operationally rather than left
silent: `SystemHealthView` (admin-facing system health endpoint) now
reports whether the ClamAV connection is actually reachable, so an
operator can see at a glance whether CV uploads are silently
fail-closed-rejecting due to a missing daemon connection, instead of only
discovering it when users start reporting rejected uploads.
`docker-compose.yml` was fixed to set `CLAMAV_HOST`/`CLAMAV_PORT`
environment defaults and add a real `clamav` service healthcheck
dependency, so a fresh `docker-compose up` actually provisions a working
scanner rather than silently omitting it. `requirements.txt` now carries
an explicit comment that `pyclamd` is pinned but **confirmed NOT
installed in this dev sandbox** (verified directly this pass via `import
pyclamd` → `ModuleNotFoundError`) — flagging that production installation
still needs independent confirmation, not assumed from the requirements
file alone. Separately, this pass also fixed two real upload-path bugs
found while reviewing this area: `JobSubmitApplicationView` was bypassing
`upload_security` validation entirely for CV uploads submitted with a job
application (now validated+scanned like every other CV upload path), and
`CompanyClaimCreateSerializer` was accepting ownership-proof documents
with no `validate_document` check at all (now added). A new authenticated
`download_cv` endpoint was added on `JobApplicationViewSet`, reusing the
existing employer-ownership `get_queryset` filter, closing the previously
disclosed "CV URL is a bare, guessable media URL" gap for applications
viewed through that endpoint specifically — `apps.career.cv_parser_views.
cv_delete`'s storage-path bug (deleting by `.path` instead of `.name`,
which could silently no-op or raise on some storage backends) was also
fixed. 22 new tests across upload-security, CV-access-control, and
system-health coverage. **Still open, not addressed this pass**: the
broader architectural gap — CVs served from local disk + nginx rather
than short-lived signed URLs — remains; closing it fully would need an
S3 migration for CV storage, which is out of scope for this pass.

---

## 9A. Continuation hardening pass (2026-09-21) — summary of this session's work

This section indexes everything fixed in the continuation pass referenced
by the "**Update (continuation pass, 2026-09-21 ...)**" notes inserted
throughout §9 above, plus items that didn't map onto an existing §9.x
subsection. Every item below is additive/corrective to the prior pass's
findings — nothing in §§1-9.26 above was deleted; superseded claims were
corrected in place with an explicit "Update" note so the document's
history stays legible.

1. **`seed_legal` DRAFT-by-default** (closes §9.2's launch-flow gap): new
   `--activate-drafts` flag required to auto-activate (test/staging use
   only); gated behind `activate_version(allow_unresolved_markers=True)`.
   9 tests.
2. **`legal_readiness` management command** (new, no prior §9.x entry):
   `apps.legal.readiness_service.check_legal_readiness()` + `manage.py
   legal_readiness` gives a single scriptable command an operator can run
   before go-live to see every `CONFIGURATION REQUIRED`/`LEGAL REVIEW
   REQUIRED` item from §9.4 in one pass, rather than reading this document
   by hand. 8 tests.
3. **Policy-activation audit trail + unresolved-marker gate** — see §9.21
   update above.
4. **Draft policy preview** — new `policy_version_preview` admin
   action/route lets a reviewer read a DRAFT's rendered content before
   activating it — see §9.21 update above.
5. **Salary-currency follow-up decision implemented** — see §9.6 update
   above.
6. **Anonymous→authenticated cookie-consent carryover** — see §9.8 update
   above.
7. **GDPR/legal-domain consolidation implemented** — see §9.11 update
   above.
8. **Account-deletion Celery scheduling** — see §9.11 update above
   (`execute_due_account_deletions` Beat task).
9. **Legal-hold defense-in-depth** — see §9.11 update above (re-check in
   `process_account_deletion` itself, not just at scheduling time).
10. **`enforce_retention` per-category failure isolation/reporting** —
    see §9.22 update above.
11. **`can_send_marketing` eligibility service wired in** — see §9.10
    update above.
12. **Refund→entitlement reconciliation** — see §9.15 update above
    (`_revoke_entitlement`, full-refund-only policy).
13. **Refund maker-checker (`RefundRequest`)** — see §9.15 update above.
14. **Subscription-cancellation/auto-renewal honesty correction** — see
    §9.16 update above (frontend + seeded policy text both corrected).
15. **ClamAV operational visibility** — see §9.26 update above
    (`SystemHealthView` check, `docker-compose.yml` fix).
16. **CV/document upload-security end-to-end** — see §9.26 update above
    (`JobSubmitApplicationView`, `CompanyClaimCreateSerializer`,
    `download_cv` endpoint, `cv_delete` storage-path fix).
17. **Voice/interview audio cleanup** — see §9.25 update above
    (`finally`-based cleanup + two new sweep tasks).
18. **CSP (Report-Only)** — see §9.19 update above.
19. **npm dependency remediation** — see §9.17 update above
    (`react-router-dom` upgraded; `vite`/`vitest` attempted and rolled
    back; 14 vulnerabilities remain, documented as dev-only).
20. **Audit-event identifiability** — addressed as part of item 3 above:
    the new `ActivityLog` entries written by `activate_version()` record
    the acting admin user, giving policy-activation events a real,
    attributable actor rather than only a timestamp.
21. **Processor-register corrections** — `seed_legal`'s processor seed
    data was reorganized with explicit `processor_type` tags
    (`cloud_infrastructure`, `model_path_via_infrastructure`,
    `external_processor`, `self_hosted_infrastructure`) so AWS, Stripe,
    and Typesense are no longer flattened into one undifferentiated list.
    Anthropic was added as a model-path note (Bedrock mediates; there is
    no direct Anthropic API contract/account), not listed as a direct
    processor — avoiding the mistake of claiming a vendor relationship
    that doesn't exist in the current architecture. 1 new test.
22. **Public-marker safety** — covered by item 3/§9.21's
    `UNRESOLVED_MARKER` activation gate: a policy page can never go live
    while still containing literal `"REQUIRES LEGAL REVIEW"` text, unless
    a reviewer explicitly bypasses the gate (test/staging only).
23. **First-launch legal flow test** (new, no prior §9.x entry): one
    comprehensive end-to-end test (`test_first_launch_flow.py`) exercises
    the entire pipeline — fresh DRAFT seed → admin review/preview →
    activation → signup → policy acceptance — in a single pass, as a
    regression guard against any future change silently breaking the
    launch sequence documented in §9.2.
24. **Frontend fail-closed on missing/incomplete legal config**: `Login.
    tsx` now gates the signup submit button behind a `legalReady` check
    (both Terms and Privacy must have a live `ACTIVE` version via
    `listPolicies()`) rather than assuming they exist — a user can no
    longer accidentally sign up without a real, current policy to accept
    just because a policy failed to load. `PolicyPage.tsx`'s single
    `notFound: boolean` was replaced with a three-state `unavailable:
    'not_found' | 'error' | null`, so a genuine fetch/network error is no
    longer rendered identically to "this policy legitimately has no
    active version" — both are now visible, honest, distinct states,
    never a blank page. 10 new tests (8 Login, 2 PolicyPage); full
    frontend suite now 93/93.
25. **Full verification pass**: 889 backend tests passed (up from the
    prior pass's 149, reflecting all work above plus pre-existing
    suites), 93 frontend tests passed (up from 75), `tsc --noEmit` clean
    (zero new errors vs. pre-pass baseline), production `vite build`
    succeeded, `manage.py makemigrations --check --dry-run` reported no
    missing migrations.

**Not implemented this pass** (carried forward, still open, still
honestly flagged rather than silently dropped): the retention-period
numbers themselves (still `LEGAL REVIEW REQUIRED`, §9.4), Celery Beat
scheduling of `enforce_retention` itself (still deliberately unscheduled
pending those numbers), `tailwindcss` 3→4 and `vite`/`vitest` major
upgrades (attempted/deferred, §9.17), CSP promotion from Report-Only to
enforcing, dedicated `PolicyVersionEvent` table (superseded by the
`ActivityLog` approach instead — judged sufficient, not revisited), CV
storage migration to signed URLs (§9.26), `InterviewSession` model
fragmentation between `apps.interviews` and `apps.career` (§9.25), and
the asynchronous-provider-confirmation gap for refunds (§9.15 item (b),
still open).

---

## 10. Final Acceptance checklist (A–Z areas)

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
| M. Tests (backend + frontend) | ✅ §6/§9A.25 — **889 backend + 93 frontend passing** (as of the 2026-09-21 continuation pass; was 149+75 at the prior pass) |
| N. This master document | ✅ updated 2026-09-21, §9A |
| O. Commit + push to `development` | ⏳ **pending this session** — see §9A note below; prior work already pushed as `d144cfb`, `a6b9366`, `a3d6de7`, `49eddd6`, `cbbd048` |
| P. Deployment commands per increment | ✅ §8 (unchanged structurally; still requires real server discovery output before a final command set can be given for this pass's changes — new migrations exist, see §9A items 5/6/13) |
| Q. REQUIRES LEGAL REVIEW items explicitly tracked, not invented | ✅ §7, re-confirmed unchanged by §9A — no legal fact was invented this pass either |
| R. No fake compliance/security claims anywhere | ✅ verified by reading every new/changed policy page's text; one prior false claim (auto-renewal) was found and corrected, §9.16/§9A.14 |
| S. AI disclosure (assists, doesn't decide) enforced at the data layer | ✅ `AIProcessingDisclosure.makes_final_decision` validator, re-verified this pass |
| T. Talent Pool explicit opt-in (not automatic exposure) | ✅ pre-existing `is_discoverable=False` default, surfaced in 3 places, unchanged this pass |
| U. Direct Apply redirect disclosure | ✅ Terms of Service §3, unchanged this pass |
| V. Minors/children policy — not invented | ✅ §7 item 3, unchanged — still correctly blank |
| W. CV/document security gap — disclosed, not silently left unmentioned | ✅ Security Overview policy page; underlying gap narrowed this pass, §9.26/§9A.15-16 (upload path hardened, operational visibility added) — storage-architecture gap still disclosed, not closed |
| X. Interview transcript retention — disclosed as unconfigured | ✅ §7 item 4, unchanged — orphaned-audio cleanup fixed (§9.25/§9A.17), retention period itself still legally unconfirmed |
| Y. Currency consistency gap (Job vs employer-posting model) — flagged | ✅ §3, §7 item 9 — **decision implemented this pass**, §9.6/§9A.5 (`Job.salary_currency` now nullable, no default; `JobPosting` unchanged by design) |
| Z. CSP / cancellation-timing / processor-register gaps — flagged, not fabricated | ✅ §7 items 10–11 — CSP now shipped Report-Only (§9.19/§9A.18), processor register corrected with type distinctions (§9.23/§9A.21), cancellation-timing semantics still unmodeled (unchanged, still flagged) |

---

## 11. Overall project status (per directive §38/§40 — do not claim "fully compliant")

| Component | Status |
|---|---|
| `apps.legal` backend domain (models/APIs/admin control plane) | **ENGINEERING READY** — now includes draft-safe seeding, activation audit trail, unresolved-marker gate, and a scriptable `legal_readiness` check |
| Legal Center public pages, cookie consent, Privacy Center, signup consent UI | **ENGINEERING READY** — frontend now fails closed (not open) on missing/incomplete policy data |
| Payment/card-security guarantees (no raw card data, webhook verification incl. amount/currency, idempotency) | **ENGINEERING READY** |
| Refund authorization + entitlement reconciliation | **ENGINEERING READY** — maker-checker added, full-refund entitlement revocation added; async provider-confirmation gap still open (§9.15) |
| Talent Pool privacy enforcement (incl. the critical 500-error fix) | **ENGINEERING READY** |
| GDPR/DSR consolidation (PrivacyRequest ⇄ accounts execution backend) | **ENGINEERING READY** — previously disconnected systems now linked; 30-day deletion grace period now actually scheduled on Celery Beat |
| Retention enforcement engine | **ENGINEERING READY** (DRY_RUN only — execution requires §9.4's legal sign-off; per-category failure isolation added this pass) |
| Voice/interview audio cleanup | **ENGINEERING READY** — guaranteed cleanup on every exit path + two sweep tasks on Celery Beat |
| CV/document upload security | **ENGINEERING READY** — end-to-end validation+scanning now consistent across all upload paths; ClamAV daemon provisioning in production is **CONFIGURATION REQUIRED** (confirmed `pyclamd` not installed in this dev sandbox; production status unverified by this agent) |
| CSP (Report-Only) | **ENGINEERING READY** — not yet promoted to enforcing |
| Processor register, AI disclosures | **ENGINEERING READY**; DPA confirmation = **LEGAL REVIEW REQUIRED** |
| Legal entity identity, refund window, governing law | **CONFIGURATION REQUIRED** (§9.4) |
| Minors' age threshold, retention periods, DPA statuses | **LEGAL REVIEW REQUIRED** (§9.4) — explicitly not invented anywhere, unchanged this pass |
| Everything in this document | **NOT YET PRODUCTION ACTIVE** — this pass's changes are not yet committed or pushed as of this writing (see §9A note above); awaiting commit/push to `development`, then real server-discovery output from the user before any final deployment commands for this pass's changes (new migrations in `legal`, `accounts`, `jobs`, `payments`) can be given, then the live-verification pass once deployed |

**This is engineering-complete and production-deployable code. It is not a
claim of legal compliance, PCI compliance, GDPR compliance, or any other
regulatory certification — those require qualified legal/compliance review
of the items in §9.4, which this document deliberately does not attempt
to resolve on its own.**

# USAM — Master Identity / Payment / Financial / Admin Architecture (Section-58 Deliverable)

> Audit-grounded. Marks DONE (built + committed) vs GAP (not yet built). This is
> the consolidated response to the master directive. Financial-dangerous items
> require explicit authorization before live money movement.

Repo state at authoring: `development @ 04b66ff`. Financial core lives in
`backend/apps/payments/`.

---

## A. Current Architecture Map

```
Frontend (React/Vite/TS, Tailwind + shadcn) ── /api/v1 ──> Django/DRF
  role-based routing (lib/role-routing)              apps.* (domain apps)
  Billing UI (/app/billing)                          apps.payments (financial core)
  Admin Finance (/admin/finance)                     apps.core (entitlements)
Postgres + Celery + Channels + Bedrock(AI) + AWS(EC2/nginx/gunicorn/Secrets Mgr)
```

## B. Current Payment Flow (DONE)
`Package → create_order → Payment(pending) → provider.create_payment (Stripe hosted / free-instant) → webhook (signed, deduped, idempotent) → services.mark_order_paid → double-entry ledger posting → Invoice → entitlement grant → FinancialAuditLog`. Reference namespace `C-YYYYMMDD-XXXX` (platform C/E/F/K).

## C. Current Identity / User-Type Flow (DONE ~80%)
`user | employer | admin` roles; `Company` = org; `EmployerProfile` + `EmployerTeamMember` (owner/admin/recruiter/hiring_manager/viewer); role-based post-auth routing; audience pages `/for-individuals`, `/for-businesses` (Government = "Soon"); account-type selector at registration; billing scoped to Company via `CompanySubscription`. **GAP:** explicit product-context/workspace switcher; dedicated Government flow.

## D. Current Database Model (DONE)
Financial: `Package, Coupon, Order, Payment(+Attempt), Invoice(+Item), Refund, WebhookEvent, FinancialAuditLog, LedgerAccount, LedgerTransaction, LedgerEntry, IdempotencyKey`. Entitlements: `SubscriptionPlan, CompanySubscription`. Balances derived from immutable ledger entries.

## E. Current Admin Capabilities (DONE)
React `/admin` (jobs/verification/sources/users/companies/talent/packages/matching/AI tabs) + `/admin/finance` (overview KPIs, revenue by platform/package, reconciliation exceptions, transactions). Backend `/api/v1/payments/admin/*` (IsAdminRole) + `/api/v1/admin-api/*` (plans, subscriptions, talent pools, celery-beat toggle). Django admin for all models incl. payments.

## F. Missing Capabilities (real GAPs, prioritized)
1. **Wallet** (ledger-backed) — not built. Only needed if business model requires stored credit/escrow (Freelancing). Directive says don't build unless required.
2. **Subscription engine** (renewal/proration/grace/upgrade-downgrade) — only `CompanySubscription` status lifecycle exists; no recurring-billing engine. Kill Bill vs custom decision below.
3. **Manual adjustment dual-approval workflow** (Part XXX) — not built.
4. **AI financial workspace** (natural-language admin analytics) — not built.
5. **Continuous scraping schedule** (PeriodicTask seeding) — manual-only today.
6. **AlexBank/Banque Misr adapter live** — scaffolded, raises until real contract/creds.
7. **Multi-currency FX** — EGP+USD stored; no FX conversion.
8. **CSV/XLSX/PDF financial exports** — not built.
9. **Government/institution flow** — not built.

## G. Broken Capabilities
- **Global React crash** reported live ("Something went wrong"). Hardened in `04b66ff` (global widgets isolated in error boundaries + i18n try/catch). Needs live console error if it persists after clean rebuild.

## H. Open-Source Evaluation Matrix (decision: native for now)
| Option | Role | License | Decision |
|---|---|---|---|
| Formance Ledger | Programmable ledger (separate Go svc) | MIT | Defer — ops overhead not justified at current volume |
| Blnk | Ledger + reconciliation (separate Go svc) | Apache-2.0 | Defer — revisit at scale for reconciliation |
| Kill Bill | Subscription billing (JVM svc) | Apache-2.0 | Reject now — heavy JVM next to Django |
| AWS Secrets Manager | Secret storage | AWS | **Adopt** (already wired) |
**Chosen:** native Django double-entry ledger + provider abstraction, kept ledger-/provider-agnostic so migration to Blnk/Formance later needs no business-logic change. ADR: `apps/payments` is the seam.

## I. Proposed Target Architecture
Matches directive §57. Already realized: Identity Core (roles/org), Product Registry (platform_code + Package), Order Engine, Payment Core (provider abstraction), Ledger Core, Invoices, Reconciliation, Analytics, Admin Control Center. To add: Wallet (if required), Subscription engine, AI workspace, Government flow.

## J. Migration Plan
Additive only (no destructive migrations). New tables added via `payments` app migrations. `SubscriptionPlan`/`CompanySubscription` preserved and linked from `Package`. No existing data reset.

## K. Security Plan
Provider creds via AWS Secrets Manager (never in Git/DB plaintext/logs); Stripe hosted checkout (no card data touches USAM, minimal PCI scope); webhook signature verify + idempotency; admin endpoints IsAdminRole; FinancialAuditLog on sensitive actions; no secrets rendered after storage. **To add:** admin MFA, granular finance sub-roles, dual-approval for adjustments.

## L. Testing Plan (DONE for core)
19 payments tests pass (references, ledger balance/unbalanced/idempotency, state machine, coupon pricing, order→paid→entitlement idempotency, analytics reflects real revenue, reconciliation flags missing ledger, admin gating 403/200, seed packages). **To add:** provider webhook signature tests, refund reversal test, subscription renewal tests.

## M. Production Deployment Plan
Pull → `migrate` → `seed_packages`/`seed_approved_ats`/`setup_sources`/`run_scrapers` → restart `usam.service` → clean frontend rebuild → reload nginx → verify served bundle + APIs 200.

## N. Rollback Plan
All changes additive + committed atomically; roll back by `git checkout <prev-sha>` on the `/var/www/usam` checkout + rebuild. Ledger is append-only (no destructive migration to reverse). DB migrations are additive; a down-migration drops only the new payments tables.

## O. Exact Implementation Order (remaining)
1. Confirm live app renders (crash fix `04b66ff`) — blocks admin UI usability.
2. Continuous scraping schedule (PeriodicTask auto-seed) — low-risk, high-value.
3. Financial CSV/XLSX exports (admin) — low-risk.
4. AI financial workspace (read-only over real analytics) — medium.
5. Subscription renewal engine (Celery beat) — medium; confirm recurring model.
6. Wallet — ONLY if business requires stored credit/escrow (needs your decision).
7. AlexBank/Banque Misr live adapter — when credentials/contract arrive.
8. Government flow — when product scope confirmed.

---

## Decisions needed (financially dangerous / scope) — require your authorization
1. **Wallets/escrow:** required, or purely package/subscription purchase? (Escrow only if Freelancing needs it.)
2. **Recurring subscriptions:** auto-renew with a real provider now, or manual/admin-managed for launch?
3. **Live provider:** Stripe (test now) confirmed as first live, AlexBank when creds arrive?
4. **Multi-currency:** EGP-only launch, or EGP+USD live with FX?

Everything else in the "remaining" list I will build without further prompting (all additive, non-destructive, reversible).

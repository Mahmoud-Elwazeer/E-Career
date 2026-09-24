# USAM — Role Separation + Financial Infrastructure Audit (code-verified)

_Date: 2026-09-24. Phase-0 audit per the directive. Everything below is read
from real backend code, not status docs._

---

## PART A — Account / Role / Organization model

### What EXISTS (verified)
- **`User.role`** — `"user" | "employer" | "admin"` (`apps/accounts` / `services/auth`).
- **`Company`** (`apps/jobs/models.py`) — the de-facto Organization entity.
- **`EmployerProfile`** (`apps/employers/models.py`) — OneToOne user↔Company,
  `job_title`, `phone`, admin `is_verified`. A user becomes an employer by
  creating this (via `/employer/register/`).
- **`EmployerTeamMember`** (`apps/employers/models.py`) — **multi-seat org model
  already exists**: links additional users to a `Company` with roles
  `owner / admin / recruiter / hiring_manager / viewer`, plus `invited_by`.
- **`SubscriptionPlan`** (`apps/core/models.py`) — entitlement definition:
  `feature_flags` (JSON), `job_posting_limit`, `candidate_search_limit`,
  `ai_features_enabled`, `is_active`. **No billing fields** (by design).
- **`CompanySubscription`** (`apps/core/models.py`) — Company↔Plan with a
  status lifecycle (`trial/active/suspended/cancelled`). **Billing is correctly
  scoped to the Company/Org, not the individual user** — this already matches
  the directive's Part XXVII requirement.
- **Frontend role separation (this session's earlier work):** role-based
  post-auth routing (`lib/role-routing.ts`), dedicated `/for-individuals` and
  `/for-businesses` pages, employer vs individual nav arrays, account-type
  selector at registration.

### What's PARTIAL / MISSING
- **No generic `Organization`/`Workspace`/`Membership` abstraction** — `Company`
  + `EmployerTeamMember` cover the employer side, but there is no unified
  workspace concept, and an individual "workspace" is implicit (just the user).
  For the directive's multi-role vision (one human = individual identity +
  org membership), the building blocks exist (`EmployerTeamMember` gives
  membership) but aren't unified behind a "current workspace/product context".
- **No product-context switch** — the app infers employer via `role==='employer'`;
  there's no explicit "acting as Individual vs Company X" switcher.
- **Entitlement enforcement** — `SubscriptionPlan` limits exist but I have not
  verified they are enforced at every gated action (job post limit, candidate
  search limit). Needs a dedicated entitlement service audit.

### Recommendation (role separation)
The employer org model is largely present. The pragmatic, low-risk path is:
1. Treat `Company` as the Organization and `EmployerTeamMember` as Membership
   (no new schema needed short-term).
2. Add an explicit **product-context / workspace switch** in the frontend
   (Individual ↔ each Company membership) rather than a new backend model.
3. Only introduce a formal `Organization`/`Workspace` table if/when a user must
   belong to multiple companies with independent billing — defer until needed.

---

## PART B — Financial / Payment infrastructure

### What EXISTS (verified)
- `SubscriptionPlan` + `CompanySubscription` (entitlement definitions + status
  lifecycle) — **but explicitly no payment/billing fields.**
- Admin CRUD for plans (`apps/core/admin_api_views.py`
  `SubscriptionPlanListView/DetailView`).

### What's MISSING (essentially the entire financial core — greenfield)
No models/services exist for any of:
- Payment, PaymentAttempt, PaymentIntent, Order
- Invoice, InvoiceItem, Receipt
- Price, Discount, Coupon, Tax, Currency, Fee
- Refund, Credit
- Wallet, WalletTransaction
- LedgerAccount, LedgerEntry, Transaction (no double-entry ledger)
- Payout, Settlement, ReconciliationRecord
- Provider, ProviderAccount, ProviderTransaction, WebhookEvent
- Any payment provider integration (no Stripe/Paymob/Fawry/AlexBank code)
- Idempotency keys, webhook signature verification, reconciliation

**Implication:** there is nothing fake to remove — the financial subsystem is a
genuine greenfield build. That is a multi-week, security-critical program
(real money movement + real bank credentials).

---

## PART C — Open-source financial-core evaluation (against this stack)

Stack reality: **Django/DRF + PostgreSQL + Celery + AWS**, single-currency
focus initially (EGP/USD), Egypt-first providers (AlexBank/Paymob/Fawry).

| Option | Role | License | Fit for this stack | Verdict |
|---|---|---|---|---|
| **Formance Ledger** | Programmable double-entry ledger (separate Go service + its own store) | MIT | Powerful, but adds a separate service to operate; overkill for early volume | Reference / defer |
| **Blnk** | Double-entry ledger + balances + reconciliation + inflight (separate Go service) | Apache-2.0 | Strong feature match (reconciliation!), but again a separate service | Reference / consider at scale |
| **Kill Bill** | Subscription billing + invoicing (JVM service + its own DB) | Apache-2.0 | Heavy JVM stack next to Django; high ops cost | Reject for now |
| **AWS Secrets Manager** | Secret storage (NOT a ledger) | AWS | Correct tool for AlexBank credentials + rotation | **Adopt for secrets** |

**Recommendation:** Do **not** stand up Formance/Blnk/Kill Bill as separate
services yet. For current volume the smallest coherent architecture is a
**native Django double-entry ledger** (LedgerAccount + immutable LedgerEntry,
balance derived from entries, idempotency keys, provider adapters) inside the
existing app/DB — which is operationally simple, fully testable, and AWS-native.
Keep the schema **provider- and ledger-agnostic** so we can migrate the ledger
to Blnk/Formance later without changing business logic if volume demands it.
Use **AWS Secrets Manager** for AlexBank/provider credentials (never in Git/DB
plaintext/logs).

---

## PART D — Recommended phased plan (dependency order)

1. **Financial domain models** (native): Product/Price/Package, Order,
   Payment(+Attempt), Invoice(+Item), Refund, Coupon, plus a **double-entry
   Ledger** (LedgerAccount, LedgerEntry) with derived balances + idempotency.
2. **Platform namespace on every transaction** — `platform_code` (C/E/F/K) +
   globally unique reference (e.g. `C-YYYYMMDD-<base32>`).
3. **Payment provider abstraction** — `PaymentProvider` interface + adapters;
   implement one real adapter first (Paymob or Stripe test) to prove the flow;
   **AlexBank adapter scaffolded, credentials via Secrets Manager when supplied.**
4. **Webhook system** — signature verify, idempotency, dedup, persist, retry,
   audit.
5. **Entitlement service** — package → features/limits → usage, enforced at
   gated actions; wire to `SubscriptionPlan`/`CompanySubscription`.
6. **Reconciliation** — internal orders/payments/ledger vs provider records.
7. **Financial admin control center** — real analytics from real data.
8. **Security hardening + full test matrix** (unit/integration/E2E, failure &
   idempotency tests).

---

## PART E — Decisions needed from the product owner before money-moving code

Because this subsystem moves real money with real bank credentials, confirm:

1. **Ledger choice** — proceed with the native Django double-entry ledger
   (recommended), or mandate Formance/Blnk from day one?
2. **First live provider** — Paymob, Fawry, or Stripe? (AlexBank later.)
3. **Wallets** — does the business model actually need user/employer wallets,
   escrow, or payouts, or is it purely package/subscription purchase? (Escrow
   only if Freelancing product needs it — the directive says don't build escrow
   unless required.)
4. **Currencies** — single (EGP) initially, or multi-currency + FX from day one?
5. **Secrets** — confirm AWS Secrets Manager is available/allowed on the current
   AWS account for storing AlexBank credentials.

Answers to these determine the schema and prevent expensive rework. This audit
+ the phased plan is the Phase-0 deliverable; implementation of the money-moving
core should start only after these are confirmed.

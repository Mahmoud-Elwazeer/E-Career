# PROMPT — E-Career Phase 8: Billing / Package Engine (ONLY run when you decide monetization is ready)

**⚠️ DO NOT RUN THIS YET.** This phase was explicitly deferred twice
(Phase 2 item 2.22, and again in `COMPETITIVE_ANALYSIS_JOBRIGHT.md`)
because the core product (real scraped jobs, working matching/
recommendations, working AI backbone) needed to be verified end-to-end
first. That verification is now largely done (see
`audit/LIVE_VERIFICATION_REPORT.md` — 11/11 engines PASS or PARTIAL
PASS) — but the decision to start charging money is a business decision,
not a technical readiness question. **Only hand this prompt to Claude
Code once you have personally decided the platform is ready to bill
real employers for real usage.** If you're not sure, run
`PHASE_6_FINAL_AUDIT_PROMPT.md` and `PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md`
first and re-read their "is this production-ready" verdicts before
deciding.

---

You are a senior full-stack engineer working on E-Career at
`M:\job already web for jobs\E-Career`. Read `AGENTS.md`, `CLAUDE.md`,
`MASTER_IMPLEMENTATION_PLAN.md`, and
`audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT_PROMPT.md`'s eventual audit output
(if it exists — `audit/PHASE_7_ADMIN_GOVERNANCE_AUDIT.md`) first. **Phase
7's audit should have already built the Packages/Entitlements model
(feature-flag-driven, non-payment) — this phase adds ACTUAL PAYMENT
processing on top of that entitlement structure. Do not build a second,
parallel entitlement system here — if Phase 7's entitlement model
doesn't exist yet, stop and build that first (or tell the user to run
Phase 7 first).**

## Scope

1. **Package/Plan model** (if Phase 7 didn't already build this):
   `SubscriptionPlan` (name, price, billing_interval, feature flags
   unlocked, job posting limits, talent pool access tier, AI feature
   access) and `CompanySubscription` (company, plan, status, current
   period start/end, Stripe customer/subscription IDs).
2. **Stripe integration** (or confirm with the user if a different
   payment provider is preferred — do not assume Stripe unhesitatingly):
   - Checkout session creation for plan signup/upgrade/downgrade.
   - Webhook handler for `invoice.paid`, `invoice.payment_failed`,
     `customer.subscription.updated`, `customer.subscription.deleted` —
     each must update `CompanySubscription.status` and, on payment
     failure, apply a grace period before actually revoking access (do
     not instantly cut off a company mid-billing-cycle glitch).
   - Idempotent webhook processing (Stripe can send duplicate events —
     use the event ID to dedupe).
3. **Entitlement enforcement**: every feature-gated action (job posting
   limit, talent pool search, AI-powered candidate ranking, etc.) must
   check the company's active `CompanySubscription` and its plan's
   limits BEFORE performing the action, returning a clear 402/403 with
   an upgrade prompt when the limit is exceeded — not a generic 500.
4. **Admin visibility** (extend the Phase 7 admin control plane, don't
   build a separate billing dashboard): admin must see every company's
   plan, billing status, payment history, and be able to manually
   override/comp a plan (with an `ActivityLog` entry recording who did
   it and why — this is a sensitive, auditable action per Phase 7's
   security requirements).
5. **Frontend**: pricing page, checkout flow, billing settings page
   (current plan, upgrade/downgrade, payment method, invoice history),
   and in-app upgrade prompts when a company hits a plan limit.

## Rules

- Never touch `.env` directly — the user must add `STRIPE_SECRET_KEY`,
  `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` themselves.
- Never log or store raw card data — Stripe Checkout/Elements handles
  that; the backend only ever sees tokens/IDs.
- Test with Stripe's test mode and test webhook signing secret — do not
  process real payments during development.
- Local commits only, do not push — same convention as every prior phase.

## When done

Write `audit/PHASE_8_BILLING_COMPLETION_REPORT.md` with the same rigor as
every prior phase report: what was built, what was tested (including
simulated webhook events), and any human action items (Stripe account
setup, webhook endpoint registration in the Stripe dashboard, API keys).

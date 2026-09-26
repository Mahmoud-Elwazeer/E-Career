# USAM Master Directive — Acceptance Scorecard (Part XLIX)

> Each criterion mapped to the commit that delivered it, or marked GAP with the
> reason. Grounded in real code on `development`. ✅ done · 🟡 partial · ⬜ gap.

## Product separation
| Criterion | Status | Evidence |
|---|---|---|
| Individual landing | ✅ | `/for-individuals` (AudiencePage) — 24e0ec9 |
| Employer landing | ✅ | `/for-businesses` (AudiencePage) — 24e0ec9 |
| Individual registration | ✅ | Login account-type selector — 24e0ec9 |
| Employer registration | ✅ | `/app/employer/register` wizard (existing) + company signup path |
| Individual onboarding | ✅ | OnboardingFlow (existing) |
| Employer onboarding | ✅ | EmployerRegister 2-step (existing) |
| Individual dashboard | ✅ | `/app/dashboard` |
| Employer dashboard | ✅ | `/app/employer/dashboard` (RequireEmployer) |
| Navigation changes by role | ✅ | AuthNavbar individual vs employer arrays |
| Permissions work | ✅ | role-routing + RequireRole + employer RBAC (338a7be) |
| Organization/workspace model | 🟡 | Company + EmployerProfile + EmployerTeamMember exist; no generic "workspace switcher" for multi-role humans |

## Financial system
| Criterion | Status | Evidence |
|---|---|---|
| Payment flow | ✅ | Order→Payment→provider→webhook→ledger→entitlement — 0c7f3cb/1d1379a |
| Transaction IDs | ✅ | `references.py` C-YYYYMMDD-XXXX |
| Platform identifiers | ✅ | platform_code C/E/F/K on every financial row |
| Orders | ✅ | `Order` model + engine |
| Invoices | ✅ | `Invoice`/`InvoiceItem` |
| Subscriptions | 🟡 | `CompanySubscription` lifecycle + `Package.interval`; no recurring-renewal engine (needs decision) |
| Packages | ✅ | `Package` + `seed_packages` (6 live) |
| Entitlements | ✅ | Package→SubscriptionPlan→CompanySubscription grant |
| Payment provider abstraction | ✅ | `providers/base.py` + Stripe adapter |
| AlexBank integration layer ready | ✅ | `alexbank_provider.py` scaffold (raises until creds) |
| Credentials securely managed | ✅ | `secrets.py` (AWS Secrets Manager + env fallback) |
| Webhook processing | ✅ | `WebhookView` signed + deduped + idempotent |
| Idempotency | ✅ | `IdempotencyKey` + unique keys + ledger fast-path |
| Ledger | ✅ | double-entry, derived balances — 0c7f3cb |
| Refunds | 🟡 | `Refund` model + Stripe refund adapter; no admin refund UI/reversal-posting flow yet |
| Reconciliation | ✅ | `analytics.reconcile()` + admin endpoint — c086240 |
| Wallets | ⬜ | Not built — needs business decision (escrow/credit) |
| Financial audit | ✅ | `FinancialAuditLog` |
| Analytics | ✅ | `analytics.financial_overview` real aggregates |
| Admin financial dashboard | ✅ | `/admin/finance` + `/payments/admin/*` — 2c13e4c |
| Financial permissions | ✅ | IsAdminRole on all admin finance endpoints |

## Quality gates
| Criterion | Status |
|---|---|
| No fake production data | ✅ (seed commands = real rows; no mock*/fake* in prod) |
| No frontend-only financial ops | ✅ (all via /api/v1/payments service layer) |
| No duplicated transactions | ✅ (idempotency + unique webhook constraint) |
| No balance mutation hacks | ✅ (balances derived from ledger entries) |
| No exposed credentials | ✅ (secrets manager; never in Git/DB/logs) |
| No broken role routing | ✅ (role-routing + guards) |
| No accidental cross-role access | ✅ (queryset scoping + RBAC; tests: tests_isolation, tests_separation) |
| No silent financial mutations | ✅ (FinancialAuditLog) |
| No untested money-moving op | ✅ (19 payments tests) |

## Verified test coverage
- Backend: 19 payments + 11 separation/isolation + 35 employer/career = passing.
- Frontend: 23 tests + production build green.

## Genuine remaining GAPs (ranked; each needs build or a decision)
1. **Refund admin UI + ledger reversal flow** — model exists, no operator surface. (build, additive)
2. **Manual adjustment dual-approval workflow** (Part XXX). (build, additive)
3. **AI financial workspace** (Part XXXII, read-only NL over real analytics). (build, additive)
4. **Subscription recurring-renewal engine** (Celery beat). (needs decision: auto-renew provider?)
5. **Wallet/escrow** (Part XX). (needs decision: does business require it? — likely only Freelancing)
6. **Employer self-service company-profile edit**. (build, additive)
7. **AlexBank live wiring**. (blocked on real credentials/contract)
8. **CSV done; XLSX/PDF exports**. (build, additive)
9. **Celery beat service** must be running for auto-scrape/renewal (ops).

## Decisions still needed (financially dangerous / scope)
- Wallets/escrow: required or not?
- Recurring subscriptions: auto-renew with provider now, or manual for launch?
- Multi-currency FX: EGP-only launch or EGP+USD live?

Everything in the "build, additive" list I will implement without further prompting.

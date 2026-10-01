# Bank of Alexandria (AlexBank) — Integration Checklist

**Status: adapter infrastructure COMPLETE, live API BLOCKED pending this spec.**

The adapter (`apps/payments/providers/alexbank_provider.py`) already has the
lifecycle states, typed errors, config validation, a health probe, and a
deterministic mock for testing. What it does **not** have — and cannot have
without the bank — is the real request/response contract. Everything below is
what we need **from Bank of Alexandria** (or their acquiring/PSP partner) before
wiring the live path. Nothing here is guessed; each item is a hard dependency.

When each value arrives, store it in **AWS Secrets Manager** under the key named
in the "Secret key" column — never in `.env`, source, or the database.

---

## 1. Merchant onboarding / credentials

| Item | Secret key | Notes |
|---|---|---|
| Merchant ID | `ALEXBANK_MERCHANT_ID` | The acquiring merchant identifier. |
| API key / client credential | `ALEXBANK_API_KEY` | API key, or OAuth client_id+secret (tell us which). |
| API base URL | `ALEXBANK_BASE_URL` | Separate **sandbox** and **production** hostnames. |
| Terminal ID (if scoped per terminal) | `ALEXBANK_TERMINAL_ID` | Optional; some acquirers require it. |
| Webhook/callback signing secret | `ALEXBANK_WEBHOOK_SECRET` | For verifying inbound callbacks. |

Also tell us:
- [ ] Is auth a static API key header, HMAC-signed requests, OAuth2, or mTLS?
- [ ] If HMAC/signing: which fields are signed, hash algorithm, header name.
- [ ] If mTLS: client certificate + CA chain delivery method.
- [ ] IP allow-listing requirements (egress IPs they must whitelist for us).

## 2. Payment initiation (create_payment)

- [ ] Endpoint path + HTTP method for creating a payment/checkout.
- [ ] Request body schema (fields, types, required/optional).
- [ ] How amount is expressed: **minor units** (we use integer minor units) vs
      decimal, and the decimal separator.
- [ ] Supported currencies (we expect **EGP**; confirm others).
- [ ] Our order reference field name (we send a reference like `C-PAY-…`; max
      length they allow — ours is ≤ 40 chars).
- [ ] Flow type: hosted redirect page, iframe, or direct API with our own form.
- [ ] If hosted: the field in the response that carries the redirect URL.
- [ ] Response body schema incl. the bank's payment/transaction identifier
      field (maps to our `provider_reference`).

## 3. 3-D Secure / authentication

- [ ] Is 3-D Secure enforced? Which version (3DS2)?
- [ ] Redirect/return URL parameters they append on completion.
- [ ] How the final status is conveyed after 3DS (callback, return URL query,
      or a separate verify call).

## 4. Status query (verify_payment)

- [ ] Endpoint + method to query a payment's authoritative status.
- [ ] Request params (by bank reference, by our reference, or both).
- [ ] The full set of native status values and what each means, so we can map
      them onto our lifecycle:
      `initiated / pending_3ds / authorized / captured / failed / cancelled / expired / refunded`.
- [ ] Whether auth and capture are separate steps (do we need an explicit
      capture call, or is it auto-capture?).

## 5. Refunds (refund_payment)

- [ ] Endpoint + method for full and **partial** refunds.
- [ ] Request schema; whether refunds are by original bank reference.
- [ ] Refund status values + how long settlement takes.
- [ ] Any cut-off window (e.g. same-day void vs next-day refund).

## 6. Webhooks / callbacks (parse_webhook)

- [ ] Does the bank push asynchronous callbacks? Endpoint they will POST to
      (we expose `POST /api/v1/payments/webhooks/alexbank/`).
- [ ] Callback payload schema + content-type.
- [ ] Signature scheme: header name, algorithm, and exactly which bytes are
      signed (raw body vs canonicalized fields).
- [ ] Retry policy and how to acknowledge (expected HTTP status/body).
- [ ] Idempotency: a stable event id we can dedupe on.

## 7. Reconciliation / settlement

- [ ] Settlement report format (CSV/SFTP/API) and schedule.
- [ ] Fields that let us match a settlement line to our payment reference.
- [ ] Fee structure and how fees appear (so the ledger `fees` account is exact).
- [ ] Currency/rounding rules on settlement.

## 8. Limits & constraints

- [ ] Min/max transaction amount.
- [ ] Reference/description length limits and allowed character set.
- [ ] Rate limits on the API.
- [ ] Sandbox test cards / test credentials for end-to-end verification.

---

## What happens once this is provided

1. Values go into AWS Secrets Manager under the keys above.
2. We implement the four methods in `AlexBankProvider` against the real
   contract, mapping native statuses onto `AlexBankState`.
3. `AlexBankProvider.health()` flips `live_enabled` to `True`.
4. We verify end to end in sandbox using the test credentials from §8, then
   switch `ALEXBANK_BASE_URL` to production.

Until then the live adapter raises `AlexBankNotImplemented` on every money
operation, so **no fabricated payment can reach production** through AlexBank.

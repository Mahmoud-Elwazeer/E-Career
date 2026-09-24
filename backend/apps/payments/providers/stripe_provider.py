"""
Stripe adapter — the first real provider (has a full test mode we can verify
end to end). Uses hosted Checkout so no raw card data touches USAM (PCI-safe).

Credentials come from the secrets helper (STRIPE_SECRET_KEY,
STRIPE_WEBHOOK_SECRET) — never hard-coded. If the `stripe` SDK or key is
absent, operations raise ProviderError (they are never silently faked).
"""
from __future__ import annotations

from .base import PaymentProvider, ProviderResult, ProviderError
from ..secrets import get_secret


class StripeProvider(PaymentProvider):
    name = "stripe"

    def _client(self):
        try:
            import stripe
        except ImportError as e:  # pragma: no cover - env dependent
            raise ProviderError("stripe SDK not installed") from e
        key = get_secret("STRIPE_SECRET_KEY")
        if not key:
            raise ProviderError("STRIPE_SECRET_KEY not configured")
        stripe.api_key = key
        return stripe

    def create_payment(self, *, amount, currency, reference, metadata=None):
        stripe = self._client()
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": f"USAM order {reference}"},
                        "unit_amount": int(amount),
                    },
                    "quantity": 1,
                }],
                metadata={"reference": reference, **(metadata or {})},
                success_url=get_secret("PAYMENTS_SUCCESS_URL", "https://jobs.usamif.com/app/billing?status=success"),
                cancel_url=get_secret("PAYMENTS_CANCEL_URL", "https://jobs.usamif.com/app/billing?status=cancelled"),
                client_reference_id=reference,
            )
            return ProviderResult(ok=True, provider_reference=session.id,
                                  status=session.status or "created",
                                  checkout_url=session.url or "", raw=dict(session))
        except Exception as e:  # provider/network error
            raise ProviderError(str(e)) from e

    def verify_payment(self, provider_reference):
        stripe = self._client()
        try:
            session = stripe.checkout.Session.retrieve(provider_reference)
            paid = session.get("payment_status") == "paid"
            return ProviderResult(ok=paid, provider_reference=provider_reference,
                                  status=session.get("payment_status", ""), raw=dict(session))
        except Exception as e:
            raise ProviderError(str(e)) from e

    def refund_payment(self, *, provider_reference, amount):
        stripe = self._client()
        try:
            # provider_reference here is expected to be a PaymentIntent id.
            refund = stripe.Refund.create(payment_intent=provider_reference, amount=int(amount))
            return ProviderResult(ok=refund.get("status") == "succeeded",
                                  provider_reference=refund.get("id", ""),
                                  status=refund.get("status", ""), raw=dict(refund))
        except Exception as e:
            raise ProviderError(str(e)) from e

    def parse_webhook(self, *, body, headers):
        stripe = self._client()
        secret = get_secret("STRIPE_WEBHOOK_SECRET")
        sig = headers.get("Stripe-Signature") or headers.get("stripe-signature", "")
        if not secret:
            raise ProviderError("STRIPE_WEBHOOK_SECRET not configured")
        try:
            event = stripe.Webhook.construct_event(body, sig, secret)
        except Exception as e:
            raise ProviderError(f"Invalid Stripe signature: {e}") from e
        obj = event["data"]["object"]
        return {
            "event_id": event["id"],
            "event_type": event["type"],
            "provider_reference": obj.get("id", ""),
            "status": obj.get("payment_status") or obj.get("status", ""),
            "signature_valid": True,
            "raw": event,
        }

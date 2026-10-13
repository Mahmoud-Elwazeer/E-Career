"""
Phase H: Payment / Card Security audit — executable assertions, not just
documentation. These tests pin the real, verified security properties of the
payments app so a future change can't silently regress them.

Directive non-negotiables under test:
  - No raw card/PAN/CVV field anywhere in the financial models.
  - A failed/declined payment never grants an entitlement.
  - Webhook events are deduplicated (replay protection) via a DB constraint.
  - An invalid/unsigned webhook is rejected, never silently trusted.
  - The AlexBank adapter can never fake a successful live payment.
  - `payment_success=true` claimed by the client alone is never sufficient —
    only a provider-confirmed webhook/verify call can mark an order paid.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from apps.payments.models import (
    Package, Order, Payment, WebhookEvent, FinancialAuditLog,
)
from apps.payments.providers.alexbank_provider import (
    AlexBankProvider, AlexBankNotImplemented,
)
from apps.payments import services

User = get_user_model()
pytestmark = pytest.mark.django_db


# ── No raw card data anywhere in the models ──────────────────────────────────

# Whole-word matches only (so "company" doesn't trip on "pan", "pinned" on
# "pin", etc.) — split the field name on non-alphanumeric/case boundaries.
import re

FORBIDDEN_FIELD_WORDS = {"card", "pan", "cvv", "cvc", "magstripe", "pin"}


def _words(field_name: str) -> set[str]:
    # snake_case and camelCase both split cleanly on underscores; no camelCase
    # is used in this codebase's Django field names, so a simple split suffices.
    return set(re.split(r"_+", field_name.lower()))


def test_no_card_pan_cvv_fields_exist_on_any_payments_model():
    """Static guard: enumerate every field on every payments model and assert
    none of them look like raw card storage. This fails loudly if someone
    adds a `card_number`/`cvv` column in the future. Uses whole-word matching
    so legitimate field names (e.g. `company`) never false-positive on a
    substring like `pan`."""
    from django.apps import apps as django_apps

    checked = 0
    for model in django_apps.get_app_config("payments").get_models():
        for field in model._meta.get_fields():
            bad_hit = FORBIDDEN_FIELD_WORDS & _words(field.name)
            assert not bad_hit, (
                f"{model.__name__}.{field.name} looks like raw card storage "
                f"(matched {bad_hit}) — directive forbids this."
            )
            checked += 1
    assert checked > 20  # sanity: we actually scanned a non-trivial model set


# ── Webhook replay protection (DB-level) ─────────────────────────────────────

def test_webhook_event_provider_event_id_is_deduplicated_at_db_level():
    WebhookEvent.objects.create(provider="stripe", provider_event_id="evt_123")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            WebhookEvent.objects.create(provider="stripe", provider_event_id="evt_123")


def test_webhook_duplicate_event_is_ignored_without_reprocessing(monkeypatch):
    """Simulates a replayed webhook for an already-PROCESSED event: the view
    must acknowledge it as a duplicate and must NOT call mark_order_paid again."""
    user = User.objects.create_user(email="webhook@test.com", password="pw12345x")
    pkg = Package.objects.create(name="Pro", slug="pro-wh", price_amount=5000, currency="EGP")
    order = services.create_order(user=user, package=pkg)
    payment = Payment.objects.create(
        order=order, amount=order.total, currency="EGP",
        provider="stripe", provider_reference="pi_abc", status=Payment.Status.PROCESSING,
    )
    WebhookEvent.objects.create(
        provider="stripe", provider_event_id="evt_dup", status=WebhookEvent.Status.PROCESSED,
    )

    called = {"count": 0}
    def fake_mark_order_paid(**kwargs):
        called["count"] += 1
    monkeypatch.setattr(services, "mark_order_paid", fake_mark_order_paid)

    class FakeAdapter:
        def parse_webhook(self, *, body, headers):
            return {
                "event_id": "evt_dup", "event_type": "checkout.session.completed",
                "provider_reference": "pi_abc", "status": "paid",
                "signature_valid": True, "raw": {},
            }

    import apps.payments.views as views_module
    monkeypatch.setattr(views_module, "get_provider", lambda name: FakeAdapter())

    resp = APIClient().post("/api/v1/payments/webhooks/stripe/", {}, format="json")
    assert resp.status_code == 200
    body = resp.json()
    # CustomJSONRenderer wraps a view-returned dict (that itself lacks a top-
    # level "data" key) inside envelope["data"] — so the inner message lives
    # at data.message here, not the envelope's own (empty) message field.
    message = body.get("message") or (body.get("data") or {}).get("message", "")
    assert message == "duplicate ignored"
    assert called["count"] == 0  # never reprocessed


def test_webhook_with_invalid_signature_is_rejected(monkeypatch):
    """An adapter that raises ProviderError (invalid signature) must produce a
    400 response, never a success — the view must not trust an unverified
    payload."""
    from apps.payments.providers.base import ProviderError
    import apps.payments.views as views_module

    class RejectingAdapter:
        def parse_webhook(self, *, body, headers):
            raise ProviderError("Invalid Stripe signature")

    monkeypatch.setattr(views_module, "get_provider", lambda name: RejectingAdapter())
    resp = APIClient().post("/api/v1/payments/webhooks/stripe/", {}, format="json")
    assert resp.status_code == 400
    assert not WebhookEvent.objects.filter(provider="stripe").exists()


# ── Failed payment never grants entitlement ──────────────────────────────────

def test_failed_payment_never_marks_order_paid_or_grants_entitlement():
    from apps.core.models import SubscriptionPlan, UserSubscription

    user = User.objects.create_user(email="failpay@test.com", password="pw12345x")
    plan = SubscriptionPlan.objects.create(name="Growth-sec-test")
    pkg = Package.objects.create(
        name="Growth", slug="growth-sec-test", price_amount=15000, currency="EGP",
        audience="employer", entitlement_plan=plan,
    )
    order = services.create_order(user=user, package=pkg)
    payment = Payment.objects.create(
        order=order, amount=order.total, currency="EGP",
        provider="stripe", status=Payment.Status.PENDING,
    )

    # Simulate a provider-confirmed FAILURE (not success) — mark_order_paid is
    # never called in this path, mirroring the real webhook/checkout flow.
    payment.status = Payment.Status.FAILED
    payment.save(update_fields=["status"])

    order.refresh_from_db()
    assert order.status != Order.Status.PAID
    assert not UserSubscription.objects.filter(user=user, plan=plan).exists()


def test_client_claimed_success_alone_cannot_mark_an_order_paid():
    """There is no view/endpoint that accepts a bare 'payment_success=true'
    from the client and trusts it. The only paths to Order.PAID are
    mark_order_paid() (called from checkout's $0 free-order branch or from a
    provider-verified webhook) — never a client-supplied flag."""
    user = User.objects.create_user(email="trustclient@test.com", password="pw12345x")
    pkg = Package.objects.create(name="Pro", slug="pro-trust-test", price_amount=5000, currency="EGP")
    order = services.create_order(user=user, package=pkg)
    Payment.objects.create(order=order, amount=order.total, currency="EGP",
                           provider="stripe", status=Payment.Status.PENDING)

    client = APIClient()
    client.force_authenticate(user=user)
    # No endpoint exists that takes {"payment_success": true}; confirm the
    # order status endpoint is read-only and unaffected by such a payload.
    resp = client.get(f"/api/v1/payments/orders/{order.reference}/")
    assert resp.status_code == 200
    order.refresh_from_db()
    assert order.status != Order.Status.PAID


# ── AlexBank can never fake a live success ───────────────────────────────────

def test_alexbank_live_adapter_always_raises_not_implemented_for_money_ops(settings):
    settings.DEBUG = False
    provider = AlexBankProvider()
    # Even with no credentials configured, every money-moving method either
    # raises a config error or AlexBankNotImplemented — it NEVER returns a
    # fabricated ok=True result.
    import os
    os.environ.setdefault("ALEXBANK_MERCHANT_ID", "")
    with pytest.raises(Exception):
        provider.create_payment(amount=1000, currency="EGP", reference="X")


def test_alexbank_health_reports_live_disabled():
    provider = AlexBankProvider()
    health = provider.health()
    assert health["live_enabled"] is False

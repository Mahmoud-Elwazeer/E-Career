"""
Unit tests for the financial core: references, double-entry ledger, idempotency,
payment state machine, coupon pricing, and the order->paid->entitlement flow.

No live provider calls — a fake provider stands in only inside these fixtures.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.payments.references import Platform, generate_reference
from apps.payments.ledger import (
    post_transaction, Posting, get_or_create_account, UnbalancedTransaction,
)
from apps.payments.models import Package, Coupon, Order, Payment
from apps.payments import services

User = get_user_model()
pytestmark = pytest.mark.django_db


# ── References ────────────────────────────────────────────────────────────────
def test_reference_has_platform_prefix_and_is_unique():
    r1 = generate_reference(Platform.CAREER)
    r2 = generate_reference(Platform.CAREER)
    assert r1.startswith("C-")
    assert r1 != r2
    assert len(r1.split("-")) == 3


def test_reference_rejects_unknown_platform():
    with pytest.raises(ValueError):
        generate_reference("Z")


# ── Ledger: double entry + derived balance ────────────────────────────────────
def test_ledger_balance_is_derived_and_balanced():
    get_or_create_account("cash:test", name="Cash", kind="asset")
    get_or_create_account("revenue:test", name="Rev", kind="revenue")
    txn = post_transaction(
        idempotency_key="t1",
        postings=[
            Posting("cash:test", 5000),
            Posting("revenue:test", -5000),
        ],
        description="sale",
    )
    assert txn.is_balanced()
    from apps.payments.models import LedgerAccount
    assert LedgerAccount.objects.get(code="cash:test").balance() == 5000
    assert LedgerAccount.objects.get(code="revenue:test").balance() == -5000


def test_ledger_rejects_unbalanced():
    get_or_create_account("cash:test2", name="Cash", kind="asset")
    get_or_create_account("revenue:test2", name="Rev", kind="revenue")
    with pytest.raises(UnbalancedTransaction):
        post_transaction(
            idempotency_key="t-bad",
            postings=[Posting("cash:test2", 5000), Posting("revenue:test2", -4000)],
        )


def test_ledger_idempotent_replay_does_not_double_post():
    get_or_create_account("cash:test3", name="Cash", kind="asset")
    get_or_create_account("revenue:test3", name="Rev", kind="revenue")
    p = [Posting("cash:test3", 1000), Posting("revenue:test3", -1000)]
    t1 = post_transaction(idempotency_key="same-key", postings=p)
    t2 = post_transaction(idempotency_key="same-key", postings=p)
    assert t1.id == t2.id
    from apps.payments.models import LedgerAccount
    # Balance reflects a single posting, not two.
    assert LedgerAccount.objects.get(code="cash:test3").balance() == 1000


# ── Payment state machine ─────────────────────────────────────────────────────
def _order(**kw):
    user = User.objects.create_user(email="pay@test.com", password="x")
    pkg = Package.objects.create(name="Pro", slug="pro", price_amount=10000, currency="EGP")
    return Order.objects.create(user=user, package=pkg, subtotal=10000, total=10000, currency="EGP")


def test_payment_valid_and_invalid_transitions():
    order = _order()
    pay = Payment.objects.create(order=order, amount=10000, currency="EGP")
    assert pay.status == "created"
    assert pay.can_transition_to("pending")
    assert not pay.can_transition_to("refunded")  # can't skip to refunded from created
    pay.status = "succeeded"
    assert pay.can_transition_to("refunded")
    assert not pay.can_transition_to("pending")   # no going back


# ── Coupon pricing ────────────────────────────────────────────────────────────
def test_coupon_percent_and_fixed():
    pct = Coupon.objects.create(code="HALF", discount_type="percent", value=50)
    fix = Coupon.objects.create(code="MINUS100", discount_type="fixed", value=100)
    assert pct.discount_for(10000) == 5000
    assert fix.discount_for(10000) == 100
    # discount never exceeds the amount
    assert fix.discount_for(50) == 50


# ── Order -> paid -> entitlement (idempotent) ─────────────────────────────────
def test_mark_order_paid_posts_ledger_and_is_idempotent():
    user = User.objects.create_user(email="buyer@test.com", password="x")
    pkg = Package.objects.create(name="Employer", slug="emp", price_amount=20000,
                                 currency="EGP", audience="employer")
    order = services.create_order(user=user, package=pkg)
    pay = Payment.objects.create(order=order, amount=order.total, currency="EGP",
                                 provider="stripe", status="pending")
    services.mark_order_paid(order=order, payment=pay)
    order.refresh_from_db(); pay.refresh_from_db()
    assert order.status == "paid"
    assert pay.status == "succeeded"
    assert pay.ledger_transaction is not None
    # Revenue account credited by the order total (negative = revenue).
    from apps.payments.models import LedgerAccount
    rev = LedgerAccount.objects.get(code="revenue:c:egp")
    assert rev.balance() == -20000
    # Calling again is a no-op (idempotent) — revenue not doubled.
    services.mark_order_paid(order=order, payment=pay)
    rev.refresh_from_db()
    assert LedgerAccount.objects.get(code="revenue:c:egp").balance() == -20000


def test_create_order_applies_coupon():
    user = User.objects.create_user(email="c@test.com", password="x")
    pkg = Package.objects.create(name="P", slug="p", price_amount=10000, currency="EGP")
    coupon = Coupon.objects.create(code="TEN", discount_type="percent", value=10)
    order = services.create_order(user=user, package=pkg, coupon=coupon)
    assert order.subtotal == 10000
    assert order.discount == 1000
    assert order.total == 9000

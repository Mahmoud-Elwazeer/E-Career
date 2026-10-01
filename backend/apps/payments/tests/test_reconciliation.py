"""Real tests for the refund + reconciliation flows (task #7).

Complements test_financial_core.py (which covers balanced posting, derived
balance, unbalanced rejection, idempotent replay, the payment state machine,
coupons, and order->paid->entitlement). Here we exercise:

  * refund as a REVERSING double entry (never a mutated balance),
  * full-refund status transitions + refund idempotency,
  * net ledger position after sale+refund (zero), and
  * analytics.reconcile() — the matched path and every exception type the code
    actually produces: missing_ledger, amount_mismatch, status_mismatch.

Honest scope note: the reconcile() docstring also lists "orphan_ledger", but
the current implementation does not emit it (no orphan scan exists), so there
is no test asserting it — asserting a non-existent behaviour would be a false
green. The ledger's "immutability" is likewise a design convention (corrections
are reversing transactions), not a DB-enforced guard; the reversal test pins
the real mechanism.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.payments.ledger import post_transaction, Posting, get_or_create_account
from apps.payments.models import (
    Package, Order, Payment, Refund, LedgerAccount, LedgerTransaction,
)
from apps.payments import services, analytics

User = get_user_model()
pytestmark = pytest.mark.django_db


def _paid_order(email, amount=20000):
    """Create and fully pay an order (no live provider), returning (order, payment)."""
    user = User.objects.create_user(email=email, password="x")
    pkg = Package.objects.create(
        name=f"Pkg {email}", slug=f"pkg-{email}", price_amount=amount,
        currency="EGP", audience="employer",
    )
    order = services.create_order(user=user, package=pkg)
    pay = Payment.objects.create(order=order, amount=order.total, currency="EGP",
                                 provider="", status="pending")
    services.mark_order_paid(order=order, payment=pay)
    order.refresh_from_db(); pay.refresh_from_db()
    return order, pay


# ── Refund posts a reversing double entry ────────────────────────────────────
def test_refund_reverses_the_sale_posting():
    order, pay = _paid_order("refrev@test.com", amount=20000)
    rev_code = f"revenue:{order.platform_code.lower()}:egp"
    cash_code = "cash:provider:egp"

    # After the sale: revenue credited (-), cash asset debited-positive (+).
    assert LedgerAccount.objects.get(code=rev_code).balance() == -20000
    assert LedgerAccount.objects.get(code=cash_code).balance() == 20000

    refund = services.refund_payment(payment=pay, reason="customer request")
    assert refund.status == Refund.Status.SUCCEEDED
    assert refund.ledger_transaction is not None

    # The reversal mirrors the sale: revenue back to 0, cash back to 0.
    assert LedgerAccount.objects.get(code=rev_code).balance() == 0
    assert LedgerAccount.objects.get(code=cash_code).balance() == 0


def test_full_refund_flips_payment_and_order_to_refunded():
    order, pay = _paid_order("reffull@test.com", amount=15000)
    services.refund_payment(payment=pay, reason="full")
    pay.refresh_from_db(); order.refresh_from_db()
    assert pay.status == Payment.Status.REFUNDED
    assert order.status == Order.Status.REFUNDED


def test_refund_rejects_non_succeeded_payment():
    user = User.objects.create_user(email="refbad@test.com", password="x")
    pkg = Package.objects.create(name="X", slug="x-refbad", price_amount=1000, currency="EGP")
    order = Order.objects.create(user=user, package=pkg, subtotal=1000, total=1000, currency="EGP")
    pay = Payment.objects.create(order=order, amount=1000, currency="EGP", status="pending")
    with pytest.raises(ValueError):
        services.refund_payment(payment=pay, reason="too early")


def test_refund_rejects_amount_over_payment():
    order, pay = _paid_order("refover@test.com", amount=5000)
    with pytest.raises(ValueError):
        services.refund_payment(payment=pay, amount=9999, reason="too much")


def test_refund_ledger_reversal_is_idempotent():
    order, pay = _paid_order("refidem@test.com", amount=8000)
    rev_code = f"revenue:{order.platform_code.lower()}:egp"
    r1 = services.refund_payment(payment=pay, reason="dupe")
    txn_count_1 = LedgerTransaction.objects.count()
    # The reversal posting is keyed on the refund reference; re-posting the same
    # key must not double-reverse (balance stays at 0, no extra txn).
    post_transaction(
        idempotency_key=f"refund:{r1.reference}",
        platform_code=order.platform_code,
        description="replay",
        postings=[
            Posting(f"revenue:{order.platform_code.lower()}:egp", 8000, "EGP"),
            Posting("cash:provider:egp", -8000, "EGP"),
        ],
    )
    assert LedgerTransaction.objects.count() == txn_count_1
    assert LedgerAccount.objects.get(code=rev_code).balance() == 0


# ── post_transaction: missing account is a hard error ────────────────────────
def test_post_transaction_missing_account_raises():
    get_or_create_account("cash:exists", name="Cash", kind="asset")
    with pytest.raises(LedgerAccount.DoesNotExist):
        post_transaction(
            idempotency_key="missing-acct",
            postings=[Posting("cash:exists", 100), Posting("revenue:ghost", -100)],
        )
    # The atomic block rolled back: no half-written transaction remains.
    assert not LedgerTransaction.objects.filter(idempotency_key="missing-acct").exists()


# ── reconcile(): matched path ────────────────────────────────────────────────
def test_reconcile_clean_books_have_no_exceptions():
    _paid_order("recok@test.com", amount=12000)
    result = analytics.reconcile()
    assert result["exception_count"] == 0
    assert result["matched"] >= 1


def test_reconcile_free_order_counts_as_matched():
    # A zero-total paid order needs no ledger txn and must still reconcile.
    user = User.objects.create_user(email="recfree@test.com", password="x")
    pkg = Package.objects.create(name="Free", slug="free-rec", price_amount=0, currency="EGP")
    order = services.create_order(user=user, package=pkg)
    pay = Payment.objects.create(order=order, amount=0, currency="EGP", status="pending")
    services.mark_order_paid(order=order, payment=pay)
    result = analytics.reconcile()
    assert result["exception_count"] == 0


# ── reconcile(): each real exception type ────────────────────────────────────
def test_reconcile_flags_missing_ledger():
    # Paid order + succeeded payment but the ledger link was lost.
    order, pay = _paid_order("recmiss@test.com", amount=7000)
    pay.ledger_transaction = None
    pay.save(update_fields=["ledger_transaction"])
    result = analytics.reconcile()
    types = {e["type"] for e in result["exceptions"]}
    assert "missing_ledger" in types


def test_reconcile_flags_amount_mismatch_on_unbalanced_ledger():
    order, pay = _paid_order("recamt@test.com", amount=9000)
    # Corrupt the ledger so the transaction no longer balances.
    txn = pay.ledger_transaction
    entry = txn.entries.first()
    # Ledger entries are immutable at the model layer; simulate on-disk
    # corruption via a raw queryset update (bypasses the save() guard) so the
    # reconciler's balance check has something unbalanced to catch.
    from apps.payments.models import LedgerEntry
    LedgerEntry.objects.filter(pk=entry.pk).update(amount=entry.amount + 1)
    result = analytics.reconcile()
    types = {e["type"] for e in result["exceptions"]}
    assert "amount_mismatch" in types


def test_reconcile_flags_status_mismatch_paid_order_without_succeeded_payment():
    order, pay = _paid_order("recstat1@test.com", amount=4000)
    # Order is paid but its only payment is no longer succeeded.
    pay.status = Payment.Status.REFUNDED
    pay.save(update_fields=["status"])
    result = analytics.reconcile()
    types = {e["type"] for e in result["exceptions"]}
    assert "status_mismatch" in types


def test_reconcile_flags_status_mismatch_succeeded_payment_on_unpaid_order():
    order, pay = _paid_order("recstat2@test.com", amount=4000)
    # Succeeded payment but the order drifted to a non-paid status.
    order.status = Order.Status.CREATED
    order.save(update_fields=["status"])
    result = analytics.reconcile()
    msgs = [e for e in result["exceptions"] if e["type"] == "status_mismatch"]
    assert any("payment" in e for e in msgs)


# ============================================================================
# Ledger immutability (enforced, not just documented)
# ============================================================================

def test_ledger_entry_cannot_be_updated():
    from apps.payments.models_ledger import LedgerImmutableError
    get_or_create_account("imm:cash", name="Cash", kind="asset")
    get_or_create_account("imm:rev", name="Rev", kind="revenue")
    txn = post_transaction(
        idempotency_key="imm-1",
        postings=[Posting("imm:cash", 1000), Posting("imm:rev", -1000)],
    )
    entry = txn.entries.first()
    entry.amount = 999
    with pytest.raises(LedgerImmutableError):
        entry.save()


def test_ledger_entry_cannot_be_deleted():
    from apps.payments.models_ledger import LedgerImmutableError
    get_or_create_account("imm2:cash", name="Cash", kind="asset")
    get_or_create_account("imm2:rev", name="Rev", kind="revenue")
    txn = post_transaction(
        idempotency_key="imm-2",
        postings=[Posting("imm2:cash", 1000), Posting("imm2:rev", -1000)],
    )
    entry = txn.entries.first()
    with pytest.raises(LedgerImmutableError):
        entry.delete()


def test_initial_entry_insert_still_works():
    # The guard must not block the FIRST write (post_transaction creates entries).
    get_or_create_account("imm3:cash", name="Cash", kind="asset")
    get_or_create_account("imm3:rev", name="Rev", kind="revenue")
    txn = post_transaction(
        idempotency_key="imm-3",
        postings=[Posting("imm3:cash", 500), Posting("imm3:rev", -500)],
    )
    assert txn.entries.count() == 2


# ============================================================================
# Orphan-ledger reconciliation
# ============================================================================

def test_reconcile_flags_orphan_ledger():
    # A balanced ledger movement with NO linked order/refund/adjustment.
    get_or_create_account("orph:cash", name="Cash", kind="asset")
    get_or_create_account("orph:rev", name="Rev", kind="revenue")
    post_transaction(
        idempotency_key="orphan-1",
        postings=[Posting("orph:cash", 1000), Posting("orph:rev", -1000)],
        description="mystery movement",
    )
    result = analytics.reconcile()
    types = {e["type"] for e in result["exceptions"]}
    assert "orphan_ledger" in types


def test_reconcile_does_not_flag_order_ledger_as_orphan():
    # A normal paid order's ledger txn is linked via Payment -> not an orphan.
    _paid_order("notorphan@test.com", amount=6000)
    result = analytics.reconcile()
    orphans = [e for e in result["exceptions"] if e["type"] == "orphan_ledger"]
    assert orphans == []


def test_reconcile_does_not_flag_approved_adjustment_as_orphan():
    # An approved manual adjustment posts a ledger txn linked via
    # AdjustmentRequest.ledger_transaction -> must NOT be flagged orphan.
    from django.contrib.auth import get_user_model
    User = get_user_model()
    requester = User.objects.create_user(email="adj-req@test.com", password="x")
    approver = User.objects.create_user(email="adj-app@test.com", password="x")
    get_or_create_account("adj:a", name="A", kind="asset")
    get_or_create_account("adj:b", name="B", kind="revenue")
    adj = services.request_adjustment(
        requester=requester, account_code="adj:a", counter_account_code="adj:b",
        amount=1000, currency="EGP", reason="correction",
    )
    services.approve_adjustment(adjustment=adj, approver=approver)
    result = analytics.reconcile()
    orphans = [e for e in result["exceptions"] if e["type"] == "orphan_ledger"]
    assert orphans == []

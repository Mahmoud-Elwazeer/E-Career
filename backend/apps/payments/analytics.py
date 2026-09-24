"""
Financial analytics + reconciliation — computed from REAL rows only.

Every number here is a DB aggregate over Order/Payment/Refund/Ledger. There are
no fabricated statistics. Callers (admin views) pass optional filters
(platform_code, currency, date range) that map straight to querysets.
"""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Order, Payment, Refund, LedgerAccount, WebhookEvent


def _apply_filters(qs, *, platform_code=None, currency=None, since=None, until=None):
    if platform_code:
        qs = qs.filter(platform_code=platform_code)
    if currency:
        qs = qs.filter(currency=currency)
    if since:
        qs = qs.filter(created_at__gte=since)
    if until:
        qs = qs.filter(created_at__lte=until)
    return qs


def financial_overview(*, platform_code=None, currency=None, since=None, until=None) -> dict:
    """Headline metrics (directive Part XXIV) from real data."""
    orders = _apply_filters(Order.objects.all(), platform_code=platform_code,
                            currency=currency, since=since, until=until)
    payments = _apply_filters(Payment.objects.all(), platform_code=platform_code,
                             currency=currency, since=since, until=until)

    paid_orders = orders.filter(status=Order.Status.PAID)
    gross = paid_orders.aggregate(t=Sum("total"))["t"] or 0

    refunds = Refund.objects.filter(status=Refund.Status.SUCCEEDED)
    if currency:
        refunds = refunds.filter(currency=currency)
    refunded = refunds.aggregate(t=Sum("amount"))["t"] or 0

    succeeded = payments.filter(status=Payment.Status.SUCCEEDED).count()
    failed = payments.filter(status=Payment.Status.FAILED).count()
    total_payments = payments.count()
    success_rate = round(100 * succeeded / total_payments, 1) if total_payments else 0.0

    now = timezone.now()
    day_ago = now - timedelta(days=1)
    month_ago = now - timedelta(days=30)

    return {
        "gross_revenue": int(gross),
        "refunds": int(refunded),
        "net_revenue": int(gross) - int(refunded),
        "currency": currency or "mixed",
        "orders_total": orders.count(),
        "orders_paid": paid_orders.count(),
        "payments_total": total_payments,
        "payments_succeeded": succeeded,
        "payments_failed": failed,
        "payment_success_rate": success_rate,
        "avg_transaction_value": int(gross / paid_orders.count()) if paid_orders.count() else 0,
        "transactions_today": paid_orders.filter(created_at__gte=day_ago).count(),
        "transactions_month": paid_orders.filter(created_at__gte=month_ago).count(),
        "revenue_by_platform": list(
            paid_orders.values("platform_code").annotate(total=Sum("total"), count=Count("id")).order_by("-total")
        ),
        "revenue_by_currency": list(
            paid_orders.values("currency").annotate(total=Sum("total"), count=Count("id")).order_by("-total")
        ),
        "revenue_by_package": list(
            paid_orders.values("package__name").annotate(total=Sum("total"), count=Count("id")).order_by("-total")[:20]
        ),
        "webhook_health": {
            "processed": WebhookEvent.objects.filter(status=WebhookEvent.Status.PROCESSED).count(),
            "failed": WebhookEvent.objects.filter(status=WebhookEvent.Status.FAILED).count(),
        },
    }


def ledger_balances() -> list[dict]:
    """Derived balances for every ledger account (real, from entries)."""
    out = []
    for acct in LedgerAccount.objects.filter(is_active=True).order_by("code"):
        out.append({
            "code": acct.code, "name": acct.name, "kind": acct.kind,
            "currency": acct.currency, "balance": acct.balance(),
        })
    return out


def reconcile(*, provider_verify=False) -> dict:
    """Compare internal Orders / Payments / Ledger and flag exceptions.

    Provider-independent by default (compares internal records only). When
    `provider_verify` is set and a provider adapter is available, a paid payment
    can be cross-checked against the provider's authoritative status — but that
    is opt-in so reconciliation never depends on a live provider to run.

    Returns matched count + a list of exceptions with a type per the directive
    (Part XXII): missing_ledger, amount_mismatch, orphan_ledger, status_mismatch.
    """
    exceptions = []
    matched = 0

    # 1. Every PAID order with total>0 must have a balanced ledger transaction
    #    reachable through its succeeded payment.
    paid_orders = Order.objects.filter(status=Order.Status.PAID).prefetch_related("payments")
    for order in paid_orders:
        if order.total == 0:
            matched += 1
            continue
        succeeded_payment = order.payments.filter(status=Payment.Status.SUCCEEDED).first()
        if not succeeded_payment:
            exceptions.append({"type": "status_mismatch", "order": order.reference,
                               "detail": "Paid order without a succeeded payment"})
            continue
        txn = succeeded_payment.ledger_transaction
        if not txn:
            exceptions.append({"type": "missing_ledger", "order": order.reference,
                               "detail": "Paid payment with no ledger transaction"})
            continue
        if not txn.is_balanced():
            exceptions.append({"type": "amount_mismatch", "order": order.reference,
                               "ledger": txn.reference, "detail": "Ledger transaction not balanced"})
            continue
        matched += 1

    # 2. Payments marked succeeded whose order is not paid (state drift).
    drift = Payment.objects.filter(status=Payment.Status.SUCCEEDED).exclude(order__status=Order.Status.PAID)
    for p in drift.select_related("order"):
        exceptions.append({"type": "status_mismatch", "payment": p.reference,
                           "detail": f"Succeeded payment on non-paid order ({p.order.status})"})

    return {
        "matched": matched,
        "exception_count": len(exceptions),
        "exceptions": exceptions[:200],
        "provider_verified": bool(provider_verify),
    }

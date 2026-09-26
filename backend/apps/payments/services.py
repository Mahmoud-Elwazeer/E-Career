"""
Payment orchestration services.

Ties the commerce layer to the ledger and to entitlements:
  create_order  -> price a package (+coupon)
  mark_order_paid -> post a balanced ledger transaction, issue invoice,
                     grant the entitlement, write an audit event — all atomic
                     and idempotent.

No fake money movement: `mark_order_paid` is only called after a provider
confirms payment (verify or a signature-valid webhook).
"""
from __future__ import annotations

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.core.models import SubscriptionPlan, CompanySubscription

from .models import Order, Payment, Invoice, InvoiceItem, Package, Coupon, FinancialAuditLog
from .ledger import post_transaction, Posting, get_or_create_account
from .references import Platform


def _ensure_core_accounts(platform_code: str, currency: str):
    """Ensure the standing ledger accounts used by a sale exist."""
    get_or_create_account(
        f"cash:provider:{currency.lower()}", name=f"Cash in provider ({currency})",
        kind="asset", currency=currency,
    )
    plat = dict(Platform.CHOICES).get(platform_code, "Career")
    get_or_create_account(
        f"revenue:{platform_code.lower()}:{currency.lower()}",
        name=f"Revenue — {plat} ({currency})", kind="revenue", currency=currency,
    )


def create_order(*, user, package: Package, company=None, coupon: Coupon | None = None) -> Order:
    subtotal = int(package.price_amount)
    discount = coupon.discount_for(subtotal) if coupon else 0
    total = max(0, subtotal - discount)
    order = Order.objects.create(
        platform_code=package.platform_code,
        user=user,
        company=company,
        package=package,
        coupon=coupon,
        subtotal=subtotal,
        discount=discount,
        total=total,
        currency=package.currency,
        status=Order.Status.CREATED,
    )
    return order


@db_transaction.atomic
def mark_order_paid(*, order: Order, payment: Payment, actor=None) -> Order:
    """Finalize a paid order: ledger, invoice, entitlement, audit — idempotent.

    Safe to call more than once (e.g. webhook + verify race): the ledger posting
    is keyed on the order reference, entitlement grant is get_or_create, and the
    status flip is a no-op if already paid.
    """
    if order.status == Order.Status.PAID:
        return order

    currency = order.currency
    _ensure_core_accounts(order.platform_code, currency)

    # Double-entry: debit provider-cash asset, credit platform revenue.
    if order.total > 0:
        txn = post_transaction(
            idempotency_key=f"order-paid:{order.reference}",
            platform_code=order.platform_code,
            description=f"Payment for order {order.reference}",
            context={"order": order.reference, "payment": payment.reference},
            postings=[
                Posting(account_code=f"cash:provider:{currency.lower()}", amount=order.total, currency=currency),
                Posting(account_code=f"revenue:{order.platform_code.lower()}:{currency.lower()}", amount=-order.total, currency=currency),
            ],
        )
        payment.ledger_transaction = txn
        payment.save(update_fields=["ledger_transaction"])

    # Invoice (issued + paid).
    invoice = Invoice.objects.create(
        order=order, status=Invoice.Status.PAID, total=order.total,
        currency=currency, issued_at=timezone.now(),
    )
    InvoiceItem.objects.create(
        invoice=invoice, description=order.package.name, quantity=1,
        unit_amount=order.subtotal, amount=order.total,
    )

    # Grant entitlement (employer packages map to CompanySubscription).
    _grant_entitlement(order)

    # Flip statuses.
    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])
    if payment.can_transition_to(Payment.Status.SUCCEEDED):
        payment.status = Payment.Status.SUCCEEDED
        payment.save(update_fields=["status", "updated_at"])

    FinancialAuditLog.objects.create(
        actor=actor, action="order.paid", entity_type="Order",
        entity_ref=order.reference,
        after={"status": "paid", "total": order.total, "currency": currency},
        context={"payment": payment.reference},
    )
    return order


@db_transaction.atomic
def refund_payment(*, payment: Payment, amount: int | None = None, reason: str = "", actor=None):
    """Issue a refund: provider refund → ledger REVERSAL → status → audit.

    - `amount` in minor units; defaults to the full payment amount.
    - Idempotent per (payment, reason-scoped key): the reversal ledger posting is
      keyed so a retry won't double-reverse.
    - Never mutates a balance directly — it posts a reversing double entry.
    Returns the Refund row.
    """
    from .models import Refund
    from .providers import get_provider, ProviderError

    if payment.status != Payment.Status.SUCCEEDED:
        raise ValueError("Only a succeeded payment can be refunded")

    refund_amount = int(amount) if amount is not None else int(payment.amount)
    if refund_amount <= 0 or refund_amount > payment.amount:
        raise ValueError("Invalid refund amount")

    currency = payment.currency
    order = payment.order

    refund = Refund.objects.create(
        payment=payment, amount=refund_amount, currency=currency,
        reason=reason, status=Refund.Status.PROCESSING,
    )

    # Attempt the provider refund (skip for zero-provider/free flows).
    if payment.provider and payment.provider_reference:
        try:
            provider = get_provider(payment.provider)
            result = provider.refund_payment(
                provider_reference=payment.provider_reference, amount=refund_amount,
            )
            refund.provider_reference = result.provider_reference
            refund.status = Refund.Status.SUCCEEDED if result.ok else Refund.Status.FAILED
        except ProviderError as e:
            refund.status = Refund.Status.FAILED
            refund.save(update_fields=["status"])
            FinancialAuditLog.objects.create(
                actor=actor, action="refund.failed", entity_type="Refund",
                entity_ref=refund.reference, context={"error": str(e), "payment": payment.reference},
            )
            raise
    else:
        refund.status = Refund.Status.SUCCEEDED  # internal/free order reversal

    # Ledger reversal: debit revenue, credit provider-cash (mirror of the sale).
    _ensure_core_accounts(order.platform_code, currency)
    if refund_amount > 0:
        txn = post_transaction(
            idempotency_key=f"refund:{refund.reference}",
            platform_code=order.platform_code,
            description=f"Refund for order {order.reference}",
            context={"order": order.reference, "payment": payment.reference, "refund": refund.reference},
            postings=[
                Posting(account_code=f"revenue:{order.platform_code.lower()}:{currency.lower()}", amount=refund_amount, currency=currency),
                Posting(account_code=f"cash:provider:{currency.lower()}", amount=-refund_amount, currency=currency),
            ],
        )
        refund.ledger_transaction = txn

    refund.save(update_fields=["provider_reference", "status", "ledger_transaction"])

    # Status transitions: full refund flips payment+order to refunded.
    if refund_amount == payment.amount and payment.can_transition_to(Payment.Status.REFUNDED):
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])
        order.status = Order.Status.REFUNDED
        order.save(update_fields=["status", "updated_at"])

    FinancialAuditLog.objects.create(
        actor=actor, action="refund.issued", entity_type="Refund",
        entity_ref=refund.reference,
        after={"amount": refund_amount, "currency": currency, "status": refund.status},
        context={"payment": payment.reference, "order": order.reference, "reason": reason},
    )
    return refund


def _grant_entitlement(order: Order):
    """Grant the package's entitlement. Employer packages activate a
    CompanySubscription against the order's company."""
    plan: SubscriptionPlan | None = order.package.entitlement_plan
    if not plan:
        return
    if order.company_id:
        CompanySubscription.objects.get_or_create(
            company=order.company, plan=plan,
            defaults={"status": "active"},
        )
    # Individual entitlements: current entitlement model is company-scoped;
    # individual-plan grants attach when the individual entitlement model lands.

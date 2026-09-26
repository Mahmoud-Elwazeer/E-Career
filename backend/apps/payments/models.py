"""
Financial domain models (directive Parts XI–XIII, XXIX).

Money is stored in integer MINOR units + an ISO-4217 currency. Every
customer-facing financial object carries a platform-namespaced `reference`.
The Ledger (models_ledger) is the balance source of truth; these models are the
business/commerce layer that drives ledger postings.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel
from .references import Platform, generate_reference

# Re-export ledger models so `from apps.payments.models import *` and Django
# app model discovery see them as part of this app.
from .models_ledger import (  # noqa: F401
    LedgerAccount, LedgerTransaction, LedgerEntry, IdempotencyKey,
)


class Currency(models.TextChoices):
    EGP = "EGP", "Egyptian Pound"
    USD = "USD", "US Dollar"


class Package(UUIDModel):
    """A sellable package/plan (what the customer buys).

    Links to the existing entitlement definition (`core.SubscriptionPlan`) so a
    purchase can grant real feature access without duplicating entitlement logic.
    """

    class Audience(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        EMPLOYER = "employer", "Employer"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    audience = models.CharField(max_length=20, choices=Audience.choices,
                                default=Audience.EMPLOYER, db_index=True)
    platform_code = models.CharField(max_length=1, choices=Platform.CHOICES,
                                     default=Platform.CAREER, db_index=True)
    # Price in minor units + currency + optional recurring interval.
    price_amount = models.BigIntegerField(default=0, help_text="Minor units")
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EGP)
    interval = models.CharField(
        max_length=12, default="one_time",
        choices=[("one_time", "One-time"), ("month", "Monthly"), ("year", "Yearly")],
    )
    entitlement_plan = models.ForeignKey(
        "core.SubscriptionPlan", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="packages",
        help_text="Entitlement granted when this package is purchased",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "payments_package"
        ordering = ["audience", "price_amount"]

    def __str__(self):
        return f"{self.name} ({self.price_amount} {self.currency})"


class Coupon(UUIDModel):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percent"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(max_length=40, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.BigIntegerField(help_text="Percent (0-100) or fixed minor units")
    max_redemptions = models.IntegerField(default=0, help_text="0 = unlimited")
    times_redeemed = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments_coupon"

    def __str__(self):
        return self.code

    def discount_for(self, amount: int) -> int:
        """Return the discount (minor units) this coupon applies to `amount`."""
        if self.discount_type == self.DiscountType.PERCENT:
            return max(0, min(amount, amount * int(self.value) // 100))
        return max(0, min(amount, int(self.value)))


class Order(UUIDModel):
    """A customer's intent to purchase a package. Drives payment + entitlement."""

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending payment"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    reference = models.CharField(max_length=40, unique=True, db_index=True)
    platform_code = models.CharField(max_length=1, choices=Platform.CHOICES,
                                     default=Platform.CAREER, db_index=True)
    # Billing is scoped to the org (Company) where applicable, else the user.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name="orders")
    company = models.ForeignKey("jobs.Company", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="orders")
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name="orders")
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="orders")

    subtotal = models.BigIntegerField(default=0)
    discount = models.BigIntegerField(default=0)
    total = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EGP)
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.CREATED, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_order"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference(self.platform_code)
        super().save(*args, **kwargs)


class Payment(UUIDModel):
    """A payment against an order, tracked through a strict state machine."""

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    # Allowed forward transitions (directive Part XLI). Invalid moves rejected.
    TRANSITIONS = {
        "created": {"pending", "processing", "cancelled", "failed"},
        "pending": {"processing", "succeeded", "failed", "cancelled"},
        "processing": {"succeeded", "failed"},
        "succeeded": {"refunded"},
        "failed": set(),
        "cancelled": set(),
        "refunded": set(),
    }

    reference = models.CharField(max_length=40, unique=True, db_index=True)
    platform_code = models.CharField(max_length=1, choices=Platform.CHOICES,
                                     default=Platform.CAREER, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    amount = models.BigIntegerField()
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EGP)
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.CREATED, db_index=True)
    provider = models.CharField(max_length=40, default="", db_index=True)
    provider_reference = models.CharField(max_length=200, blank=True, db_index=True)
    ledger_transaction = models.ForeignKey(
        LedgerTransaction, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="payments",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments_payment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference(self.platform_code)
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.TRANSITIONS.get(self.status, set())


class PaymentAttempt(UUIDModel):
    """An individual provider call for a payment (for retry visibility)."""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="attempts")
    provider = models.CharField(max_length=40)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    http_status = models.IntegerField(null=True, blank=True)
    succeeded = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "payments_payment_attempt"
        ordering = ["-created_at"]


class Invoice(UUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        VOID = "void", "Void"
        REFUNDED = "refunded", "Refunded"

    reference = models.CharField(max_length=40, unique=True, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="invoices")
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.DRAFT, db_index=True)
    total = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EGP)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_invoice"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference(self.order.platform_code)
        super().save(*args, **kwargs)


class InvoiceItem(UUIDModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_amount = models.BigIntegerField(default=0)
    amount = models.BigIntegerField(default=0)

    class Meta:
        db_table = "payments_invoice_item"


class Refund(UUIDModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    reference = models.CharField(max_length=40, unique=True, db_index=True)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount = models.BigIntegerField()
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EGP)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.REQUESTED, db_index=True)
    provider_reference = models.CharField(max_length=200, blank=True)
    ledger_transaction = models.ForeignKey(
        LedgerTransaction, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="refunds",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "payments_refund"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference(self.payment.platform_code)
        super().save(*args, **kwargs)


class WebhookEvent(UUIDModel):
    """Every inbound provider webhook, deduplicated + processed idempotently."""

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        VERIFIED = "verified", "Verified"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"
        IGNORED = "ignored", "Ignored"

    provider = models.CharField(max_length=40, db_index=True)
    provider_event_id = models.CharField(max_length=200, db_index=True)
    event_type = models.CharField(max_length=100, blank=True)
    signature_valid = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.RECEIVED, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=120, blank=True)
    error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments_webhook_event"
        ordering = ["-received_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="uniq_provider_event",
            )
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_event_id}"


class AdjustmentRequest(UUIDModel):
    """A controlled manual financial adjustment (directive Part XXX).

    Admins NEVER edit a balance directly. They REQUEST an adjustment (amount +
    currency + reason + target ledger account); a DIFFERENT admin APPROVES it;
    only then is a balanced ledger correction posted. Requester != approver.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved (posted)"
        REJECTED = "rejected", "Rejected"

    reference = models.CharField(max_length=40, unique=True, db_index=True)
    platform_code = models.CharField(max_length=1, choices=Platform.CHOICES,
                                     default=Platform.CAREER, db_index=True)
    # The ledger account to adjust and its counter-account (both required so the
    # posting stays balanced double-entry).
    account_code = models.CharField(max_length=100)
    counter_account_code = models.CharField(max_length=100)
    amount = models.BigIntegerField(help_text="Signed minor units applied to account_code")
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EGP)
    reason = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.PENDING, db_index=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                     related_name="adjustment_requests")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="adjustment_approvals")
    ledger_transaction = models.ForeignKey(
        LedgerTransaction, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="adjustments",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments_adjustment_request"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference(self.platform_code)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.get_status_display()}"


class FinancialAuditLog(UUIDModel):
    """Immutable audit trail for sensitive financial actions (Part XXIX)."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="financial_audit_events")
    action = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=60, blank=True)
    entity_ref = models.CharField(max_length=120, blank=True, db_index=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    context = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    correlation_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "payments_financial_audit_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.entity_ref}"

from django.contrib import admin

from .models import (
    Package, Coupon, Order, Payment, PaymentAttempt, Invoice, InvoiceItem,
    Refund, WebhookEvent, FinancialAuditLog,
    LedgerAccount, LedgerTransaction, LedgerEntry, IdempotencyKey,
)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "audience", "platform_code", "price_amount", "currency", "interval", "is_active")
    list_filter = ("audience", "platform_code", "currency", "is_active")
    search_fields = ("name", "slug")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "times_redeemed", "active", "expires_at")
    search_fields = ("code",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "platform_code", "user", "company", "package", "total", "currency", "status", "created_at")
    list_filter = ("status", "platform_code", "currency")
    search_fields = ("reference", "user__email")
    readonly_fields = ("reference",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "order", "amount", "currency", "status", "provider", "created_at")
    list_filter = ("status", "provider", "currency", "platform_code")
    search_fields = ("reference", "provider_reference")
    readonly_fields = ("reference",)


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ("payment", "provider", "succeeded", "http_status", "created_at")
    list_filter = ("provider", "succeeded")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("reference", "order", "status", "total", "currency", "issued_at")
    list_filter = ("status", "currency")
    search_fields = ("reference",)


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("reference", "payment", "amount", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("reference", "provider_reference")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "provider_event_id", "event_type", "status", "signature_valid", "received_at")
    list_filter = ("provider", "status", "signature_valid")
    search_fields = ("provider_event_id", "correlation_id")


@admin.register(FinancialAuditLog)
class FinancialAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_ref", "actor", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_ref", "correlation_id")
    readonly_fields = ("action", "entity_type", "entity_ref", "before", "after", "context", "actor", "created_at")


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "currency", "is_active", "balance")
    list_filter = ("kind", "currency", "is_active")
    search_fields = ("code", "name")


@admin.register(LedgerTransaction)
class LedgerTransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "platform_code", "description", "created_at", "is_balanced")
    search_fields = ("reference", "idempotency_key")
    readonly_fields = ("reference", "idempotency_key")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("transaction", "account", "amount", "currency", "created_at")
    list_filter = ("currency",)


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("scope", "key", "result_ref", "created_at")
    list_filter = ("scope",)
    search_fields = ("key", "result_ref")

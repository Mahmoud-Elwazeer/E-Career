"""
Admin Financial Control Center API (directive Parts XXIII–XXVI).

Admin-gated (IsAdminRole). Every response is real data aggregated from the
financial models — no fabricated statistics. Read-only analytics + reconciliation
trigger. Manual money mutation is intentionally NOT exposed here (that requires
the controlled adjustment workflow in Part XXX, built separately).
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.core.permissions import IsAdminRole

from . import analytics
from .models import Payment, Order, WebhookEvent, FinancialAuditLog


def _parse_common(request):
    platform = request.query_params.get("platform") or None
    currency = request.query_params.get("currency") or None
    days = request.query_params.get("days")
    since = None
    if days:
        try:
            since = timezone.now() - timedelta(days=int(days))
        except ValueError:
            since = None
    return platform, currency, since


@api_view(["GET"])
@permission_classes([IsAdminRole])
def financial_overview(request):
    platform, currency, since = _parse_common(request)
    data = analytics.financial_overview(platform_code=platform, currency=currency, since=since)
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([IsAdminRole])
def ledger_balances(request):
    return Response({"success": True, "data": analytics.ledger_balances()})


@api_view(["GET"])
@permission_classes([IsAdminRole])
def reconciliation(request):
    provider_verify = request.query_params.get("provider_verify") == "1"
    return Response({"success": True, "data": analytics.reconcile(provider_verify=provider_verify)})


@api_view(["GET"])
@permission_classes([IsAdminRole])
def transactions(request):
    """Recent payments across the platform, newest first (admin view)."""
    platform, currency, since = _parse_common(request)
    qs = Payment.objects.select_related("order", "order__package").order_by("-created_at")
    if platform:
        qs = qs.filter(platform_code=platform)
    if currency:
        qs = qs.filter(currency=currency)
    if since:
        qs = qs.filter(created_at__gte=since)
    rows = [{
        "reference": p.reference,
        "platform": p.platform_code,
        "order": p.order.reference,
        "package": p.order.package.name,
        "amount": p.amount,
        "currency": p.currency,
        "status": p.status,
        "provider": p.provider,
        "provider_reference": p.provider_reference,
        "created_at": p.created_at,
    } for p in qs[:200]]
    return Response({"success": True, "data": rows})


@api_view(["GET"])
@permission_classes([IsAdminRole])
def export_transactions_csv(request):
    """Stream a CSV of payments for finance/reporting (directive Part XXXIII).

    Admin-gated; respects the same platform/currency/days filters. No card data.
    """
    import csv
    from django.http import StreamingHttpResponse

    platform, currency, since = _parse_common(request)
    qs = Payment.objects.select_related("order", "order__package").order_by("-created_at")
    if platform:
        qs = qs.filter(platform_code=platform)
    if currency:
        qs = qs.filter(currency=currency)
    if since:
        qs = qs.filter(created_at__gte=since)

    class Echo:
        def write(self, value):
            return value

    def rows():
        writer = csv.writer(Echo())
        yield writer.writerow([
            "reference", "platform", "order", "package", "amount_minor",
            "currency", "status", "provider", "provider_reference", "created_at",
        ])
        for p in qs.iterator(chunk_size=500):
            yield writer.writerow([
                p.reference, p.platform_code, p.order.reference, p.order.package.name,
                p.amount, p.currency, p.status, p.provider, p.provider_reference,
                p.created_at.isoformat(),
            ])

    resp = StreamingHttpResponse(rows(), content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="usam-transactions.csv"'
    # Audit the export (directive Part XXIX).
    FinancialAuditLog.objects.create(
        actor=request.user, action="finance.export.transactions",
        entity_type="Payment", entity_ref="csv",
        context={"platform": platform or "all", "currency": currency or "all"},
    )
    return resp


@api_view(["GET"])
@permission_classes([IsAdminRole])
def audit_log(request):
    rows = [{
        "action": a.action, "entity_type": a.entity_type, "entity_ref": a.entity_ref,
        "actor": getattr(a.actor, "email", None), "created_at": a.created_at,
        "after": a.after,
    } for a in FinancialAuditLog.objects.select_related("actor").order_by("-created_at")[:200]]
    return Response({"success": True, "data": rows})

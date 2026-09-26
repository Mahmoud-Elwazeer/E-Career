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


@api_view(["POST"])
@permission_classes([IsAdminRole])
def issue_refund(request):
    """Admin-issued refund (directive Part XX/XXI/XXIX).

    Body: {payment_reference, amount? (minor units, default full), reason?}.
    Runs the provider refund + ledger reversal + status + audit atomically.
    """
    from . import services
    ref = request.data.get("payment_reference")
    amount = request.data.get("amount")
    reason = request.data.get("reason", "")
    payment = Payment.objects.filter(reference=ref).select_related("order").first()
    if not payment:
        return Response({"success": False, "message": "Unknown payment"}, status=404)
    try:
        refund = services.refund_payment(
            payment=payment,
            amount=int(amount) if amount is not None else None,
            reason=reason, actor=request.user,
        )
    except ValueError as e:
        return Response({"success": False, "message": str(e)}, status=400)
    except Exception as e:  # provider failure already audited
        return Response({"success": False, "message": f"Refund failed: {e}"}, status=502)
    return Response({"success": True, "data": {
        "refund": refund.reference, "status": refund.status, "amount": refund.amount,
    }})


@api_view(["GET", "POST"])
@permission_classes([IsAdminRole])
def adjustments(request):
    """List pending/all adjustments, or create a new PENDING adjustment request."""
    from . import services
    from .models import AdjustmentRequest

    if request.method == "POST":
        try:
            adj = services.request_adjustment(
                requester=request.user,
                account_code=request.data.get("account_code"),
                counter_account_code=request.data.get("counter_account_code"),
                amount=request.data.get("amount"),
                currency=request.data.get("currency", "EGP"),
                reason=request.data.get("reason", ""),
                platform_code=request.data.get("platform_code", "C"),
            )
        except (ValueError, TypeError) as e:
            return Response({"success": False, "message": str(e)}, status=400)
        return Response({"success": True, "data": {"reference": adj.reference, "status": adj.status}})

    rows = [{
        "reference": a.reference, "platform": a.platform_code, "amount": a.amount,
        "currency": a.currency, "account": a.account_code, "counter": a.counter_account_code,
        "reason": a.reason, "status": a.status,
        "requested_by": getattr(a.requested_by, "email", None),
        "approved_by": getattr(a.approved_by, "email", None),
        "created_at": a.created_at,
    } for a in AdjustmentRequest.objects.select_related("requested_by", "approved_by").order_by("-created_at")[:200]]
    return Response({"success": True, "data": rows})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def adjustment_decide(request, reference):
    """Approve or reject a pending adjustment. Approver must differ from requester."""
    from . import services
    from .models import AdjustmentRequest
    adj = AdjustmentRequest.objects.filter(reference=reference).first()
    if not adj:
        return Response({"success": False, "message": "Unknown adjustment"}, status=404)
    decision = request.data.get("decision")
    try:
        if decision == "approve":
            services.approve_adjustment(adjustment=adj, approver=request.user)
        elif decision == "reject":
            services.reject_adjustment(adjustment=adj, approver=request.user, note=request.data.get("note", ""))
        else:
            return Response({"success": False, "message": "decision must be approve|reject"}, status=400)
    except ValueError as e:
        return Response({"success": False, "message": str(e)}, status=400)
    adj.refresh_from_db()
    return Response({"success": True, "data": {"reference": adj.reference, "status": adj.status}})


@api_view(["GET", "POST"])
@permission_classes([IsAdminRole])
def subscriptions(request):
    """List company subscriptions, or change a subscription's status.

    Launch model is MANUAL/admin-managed (no auto-charge without a live provider):
    admins activate/suspend/cancel. Body(POST): {uuid, status}.
    """
    from apps.core.models import CompanySubscription
    from .models import FinancialAuditLog

    if request.method == "POST":
        sub = CompanySubscription.objects.filter(uuid=request.data.get("uuid")).first()
        if not sub:
            return Response({"success": False, "message": "Unknown subscription"}, status=404)
        new_status = request.data.get("status")
        valid = {s[0] for s in CompanySubscription.STATUS_CHOICES}
        if new_status not in valid:
            return Response({"success": False, "message": f"status must be one of {sorted(valid)}"}, status=400)
        before = sub.status
        sub.status = new_status
        sub.save(update_fields=["status"])
        FinancialAuditLog.objects.create(
            actor=request.user, action="subscription.status_changed",
            entity_type="CompanySubscription", entity_ref=str(sub.uuid),
            before={"status": before}, after={"status": new_status},
        )
        return Response({"success": True, "data": {"uuid": str(sub.uuid), "status": sub.status}})

    rows = [{
        "uuid": str(s.uuid),
        "company": s.company.name,
        "plan": s.plan.name,
        "status": s.status,
        "started_at": s.started_at,
    } for s in CompanySubscription.objects.select_related("company", "plan").order_by("-started_at")[:200]]
    return Response({"success": True, "data": rows})


def _export_rows(request):
    """Shared query for transaction exports (CSV/XLSX/PDF)."""
    platform, currency, since = _parse_common(request)
    qs = Payment.objects.select_related("order", "order__package").order_by("-created_at")
    if platform:
        qs = qs.filter(platform_code=platform)
    if currency:
        qs = qs.filter(currency=currency)
    if since:
        qs = qs.filter(created_at__gte=since)
    return qs


@api_view(["GET"])
@permission_classes([IsAdminRole])
def export_transactions_xlsx(request):
    """XLSX export of payments (openpyxl, already a dependency)."""
    from openpyxl import Workbook
    from django.http import HttpResponse
    import io

    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"
    ws.append(["reference", "platform", "order", "package", "amount_minor", "currency", "status", "provider", "created_at"])
    for p in _export_rows(request).iterator(chunk_size=500):
        ws.append([p.reference, p.platform_code, p.order.reference, p.order.package.name,
                   p.amount, p.currency, p.status, p.provider, p.created_at.isoformat()])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    FinancialAuditLog.objects.create(
        actor=request.user, action="finance.export.transactions.xlsx",
        entity_type="Payment", entity_ref="xlsx",
    )
    resp = HttpResponse(buf.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = 'attachment; filename="usam-transactions.xlsx"'
    return resp


@api_view(["GET"])
@permission_classes([IsAdminRole])
def export_transactions_pdf(request):
    """PDF export of a revenue summary + recent transactions (xhtml2pdf, a dep)."""
    from django.http import HttpResponse
    import io
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return Response({"success": False, "message": "PDF engine unavailable"}, status=501)

    overview = analytics.financial_overview()
    rows = _export_rows(request)[:100]
    tr_html = "".join(
        f"<tr><td>{p.reference}</td><td>{p.platform_code}</td><td>{p.order.package.name}</td>"
        f"<td>{p.amount/100:.2f} {p.currency}</td><td>{p.status}</td></tr>"
        for p in rows
    )
    html = f"""
    <h2>USAM Financial Report</h2>
    <p>Gross revenue: {overview['gross_revenue']/100:.2f} · Net: {overview['net_revenue']/100:.2f}
       · Success rate: {overview['payment_success_rate']}%</p>
    <table border="1" cellpadding="4" cellspacing="0" width="100%">
      <tr><th>Reference</th><th>Platform</th><th>Package</th><th>Amount</th><th>Status</th></tr>
      {tr_html}
    </table>"""
    buf = io.BytesIO()
    pisa.CreatePDF(html, dest=buf)
    buf.seek(0)
    FinancialAuditLog.objects.create(
        actor=request.user, action="finance.export.transactions.pdf",
        entity_type="Payment", entity_ref="pdf",
    )
    resp = HttpResponse(buf.read(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="usam-financial-report.pdf"'
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

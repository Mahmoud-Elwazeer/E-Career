"""
Payments API (directive Part XXXVIII — frontend never touches financial state
directly; it goes through this service layer).

Endpoints:
  GET  /api/v1/payments/packages/                 list active packages
  POST /api/v1/payments/checkout/                 create order + provider checkout
  GET  /api/v1/payments/orders/<ref>/             order status (owner only)
  GET  /api/v1/payments/transactions/             current user's financial history
  POST /api/v1/payments/webhooks/<provider>/      provider webhook receiver
"""
from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Package, Order, Payment, WebhookEvent
from . import services
from .providers import get_provider, ProviderError
from .serializers import PackageSerializer, OrderSerializer


class PackageListView(generics.ListAPIView):
    serializer_class = PackageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Package.objects.filter(is_active=True)
        audience = self.request.query_params.get("audience")
        if audience:
            qs = qs.filter(audience=audience)
        return qs


class CheckoutView(APIView):
    """Create an order for a package and start a provider checkout session."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        package_slug = request.data.get("package")
        provider_name = (request.data.get("provider") or "stripe").lower()
        pkg = Package.objects.filter(slug=package_slug, is_active=True).first()
        if not pkg:
            return Response({"success": False, "message": "Unknown package"},
                            status=status.HTTP_404_NOT_FOUND)

        # Employer packages bill the user's company where present.
        company = getattr(getattr(request.user, "employer_profile", None), "company", None)
        order = services.create_order(user=request.user, package=pkg, company=company)
        payment = Payment.objects.create(
            order=order, amount=order.total, currency=order.currency,
            provider=provider_name, status=Payment.Status.PENDING,
            platform_code=order.platform_code,
        )
        order.status = Order.Status.PENDING
        order.save(update_fields=["status", "updated_at"])

        # Free orders (total 0) are fulfilled immediately without a provider.
        if order.total == 0:
            services.mark_order_paid(order=order, payment=payment, actor=request.user)
            return Response({"success": True, "data": {"order": order.reference, "checkout_url": ""}})

        try:
            provider = get_provider(provider_name)
            result = provider.create_payment(
                amount=order.total, currency=order.currency, reference=order.reference,
                metadata={"order": order.reference, "user_id": str(request.user.id)},
            )
        except ProviderError as e:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "updated_at"])
            return Response({"success": False, "message": str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)

        payment.provider_reference = result.provider_reference
        payment.status = Payment.Status.PROCESSING
        payment.save(update_fields=["provider_reference", "status", "updated_at"])

        return Response({"success": True, "data": {
            "order": order.reference,
            "checkout_url": result.checkout_url,
            "provider_reference": result.provider_reference,
        }})


class OrderStatusView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"

    def get_queryset(self):
        # Owner-scoped: a user can only read their own orders.
        return Order.objects.filter(user=self.request.user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_view(request):
    """The signed-in user's platform-credit wallet: derived balance + history."""
    from . import wallet
    currency = request.query_params.get("currency", "EGP")
    return Response({"success": True, "data": {
        "currency": currency,
        "balance": wallet.balance(request.user, currency),
        "history": wallet.history(request.user, currency),
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    """The signed-in user's financial history (their orders + payments)."""
    orders = (Order.objects.filter(user=request.user)
              .select_related("package").order_by("-created_at")[:200])
    data = [{
        "reference": o.reference,
        "platform": o.platform_code,
        "description": o.package.name,
        "amount": o.total,
        "currency": o.currency,
        "status": o.status,
        "created_at": o.created_at,
    } for o in orders]
    return Response({"success": True, "data": data})


class WebhookView(APIView):
    """Provider webhook receiver: verify signature, dedup, process idempotently."""
    permission_classes = [AllowAny]

    def post(self, request, provider):
        provider = (provider or "").lower()
        try:
            adapter = get_provider(provider)
            event = adapter.parse_webhook(body=request.body, headers=dict(request.headers))
        except ProviderError as e:
            # Signature invalid or unparseable — record nothing actionable.
            return Response({"success": False, "message": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

        # Dedup on (provider, provider_event_id).
        obj, created = WebhookEvent.objects.get_or_create(
            provider=provider, provider_event_id=event["event_id"],
            defaults={
                "event_type": event.get("event_type", ""),
                "signature_valid": event.get("signature_valid", False),
                "payload": event.get("raw", {}),
                "status": WebhookEvent.Status.VERIFIED,
            },
        )
        if not created and obj.status == WebhookEvent.Status.PROCESSED:
            # Already processed — acknowledge without re-processing.
            return Response({"success": True, "message": "duplicate ignored"})

        # Resolve the payment by provider reference and finalize if paid —
        # but ONLY after the webhook's own reported amount+currency are
        # cross-checked against the Payment row we already created at
        # checkout time. A valid signature only proves the event came from
        # the provider; it does not prove the event is CONFIRMING what we
        # actually expect to be charged for this specific payment. Without
        # this check, a validly-signed webhook referencing the right
        # provider_reference but a different amount/currency (e.g. a stale
        # or mismatched event) could incorrectly mark an order paid.
        try:
            ref = event.get("provider_reference", "")
            payment = Payment.objects.filter(provider_reference=ref).select_related("order").first()
            if payment and event.get("status") in ("paid", "succeeded"):
                mismatch = _webhook_amount_mismatch(event, payment)
                if mismatch:
                    obj.status = WebhookEvent.Status.FAILED
                    obj.error = mismatch
                    obj.save(update_fields=["status", "error"])
                    return Response(
                        {"success": False, "message": "amount/currency mismatch — not processed"},
                        status=status.HTTP_409_CONFLICT,
                    )
                services.mark_order_paid(order=payment.order, payment=payment)
            obj.status = WebhookEvent.Status.PROCESSED
            obj.processed_at = timezone.now()
            obj.save(update_fields=["status", "processed_at"])
        except Exception as e:  # pragma: no cover - defensive
            obj.status = WebhookEvent.Status.FAILED
            obj.error = str(e)
            obj.save(update_fields=["status", "error"])
            return Response({"success": False, "message": "processing error"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"success": True})


def _webhook_amount_mismatch(event: dict, payment: Payment) -> str:
    """Return a non-empty error string if the webhook's reported amount or
    currency disagrees with the stored Payment row; empty string if they
    match or the provider adapter didn't surface amount/currency (older/
    other adapters) — absence is not treated as a mismatch so this stays
    backward-compatible with adapters that don't report these fields."""
    event_amount = event.get("amount")
    event_currency = event.get("currency")
    if event_amount is not None and int(event_amount) != int(payment.amount):
        return f"amount mismatch: webhook={event_amount} payment={payment.amount}"
    if event_currency and event_currency.upper() != (payment.currency or "").upper():
        return f"currency mismatch: webhook={event_currency} payment={payment.currency}"
    return ""

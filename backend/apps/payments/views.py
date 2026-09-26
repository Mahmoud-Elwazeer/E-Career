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

        # Resolve the payment by provider reference and finalize if paid.
        try:
            ref = event.get("provider_reference", "")
            payment = Payment.objects.filter(provider_reference=ref).select_related("order").first()
            if payment and event.get("status") in ("paid", "succeeded"):
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

"""
Public + authenticated Legal/Privacy API.

Endpoints:
  GET  /api/v1/legal/policies/                  list policy documents + live version
  GET  /api/v1/legal/policies/<slug>/            one document's live version
  POST /api/v1/legal/policies/<slug>/accept/     record acceptance (auth required)
  GET  /api/v1/legal/consent-purposes/           list purposes (+ current grant state if auth'd)
  POST /api/v1/legal/consent/                    grant/withdraw one purpose
  GET  /api/v1/legal/marketing-preference/       get/update marketing opt-ins
  GET  /api/v1/legal/cookie-categories/          public: categories for the banner
  POST /api/v1/legal/cookie-consent/             record a cookie consent snapshot (auth optional)
  GET  /api/v1/legal/cookie-consent/me/          latest snapshot for this user/session
  POST /api/v1/legal/privacy-requests/           open a DSR
  GET  /api/v1/legal/privacy-requests/           list the caller's own DSRs
  GET  /api/v1/legal/privacy-requests/<uuid>/    DSR detail (owner only)
  GET  /api/v1/legal/entity/                     public legal-entity facts for Legal Center/footer
  GET  /api/v1/legal/ai-disclosures/             public AI processing register
"""
from __future__ import annotations

from django.db import transaction as db_transaction
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    PolicyDocument, PolicyVersion, ConsentPurpose, CookieCategory, CookieConsent,
    MarketingPreference, PrivacyRequest, LegalEntityConfig, AIProcessingDisclosure,
    ProcessorRecord, DataTransferRecord,
)
from .serializers import (
    PolicyDocumentSerializer, PolicyVersionPublicSerializer, PolicyAcceptanceSerializer,
    ConsentPurposeSerializer, MarketingPreferenceSerializer, CookieCategorySerializer,
    CookieConsentSerializer, PrivacyRequestSerializer, LegalEntityConfigSerializer,
    AIProcessingDisclosureSerializer, ProcessorRecordPublicSerializer,
    DataTransferRecordPublicSerializer,
)
from . import services


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ── Policies ─────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def policy_list(request):
    docs = PolicyDocument.objects.filter(is_active=True)
    data = PolicyDocumentSerializer(docs, many=True).data
    return Response({"success": True, "data": data})


@api_view(["GET"])
@permission_classes([AllowAny])
def policy_detail(request, slug):
    locale = request.query_params.get("locale", "en")
    jurisdiction = request.query_params.get("jurisdiction")
    version = services.get_active_version(slug, locale=locale, jurisdiction=jurisdiction)
    if not version:
        return Response(
            {"success": False, "message": "No active version for this policy yet."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({"success": True, "data": PolicyVersionPublicSerializer(version).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@db_transaction.atomic
def policy_accept(request, slug):
    """Record acceptance of a policy document.

    The frontend never supplies (and this view never trusts) a specific
    policy_version id — it always re-resolves "the currently ACTIVE version"
    fresh, inside this request's own transaction, at the moment of
    submission. This closes the race window the directive calls out
    explicitly: a user who loaded the signup page while v1 was active, then
    submitted after an admin activated v2, gets their acceptance correctly
    bound to v2 (whatever is truly active right now), never to a stale
    version the frontend merely rendered earlier. Backend remains
    authoritative; the frontend checkbox is only a UI gate for the submit
    button, not a source of truth for which version was accepted.
    """
    locale = request.data.get("locale", "en")
    version = services.get_active_version(slug, locale=locale)
    if not version:
        return Response(
            {"success": False, "message": "No active version to accept."},
            status=status.HTTP_404_NOT_FOUND,
        )
    method = request.data.get("method", "settings")
    acceptance = services.record_acceptance(
        user=request.user, policy_version=version, method=method,
        ip_address=_client_ip(request), user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
    return Response(
        {"success": True, "data": PolicyAcceptanceSerializer(acceptance).data},
        status=status.HTTP_201_CREATED,
    )


# ── Consent purposes ──────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def consent_purpose_list(request):
    purposes = ConsentPurpose.objects.filter(is_active=True)
    user = request.user if request.user.is_authenticated else None
    data = ConsentPurposeSerializer(purposes, many=True, context={"user": user}).data
    return Response({"success": True, "data": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def consent_set(request):
    purpose_key = request.data.get("purpose")
    granted = request.data.get("granted")
    if purpose_key is None or not isinstance(granted, bool):
        return Response(
            {"success": False, "message": "purpose (str) and granted (bool) are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        record = services.set_consent(
            user=request.user, purpose_key=purpose_key, granted=granted,
            method=request.data.get("method", "settings"), ip_address=_client_ip(request),
        )
    except ConsentPurpose.DoesNotExist:
        return Response({"success": False, "message": "Unknown consent purpose."}, status=404)
    except ValueError as e:
        return Response({"success": False, "message": str(e)}, status=400)
    from .serializers import ConsentRecordSerializer
    return Response({"success": True, "data": ConsentRecordSerializer(record).data}, status=201)


# ── Marketing preference (separate from transactional NotificationPreference) ─

class MarketingPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pref, _ = MarketingPreference.objects.get_or_create(user=request.user)
        return Response({"success": True, "data": MarketingPreferenceSerializer(pref).data})

    def patch(self, request):
        from django.utils import timezone
        pref, _ = MarketingPreference.objects.get_or_create(user=request.user)
        serializer = MarketingPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if not pref.email_marketing_opt_in and not pref.sms_marketing_opt_in:
            pref.unsubscribed_at = timezone.now()
            pref.save(update_fields=["unsubscribed_at"])
        return Response({"success": True, "data": MarketingPreferenceSerializer(pref).data})


# ── Cookie consent ───────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def cookie_category_list(request):
    cats = CookieCategory.objects.filter(is_active=True)
    return Response({"success": True, "data": CookieCategorySerializer(cats, many=True).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def cookie_consent_record(request):
    """Record a cookie-consent snapshot. Works for both authenticated users
    and anonymous visitors (session_key) — necessary cookies must function,
    and the banner itself must work, before any login."""
    action = request.data.get("action")
    categories = request.data.get("categories") or {}
    valid_actions = {k for k, _ in CookieConsent.Action.choices}
    if action not in valid_actions:
        return Response({"success": False, "message": "Invalid action."}, status=400)

    categories.setdefault("necessary", True)  # necessary is never actually optional

    session_key = request.data.get("session_key", "")
    if not request.session.session_key:
        request.session.save()
    session_key = session_key or request.session.session_key or ""

    policy_version = services.get_active_version("cookies")
    consent = CookieConsent.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key if not request.user.is_authenticated else "",
        policy_version=policy_version,
        action=action, categories=categories, ip_address=_client_ip(request),
    )
    return Response(
        {"success": True, "data": CookieConsentSerializer(consent).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def cookie_consent_me(request):
    if request.user.is_authenticated:
        consent = CookieConsent.objects.filter(user=request.user).order_by("-created_at").first()
    else:
        key = request.session.session_key
        consent = (CookieConsent.objects.filter(session_key=key).order_by("-created_at").first()
                  if key else None)
    if not consent:
        return Response({"success": True, "data": None})
    return Response({"success": True, "data": CookieConsentSerializer(consent).data})


# ── Privacy Center / DSR ──────────────────────────────────────────────────────

class PrivacyRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PrivacyRequestSerializer

    def get_queryset(self):
        return PrivacyRequest.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        request_type = request.data.get("request_type")
        valid_types = {k for k, _ in PrivacyRequest.RequestType.choices}
        if request_type not in valid_types:
            return Response({"success": False, "message": "Invalid request_type."}, status=400)
        req = services.open_privacy_request(
            user=request.user, request_type=request_type,
            details=request.data.get("details", ""),
            jurisdiction=request.data.get("jurisdiction", "OTHER"),
            ip_address=_client_ip(request),
        )
        return Response(
            {"success": True, "data": PrivacyRequestSerializer(req).data},
            status=status.HTTP_201_CREATED,
        )


class PrivacyRequestDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PrivacyRequestSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return PrivacyRequest.objects.filter(user=self.request.user)


# ── Public legal-entity facts + AI disclosure register ──────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def legal_entity_public(request):
    cfg = LegalEntityConfig.load()
    return Response({"success": True, "data": LegalEntityConfigSerializer(cfg).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def ai_disclosure_list(request):
    items = AIProcessingDisclosure.objects.filter(is_active=True)
    return Response({"success": True, "data": AIProcessingDisclosureSerializer(items, many=True).data})


# ── Public processor / transfer registers (continuation pass) ───────────────
# Backs the new /legal/subprocessors and /legal/international-transfers
# pages. These are READ-ONLY, public-safe views of the same
# ProcessorRecord/DataTransferRecord data the Admin Legal Control Plane
# already manages — no new data model, just a public-safe projection of it
# (see ProcessorRecordPublicSerializer/DataTransferRecordPublicSerializer
# for exactly which internal fields are excluded).

@api_view(["GET"])
@permission_classes([AllowAny])
def processor_register_public(request):
    items = ProcessorRecord.objects.filter(is_active=True).order_by("name")
    return Response({"success": True, "data": ProcessorRecordPublicSerializer(items, many=True).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def data_transfer_register_public(request):
    items = DataTransferRecord.objects.all().order_by("destination_country")
    return Response({"success": True, "data": DataTransferRecordPublicSerializer(items, many=True).data})

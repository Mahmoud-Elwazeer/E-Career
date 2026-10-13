"""
Admin Legal Control Plane API — IsAdminRole-gated.

Policy version authoring/activation, cookie category config, retention
matrix, processor/transfer registers, jurisdiction profiles, legal entity
config, DSR queue management, incident reports, legal holds. Every mutating
action here already lands in a model with its own append-only audit trail
(PrivacyRequestEvent, PolicyVersion history, ConsentRecord history) — no
separate audit log needed for this app, mirroring the payments app's
decision to let the ledger/webhook tables double as the audit trail.
"""
from __future__ import annotations

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.core.permissions import IsAdminRole

from .models import (
    PolicyDocument, PolicyVersion, CookieCategory, RetentionPolicy, ProcessorRecord,
    DataTransferRecord, JurisdictionPolicyProfile, LegalEntityConfig,
    AIProcessingDisclosure, IncidentReport, LegalHold, PrivacyRequest,
)
from .serializers import (
    PolicyDocumentSerializer, PolicyVersionAdminSerializer, CookieCategorySerializer,
    RetentionPolicySerializer, ProcessorRecordSerializer, DataTransferRecordSerializer,
    JurisdictionPolicyProfileSerializer, LegalEntityConfigSerializer,
    AIProcessingDisclosureSerializer, IncidentReportSerializer, LegalHoldSerializer,
    PrivacyRequestSerializer,
)
from . import services


# ── Policy documents + versions ──────────────────────────────────────────────

class AdminPolicyDocumentListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = PolicyDocumentSerializer
    queryset = PolicyDocument.objects.all()


class AdminPolicyVersionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = PolicyVersionAdminSerializer

    def get_queryset(self):
        qs = PolicyVersion.objects.select_related("document").order_by("-created_at")
        doc = self.request.query_params.get("document")
        if doc:
            qs = qs.filter(document__slug=doc)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminPolicyVersionDetailView(generics.RetrieveUpdateAPIView):
    """Edits are only permitted while the version is DRAFT — once IN_REVIEW or
    later, content is frozen (directive: never overwrite a published version).
    """
    permission_classes = [IsAdminRole]
    serializer_class = PolicyVersionAdminSerializer
    lookup_field = "uuid"
    queryset = PolicyVersion.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != PolicyVersion.Status.DRAFT:
            return Response(
                {"success": False, "message": "Only a DRAFT version's content may be edited. "
                                               "Create a new version instead."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def policy_version_transition(request, uuid):
    """Move a version through DRAFT -> IN_REVIEW -> APPROVED (plain status
    writes) or APPROVED/SCHEDULED -> ACTIVE (via services.activate_version,
    which also retires the sibling that was previously live)."""
    try:
        version = PolicyVersion.objects.get(uuid=uuid)
    except PolicyVersion.DoesNotExist:
        return Response({"success": False, "message": "Not found."}, status=404)

    new_status = request.data.get("status")
    valid = {s for s, _ in PolicyVersion.Status.choices}
    if new_status not in valid:
        return Response({"success": False, "message": "Invalid status."}, status=400)

    if new_status == PolicyVersion.Status.ACTIVE:
        try:
            version = services.activate_version(version=version, approver=request.user)
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=409)
    else:
        version.status = new_status
        if new_status == PolicyVersion.Status.APPROVED:
            version.approved_by = request.user
        version.save()

    return Response({"success": True, "data": PolicyVersionAdminSerializer(version).data})


# ── Cookie categories ────────────────────────────────────────────────────────

class AdminCookieCategoryListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = CookieCategorySerializer
    queryset = CookieCategory.objects.all()


class AdminCookieCategoryDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = CookieCategorySerializer
    lookup_field = "uuid"
    queryset = CookieCategory.objects.all()


# ── Retention matrix ─────────────────────────────────────────────────────────

class AdminRetentionPolicyListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = RetentionPolicySerializer
    queryset = RetentionPolicy.objects.all()


class AdminRetentionPolicyDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = RetentionPolicySerializer
    lookup_field = "uuid"
    queryset = RetentionPolicy.objects.all()

    def update(self, request, *args, **kwargs):
        from django.utils import timezone
        resp = super().update(request, *args, **kwargs)
        if resp.status_code == 200 and "retention_period_days" in request.data:
            instance = self.get_object()
            instance.reviewed_at = timezone.now()
            instance.save(update_fields=["reviewed_at"])
        return resp


# ── Processor + transfer registers ──────────────────────────────────────────

class AdminProcessorListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = ProcessorRecordSerializer
    queryset = ProcessorRecord.objects.all()


class AdminProcessorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = ProcessorRecordSerializer
    lookup_field = "uuid"
    queryset = ProcessorRecord.objects.all()


class AdminDataTransferListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = DataTransferRecordSerializer
    queryset = DataTransferRecord.objects.all()


class AdminDataTransferDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = DataTransferRecordSerializer
    lookup_field = "uuid"
    queryset = DataTransferRecord.objects.all()


# ── Jurisdiction profiles ────────────────────────────────────────────────────

class AdminJurisdictionProfileListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = JurisdictionPolicyProfileSerializer
    queryset = JurisdictionPolicyProfile.objects.all()


class AdminJurisdictionProfileDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = JurisdictionPolicyProfileSerializer
    lookup_field = "uuid"
    queryset = JurisdictionPolicyProfile.objects.all()


# ── Legal entity config (singleton) ──────────────────────────────────────────

@api_view(["GET", "PATCH"])
@permission_classes([IsAdminRole])
def legal_entity_config(request):
    cfg = LegalEntityConfig.load()
    if request.method == "PATCH":
        serializer = LegalEntityConfigSerializer(cfg, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
    return Response({"success": True, "data": LegalEntityConfigSerializer(cfg).data})


# ── AI processing disclosures ────────────────────────────────────────────────

class AdminAIProcessingDisclosureListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AIProcessingDisclosureSerializer
    queryset = AIProcessingDisclosure.objects.all()


class AdminAIProcessingDisclosureDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AIProcessingDisclosureSerializer
    lookup_field = "uuid"
    queryset = AIProcessingDisclosure.objects.all()


# ── Incidents ─────────────────────────────────────────────────────────────────

class AdminIncidentListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = IncidentReportSerializer
    queryset = IncidentReport.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminIncidentDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = IncidentReportSerializer
    lookup_field = "uuid"
    queryset = IncidentReport.objects.all()


# ── Legal holds ──────────────────────────────────────────────────────────────

class AdminLegalHoldListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = LegalHoldSerializer
    queryset = LegalHold.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def legal_hold_release(request, uuid):
    from django.utils import timezone
    try:
        hold = LegalHold.objects.get(uuid=uuid)
    except LegalHold.DoesNotExist:
        return Response({"success": False, "message": "Not found."}, status=404)
    if hold.released_at is None:
        hold.released_at = timezone.now()
        hold.save(update_fields=["released_at"])
    return Response({"success": True, "data": LegalHoldSerializer(hold).data})


# ── DSR admin queue ───────────────────────────────────────────────────────────

class AdminPrivacyRequestListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = PrivacyRequestSerializer

    def get_queryset(self):
        qs = PrivacyRequest.objects.select_related("user").order_by("-created_at")
        req_status = self.request.query_params.get("status")
        if req_status:
            qs = qs.filter(status=req_status)
        return qs


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_privacy_request_transition(request, uuid):
    try:
        req = PrivacyRequest.objects.get(uuid=uuid)
    except PrivacyRequest.DoesNotExist:
        return Response({"success": False, "message": "Not found."}, status=404)
    new_status = request.data.get("status")
    try:
        req = services.transition_privacy_request(
            request=req, new_status=new_status, actor=request.user,
            note=request.data.get("note", ""),
        )
    except ValueError as e:
        return Response({"success": False, "message": str(e)}, status=400)
    return Response({"success": True, "data": PrivacyRequestSerializer(req).data})

"""Company Claim API (Task #12) — employer-facing endpoints for claiming an
existing (usually scraper-discovered) Company.

Kept in its own module rather than crowding views.py further, since this is
a self-contained feature with its own small serializer set. Delegates all
state transitions to apps.jobs.company_claim.CompanyClaimService so the
EmployerProfile/EmployerTeamMember side effects of approval live in ONE
place regardless of caller (this API or the admin actions in
apps/jobs/admin.py).
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.jobs.models import Company, CompanyClaim
from apps.jobs.company_claim import company_claim_service, email_domain


class CompanyClaimSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_slug = serializers.CharField(source="company.slug", read_only=True)
    claimant_email = serializers.EmailField(source="claimant.email", read_only=True)
    dns_record_name = serializers.SerializerMethodField()

    class Meta:
        model = CompanyClaim
        fields = [
            "id", "uuid", "company", "company_name", "company_slug",
            "claimant_email", "status", "evidence_type",
            "claimant_email_domain", "is_free_mail_domain",
            "dns_challenge_token", "dns_record_name", "dns_verified_at",
            "confidence", "evidence", "document",
            "reviewed_at", "review_note", "created_at",
        ]
        read_only_fields = [
            "id", "uuid", "status", "claimant_email_domain", "is_free_mail_domain",
            "dns_challenge_token", "dns_verified_at", "confidence", "evidence",
            "reviewed_at", "review_note", "created_at",
        ]

    def get_dns_record_name(self, obj):
        """The exact TXT record name the claimant must publish, for the
        dns_txt evidence type. Only meaningful once a token exists."""
        if not obj.dns_challenge_token or not obj.company.domain:
            return None
        from apps.jobs.company_claim import DNS_TXT_PREFIX
        return f"{DNS_TXT_PREFIX}.{obj.company.domain}"


class CompanyClaimCreateSerializer(serializers.Serializer):
    """Input for POST /api/v1/employer/company-claims/ — intentionally a
    plain Serializer (not ModelSerializer) since the evidence_type the
    claimant picks determines which other fields are relevant, and the
    actual evaluation/scoring happens in the view, not here."""
    company_id = serializers.IntegerField()
    evidence_type = serializers.ChoiceField(choices=[
        CompanyClaim.EVIDENCE_CORPORATE_EMAIL,
        CompanyClaim.EVIDENCE_DNS_TXT,
        CompanyClaim.EVIDENCE_DOCUMENT,
    ])  # admin_manual is deliberately excluded - not reachable from this API
    document = serializers.FileField(required=False, allow_null=True)

    def validate_company_id(self, value):
        try:
            return Company.objects.get(id=value, is_active=True).id
        except Company.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive company.")

    def validate(self, attrs):
        if attrs["evidence_type"] == CompanyClaim.EVIDENCE_DOCUMENT and not attrs.get("document"):
            raise serializers.ValidationError({"document": "A document is required for this evidence type."})
        return attrs


class CompanyClaimViewSet(viewsets.ModelViewSet):
    """
    GET  /api/v1/employer/company-claims/          - the caller's own claims
    POST /api/v1/employer/company-claims/          - create a claim
    POST /api/v1/employer/company-claims/{id}/verify-dns/ - re-check a dns_txt claim
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyClaimSerializer
    http_method_names = ["get", "post", "head", "options"]  # no PATCH/DELETE - claims are append-only + admin-reviewed

    def get_queryset(self):
        return CompanyClaim.objects.filter(claimant=self.request.user).select_related("company", "claimant")

    def create(self, request, *args, **kwargs):
        in_ser = CompanyClaimCreateSerializer(data=request.data)
        in_ser.is_valid(raise_exception=True)
        data = in_ser.validated_data
        company = Company.objects.get(id=data["company_id"])

        existing_active = CompanyClaim.objects.filter(
            company=company, claimant=request.user,
            status__in=[CompanyClaim.STATUS_PENDING, CompanyClaim.STATUS_VERIFICATION_REQUIRED, CompanyClaim.STATUS_UNDER_REVIEW],
        ).first()
        if existing_active:
            return Response(
                {"success": False, "error": "You already have an active claim on this company.",
                 "data": CompanyClaimSerializer(existing_active).data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        evidence_type = data["evidence_type"]
        claim = CompanyClaim(
            company=company, claimant=request.user, evidence_type=evidence_type,
        )

        if evidence_type == CompanyClaim.EVIDENCE_CORPORATE_EMAIL:
            domain = email_domain(request.user.email)
            claim.claimant_email_domain = domain
            result = company_claim_service.evaluate_corporate_email(company=company, claimant_email=request.user.email)
            claim.confidence = result.confidence
            claim.evidence = result.evidence
            claim.is_free_mail_domain = result.is_free_mail_domain
            claim.status = result.recommended_status

        elif evidence_type == CompanyClaim.EVIDENCE_DNS_TXT:
            if not company.domain:
                return Response(
                    {"success": False, "error": "This company has no known domain on record - DNS verification is not possible yet. Use document evidence instead, or ask an admin to set the company's domain."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            claim.dns_challenge_token = company_claim_service.generate_dns_token()
            claim.status = CompanyClaim.STATUS_VERIFICATION_REQUIRED
            claim.evidence = {"instructions": "Publish the dns_challenge_token as a TXT record, then call verify-dns."}

        else:  # document
            claim.document = data.get("document")
            claim.status = CompanyClaim.STATUS_VERIFICATION_REQUIRED

        claim.save()
        out = CompanyClaimSerializer(claim)
        return Response({"success": True, "data": out.data, "message": "Claim submitted.", "errors": None},
                         status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="verify-dns")
    def verify_dns(self, request, pk=None):
        claim = self.get_object()
        if claim.evidence_type != CompanyClaim.EVIDENCE_DNS_TXT:
            return Response({"success": False, "error": "This claim is not a dns_txt claim."}, status=status.HTTP_400_BAD_REQUEST)
        if claim.status not in (CompanyClaim.STATUS_PENDING, CompanyClaim.STATUS_VERIFICATION_REQUIRED):
            return Response({"success": False, "error": f"Claim is already {claim.status}; cannot re-verify."},
                             status=status.HTTP_400_BAD_REQUEST)

        result = company_claim_service.check_dns_txt(
            domain=claim.company.domain, expected_token=claim.dns_challenge_token,
        )
        claim.confidence = result.confidence
        claim.evidence = {**claim.evidence, **result.evidence}
        claim.status = result.recommended_status
        if result.evidence.get("token_matched"):
            from django.utils import timezone
            claim.dns_verified_at = timezone.now()
        claim.save(update_fields=["confidence", "evidence", "status", "dns_verified_at", "updated_at"])

        return Response({"success": True, "data": CompanyClaimSerializer(claim).data, "message": "", "errors": None})

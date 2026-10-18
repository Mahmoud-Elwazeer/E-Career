from rest_framework import serializers

from .models import (
    PolicyDocument, PolicyVersion, PolicyAcceptance, ConsentPurpose, ConsentRecord,
    CookieCategory, CookieConsent, MarketingPreference, PrivacyRequest, PrivacyRequestEvent,
    RetentionPolicy, ProcessorRecord, DataTransferRecord, JurisdictionPolicyProfile,
    LegalEntityConfig, AIProcessingDisclosure, IncidentReport, LegalHold,
)


class PolicyVersionPublicSerializer(serializers.ModelSerializer):
    document_slug = serializers.CharField(source="document.slug", read_only=True)
    document_title = serializers.CharField(source="document.title", read_only=True)

    class Meta:
        model = PolicyVersion
        fields = [
            "uuid", "document_slug", "document_title", "version_label", "locale",
            "jurisdiction", "status", "content_markdown", "summary_of_changes",
            "material_change", "is_machine_translated", "effective_at",
        ]


class PolicyVersionAdminSerializer(serializers.ModelSerializer):
    document_slug = serializers.CharField(source="document.slug", read_only=True)

    class Meta:
        model = PolicyVersion
        fields = [
            "uuid", "document", "document_slug", "version_label", "locale", "jurisdiction",
            "status", "content_markdown", "summary_of_changes", "material_change",
            "is_machine_translated", "effective_at", "retired_at", "created_by",
            "approved_by", "created_at",
        ]
        read_only_fields = ["uuid", "document_slug", "effective_at", "retired_at",
                           "created_by", "approved_by", "created_at"]


class PolicyDocumentSerializer(serializers.ModelSerializer):
    live_version = PolicyVersionPublicSerializer(read_only=True)

    class Meta:
        model = PolicyDocument
        fields = ["uuid", "slug", "doc_type", "title", "is_active", "live_version"]


class PolicyAcceptanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyAcceptance
        fields = ["uuid", "policy_version", "method", "accepted_at"]
        read_only_fields = fields


class ConsentPurposeSerializer(serializers.ModelSerializer):
    granted = serializers.SerializerMethodField()

    class Meta:
        model = ConsentPurpose
        fields = ["uuid", "key", "category", "label", "description", "is_required", "granted"]

    def get_granted(self, obj):
        user = self.context.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            return None
        from .services import current_consent_status
        return current_consent_status(user, obj.key)


class ConsentRecordSerializer(serializers.ModelSerializer):
    purpose_key = serializers.CharField(source="purpose.key", read_only=True)

    class Meta:
        model = ConsentRecord
        fields = ["uuid", "purpose_key", "status", "method", "created_at"]
        read_only_fields = fields


class MarketingPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingPreference
        fields = ["email_marketing_opt_in", "sms_marketing_opt_in", "unsubscribed_at", "updated_at"]
        read_only_fields = ["unsubscribed_at", "updated_at"]


class CookieCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CookieCategory
        fields = ["uuid", "key", "label", "description", "is_essential", "is_active"]


class CookieConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CookieConsent
        fields = ["uuid", "action", "categories", "created_at", "carried_over_from_session_key"]
        read_only_fields = ["uuid", "created_at", "carried_over_from_session_key"]


class PrivacyRequestEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyRequestEvent
        fields = ["uuid", "event_type", "note", "created_at"]
        read_only_fields = fields


class PrivacyRequestSerializer(serializers.ModelSerializer):
    events = PrivacyRequestEventSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = PrivacyRequest
        fields = [
            "uuid", "user_email", "request_type", "status", "jurisdiction", "details",
            "resolution_note", "due_at", "created_at", "updated_at", "resolved_at", "events",
        ]
        read_only_fields = ["uuid", "user_email", "status", "due_at", "created_at",
                           "updated_at", "resolved_at", "events", "resolution_note"]


class RetentionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = RetentionPolicy
        fields = [
            "uuid", "data_category", "description", "retention_period_days",
            "legal_basis", "requires_legal_review", "jurisdiction", "reviewed_at",
        ]


class ProcessorRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessorRecord
        fields = [
            "uuid", "name", "purpose", "data_categories", "country",
            "contract_reference", "dpa_signed", "is_active", "notes", "updated_at",
        ]


class DataTransferRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataTransferRecord
        fields = [
            "uuid", "processor", "destination_country", "data_categories", "mechanism",
            "authorization_reference", "notes", "updated_at",
        ]


class JurisdictionPolicyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JurisdictionPolicyProfile
        fields = [
            "uuid", "jurisdiction", "regulator_name", "law_name", "dsr_sla_days",
            "breach_notification_hours", "minor_age_threshold", "requires_legal_review",
            "source_notes", "updated_at",
        ]


class LegalEntityConfigSerializer(serializers.ModelSerializer):
    is_configured = serializers.BooleanField(read_only=True)

    class Meta:
        model = LegalEntityConfig
        fields = [
            "legal_entity_name", "registered_address", "tax_or_registration_id",
            "dpo_name", "dpo_email", "privacy_contact_email", "support_contact_email",
            "default_refund_window_days", "is_configured", "updated_at",
        ]
        read_only_fields = ["is_configured", "updated_at"]


class AIProcessingDisclosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProcessingDisclosure
        fields = [
            "uuid", "feature_key", "feature_label", "description", "data_categories_used",
            "makes_final_decision", "retention_note", "is_active", "updated_at",
        ]

    def validate_makes_final_decision(self, value):
        if value:
            raise serializers.ValidationError(
                "AI features cannot be marked as making the final decision — "
                "per platform policy, AI assists; a human makes the final call."
            )
        return value


class IncidentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = [
            "uuid", "reference", "summary", "severity", "status",
            "affected_data_categories", "affected_user_count", "detected_at",
            "regulator_notified_at", "users_notified_at", "remediation", "created_at",
        ]


class LegalHoldSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = LegalHold
        fields = [
            "uuid", "reference", "scope_description", "reason", "user",
            "created_at", "released_at", "is_active",
        ]

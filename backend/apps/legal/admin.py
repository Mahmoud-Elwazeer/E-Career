from django.contrib import admin

from .models import (
    PolicyDocument, PolicyVersion, PolicyAcceptance, ConsentPurpose, ConsentRecord,
    MarketingPreference, CookieCategory, CookieConsent, PrivacyRequest, PrivacyRequestEvent,
    DataExportJob, DeletionJob, RetentionPolicy, LegalHold, ProcessorRecord,
    DataTransferRecord, JurisdictionPolicyProfile, IncidentReport, AIProcessingDisclosure,
    LegalEntityConfig,
)


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "doc_type", "is_active")
    search_fields = ("title", "slug")


@admin.register(PolicyVersion)
class PolicyVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_label", "locale", "jurisdiction", "status",
                    "material_change", "effective_at")
    list_filter = ("status", "locale", "jurisdiction", "material_change")
    search_fields = ("document__slug", "version_label")
    readonly_fields = ("created_by", "approved_by")


@admin.register(PolicyAcceptance)
class PolicyAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("user", "policy_version", "method", "accepted_at")
    list_filter = ("method",)
    search_fields = ("user__email",)
    readonly_fields = ("user", "policy_version", "method", "accepted_at", "ip_address", "user_agent")


@admin.register(ConsentPurpose)
class ConsentPurposeAdmin(admin.ModelAdmin):
    list_display = ("label", "key", "category", "is_required", "is_active")
    list_filter = ("category", "is_required", "is_active")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "status", "method", "created_at")
    list_filter = ("status", "purpose")
    search_fields = ("user__email",)
    readonly_fields = ("user", "purpose", "status", "method", "ip_address", "created_at")


@admin.register(MarketingPreference)
class MarketingPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_marketing_opt_in", "sms_marketing_opt_in", "unsubscribed_at")
    search_fields = ("user__email",)


@admin.register(CookieCategory)
class CookieCategoryAdmin(admin.ModelAdmin):
    list_display = ("label", "key", "is_essential", "is_active")


@admin.register(CookieConsent)
class CookieConsentAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "action", "created_at")
    list_filter = ("action",)
    readonly_fields = ("user", "session_key", "policy_version", "action", "categories",
                       "ip_address", "created_at")


class PrivacyRequestEventInline(admin.TabularInline):
    model = PrivacyRequestEvent
    extra = 0
    readonly_fields = ("actor", "event_type", "note", "created_at")


@admin.register(PrivacyRequest)
class PrivacyRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "request_type", "status", "jurisdiction", "due_at", "created_at")
    list_filter = ("request_type", "status", "jurisdiction")
    search_fields = ("user__email",)
    inlines = [PrivacyRequestEventInline]


@admin.register(DataExportJob)
class DataExportJobAdmin(admin.ModelAdmin):
    list_display = ("privacy_request", "status", "created_at", "completed_at")
    list_filter = ("status",)


@admin.register(DeletionJob)
class DeletionJobAdmin(admin.ModelAdmin):
    list_display = ("privacy_request", "status", "scheduled_for", "executed_at")
    list_filter = ("status",)


@admin.register(RetentionPolicy)
class RetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ("data_category", "retention_period_days", "requires_legal_review", "jurisdiction")
    list_filter = ("requires_legal_review", "jurisdiction")
    search_fields = ("data_category",)


@admin.register(LegalHold)
class LegalHoldAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "created_at", "released_at")
    search_fields = ("reference",)


@admin.register(ProcessorRecord)
class ProcessorRecordAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "dpa_signed", "is_active")
    search_fields = ("name",)


@admin.register(DataTransferRecord)
class DataTransferRecordAdmin(admin.ModelAdmin):
    list_display = ("destination_country", "mechanism", "processor", "updated_at")
    list_filter = ("mechanism",)


@admin.register(JurisdictionPolicyProfile)
class JurisdictionPolicyProfileAdmin(admin.ModelAdmin):
    list_display = ("jurisdiction", "regulator_name", "dsr_sla_days",
                    "breach_notification_hours", "minor_age_threshold", "requires_legal_review")


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ("reference", "severity", "status", "detected_at", "affected_user_count")
    list_filter = ("severity", "status")
    search_fields = ("reference",)


@admin.register(AIProcessingDisclosure)
class AIProcessingDisclosureAdmin(admin.ModelAdmin):
    list_display = ("feature_label", "feature_key", "makes_final_decision", "is_active")


@admin.register(LegalEntityConfig)
class LegalEntityConfigAdmin(admin.ModelAdmin):
    list_display = ("legal_entity_name", "privacy_contact_email", "default_refund_window_days")

    def has_add_permission(self, request):
        # Singleton — only allow adding if none exists yet.
        return not LegalEntityConfig.objects.exists()

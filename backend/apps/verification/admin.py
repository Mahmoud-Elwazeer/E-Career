from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import VerificationResult


@admin.register(VerificationResult)
class VerificationResultAdmin(ModelAdmin):
    list_display = [
        "job",
        "status",
        "trust_score",
        "ats_platform_detected",
        "domain_trust",
        "url_accessible",
        "is_duplicate",
        "verified_at",
    ]
    list_filter = ["status", "ats_platform_detected", "url_accessible", "is_duplicate"]
    search_fields = ["job__title", "job__company__name", "final_url"]
    readonly_fields = [
        "uuid", "created_at", "updated_at", "verified_at",
        "verification_duration_ms", "redirect_chain", "legitimacy_flags",
        "content_hash",
    ]
    ordering = ["-verified_at"]

    fieldsets = (
        ("Status", {
            "fields": ("job", "status", "trust_score", "notes"),
        }),
        ("Stage 1: ATS Fingerprint", {
            "fields": ("ats_platform_detected", "ats_confidence"),
        }),
        ("Stage 2: Redirect Resolution", {
            "fields": ("final_url", "redirect_chain", "redirect_count"),
        }),
        ("Stage 3: Domain Verification", {
            "fields": ("domain_trust", "domain_matches_company", "ssl_valid"),
        }),
        ("Stage 4: Legitimacy", {
            "fields": ("legitimacy_score", "legitimacy_flags"),
        }),
        ("Stage 5: Freshness", {
            "fields": ("url_accessible", "last_verified_at", "consecutive_failures", "http_status_code"),
        }),
        ("Stage 6: Deduplication", {
            "fields": ("is_duplicate", "duplicate_of", "content_hash"),
        }),
        ("Metadata", {
            "fields": ("uuid", "verified_at", "verification_duration_ms", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

"""
Admin configuration for Jobs app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from import_export.admin import ImportExportModelAdmin

from apps.jobs.models import BusinessContact, Company, CompanyClaim, CompanyEnrichment, CompanyResolutionIdentity, Source, Tag, Job, JobTag


class JobTagInline(TabularInline):
    model = JobTag
    extra = 1
    autocomplete_fields = ["tag"]


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    """
    Enhanced Company admin with unfold styling.
    """
    list_display = ["name", "industry", "is_active", "job_count", "created_at"]
    list_filter = ["industry", "is_active"]
    search_fields = ["name", "slug", "website"]
    ordering = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    
    @display(description="Active Jobs")
    def job_count(self, obj):
        return obj.jobs.filter(status='active').count()


@admin.register(CompanyResolutionIdentity)
class CompanyResolutionIdentityAdmin(ModelAdmin):
    """
    Read-mostly admin for inspecting Company Resolution Service evidence:
    which (ATS platform, tenant slug) pairs resolved to which canonical
    Company, how (identity/domain/slug/created), and with what confidence.
    Useful for auditing before a future Company Claim decision.
    """
    list_display = ["platform", "tenant_slug", "company_link", "matched_by",
                     "confidence", "created_at"]
    list_filter = ["platform", "matched_by"]
    search_fields = ["tenant_slug", "company__name", "company__slug", "domain"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at", "evidence"]
    autocomplete_fields = ["company", "source"]

    @display(description="Company", ordering="company__name")
    def company_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/company/{}/change/">{}</a>',
            obj.company.id, obj.company.name,
        )


@admin.register(CompanyClaim)
class CompanyClaimAdmin(ModelAdmin):
    """
    Admin review queue for Company Claims (Task #12). Mirrors
    EmployerProfileAdmin's approve/reject action pattern (bulk actions +
    ActivityLog audit trail), plus a revoke action for already-approved
    claims. Approval/rejection/revocation always go through
    CompanyClaimService so the EmployerProfile/EmployerTeamMember side
    effects happen consistently - this admin never flips `status` directly
    via a bulk `.update()` the way the simpler EmployerProfile actions do,
    because approval here has real side effects beyond the claim row itself.
    """
    list_display = [
        "claimant_email", "company_link", "status_badge", "evidence_type",
        "confidence", "is_free_mail_domain", "created_at",
    ]
    list_filter = ["status", "evidence_type", "is_free_mail_domain"]
    search_fields = ["claimant__email", "company__name", "company__slug", "claimant_email_domain"]
    ordering = ["-created_at"]
    readonly_fields = [
        "uuid", "created_at", "updated_at", "evidence", "confidence",
        "claimant_email_domain", "is_free_mail_domain", "dns_challenge_token",
        "dns_verified_at", "reviewed_by", "reviewed_at",
    ]
    autocomplete_fields = ["company", "claimant"]
    actions = ["approve_claims", "reject_claims", "revoke_claims"]

    @display(description="Claimant", ordering="claimant__email")
    def claimant_email(self, obj):
        return obj.claimant.email

    @display(description="Company", ordering="company__name")
    def company_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/company/{}/change/">{}</a>',
            obj.company.id, obj.company.name,
        )

    @display(
        description="Status",
        label={
            "pending": "gray",
            "verification_required": "warning",
            "under_review": "blue",
            "approved": "success",
            "rejected": "danger",
            "revoked": "danger",
        },
    )
    def status_badge(self, obj):
        return obj.get_status_display()

    @admin.action(description="Approve selected claims")
    def approve_claims(self, request, queryset):
        from apps.core.models import ActivityLog
        from apps.jobs.company_claim import company_claim_service

        approved, failed = 0, 0
        for claim in queryset.exclude(status=CompanyClaim.STATUS_APPROVED):
            try:
                company_claim_service.approve(claim, reviewed_by=request.user, note="Approved via admin bulk action")
                ActivityLog.objects.create(
                    user=request.user, action="approve_company_claim",
                    target_type="CompanyClaim", target_id=str(claim.pk),
                    metadata={"company": claim.company.name, "claimant": claim.claimant.email},
                )
                approved += 1
            except ValueError as e:
                failed += 1
                self.message_user(request, f"Claim {claim.pk} not approved: {e}", messages.ERROR)
        if approved:
            self.message_user(request, f"{approved} claim(s) approved.", messages.SUCCESS)
        if failed:
            self.message_user(request, f"{failed} claim(s) could not be approved - see errors above.", messages.WARNING)

    @admin.action(description="Reject selected claims")
    def reject_claims(self, request, queryset):
        from apps.core.models import ActivityLog
        from apps.jobs.company_claim import company_claim_service

        count = 0
        for claim in queryset.exclude(status__in=[CompanyClaim.STATUS_APPROVED, CompanyClaim.STATUS_REJECTED]):
            company_claim_service.reject(claim, reviewed_by=request.user, note="Rejected via admin bulk action")
            ActivityLog.objects.create(
                user=request.user, action="reject_company_claim",
                target_type="CompanyClaim", target_id=str(claim.pk),
                metadata={"company": claim.company.name, "claimant": claim.claimant.email},
            )
            count += 1
        self.message_user(request, f"{count} claim(s) rejected.", messages.WARNING)

    @admin.action(description="Revoke selected (approved) claims")
    def revoke_claims(self, request, queryset):
        from apps.core.models import ActivityLog
        from apps.jobs.company_claim import company_claim_service

        count = 0
        for claim in queryset.filter(status=CompanyClaim.STATUS_APPROVED):
            company_claim_service.revoke(claim, reviewed_by=request.user, note="Revoked via admin bulk action")
            ActivityLog.objects.create(
                user=request.user, action="revoke_company_claim",
                target_type="CompanyClaim", target_id=str(claim.pk),
                metadata={"company": claim.company.name, "claimant": claim.claimant.email},
            )
            count += 1
        self.message_user(request, f"{count} claim(s) revoked.", messages.WARNING)


@admin.register(CompanyEnrichment)
class CompanyEnrichmentAdmin(ModelAdmin):
    """
    Read-mostly admin for inspecting Company Discovery Engine evidence
    (Task #13) - every enrichment attempt, applied or not, with its
    confidence and (for conflicts) the existing value it disagreed with.
    Mirrors CompanyResolutionIdentityAdmin's read-mostly, company_link
    pattern.
    """
    list_display = ["company_link", "field_name", "value", "method",
                     "confidence", "applied", "conflict", "created_at"]
    list_filter = ["field_name", "method", "applied", "conflict"]
    search_fields = ["company__name", "company__slug", "value"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at", "evidence"]
    autocomplete_fields = ["company"]

    @display(description="Company", ordering="company__name")
    def company_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/company/{}/change/">{}</a>',
            obj.company.id, obj.company.name,
        )


@admin.register(BusinessContact)
class BusinessContactAdmin(ModelAdmin):
    """
    Admin for Business Contacts (Task #14) - public, role-based addresses
    only. The suppress/unsuppress actions are the operator-facing surface
    for Outreach's (Task #15) compliance gate.
    """
    list_display = ["company_link", "email", "role_prefix", "source",
                     "confidence", "verified", "is_do_not_contact", "created_at"]
    list_filter = ["source", "verified", "is_do_not_contact", "role_prefix"]
    search_fields = ["email", "company__name", "company__slug"]
    ordering = ["company__name", "role_prefix"]
    readonly_fields = ["uuid", "created_at", "updated_at", "evidence"]
    autocomplete_fields = ["company"]
    actions = ["suppress_contacts", "mark_verified"]

    @display(description="Company", ordering="company__name")
    def company_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/company/{}/change/">{}</a>',
            obj.company.id, obj.company.name,
        )

    @admin.action(description="Suppress selected contacts (do-not-contact)")
    def suppress_contacts(self, request, queryset):
        from apps.jobs.business_contact import business_contact_service
        count = 0
        for contact in queryset.exclude(is_do_not_contact=True):
            business_contact_service.suppress(contact, reason="Suppressed via admin bulk action")
            count += 1
        self.message_user(request, f"{count} contact(s) suppressed.", messages.WARNING)

    @admin.action(description="Mark selected contacts as verified")
    def mark_verified(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(verified=False).update(verified=True, verified_at=timezone.now())
        self.message_user(request, f"{count} contact(s) marked verified.", messages.SUCCESS)


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    """
    Enhanced Source admin with unfold styling.
    """
    list_display = [
        "name", "type", "ats_platform", "lifecycle_state", "is_active",
        "job_count", "jobs_found_last_run", "historical_average_jobs",
        "consecutive_zero_yield_runs", "error_count", "created_at",
    ]
    list_filter = ["type", "ats_platform", "lifecycle_state", "is_active",
                   "adaptive_allowed", "terms_review_status", "legal_review_status"]
    search_fields = ["name", "slug", "url", "country", "region"]
    ordering = ["name"]
    readonly_fields = [
        "uuid", "created_at", "updated_at",
        "jobs_found_last_run", "jobs_added_last_run", "last_run_at",
        "last_run_status", "error_count", "last_error",
        "last_success_at", "last_failure_at", "last_nonzero_at",
        "historical_average_jobs", "consecutive_zero_yield_runs",
        "lifecycle_state", "migration_history", "last_discovery_at",
    ]
    prepopulated_fields = {"slug": ("name",)}
    actions = ["enable_sources", "disable_sources"]

    @display(description="Active Jobs")
    def job_count(self, obj):
        return obj.jobs.filter(status='active').count()

    @admin.action(description="Enable selected sources")
    def enable_sources(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} source(s) enabled.")

    @admin.action(description="Disable selected sources")
    def disable_sources(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} source(s) disabled.")


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """
    Enhanced Tag admin with unfold styling.
    """
    list_display = ["name", "category", "job_count", "created_at"]
    list_filter = ["category"]
    search_fields = ["name", "slug"]
    ordering = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    
    @display(description="Jobs")
    def job_count(self, obj):
        return obj.job_tags.count()


@admin.register(Job)
class JobAdmin(ImportExportModelAdmin, ModelAdmin):
    """
    Enhanced Job admin with unfold styling and import/export functionality.
    """
    list_display = [
        "title", "company_link", "location_type_badge", "industry",
        "experience_level", "status_badge", "view_count", "posted_at", "created_at"
    ]
    list_filter = ["status", "location_type", "industry", "experience_level", "posted_at"]
    search_fields = ["title", "slug", "description", "company__name", "location"]
    ordering = ["-posted_at", "-created_at"]
    readonly_fields = ["uuid", "view_count", "click_count", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["company", "source"]
    inlines = [JobTagInline]
    
    fieldsets = (
        ("Job Info", {
            "fields": ("title", "slug", "company", "source", "status")
        }),
        ("Location & Type", {
            "fields": ("location", "location_type", "industry", "experience_level")
        }),
        ("Description", {
            "fields": ("description",)
        }),
        ("Salary", {
            "fields": ("salary_min", "salary_max", "salary_currency"),
            "classes": ("collapse",)
        }),
        ("Source", {
            "fields": ("source_url", "posted_at", "deadline")
        }),
        ("Metrics", {
            "fields": ("view_count", "click_count"),
            "classes": ("collapse",)
        }),
        ("Meta", {
            "fields": ("uuid", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    @display(description="Company", ordering="company__name")
    def company_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/company/{}/change/">{}</a>',
            obj.company.id,
            obj.company.name
        )
    
    @display(
        description="Location",
        label={
            "remote": "success",
            "onsite": "blue",
            "hybrid": "purple",
        }
    )
    def location_type_badge(self, obj):
        return obj.get_location_type_display()
    
    @display(
        description="Status",
        label={
            "active": "success",
            "pending": "warning",
            "archived": "gray",
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()
    
    @admin.action(description="Publish selected jobs")
    def publish_jobs(self, request, queryset):
        count = queryset.update(status="active", quality_state="active")
        self.message_user(request, f"{count} jobs published.")

    @admin.action(description="Archive selected jobs")
    def archive_jobs(self, request, queryset):
        count = queryset.update(status="archived", quality_state="archived")
        self.message_user(request, f"{count} jobs archived.")

    @admin.action(description="Mark as scam")
    def mark_as_scam(self, request, queryset):
        count = queryset.update(status="archived", quality_state="rejected", is_legitimate=False)
        self.message_user(request, f"{count} jobs marked as scam.")
    
    actions = ["publish_jobs", "archive_jobs", "mark_as_scam"]
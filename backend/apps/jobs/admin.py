"""
Admin configuration for Jobs app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from import_export.admin import ImportExportModelAdmin

from apps.jobs.models import Company, CompanyResolutionIdentity, Source, Tag, Job, JobTag


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
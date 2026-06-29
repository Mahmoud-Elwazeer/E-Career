"""
Admin configuration for Jobs app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import display
from unfold.enums import Color
from unfold.contrib.import_export.admin import ImportExportModelAdmin

from apps.jobs.models import Company, Source, Tag, Job, JobTag


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


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    """
    Enhanced Source admin with unfold styling.
    """
    list_display = ["name", "type", "url", "is_active", "job_count", "created_at"]
    list_filter = ["type", "is_active"]
    search_fields = ["name", "slug", "url"]
    ordering = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    
    @display(description="Active Jobs")
    def job_count(self, obj):
        return obj.jobs.filter(status='active').count()


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
class JobAdmin(ModelAdmin):
    """
    Enhanced Job admin with unfold styling.
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
            "remote": Color.GREEN,
            "onsite": Color.BLUE,
            "hybrid": Color.PURPLE,
        }
    )
    def location_type_badge(self, obj):
        return obj.get_location_type_display()
    
    @display(
        description="Status",
        label={
            "active": Color.GREEN,
            "pending": Color.YELLOW,
            "archived": Color.GRAY,
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()
    
    @admin.action(description="Publish selected jobs")
    def publish_jobs(self, request, queryset):
        count = queryset.update(status="active")
        self.message_user(request, f"{count} jobs published.")
    
    @admin.action(description="Archive selected jobs")
    def archive_jobs(self, request, queryset):
        count = queryset.update(status="archived")
        self.message_user(request, f"{count} jobs archived.")
    
    @admin.action(description="Mark as scam")
    def mark_as_scam(self, request, queryset):
        count = queryset.update(status="archived", is_legitimate=False)
        self.message_user(request, f"{count} jobs marked as scam.")
    
    actions = ["publish_jobs", "archive_jobs", "mark_as_scam"]
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin as UnfoldModelAdmin, TabularInline as UnfoldTabularInline
from apps.jobs.models import Company, Source, Tag, Job, JobTag
from apps.jobs.import_export_admin import JobImportExportMixin


class JobTagInline(UnfoldTabularInline):
    model = JobTag
    extra = 1
    autocomplete_fields = ["tag"]


@admin.register(Company)
class CompanyAdmin(UnfoldModelAdmin):
    list_display = ["name", "industry", "is_active", "created_at"]
    list_filter = ["industry", "is_active"]
    search_fields = ["name", "slug", "website"]
    ordering = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(Source)
class SourceAdmin(UnfoldModelAdmin):
    list_display = ["name", "type", "url", "is_active", "created_at"]
    list_filter = ["type", "is_active"]
    search_fields = ["name", "slug", "url"]
    ordering = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(Tag)
class TagAdmin(UnfoldModelAdmin):
    list_display = ["name", "category", "created_at"]
    list_filter = ["category"]
    search_fields = ["name", "slug"]
    ordering = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    compressed_fields = True
    warn_unsaved_form = True

# class JobSourceInline(UnfoldTabularInline):
#     model = Job.also_on_sources.through
#     extra = 1

@admin.register(Job)
class JobAdmin(JobImportExportMixin, UnfoldModelAdmin):
    list_display = [
        "title", "company", "location_type", "industry",
        "experience_level", "status_badge", "posted_at", "created_at"
    ]
    list_filter = ["status", "location_type", "industry", "experience_level", "posted_at"]
    search_fields = ["title", "slug", "description", "company__name", "location"]
    ordering = ["-posted_at", "-created_at"]
    readonly_fields = ["uuid", "view_count", "click_count", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["company", "source"]
    inlines = [JobTagInline]
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        ("Job Info", {
            "fields": ("title", "slug", "company", "status"),
        }),
        ("Location & Type", {
            "fields": ("location", "location_type", "industry", "experience_level"),
        }),
        ("Description", {
            "fields": ("description",),
        }),
        ("Salary", {
            "fields": ("salary_min", "salary_max", "salary_currency"),
        }),
        ("Source", {
            "fields": ("source", "source_url",  "posted_at", "deadline"),
        }),
        ("Metrics", {
            "fields": ("view_count", "click_count"),
        }),
        ("Meta", {
            "fields": ("uuid", "created_at", "updated_at"),
        }),
    )

    def status_badge(self, obj):
        colors = {"active": "green", "pending": "orange", "archived": "gray"}
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color:{};">{}</span>', color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    @admin.action(description="Publish selected jobs")
    def publish_jobs(self, request, queryset):
        updated = queryset.update(status="active")
        self.message_user(request, f"{updated} jobs published.")

    @admin.action(description="Archive selected jobs")
    def archive_jobs(self, request, queryset):
        updated = queryset.update(status="archived")
        self.message_user(request, f"{updated} jobs archived.")

    actions_submit_line = [] 
    actions = ["publish_jobs", "archive_jobs"]

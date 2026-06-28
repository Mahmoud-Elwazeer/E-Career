from django.contrib import admin
from apps.analytics.models import JobView, JobClick, SearchLog


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ["job", "user", "ip_address", "viewed_at"]
    list_filter = ["viewed_at"]
    search_fields = ["job__title", "user__email", "ip_address"]
    ordering = ["-viewed_at"]
    readonly_fields = list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(JobClick)
class JobClickAdmin(admin.ModelAdmin):
    list_display = ["job", "source", "user", "ip_address", "clicked_at"]
    list_filter = ["clicked_at", "source"]
    search_fields = ["job__title", "user__email"]
    ordering = ["-clicked_at"]
    readonly_fields = list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ["query", "user", "results_count", "searched_at"]
    list_filter = ["searched_at"]
    search_fields = ["query", "user__email"]
    ordering = ["-searched_at"]
    readonly_fields = list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
"""
Admin configuration for Analytics app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
try:
    from unfold.enums import Color
except ImportError:
    class Color:
        GREEN = "green"
        GRAY = "gray"
        RED = "red"
        YELLOW = "yellow"
        BLUE = "blue"

from apps.analytics.models import JobView, JobClick, SearchLog


@admin.register(JobView)
class JobViewAdmin(ModelAdmin):
    """
    Enhanced JobView admin with unfold styling.
    Read-only analytics model.
    """
    list_display = ["job", "user", "ip_address", "viewed_at"]
    list_filter = ["viewed_at"]
    search_fields = ["job__title", "user__email", "ip_address"]
    ordering = ["-viewed_at"]
    readonly_fields = ["job", "user", "ip_address", "viewed_at"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(JobClick)
class JobClickAdmin(ModelAdmin):
    """
    Enhanced JobClick admin with unfold styling.
    Read-only analytics model.
    """
    list_display = ["job", "source", "user", "ip_address", "clicked_at"]
    list_filter = ["clicked_at", "source"]
    search_fields = ["job__title", "user__email"]
    ordering = ["-clicked_at"]
    readonly_fields = ["job", "source", "user", "ip_address", "clicked_at"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SearchLog)
class SearchLogAdmin(ModelAdmin):
    """
    Enhanced SearchLog admin with unfold styling.
    Read-only analytics model.
    """
    list_display = ["query", "user", "results_count", "searched_at"]
    list_filter = ["searched_at"]
    search_fields = ["query", "user__email"]
    ordering = ["-searched_at"]
    readonly_fields = ["query", "user", "filters", "results_count", "searched_at"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
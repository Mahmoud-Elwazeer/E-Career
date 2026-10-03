"""Admin configuration for the Scraper app (§8/§10/§29 of the production-scale directive)."""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from apps.scraper.models import ScraperRun


@admin.register(ScraperRun)
class ScraperRunAdmin(ModelAdmin):
    """Read-only run history + Direct-Apply resolution metrics per run.

    Answers the directive's two explicit questions directly in admin:
      "Which source produces the most jobs?"               -> sort by fetched
      "Which source produces the most VERIFIED DIRECT APPLY jobs?"
                                                             -> sort by direct_apply_verified
    """
    list_display = [
        "source_link", "provider", "strategy_tier", "started_at",
        "fetched", "created", "direct_apply_candidates",
        "direct_apply_verified", "resolution_rate_display",
        "indexed", "degraded_badge",
    ]
    list_filter = ["provider", "strategy_tier", "degraded", "zero_yield_anomaly"]
    search_fields = ["source__slug", "source__name"]
    ordering = ["-started_at"]
    readonly_fields = [f.name for f in ScraperRun._meta.fields] + ["resolution_rate_display"]
    autocomplete_fields = ["source"]

    def has_add_permission(self, request):
        # ScraperRun rows are produced only by the real ingestion pipeline
        # (orchestrator._process_jobs via ScraperRun.record) - never
        # hand-created in admin, to keep this an honest run history.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description="Source", ordering="source__name")
    def source_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/source/{}/change/">{}</a>',
            obj.source.id, obj.source.slug,
        )

    @display(description="Direct-Apply Rate")
    def resolution_rate_display(self, obj):
        return f"{obj.direct_apply_resolution_rate:.0%}"

    @display(
        description="Health",
        label={"True": "danger"},
    )
    def degraded_badge(self, obj):
        return "DEGRADED" if obj.degraded else "OK"

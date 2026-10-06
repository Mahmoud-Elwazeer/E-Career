from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from apps.outreach.models import (
    OutreachCampaign, OutreachMessage, OutreachResponse, OutreachSuppression, OutreachTemplate,
)


@admin.register(OutreachTemplate)
class OutreachTemplateAdmin(ModelAdmin):
    list_display = ["name", "subject", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "subject"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(OutreachCampaign)
class OutreachCampaignAdmin(ModelAdmin):
    """Campaign status is editable here, but note the model-level invariant:
    only STATUS_DRY_RUN campaigns ever produce a logged message at all -
    there is no status this admin can set that results in a real send,
    because no real-send code exists in this app."""
    list_display = ["name", "template", "status_badge", "rate_limit_per_day",
                     "message_count", "created_by", "created_at"]
    list_filter = ["status"]
    search_fields = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    autocomplete_fields = ["template", "created_by"]

    @display(
        description="Status",
        label={"draft": "gray", "dry_run": "blue", "paused": "warning", "completed": "success"},
    )
    def status_badge(self, obj):
        return obj.get_status_display()

    @display(description="Messages Logged")
    def message_count(self, obj):
        return obj.messages.count()


@admin.register(OutreachSuppression)
class OutreachSuppressionAdmin(ModelAdmin):
    list_display = ["email", "reason", "created_at"]
    list_filter = ["reason"]
    search_fields = ["email"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(OutreachMessage)
class OutreachMessageAdmin(ModelAdmin):
    """Read-mostly - every row here is an audit record of a dry-run
    evaluation, not an action to take."""
    list_display = ["contact_email", "campaign", "status_badge", "created_at"]
    list_filter = ["status", "campaign"]
    search_fields = ["contact__email", "campaign__name"]
    readonly_fields = ["uuid", "created_at", "updated_at", "rendered_subject", "rendered_body"]
    autocomplete_fields = ["campaign", "contact"]

    @display(description="Contact", ordering="contact__email")
    def contact_email(self, obj):
        return obj.contact.email

    @display(
        description="Status",
        label={"dry_run_logged": "success", "suppressed": "danger", "rate_limited": "warning"},
    )
    def status_badge(self, obj):
        return obj.get_status_display()


@admin.register(OutreachResponse)
class OutreachResponseAdmin(ModelAdmin):
    list_display = ["message", "response_type", "created_at"]
    list_filter = ["response_type"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    autocomplete_fields = ["message"]

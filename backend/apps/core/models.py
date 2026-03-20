import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model providing created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(TimeStampedModel):
    """Abstract base model providing uuid as a public-facing identifier."""

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteModel(UUIDModel):
    """Abstract base model providing soft-delete functionality."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


class FeatureFlag(UUIDModel):
    """Feature flags for toggling functionality on/off."""

    key = models.CharField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "core_featureflag"
        ordering = ["key"]
        verbose_name = "Feature Flag"
        verbose_name_plural = "Feature Flags"

    def __str__(self):
        return f"{self.label} ({'on' if self.is_enabled else 'off'})"


class ActivityLog(models.Model):
    """Admin audit log for tracking user actions."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=200, db_index=True)
    target_type = models.CharField(max_length=100, blank=True, db_index=True)
    target_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "core_activitylog"
        ordering = ["-created_at"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"


def media_upload_path(instance, filename):
    return f"media/{instance.uuid}/{filename}"


class Media(UUIDModel):
    """Uploaded media files (images, etc.)."""

    MIME_TYPE_CHOICES = [
        ("image/jpeg", "JPEG Image"),
        ("image/png", "PNG Image"),
        ("image/gif", "GIF Image"),
        ("image/webp", "WebP Image"),
        ("image/svg+xml", "SVG Image"),
        ("application/pdf", "PDF Document"),
    ]

    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=media_upload_path)
    size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
    )

    class Meta:
        db_table = "core_media"
        ordering = ["-created_at"]
        verbose_name = "Media"
        verbose_name_plural = "Media"

    def __str__(self):
        return self.filename

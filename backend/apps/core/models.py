import uuid
from django.db import models
from django.conf import settings


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


class PlatformConfig(models.Model):
    """
    Single-row global platform configuration.
    All settings editable from admin.
    """
    
    # Scraping configuration
    scrape_interval_hours = models.IntegerField(
        default=6,
        help_text="How often to run full scrape"
    )
    url_verify_interval_h = models.IntegerField(
        default=24,
        help_text="How often to verify apply URLs"
    )
    legitimacy_threshold = models.FloatField(
        default=0.6,
        help_text="Minimum legitimacy score (0.0-1.0)"
    )
    max_job_age_days = models.IntegerField(
        default=90,
        help_text="Auto-expire jobs older than this"
    )
    
    # Recommendation engine
    min_match_score_alert = models.IntegerField(
        default=70,
        help_text="Minimum score to trigger job alert"
    )
    max_alerts_per_day = models.IntegerField(
        default=5,
        help_text="Maximum job alerts per user per day"
    )
    match_weights = models.JSONField(
        default=dict,
        help_text="Scoring weights by dimension"
    )
    
    # Email configuration
    email_rotation_mode = models.CharField(
        max_length=20,
        default='round_robin',
        choices=[
            ('round_robin', 'Round Robin'),
            ('least_used', 'Least Used'),
            ('priority', 'Priority Order'),
        ]
    )
    digest_weekday = models.IntegerField(
        default=1,
        help_text="1=Monday, 7=Sunday"
    )
    digest_hour = models.IntegerField(
        default=9,
        help_text="Hour to send digest (0-23)"
    )
    re_engagement_days = models.IntegerField(
        default=7,
        help_text="Send re-engagement email after X days inactive"
    )
    
    # Platform controls
    require_admin_job_review = models.BooleanField(
        default=False,
        help_text="Require admin approval for employer-posted jobs"
    )
    maintenance_mode = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        related_name='platform_config_updates'
    )
    
    class Meta:
        verbose_name = 'Platform Configuration'
        verbose_name_plural = 'Platform Configuration'
    
    def save(self, *args, **kwargs):
        # Enforce single row
        self.pk = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "Platform Configuration"


class ProxyPool(models.Model):
    """
    Proxy rotation pool for scrapers.
    Used for sources that require proxies (LinkedIn, Indeed).
    """
    host = models.CharField(max_length=200)
    port = models.IntegerField()
    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    fail_count = models.IntegerField(default=0)
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Proxy'
        verbose_name_plural = 'Proxy Pool'
    
    def __str__(self):
        return f"{self.host}:{self.port}"


class PipelineHealth(models.Model):
    """
    Tracks health status of each background task.
    Visible in admin dashboard.
    """
    task_name = models.CharField(max_length=100, unique=True)
    
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(
        max_length=20,
        default='never',
        choices=[
            ('never', 'Never Run'),
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ]
    )
    last_duration = models.FloatField(
        null=True,
        blank=True,
        help_text="Duration in seconds"
    )
    last_error = models.TextField(blank=True)
    
    run_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pipeline Health'
        verbose_name_plural = 'Pipeline Health'
        ordering = ['task_name']
    
    def __str__(self):
        return f"{self.task_name} - {self.last_status}"
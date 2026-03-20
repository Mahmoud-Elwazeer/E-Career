from django.db import models
from apps.core.models import UUIDModel


class SavedJob(models.Model):
    """A job saved/bookmarked by a user."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="saved_jobs",
        db_index=True,
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="saves",
        db_index=True,
    )
    saved_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "users_savedjob"
        ordering = ["-saved_at"]
        unique_together = [("user", "job")]
        verbose_name = "Saved Job"
        verbose_name_plural = "Saved Jobs"

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"


class Alert(UUIDModel):
    """A job alert subscription for a user."""

    FREQUENCY_CHOICES = [
        ("instant", "Instant"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
    ]

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="alerts",
        db_index=True,
    )
    keyword = models.CharField(max_length=200, blank=True)
    work_mode = models.CharField(max_length=20, blank=True)
    industry = models.CharField(max_length=50, blank=True)
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default="daily", db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "users_alert"
        ordering = ["-created_at"]
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def __str__(self):
        parts = []
        if self.keyword:
            parts.append(f'"{self.keyword}"')
        if self.work_mode:
            parts.append(self.work_mode)
        if self.industry:
            parts.append(self.industry)
        label = ", ".join(parts) if parts else "All jobs"
        return f"{self.user.email}: {label} ({self.frequency})"


class Notification(UUIDModel):
    """An in-app notification for a user."""

    NOTIFICATION_TYPE_CHOICES = [
        ("alert_match", "Alert Match"),
        ("system", "System"),
        ("welcome", "Welcome"),
    ]

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        null=True,
        blank=True,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        db_table = "users_notification"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.email}: {self.title}"

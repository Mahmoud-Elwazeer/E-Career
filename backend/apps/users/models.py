from django.db import models
from django.conf import settings
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


class UserProfile(models.Model):
    """
    Extended user profile with CV and career preferences.
    One-to-one with User model.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # CV upload
    cv_file = models.FileField(
        upload_to='cvs/%Y/%m/',
        null=True,
        blank=True
    )
    cv_uploaded_at = models.DateTimeField(null=True, blank=True)
    cv_parsed_at = models.DateTimeField(null=True, blank=True)
    cv_parse_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ]
    )
    portfolio_url = models.URLField(blank=True)
    
    # Parsed data from CV (extracted by Claude/Bedrock)
    skills = models.JSONField(default=list)
    experience_years = models.IntegerField(default=0)
    education = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    current_role = models.CharField(max_length=100, blank=True)
    
    # Job preferences
    desired_roles = models.JSONField(default=list)
    desired_locations = models.JSONField(default=list)
    preferred_type = models.CharField(max_length=20, blank=True)
    open_to_remote = models.BooleanField(default=True)
    min_salary = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='EGP')
    
    # Alert preferences
    email_alerts = models.BooleanField(default=True)
    alert_frequency = models.CharField(
        max_length=10,
        default='instant',
        choices=[
            ('instant', 'Instant'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ]
    )
    min_match_score = models.IntegerField(
        default=70,
        help_text="Only alert for jobs scoring above this threshold"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile: {self.user.email}"


class JobMatchScore(models.Model):
    """
    Calculated match score between a user and a job.
    Recalculated when user updates CV or job is updated.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_matches'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='user_matches'
    )
    
    score = models.IntegerField(help_text="0-100 score")
    breakdown = models.JSONField(
        default=dict,
        help_text="Breakdown by dimension: {title:85, skills:72, ...}"
    )
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'job')
        indexes = [
            models.Index(fields=['user', '-score']),
        ]
        verbose_name = 'Job Match Score'
        verbose_name_plural = 'Job Match Scores'
    
    def __str__(self):
        return f"{self.user.email} → {self.job.title} ({self.score}%)"
import uuid
import random
from django.db import models
from django.conf import settings
from django.utils import timezone


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


# ============================================================================
# Rule Engine (Week 13)
# ============================================================================

class Rule(UUIDModel):
    """
    Configurable rule for automated actions based on conditions.
    
    Rules are evaluated against context data and can trigger actions
    like recommendations, alerts, flags, reminders, or celebrations.
    
    Fields:
        name: Human-readable rule name
        description: Detailed explanation of what the rule does
        category: Classification (job, user, career, notification, etc.)
        conditions: JSONB with condition tree (ALL/ANY/NOT operators)
        action_type: Type of action to execute
        action_params: Parameters for the action
        is_active: Whether the rule is currently active
        priority: Evaluation order (higher = evaluated first)
    """
    
    CATEGORY_CHOICES = [
        ('job', 'Job Quality'),
        ('user', 'User Profile'),
        ('career', 'Career Progression'),
        ('notification', 'Notifications'),
        ('employer', 'Employer Actions'),
        ('celebration', 'Milestones'),
    ]
    
    ACTION_TYPE_CHOICES = [
        ('recommend', 'Recommend'),
        ('alert', 'Alert'),
        ('flag', 'Flag'),
        ('remind', 'Remind'),
        ('celebrate', 'Celebrate'),
        ('recommend_employer', 'Recommend to Employer'),
        ('request_cv_update', 'Request CV Update'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        db_index=True
    )
    
    conditions = models.JSONField(
        default=dict,
        help_text="Condition tree: {operator: 'ALL'|'ANY'|'NOT', conditions: [...], field, operator, value}"
    )
    
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPE_CHOICES,
        db_index=True
    )
    
    action_params = models.JSONField(
        default=dict,
        help_text="Action-specific parameters"
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=0, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "core_rule"
        ordering = ['-priority', 'name']
        verbose_name = "Rule"
        verbose_name_plural = "Rules"
    
    def __str__(self):
        return f"{self.name} ({self.category})"


# ============================================================================
# Enhanced FeatureFlag (Week 13)
# ============================================================================

class FeatureFlag(UUIDModel):
    """Enhanced feature flags with A/B testing and targeting."""
    
    key = models.CharField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    
    # Enhanced fields
    enabled_for_users = models.JSONField(
        default=list,
        help_text="List of user IDs who have this feature enabled"
    )
    enabled_percentage = models.IntegerField(
        default=0,
        help_text="Percentage of users to enable this feature for (0-100)"
    )
    regions = models.JSONField(
        default=list,
        help_text="List of regions where this feature is enabled"
    )
    employer_only = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Feature category for grouping"
    )
    
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = "core_featureflag"
        ordering = ["key"]
        verbose_name = "Feature Flag"
        verbose_name_plural = "Feature Flags"
    
    def __str__(self):
        return f"{self.label} ({'on' if self.is_enabled else 'off'})"
    
    def is_available_for_user(self, user=None):
        """Check if feature is available for a specific user."""
        import random
        
        # Check if expired
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        # Check if enabled
        if not self.is_enabled:
            return False
        
        # Check employer-only flag
        if self.employer_only and (not user or not user.is_employer):
            return False
        
        # Check user-specific override
        if user and user.id and str(user.id) in self.enabled_for_users:
            return True
        
        # Check percentage-based A/B
        if self.enabled_percentage > 0:
            if user and user.id:
                # Deterministic based on user ID
                hash_val = hash(str(user.id) + self.key) % 100
                return hash_val < self.enabled_percentage
            else:
                # Random for anonymous
                return random.random() * 100 < self.enabled_percentage
        
        # Check region
        if self.regions and user and hasattr(user, 'profile') and user.profile:
            user_region = user.profile.country or user.profile.city
            if user_region and user_region not in self.regions:
                return False
        
        return True


# ============================================================================
# GitHub Integration (Week 13)
# ============================================================================

class GitHubConnection(UUIDModel):
    """
    GitHub OAuth connection for a user.
    
    Stores GitHub OAuth tokens and connection metadata.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='github_connections',
        db_index=True
    )
    
    # GitHub connection details
    github_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100)
    access_token = models.TextField()  # Encrypted in production
    refresh_token = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Connection metadata
    avatar_url = models.URLField(blank=True)
    profile_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Last sync
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ]
    )
    last_sync_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "core_github_connection"
        verbose_name = "GitHub Connection"
        verbose_name_plural = "GitHub Connections"
    
    def __str__(self):
        return f"{self.username} ({self.user.email})"


class PortfolioAnalysis(UUIDModel):
    """
    Analysis of a user's portfolio URL.
    
    Stores AI-analyzed portfolio data including technologies,
    projects, and quality metrics.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio_analyses',
        db_index=True
    )
    
    # Portfolio URL
    url = models.URLField()
    domain = models.CharField(max_length=200, blank=True)
    
    # Analysis results
    technologies = models.JSONField(
        default=list,
        help_text="List of technologies detected"
    )
    projects = models.JSONField(
        default=list,
        help_text="List of projects with details"
    )
    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text="AI-calculated quality score (0-1)"
    )
    completeness_score = models.FloatField(
        null=True,
        blank=True,
        help_text="How complete the portfolio is (0-1)"
    )
    
    # Detailed analysis
    tech_stack = models.JSONField(
        default=dict,
        help_text="Detailed tech stack breakdown"
    )
    project_count = models.IntegerField(default=0)
    star_count = models.IntegerField(default=0)
    contribution_count = models.IntegerField(default=0)
    
    # AI observations
    observations = models.JSONField(
        default=dict,
        help_text="AI-generated observations about the portfolio"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('analyzing', 'Analyzing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
    )
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "core_portfolio_analysis"
        verbose_name = "Portfolio Analysis"
        verbose_name_plural = "Portfolio Analyses"
    
    def __str__(self):
        return f"Portfolio: {self.url} ({self.status})"

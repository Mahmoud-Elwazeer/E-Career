"""
Intelligence App Models

Stores AI prompts, model configurations, and usage tracking for the platform's
AI features (Rashid, cover letters, CV parsing, etc.)
"""
from django.db import models
from django.conf import settings
from apps.core.models import UUIDModel


class PromptVersion(UUIDModel):
    """
    Versioned prompt storage for AI features.

    Allows editing prompts without code deployment, A/B testing,
    and rollback to previous versions.
    """

    FEATURE_CHOICES = [
        ('cover_letter', 'Cover Letter Generation'),
        ('cv_tailor', 'CV Tailoring'),
        ('match_explanation', 'Job Match Explanation'),
        ('interview_questions', 'Interview Question Generation'),
        ('interview_evaluation', 'Interview Answer Evaluation'),
        ('skill_extraction', 'Skill Extraction from Jobs'),
        ('rashid_career_advice', 'Rashid Career Advice'),
        ('rashid_interview_prep', 'Rashid Interview Prep'),
        ('weekly_digest_tip', 'Weekly Digest Career Tip'),
    ]

    MODEL_CHOICES = [
        ('haiku', 'Claude 3.5 Haiku'),
        ('sonnet', 'Claude 3.5 Sonnet'),
        ('opus', 'Claude Opus'),
    ]

    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique identifier for this prompt (e.g., 'cover_letter_generation')"
    )
    feature = models.CharField(
        max_length=50,
        choices=FEATURE_CHOICES,
        db_index=True,
        help_text="Which feature uses this prompt"
    )
    version = models.IntegerField(
        default=1,
        help_text="Version number (increments on each edit)"
    )
    content = models.TextField(
        help_text="The actual prompt text. Use {variable} for template variables."
    )
    system_prompt = models.TextField(
        blank=True,
        help_text="Optional system prompt (Claude-specific)"
    )
    model_target = models.CharField(
        max_length=20,
        choices=MODEL_CHOICES,
        default='haiku',
        help_text="Which AI model this prompt is optimized for"
    )
    max_tokens = models.IntegerField(
        default=1000,
        help_text="Maximum tokens for completion"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Sampling temperature (0.0 = deterministic, 1.0 = creative)"
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Only one version per name can be active"
    )
    is_test = models.BooleanField(
        default=False,
        help_text="Mark as test version for A/B testing"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_prompts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text="Change notes, why this version was created"
    )

    class Meta:
        db_table = 'intelligence_prompt_version'
        ordering = ['-version', '-created_at']
        unique_together = ('name', 'version')
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['feature', 'is_active']),
        ]

    def __str__(self):
        active_flag = " [ACTIVE]" if self.is_active else ""
        return f"{self.get_feature_display()} v{self.version}{active_flag}"

    def save(self, *args, **kwargs):
        # Auto-increment version if creating new prompt with same name
        if not self.pk and not self.version:
            latest = PromptVersion.objects.filter(name=self.name).order_by('-version').first()
            self.version = (latest.version + 1) if latest else 1

        # Ensure only one active version per name
        if self.is_active:
            PromptVersion.objects.filter(name=self.name, is_active=True).update(is_active=False)

        super().save(*args, **kwargs)


class PromptUsage(UUIDModel):
    """
    Track usage of prompts for analytics and cost optimization.
    """
    prompt_version = models.ForeignKey(
        PromptVersion,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    tokens_used = models.IntegerField(default=0)
    latency_ms = models.IntegerField(help_text="Response time in milliseconds")
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'intelligence_prompt_usage'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prompt_version', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.prompt_version.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

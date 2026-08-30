import uuid
from django.db import models
from django.conf import settings
from apps.core.models import UUIDModel
from encrypted_model_fields.fields import EncryptedTextField


class RashidConfig(models.Model):
    """
    Single-row configuration table for Rashid AI.
    All settings editable from admin panel.
    """
    
    # AI Provider settings
    ai_provider = models.CharField(
        max_length=20,
        default='bedrock',
        choices=[
            ('bedrock', 'Amazon Bedrock'),
            ('anthropic', 'Anthropic API'),
        ]
    )
    
    # Bedrock settings
    bedrock_region = models.CharField(max_length=30, default='us-east-1')
    bedrock_model_id = models.CharField(
        max_length=100,
        default='us.anthropic.claude-sonnet-4-20250514-v1:0'
    )
    
    # Anthropic direct settings (fallback)
    anthropic_model = models.CharField(
        max_length=50,
        default='claude-sonnet-4'
    )
    
    # Generation parameters
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    
    # Prompts (all editable)
    system_prompt = models.TextField(
        default="""اسمي راشد. أنا مرشد مهني شخصي ومتخصص.
بتكلم بالعربية العامية المصرية بشكل طبيعي ومريح.

أسلوبي صريح ومحترم وعملي. مش بدّوش معلومات وبدي للموضوع.
كل شخص عندي حالة مستقلة ليها ظروفها ومهاراتها وأهدافها.

بسأل سؤال واحد في كل مرة وبستنى الإجابة قبل ما أكمل.
مش بوعد بوعود مستحيلة ومش بقول "اتعلم Python في 7 أيام".

بساعدك توصل لهدفك الحقيقي بخطة واقعية تناسب وقتك وظروفك."""
    )
    
    dialect_config = models.TextField(
        default="""Egyptian Colloquial Arabic Guidelines:
- Use إيه instead of ما
- Use عايز/عاوز instead of أريد  
- Use ازاي instead of كيف
- Use ليه instead of لماذا
- Use ممكن instead of يمكن
- Use علشان instead of لأن
Natural conversational tone, not formal Arabic."""
    )
    
    onboarding_questions = models.JSONField(
        default=list,
        help_text="List of questions for first-time users"
    )
    
    # Limits
    daily_token_limit = models.IntegerField(
        default=100000,
        help_text="Maximum tokens per user per day"
    )
    max_conversation_len = models.IntegerField(
        default=50,
        help_text="Maximum messages per conversation"
    )
    
    # Conversation retention
    auto_delete_after_days = models.IntegerField(
        default=90,
        help_text="Delete conversations older than this"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rashid Configuration'
        verbose_name_plural = 'Rashid Configuration'
    
    def save(self, *args, **kwargs):
        # Enforce single row
        self.pk = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Rashid Config (Provider: {self.ai_provider})"


class RashidProfile(models.Model):
    """
    Persistent user profile built through onboarding.
    Injected into every Rashid conversation as context.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rashid_profile'
    )
    
    # Career information
    experience_level = models.CharField(max_length=20, blank=True)
    current_role = models.CharField(max_length=100, blank=True)
    current_situation = models.TextField(blank=True)
    target_role = models.CharField(max_length=100, blank=True)
    
    # Skills and gaps
    skills = models.JSONField(default=list)
    skill_gaps = models.JSONField(default=list)
    
    # Constraints
    constraints = models.JSONField(
        default=dict,
        help_text="Time, location, financial constraints"
    )
    
    # Generated plans
    career_path = models.JSONField(null=True, blank=True)
    action_plan = models.JSONField(null=True, blank=True)
    
    # Onboarding status
    onboarding_complete = models.BooleanField(default=False)
    onboarding_step = models.IntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rashid User Profile'
        verbose_name_plural = 'Rashid User Profiles'
    
    def __str__(self):
        return f"Rashid Profile: {self.user.email}"


class RashidConversation(models.Model):
    """A single Rashid conversation session"""
    
    MODES = [
        ('general', 'General Chat'),
        ('career_path', 'Career Path Planning'),
        ('cv_review', 'CV Review'),
        ('linkedin', 'LinkedIn Optimizer'),
        ('cover_letter', 'Cover Letter Generator'),
        ('interview_prep', 'Interview Preparation'),
        ('course_advisor', 'Course Advisor'),
        ('salary_negotiation', 'Salary Negotiation'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rashid_conversations'
    )
    mode = models.CharField(
        max_length=30,
        choices=MODES,
        default='general'
    )
    
    # Auto-generated title from first message
    title = models.CharField(max_length=120, blank=True)
    
    # Optional job context
    job = models.ForeignKey(
        'jobs.Job',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Job being discussed (for 'Ask Rashid about this job')"
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Rashid Conversation'
        verbose_name_plural = 'Rashid Conversations'
    
    def __str__(self):
        return f"{self.user.email} - {self.mode} - {self.title[:50]}"


class RashidMessage(models.Model):
    """
    Individual message in a conversation.
    Content is ENCRYPTED - admin cannot read it.
    """
    conversation = models.ForeignKey(
        RashidConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    role = models.CharField(
        max_length=10,
        choices=[
            ('user', 'User'),
            ('assistant', 'Assistant'),
        ]
    )
    
    # ENCRYPTED FIELD - requires FIELD_ENCRYPTION_KEY in .env
    content = EncryptedTextField()
    
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Rashid Message'
        verbose_name_plural = 'Rashid Messages'
    
    def __str__(self):
        return f"{self.role} @ {self.created_at}"


class RashidStoryBank(models.Model):
    """
    STAR stories accumulated across sessions.
    Used for interview preparation.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='star_stories'
    )
    
    # STAR components
    situation = models.TextField()
    task = models.TextField()
    action = models.TextField()
    result = models.TextField()
    reflection = models.TextField(blank=True)
    
    tags = models.JSONField(
        default=list,
        help_text="Skills/competencies demonstrated"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'STAR Story'
        verbose_name_plural = 'STAR Stories'
    
    def __str__(self):
        return f"{self.user.email} - {self.situation[:50]}"


class RashidUsage(models.Model):
    """
    Daily token usage per user.
    Enforces daily_token_limit from RashidConfig.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rashid_usage'
    )
    date = models.DateField()
    tokens_used = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'date')
        verbose_name = 'Rashid Usage'
        verbose_name_plural = 'Rashid Usage'
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.tokens_used} tokens"
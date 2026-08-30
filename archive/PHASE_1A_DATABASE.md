> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 1A: Database Foundation

> **Duration:** 2-3 hours  
> **Dependencies:** None  
> **Branch:** development  
> **Status:** Ready to execute

---

## 📋 Overview

This phase extends the existing database schema without breaking current functionality. All changes are additive through Django migrations.

### What You'll Build:
- ✅ Extend Job, Source, Company models with scraping fields
- ✅ Create UserProfile model for CV and preferences
- ✅ Create Rashid AI models (RashidConfig, RashidProfile, etc.)
- ✅ Create Email system models (EmailAccount, EmailTemplate, etc.)
- ✅ Create Employer portal models (EmployerProfile, JobPosting, etc.)
- ✅ Create utility models (ProxyPool, PipelineHealth, etc.)

---

## 🔧 Pre-requisites

```bash
# Ensure you're on the development branch
git status

# Install new dependencies
pip install django-encrypted-model-fields==0.6.5
pip install cryptography==41.0.7

# Generate encryption key for sensitive fields
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy the output and add to .env as FIELD_ENCRYPTION_KEY
```

---

## 📦 Step 1: Install Dependencies

Add to `backend/requirements/base.txt`:

```txt
# Encryption for sensitive fields
django-encrypted-model-fields==0.6.5
cryptography==41.0.7
```

Then install:
```bash
cd backend
pip install -r requirements/base.txt
```

---

## 🗄️ Step 2: Extend Existing Models

### 2.1 Extend Job Model

**File:** `backend/apps/jobs/models.py`

Find the existing `Job` model and add these fields at the end (before the `Meta` class):

```python
# Add to existing Job model - DO NOT create a new model

class Job(UUIDModel):
    # ... existing fields ...
    
    # ============ NEW FIELDS - ADD THESE ============
    
    # Core pipeline fields
    direct_apply_url = models.URLField(
        max_length=2000, 
        db_index=True,
        help_text="Direct link to company's application page (no aggregators)"
    )
    apply_url_verified = models.BooleanField(default=False)
    apply_url_checked_at = models.DateTimeField(null=True, blank=True)
    apply_url_status_code = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Last HTTP status code from URL check"
    )
    
    # Source type classification
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('scraped', 'Scraped from ATS'),
            ('employer_posted', 'Employer Posted'),
        ],
        default='scraped',
        db_index=True
    )
    
    # Job classification
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('freelance', 'Freelance'),
        ],
        null=True, 
        blank=True, 
        db_index=True
    )
    
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('student', 'Student'),
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior'),
            ('director', 'Director'),
            ('c_level', 'C-Level'),
        ],
        null=True, 
        blank=True, 
        db_index=True
    )
    
    remote_type = models.CharField(
        max_length=10,
        choices=[
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
        ],
        null=True, 
        blank=True, 
        db_index=True
    )
    
    # Salary information
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='EGP')
    
    # Pipeline metadata
    scraped_at = models.DateTimeField(null=True, blank=True)
    source_raw_url = models.URLField(
        max_length=2000, 
        blank=True,
        help_text="Original aggregator URL (not shown to users)"
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False, db_index=True)
    
    # Legitimacy scoring (Block G)
    legitimacy_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Score from 0.0 to 1.0, higher is more legitimate"
    )
    legitimacy_flags = models.JSONField(
        default=list,
        help_text="List of flags raised by legitimacy checker"
    )
    
    # ATS metadata
    raw_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="Original scraped payload for debugging"
    )
    ats_platform = models.CharField(
        max_length=30, 
        blank=True,
        help_text="greenhouse, lever, ashby, workday, etc."
    )
    ats_job_id = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,
        help_text="ATS's own internal job ID"
    )
    
    # ============ END NEW FIELDS ============
    
    class Meta:
        # ... existing Meta ...
        pass
    
    # Add this method for URL validation
    def clean(self):
        """Validate that direct_apply_url is not from an aggregator"""
        from apps.scraper.pipeline.url_resolver import is_direct_company_url
        
        if self.direct_apply_url and not is_direct_company_url(self.direct_apply_url):
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'direct_apply_url': 'Apply URL must be a direct company link, not an aggregator (LinkedIn, Indeed, etc.)'
            })
        
        super().clean()
```

### 2.2 Extend Source Model

**File:** `backend/apps/jobs/models.py`

Find the existing `Source` model and add these fields:

```python
class Source(UUIDModel):
    # ... existing fields ...
    
    # ============ NEW FIELDS - ADD THESE ============
    
    # Scraper configuration
    scraper_class = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Python class name for this scraper"
    )
    schedule_cron = models.CharField(
        max_length=50, 
        default='0 */6 * * *',
        help_text="Cron expression for scraping schedule"
    )
    requires_playwright = models.BooleanField(
        default=False,
        help_text="Whether this source needs headless browser"
    )
    
    # Run status tracking
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(
        max_length=20, 
        default='never',
        choices=[
            ('never', 'Never Run'),
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ]
    )
    jobs_found_last_run = models.IntegerField(default=0)
    jobs_added_last_run = models.IntegerField(default=0)
    
    # ATS metadata
    ats_platform = models.CharField(
        max_length=30, 
        blank=True,
        help_text="greenhouse, lever, ashby, etc."
    )
    
    # Error tracking
    error_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    # ============ END NEW FIELDS ============
```

### 2.3 Extend Company Model

**File:** `backend/apps/jobs/models.py`

Find the existing `Company` model and add these fields:

```python
class Company(UUIDModel):
    # ... existing fields ...
    
    # ============ NEW FIELDS - ADD THESE ============
    
    # Visual branding
    logo = models.ImageField(
        upload_to='company_logos/', 
        null=True, 
        blank=True
    )
    logo_url = models.URLField(
        blank=True,
        help_text="Clearbit or manual logo URL"
    )
    
    # Company information
    domain = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,
        help_text="Company website domain (e.g., google.com)"
    )
    description = models.TextField(blank=True)
    size = models.CharField(
        max_length=20, 
        blank=True,
        help_text="1-10, 11-50, 51-200, etc."
    )
    industry = models.CharField(max_length=100, blank=True)
    headquarters = models.CharField(max_length=100, blank=True)
    
    # External links
    linkedin_url = models.URLField(blank=True)
    careers_page_url = models.URLField(
        blank=True,
        help_text="Company's official careers page"
    )
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Admin-verified company"
    )
    
    # ============ END NEW FIELDS ============
```

---

## 🆕 Step 3: Create New Apps

### 3.1 Create Rashid App

```bash
cd backend/apps
python ../manage.py startapp rashid
```

**File:** `backend/apps/rashid/models.py`

```python
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
        default='anthropic.claude-sonnet-4-20250514-v1:0'
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
```

**File:** `backend/apps/rashid/__init__.py`
```python
default_app_config = 'apps.rashid.apps.RashidConfig'
```

**File:** `backend/apps/rashid/apps.py`
```python
from django.apps import AppConfig


class RashidConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rashid'
    verbose_name = 'Rashid AI Mentor'
```

### 3.2 Create Emails App

```bash
cd backend/apps
python ../manage.py startapp emails
```

**File:** `backend/apps/emails/models.py`

```python
import uuid
from django.db import models
from django.conf import settings
from encrypted_model_fields.fields import EncryptedCharField


class EmailAccount(models.Model):
    """
    Google Workspace email account for sending campaigns.
    Credentials are ENCRYPTED.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    
    # SMTP settings
    smtp_host = models.CharField(max_length=100, default='smtp.gmail.com')
    smtp_port = models.IntegerField(default=587)
    
    # ENCRYPTED credentials
    username_enc = EncryptedCharField(max_length=255)
    password_enc = EncryptedCharField(max_length=255)
    
    # Rate limiting
    daily_limit = models.IntegerField(
        default=500,
        help_text="Maximum emails per day"
    )
    today_sent = models.IntegerField(default=0)
    last_reset = models.DateField(auto_now_add=True)
    
    # Rotation
    rotation_order = models.IntegerField(
        default=0,
        help_text="Order in rotation queue (0 = first)"
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_sent = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    tracking_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['rotation_order']
        verbose_name = 'Email Account'
        verbose_name_plural = 'Email Accounts'
    
    def __str__(self):
        return f"{self.name} ({self.email})"


class EmailTemplate(models.Model):
    """
    Email template with HTML and plain text versions.
    Supports variable substitution like {{user_name}}.
    """
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('job_alert', 'Job Alert'),
        ('weekly_digest', 'Weekly Digest'),
        ('employer_application', 'Employer: New Application'),
        ('employer_url_dead', 'Employer: Dead Apply URL'),
        ('re_engagement', 'Re-engagement Email'),
        ('password_reset', 'Password Reset'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(
        max_length=30,
        choices=TEMPLATE_TYPES
    )
    
    subject = models.CharField(
        max_length=200,
        help_text="Supports {{variables}}"
    )
    html_body = models.TextField()
    text_body = models.TextField(
        blank=True,
        help_text="Plain text fallback"
    )
    
    is_active = models.BooleanField(default=True)
    
    # Statistics
    last_sent_at = models.DateTimeField(null=True, blank=True)
    total_sent = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class EmailLog(models.Model):
    """
    Log of every email sent.
    Tracks opens and clicks via tracking pixels.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='emails_received'
    )
    account = models.ForeignKey(
        EmailAccount,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_emails'
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    
    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Tracking
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Error handling
    failed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
    
    def __str__(self):
        return f"{self.recipient} - {self.subject} - {self.sent_at}"
```

**File:** `backend/apps/emails/__init__.py`
```python
default_app_config = 'apps.emails.apps.EmailsConfig'
```

**File:** `backend/apps/emails/apps.py`
```python
from django.apps import AppConfig


class EmailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emails'
    verbose_name = 'Email System'
```

### 3.3 Create Employers App

```bash
cd backend/apps
python ../manage.py startapp employers
```

**File:** `backend/apps/employers/models.py`

```python
from django.db import models
from django.conf import settings
from apps.core.models import UUIDModel


class EmployerProfile(models.Model):
    """
    Employer user profile linked to a Company.
    Must be verified by admin before posting jobs.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_profile'
    )
    company = models.ForeignKey(
        'jobs.Company',
        on_delete=models.CASCADE,
        related_name='employers'
    )
    
    job_title = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employer_verifications_done'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Employer Profile'
        verbose_name_plural = 'Employer Profiles'
    
    def __str__(self):
        return f"{self.user.email} @ {self.company.name}"


class JobPosting(UUIDModel):
    """
    Employer-managed job posting.
    When published, it's mirrored to the main Job model.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]
    
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='job_postings'
    )
    company = models.ForeignKey(
        'jobs.Company',
        on_delete=models.CASCADE,
        related_name='employer_postings'
    )
    
    # Link to mirrored job (created on publish)
    mirrored_job = models.OneToOneField(
        'jobs.Job',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employer_posting'
    )
    
    # Job content
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    
    # MUST be company's own URL, not aggregator
    apply_url = models.URLField(
        max_length=2000,
        help_text="Direct link to your company's application page"
    )
    apply_url_verified = models.BooleanField(default=False)
    apply_url_checked_at = models.DateTimeField(null=True, blank=True)
    
    # Classification
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('freelance', 'Freelance'),
        ]
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('student', 'Student'),
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior'),
            ('director', 'Director'),
            ('c_level', 'C-Level'),
        ]
    )
    remote_type = models.CharField(
        max_length=10,
        choices=[
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
        ]
    )
    location = models.CharField(max_length=200)
    
    # Salary (optional)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='EGP')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    
    # Analytics
    views_count = models.IntegerField(default=0)
    clicks_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
    
    def __str__(self):
        return f"{self.title} @ {self.company.name} ({self.status})"
    
    def clean(self):
        """Validate apply_url is not from aggregator"""
        from apps.scraper.pipeline.url_resolver import is_direct_company_url
        from django.core.exceptions import ValidationError
        
        if self.apply_url and not is_direct_company_url(self.apply_url):
            raise ValidationError({
                'apply_url': 'Apply URL must be a direct company link, not LinkedIn, Indeed, or any aggregator.'
            })
        
        super().clean()


class JobApplication(models.Model):
    """
    Tracks when a user clicks Apply on a job.
    Optional on-platform application tracking.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    
    applied_at = models.DateTimeField(auto_now_add=True)
    
    # Snapshot of CV at time of application
    cv_snapshot = models.FileField(
        upload_to='application_cvs/%Y/%m/',
        null=True,
        blank=True
    )
    
    status = models.CharField(
        max_length=20,
        default='applied',
        choices=[
            ('applied', 'Applied'),
            ('viewed', 'Viewed by Employer'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected'),
        ]
    )
    
    class Meta:
        ordering = ['-applied_at']
        unique_together = ('user', 'job')
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
    
    def __str__(self):
        return f"{self.user.email} → {self.job.title}"
```

**File:** `backend/apps/employers/__init__.py`
```python
default_app_config = 'apps.employers.apps.EmployersConfig'
```

**File:** `backend/apps/employers/apps.py`
```python
from django.apps import AppConfig


class EmployersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.employers'
    verbose_name = 'Employer Portal'
```

---

## 📝 Step 4: Extend Users App

**File:** `backend/apps/users/models.py`

Add these new models (don't modify existing ones):

```python
# Add to existing users/models.py

from django.db import models
from django.conf import settings
from apps.core.models import UUIDModel


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
```

---

## 🔧 Step 5: Add Utility Models to Core App

**File:** `backend/apps/core/models.py`

Add these models to the existing core app:

```python
# Add to existing core/models.py

from django.db import models
from django.conf import settings


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
```

---

## ⚙️ Step 6: Update Settings

**File:** `backend/config/settings/base.py`

Add new apps to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    
    # New apps - ADD THESE
    'apps.rashid',
    'apps.emails',
    'apps.employers',
    
    # ... rest of existing apps ...
]
```

Add encryption key configuration:

```python
# Add to bottom of base.py

# ── Encryption ──────────────────────────────────────────────────────────────
from decouple import config

FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default='')

if not FIELD_ENCRYPTION_KEY:
    import warnings
    warnings.warn(
        "FIELD_ENCRYPTION_KEY not set! Encrypted fields will not work. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )
```

---

## 🚀 Step 7: Create Migrations

```bash
cd backend

# Create migrations for all modified apps
python manage.py makemigrations jobs
python manage.py makemigrations users
python manage.py makemigrations core
python manage.py makemigrations rashid
python manage.py makemigrations emails
python manage.py makemigrations employers

# Review migrations before applying
python manage.py sqlmigrate jobs 000X  # Replace X with migration number

# Apply all migrations
python manage.py migrate
```

---

## ✅ Step 8: Verify Installation

```bash
# Check all models are created
python manage.py shell

from apps.jobs.models import Job, Source, Company
from apps.users.models import UserProfile, JobMatchScore
from apps.rashid.models import RashidConfig, RashidProfile, RashidConversation
from apps.emails.models import EmailAccount, EmailTemplate, EmailLog
from apps.employers.models import EmployerProfile, JobPosting, JobApplication
from apps.core.models import PlatformConfig, ProxyPool, PipelineHealth

# Create initial config objects
RashidConfig.objects.create()
PlatformConfig.objects.create()

print("✅ All models created successfully!")
```

---

## 🎯 What's Next?

After this phase is complete:

1. ✅ All database models are in place
2. ✅ Migrations applied successfully
3. ✅ No existing functionality broken

**Next Phase:** `PHASE_1B_SCRAPING.md` - Job scraping pipeline

---

## 🐛 Troubleshooting

### Issue: Migration conflicts
**Solution:** 
```bash
python manage.py makemigrations --merge
```

### Issue: Encryption key not working
**Solution:** 
```bash
# Generate new key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo "FIELD_ENCRYPTION_KEY=your-key-here" >> .env
```

### Issue: Import errors for new apps
**Solution:**
```bash
# Ensure apps are in INSTALLED_APPS
# Restart Django server
python manage.py runserver
```

---

## 📋 Phase 1A Checklist

- [ ] Dependencies installed (`django-encrypted-model-fields`, `cryptography`)
- [ ] Encryption key generated and added to `.env`
- [ ] Job model extended with new fields
- [ ] Source model extended
- [ ] Company model extended
- [ ] Rashid app created with all models
- [ ] Emails app created with all models
- [ ] Employers app created with all models
- [ ] UserProfile and JobMatchScore models added
- [ ] PlatformConfig, ProxyPool, PipelineHealth models added
- [ ] New apps added to INSTALLED_APPS
- [ ] All migrations created
- [ ] All migrations applied successfully
- [ ] RashidConfig singleton created
- [ ] PlatformConfig singleton created
- [ ] Verification script passed

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

*Phase 1A Complete! Ready for Phase 1B: Scraping Pipeline*


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
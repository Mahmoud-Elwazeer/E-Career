> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 2D: Email System

> **Dependencies:** Phase 1B, Phase 2A complete  
> **Duration:** 3-4 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Implement comprehensive email system:
- Multi-account Google Workspace rotation
- Email templates (welcome, alerts, digest)
- Tracking pixels for open rates
- Celery tasks for campaigns
- User preferences and unsubscribe

---

## 📦 Dependencies

```bash
pip install celery django-celery-beat
pip install premailer  # For inline CSS in emails
```

---

## 🔧 Implementation

### Step 1: Email Models

**File:** `backend/emails/models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class EmailAccount(models.Model):
    """Google Workspace email account for sending"""
    
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, help_text="App password")
    display_name = models.CharField(max_length=255, default="USAM Career")
    
    # Usage tracking
    emails_sent_today = models.IntegerField(default=0)
    emails_sent_this_month = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Limits
    daily_limit = models.IntegerField(default=500)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['emails_sent_today', 'last_used_at']
    
    def __str__(self):
        return f"{self.email} ({self.emails_sent_today}/{self.daily_limit})"
    
    def can_send(self):
        """Check if account can send more emails"""
        return self.is_active and self.emails_sent_today < self.daily_limit
    
    def increment_usage(self):
        """Increment usage counters"""
        self.emails_sent_today += 1
        self.emails_sent_this_month += 1
        self.last_used_at = timezone.now()
        self.save()
    
    def reset_daily_counter(self):
        """Reset daily counter (run by Celery Beat)"""
        self.emails_sent_today = 0
        self.save()


class EmailTemplate(models.Model):
    """Email template for campaigns"""
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('job_alert', 'Job Alert'),
        ('daily_digest', 'Daily Digest'),
        ('weekly_digest', 'Weekly Digest'),
        ('application_confirmation', 'Application Confirmation'),
        ('password_reset', 'Password Reset'),
    ]
    
    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=255)
    html_content = models.TextField(help_text="HTML template with {{variables}}")
    text_content = models.TextField(help_text="Plain text version")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['template_type', 'version']
        ordering = ['-version']
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


class EmailCampaign(models.Model):
    """Email campaign for batch sending"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(User, through='CampaignRecipient')
    
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Stats
    total_recipients = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_failed = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='campaigns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class CampaignRecipient(models.Model):
    """Individual recipient in a campaign"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    email_account = models.ForeignKey(EmailAccount, on_delete=models.SET_NULL, null=True)
    
    # Tracking
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['campaign', 'user']


class EmailLog(models.Model):
    """Log of all emails sent"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails_received')
    email_account = models.ForeignKey(EmailAccount, on_delete=models.SET_NULL, null=True)
    
    subject = models.CharField(max_length=255)
    template_type = models.CharField(max_length=50, blank=True)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    # Tracking
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, default='sent')
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', '-sent_at']),
            models.Index(fields=['tracking_id']),
        ]
```

### Step 2: Email Service

**File:** `backend/emails/service.py`

```python
"""
Email sending service with account rotation
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.template import Template, Context
from premailer import transform

from .models import EmailAccount, EmailTemplate, EmailLog

logger = logging.getLogger(__name__)

class EmailService:
    """Handle email sending with multi-account rotation"""
    
    def __init__(self):
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 587
    
    def get_available_account(self):
        """Get available email account using round-robin"""
        accounts = EmailAccount.objects.filter(is_active=True)
        
        for account in accounts:
            if account.can_send():
                return account
        
        logger.error("No available email accounts")
        return None
    
    def send_email(
        self,
        to_email,
        subject,
        html_content,
        text_content=None,
        template_type=None,
        user=None,
        tracking_enabled=True
    ):
        """
        Send email with tracking
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Plain text fallback
            template_type: Template type for logging
            user: User instance for logging
            tracking_enabled: Whether to add tracking pixel
        
        Returns:
            bool: Success status
        """
        account = self.get_available_account()
        
        if not account:
            logger.error("No available email account")
            return False
        
        try:
            # Create email log
            email_log = EmailLog.objects.create(
                user=user,
                email_account=account,
                subject=subject,
                template_type=template_type or '',
                status='pending'
            )
            
            # Add tracking pixel if enabled
            if tracking_enabled:
                tracking_url = f"{settings.EMAIL_TRACKING_DOMAIN}/track/open/{email_log.tracking_id}/"
                tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" />'
                html_content += tracking_pixel
            
            # Inline CSS for better email client support
            html_content = transform(html_content)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{account.display_name} <{account.email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach plain text
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # Attach HTML
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(account.email, account.password)
                server.send_message(msg)
            
            # Update usage
            account.increment_usage()
            
            # Update log
            email_log.status = 'sent'
            email_log.save()
            
            logger.info(f"Email sent to {to_email} via {account.email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            
            if email_log:
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()
            
            return False
    
    def send_template_email(self, user, template_type, context_data=None):
        """
        Send email using template
        
        Args:
            user: User instance
            template_type: Template type
            context_data: Dict of template variables
        
        Returns:
            bool: Success status
        """
        try:
            template = EmailTemplate.objects.filter(
                template_type=template_type,
                is_active=True
            ).first()
            
            if not template:
                logger.error(f"No active template found for {template_type}")
                return False
            
            # Render template
            context_data = context_data or {}
            context_data.update({
                'user': user,
                'site_url': settings.SITE_URL,
                'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/{user.id}/"
            })
            
            html_template = Template(template.html_content)
            html_content = html_template.render(Context(context_data))
            
            text_template = Template(template.text_content)
            text_content = text_template.render(Context(context_data))
            
            # Render subject
            subject_template = Template(template.subject)
            subject = subject_template.render(Context(context_data))
            
            # Send
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_type=template_type,
                user=user
            )
        
        except Exception as e:
            logger.error(f"Failed to send template email: {e}")
            return False


# Singleton instance
email_service = EmailService()
```

### Step 3: Celery Tasks

**File:** `backend/emails/tasks.py`

```python
"""
Celery tasks for email campaigns
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import EmailCampaign, CampaignRecipient, EmailAccount
from .service import email_service
from jobs.models import Job

User = get_user_model()

@shared_task
def send_campaign_batch(campaign_id, batch_size=100):
    """Send a batch of emails for a campaign"""
    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)
        
        # Get pending recipients
        recipients = CampaignRecipient.objects.filter(
            campaign=campaign,
            status='pending'
        )[:batch_size]
        
        if not recipients.exists():
            # Campaign complete
            campaign.status = 'sent'
            campaign.completed_at = timezone.now()
            campaign.save()
            return
        
        # Update campaign status
        if campaign.status != 'sending':
            campaign.status = 'sending'
            campaign.started_at = timezone.now()
            campaign.save()
        
        # Send emails
        for recipient in recipients:
            success = email_service.send_template_email(
                user=recipient.user,
                template_type=campaign.template.template_type,
                context_data={'campaign': campaign}
            )
            
            if success:
                recipient.status = 'sent'
                recipient.sent_at = timezone.now()
                campaign.emails_sent += 1
            else:
                recipient.status = 'failed'
                campaign.emails_failed += 1
            
            recipient.save()
        
        campaign.save()
        
        # Schedule next batch
        if CampaignRecipient.objects.filter(campaign=campaign, status='pending').exists():
            send_campaign_batch.apply_async(
                args=[campaign_id, batch_size],
                countdown=10  # Wait 10 seconds between batches
            )
    
    except Exception as e:
        print(f"Error sending campaign batch: {e}")


@shared_task
def send_job_alerts():
    """Send job alerts to users with matching jobs"""
    from jobs.models import Job
    from profiles.services import MatchingService
    
    # Get users with alerts enabled
    users = User.objects.filter(
        userprofile__email_alerts_enabled=True
    )
    
    matcher = MatchingService()
    
    for user in users:
        try:
            profile = user.userprofile
            
            # Determine alert frequency
            frequency = profile.alert_frequency or 'daily'
            
            # Check last alert sent
            last_alert = EmailLog.objects.filter(
                user=user,
                template_type='job_alert'
            ).first()
            
            if last_alert:
                hours_since_last = (timezone.now() - last_alert.sent_at).total_seconds() / 3600
                
                if frequency == 'daily' and hours_since_last < 24:
                    continue
                elif frequency == 'weekly' and hours_since_last < 168:
                    continue
            
            # Find matching jobs
            recent_jobs = Job.objects.filter(
                is_active=True,
                posted_date__gte=timezone.now() - timedelta(days=1)
            )
            
            matching_jobs = []
            for job in recent_jobs[:50]:  # Limit to 50 jobs
                score = matcher.calculate_match_score(profile, job)
                if score >= 70:  # 70% match threshold
                    matching_jobs.append({
                        'job': job,
                        'score': score
                    })
            
            if matching_jobs:
                # Send alert
                email_service.send_template_email(
                    user=user,
                    template_type='job_alert',
                    context_data={
                        'jobs': matching_jobs,
                        'total_matches': len(matching_jobs)
                    }
                )
        
        except Exception as e:
            print(f"Error sending job alert to {user.email}: {e}")


@shared_task
def send_daily_digest():
    """Send daily digest to subscribed users"""
    users = User.objects.filter(
        userprofile__email_alerts_enabled=True,
        userprofile__alert_frequency='daily'
    )
    
    for user in users:
        try:
            # Get today's stats
            new_jobs_count = Job.objects.filter(
                is_active=True,
                posted_date__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            # Get user's top matches
            profile = user.userprofile
            # ... match calculation logic
            
            # Send digest
            email_service.send_template_email(
                user=user,
                template_type='daily_digest',
                context_data={
                    'new_jobs_count': new_jobs_count,
                    # ... other stats
                }
            )
        
        except Exception as e:
            print(f"Error sending daily digest to {user.email}: {e}")


@shared_task
def reset_email_account_counters():
    """Reset daily email counters for all accounts"""
    EmailAccount.objects.filter(is_active=True).update(emails_sent_today=0)


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user"""
    try:
        user = User.objects.get(id=user_id)
        email_service.send_template_email(
            user=user,
            template_type='welcome'
        )
    except Exception as e:
        print(f"Error sending welcome email: {e}")
```

### Step 4: Celery Beat Schedule

**File:** `backend/ecareer/celery.py` (update)

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('ecareer')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'send-job-alerts-every-hour': {
        'task': 'emails.tasks.send_job_alerts',
        'schedule': crontab(minute=0),  # Every hour
    },
    'send-daily-digest': {
        'task': 'emails.tasks.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'reset-email-counters': {
        'task': 'emails.tasks.reset_email_account_counters',
        'schedule': crontab(hour=0, minute=0),  # Midnight daily
    },
}
```

### Step 5: Tracking Views

**File:** `backend/emails/views.py`

```python
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from .models import EmailLog

def track_email_open(request, tracking_id):
    """Track email open via pixel"""
    try:
        email_log = EmailLog.objects.get(tracking_id=tracking_id)
        if not email_log.opened_at:
            email_log.opened_at = timezone.now()
            email_log.save()
    except EmailLog.DoesNotExist:
        pass
    
    # Return 1x1 transparent pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return HttpResponse(pixel, content_type='image/gif')


def track_email_click(request, tracking_id):
    """Track email link click"""
    try:
        email_log = EmailLog.objects.get(tracking_id=tracking_id)
        if not email_log.clicked_at:
            email_log.clicked_at = timezone.now()
            email_log.save()
    except EmailLog.DoesNotExist:
        pass
    
    # Redirect to destination
    destination = request.GET.get('url', '/')
    return redirect(destination)
```

### Step 6: Email Templates

**File:** `backend/emails/templates/email/welcome.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563eb; color: white; padding: 30px; text-align: center; }
        .content { background: white; padding: 30px; }
        .button { display: inline-block; padding: 12px 30px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>مرحباً بك في USAM Career!</h1>
        </div>
        
        <div class="content">
            <p>أهلاً {{user.first_name}}،</p>
            
            <p>نورت منصة USAM Career! احنا سعداء إنك انضميت لينا.</p>
            
            <h3>إيه اللي نقدر نساعدك بيه؟</h3>
            <ul>
                <li>🔍 البحث عن أفضل الفرص الوظيفية من آلاف الشركات</li>
                <li>🤖 رشيد - مستشارك المهني بالذكاء الاصطناعي</li>
                <li>📄 تحسين سيرتك الذاتية بشكل احترافي</li>
                <li>💼 تنبيهات فورية للوظائف المناسبة</li>
                <li>📧 متابعة طلبات التوظيف</li>
            </ul>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{{site_url}}/profile/" class="button">
                    أكمل بروفايلك
                </a>
            </p>
            
            <p>لو عندك أي أسئلة، احنا هنا علطول!</p>
            
            <p>مع تحياتنا،<br>فريق USAM Career</p>
        </div>
        
        <div class="footer">
            <p>
                <a href="{{site_url}}" style="color: #2563eb;">زيارة الموقع</a> |
                <a href="{{unsubscribe_url}}" style="color: #666;">إلغاء الاشتراك</a>
            </p>
            <p>© 2026 USAM Career. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

---

## ✅ Phase 2D Verification

### Tests

```bash
# Start Celery worker
celery -A ecareer worker -l info

# Start Celery Beat
celery -A ecareer beat -l info

# Test welcome email
python manage.py shell
>>> from emails.tasks import send_welcome_email
>>> send_welcome_email.delay(1)

# Test job alerts
>>> from emails.tasks import send_job_alerts
>>> send_job_alerts.delay()
```

### Success Criteria

- [ ] Multiple email accounts configured
- [ ] Account rotation works
- [ ] Welcome emails send automatically
- [ ] Job alerts work with matching
- [ ] Tracking pixels record opens
- [ ] Daily digest sends
- [ ] Unsubscribe works
- [ ] Email limits respected

---

**Phase 2D Complete! ✅**
Proceed to Phase 3A: Employer Portal

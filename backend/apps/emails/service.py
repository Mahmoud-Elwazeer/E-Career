"""
Email sending service with multi-account rotation.
Supports tracking pixels, templates, and rate limiting.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from django.conf import settings
from django.template import Template, Context
from django.utils import timezone

from .models import EmailAccount, EmailTemplate, EmailLog

logger = logging.getLogger(__name__)


class EmailService:
    """
    Handle email sending with multi-account rotation.
    Supports tracking pixels for open rate analytics.
    """
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_SMTP_PORT', 587)
        self.tracking_domain = getattr(settings, 'EMAIL_TRACKING_DOMAIN', settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000')
    
    def get_available_account(self):
        """
        Get available email account using round-robin rotation.
        Returns the account with lowest daily usage that can still send.
        """
        accounts = EmailAccount.objects.filter(is_active=True).order_by('rotation_order')
        
        for account in accounts:
            # Reset counter if new day
            if account.last_reset != date.today():
                account.today_sent = 0
                account.last_reset = date.today()
                account.save()
            
            # Check if account can send
            if account.today_sent < account.daily_limit:
                return account
        
        logger.error("No available email accounts - all at daily limit")
        return None
    
    def send_email(
        self,
        to_email,
        subject,
        html_content,
        text_content=None,
        template_type=None,
        user=None,
        tracking_enabled=True,
        template=None
    ):
        """
        Send email with tracking pixel support.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML content of the email
            text_content: Plain text fallback (optional)
            template_type: Type of template for logging
            user: User instance for logging (optional)
            tracking_enabled: Whether to add tracking pixel
            template: EmailTemplate instance (optional)
        
        Returns:
            tuple: (success: bool, tracking_id: str or None)
        """
        account = self.get_available_account()
        
        if not account:
            logger.error("No available email account for sending")
            return False, None
        
        email_log = None
        
        try:
            # Create email log
            email_log = EmailLog.objects.create(
                user=user,
                account=account,
                template=template,
                recipient=to_email,
                subject=subject,
                failed=False
            )
            
            # Add tracking pixel if enabled
            if tracking_enabled and account.tracking_enabled:
                tracking_url = f"{self.tracking_domain}/emails/track/{email_log.tracking_id}/"
                tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" alt="" />'
                # Insert before closing body tag or append
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
                else:
                    html_content += tracking_pixel
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{account.name} <{account.email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach plain text version
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # Attach HTML version
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(account.username_enc, account.password_enc)
                server.send_message(msg)
            
            # Update account usage
            account.today_sent += 1
            account.total_sent += 1
            account.last_used_at = timezone.now()
            account.save()
            
            # Update template stats if provided
            if template:
                template.last_sent_at = timezone.now()
                template.total_sent += 1
                template.save()
            
            logger.info(f"Email sent to {to_email} via {account.email}")
            return True, str(email_log.tracking_id)
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            
            if email_log:
                email_log.failed = True
                email_log.error_message = str(e)
                email_log.save()
            
            return False, None
    
    def send_template_email(self, user, template_type, context_data=None):
        """
        Send email using a template.
        
        Args:
            user: User instance (must have email attribute)
            template_type: Template type (e.g., 'welcome', 'job_alert')
            context_data: Dict of template variables (optional)
        
        Returns:
            tuple: (success: bool, tracking_id: str or None)
        """
        try:
            # Get active template
            template = EmailTemplate.objects.filter(
                template_type=template_type,
                is_active=True
            ).first()
            
            if not template:
                logger.error(f"No active template found for type: {template_type}")
                return False, None
            
            # Build context
            context = context_data or {}
            context.update({
                'user': user,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:3000'),
                'unsubscribe_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:3000')}/settings/notifications/"
            })
            
            # Render subject
            subject_template = Template(template.subject)
            subject = subject_template.render(Context(context))
            
            # Render HTML body
            html_template = Template(template.html_body)
            html_content = html_template.render(Context(context))
            
            # Render text body (if provided)
            text_content = None
            if template.text_body:
                text_template = Template(template.text_body)
                text_content = text_template.render(Context(context))
            
            # Send email
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_type=template_type,
                user=user,
                tracking_enabled=True,
                template=template
            )
        
        except Exception as e:
            logger.error(f"Failed to send template email: {e}")
            return False, None
    
    def send_job_alert(self, user, jobs):
        """
        Send job alert email with matching jobs.
        
        Args:
            user: User instance
            jobs: List of Job instances or job data
        
        Returns:
            tuple: (success: bool, tracking_id: str or None)
        """
        context = {
            'jobs': jobs,
            'total_jobs': len(jobs) if hasattr(jobs, '__len__') else 0,
            'alert_date': timezone.now().strftime('%Y-%m-%d')
        }
        
        return self.send_template_email(
            user=user,
            template_type='job_alert',
            context_data=context
        )
    
    def send_welcome_email(self, user):
        """
        Send welcome email to new user.
        
        Args:
            user: User instance
        
        Returns:
            tuple: (success: bool, tracking_id: str or None)
        """
        return self.send_template_email(
            user=user,
            template_type='welcome'
        )
    
    def send_weekly_digest(self, user, stats):
        """
        Send weekly digest email.
        
        Args:
            user: User instance
            stats: Dict with weekly statistics
        
        Returns:
            tuple: (success: bool, tracking_id: str or None)
        """
        context = {
            'stats': stats,
            'week_start': stats.get('week_start', ''),
            'week_end': stats.get('week_end', '')
        }
        
        return self.send_template_email(
            user=user,
            template_type='weekly_digest',
            context_data=context
        )


# Singleton instance
email_service = EmailService()
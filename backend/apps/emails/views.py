"""
Email tracking views.
Handles open tracking, click tracking, and unsubscribe.
"""

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

from .models import EmailLog, EmailTemplate

logger = logging.getLogger(__name__)


# 1x1 transparent GIF pixel
TRACKING_PIXEL = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
    b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)


@method_decorator(csrf_exempt, name='dispatch')
class TrackOpenView(View):
    """
    Track email open via tracking pixel.
    Returns a 1x1 transparent GIF.
    """
    
    def get(self, request, tracking_id):
        try:
            email_log = EmailLog.objects.get(tracking_id=tracking_id)
            
            if not email_log.opened:
                email_log.opened = True
                email_log.opened_at = timezone.now()
                email_log.save()
                logger.info(f"Email opened: {email_log.recipient} - {email_log.subject}")
        
        except EmailLog.DoesNotExist:
            logger.warning(f"Tracking ID not found: {tracking_id}")
        
        # Return transparent pixel
        return HttpResponse(TRACKING_PIXEL, content_type='image/gif')


@method_decorator(csrf_exempt, name='dispatch')
class TrackClickView(View):
    """
    Track email link click and redirect to destination.
    """
    
    def get(self, request, tracking_id):
        destination = request.GET.get('url', '/')
        
        try:
            email_log = EmailLog.objects.get(tracking_id=tracking_id)
            
            if not email_log.clicked:
                email_log.clicked = True
                email_log.clicked_at = timezone.now()
                email_log.save()
                logger.info(f"Email link clicked: {email_log.recipient} - {email_log.subject}")
        
        except EmailLog.DoesNotExist:
            logger.warning(f"Tracking ID not found: {tracking_id}")
        
        return HttpResponseRedirect(destination)


class UnsubscribeView(View):
    """
    Handle email unsubscribe requests.
    """
    
    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        from apps.profiles.models import UserProfile
        
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            
            # Update profile to disable alerts
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.email_alerts_enabled = False
            profile.save()
            
            logger.info(f"User {user.email} unsubscribed from emails")
            
            return HttpResponse(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Unsubscribed - USAM Career</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .container { max-width: 500px; margin: 0 auto; }
                        h1 { color: #2563eb; }
                        p { color: #666; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>You've been unsubscribed</h1>
                        <p>You will no longer receive email alerts from USAM Career.</p>
                        <p>You can re-enable notifications in your account settings.</p>
                    </div>
                </body>
                </html>
                """,
                content_type='text/html'
            )
        
        except User.DoesNotExist:
            return HttpResponse("User not found", status=404)


class EmailPreviewView(View):
    """
    Preview email template (admin only).
    """
    
    def get(self, request, template_id):
        from django.contrib.admin.views.decorators import staff_member_required
        from django.utils.decorators import method_decorator
        
        # Check if user is staff
        if not request.user.is_staff:
            return HttpResponse("Unauthorized", status=403)
        
        template = get_object_or_404(EmailTemplate, id=template_id)
        
        # Sample context for preview
        context = {
            'user': request.user,
            'site_url': request.build_absolute_uri('/'),
            'unsubscribe_url': '#unsubscribe',
            'jobs': [
                {'title': 'Software Engineer', 'company': 'Tech Corp', 'location': 'Cairo, Egypt'},
                {'title': 'Product Manager', 'company': 'Startup Inc', 'location': 'Remote'},
            ],
            'total_jobs': 2,
            'stats': {
                'new_jobs': 150,
                'total_companies': 50,
            }
        }
        
        from django.template import Template, Context
        html_content = Template(template.html_body).render(Context(context))
        
        return HttpResponse(html_content, content_type='text/html')
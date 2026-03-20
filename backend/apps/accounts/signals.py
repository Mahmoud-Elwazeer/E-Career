import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


@receiver(post_save, sender="accounts.User")
def on_user_created(sender, instance, created, **kwargs):
    """Send a welcome email when a new user registers."""
    if not created:
        return
    try:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        html_message = render_to_string(
            "emails/welcome.html",
            {"user": instance, "frontend_url": frontend_url},
        )
        send_mail(
            subject="Welcome to USAM Career Compass!",
            message=f"Hi {instance.first_name}, welcome to USAM Career Compass! Start exploring jobs at {frontend_url}/app/jobs",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send welcome email to %s", instance.email)

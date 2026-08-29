"""Celery tasks for Rashid proactive coaching."""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


@shared_task(name='apps.rashid.tasks.check_all_user_triggers')
def check_all_user_triggers():
    """Check all active users for proactive coaching triggers."""
    from .proactive_service import proactive_rashid_service

    User = get_user_model()
    active_users = User.objects.filter(is_active=True).values_list('id', flat=True)

    sent = 0
    for user_id in active_users:
        try:
            triggers = proactive_rashid_service.check_user_triggers(user_id)
            for trigger in triggers:
                proactive_rashid_service.create_notification_record(
                    user_id=user_id,
                    trigger_type=trigger['type'],
                    message=trigger['message'],
                    context=trigger['context'],
                )
                sent += 1
        except Exception:
            logger.exception("Error checking triggers for user %s", user_id)

    logger.info("Proactive Rashid: sent %d notifications", sent)
    return sent

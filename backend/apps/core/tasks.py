"""
Celery tasks for Core app - GDPR and maintenance tasks.
"""

import logging
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from celery import shared_task

from .gdpr_service import GDPRService

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def generate_gdpr_export(self, user_id):
    """
    Generate GDPR data export for a user.

    Creates a JSON file with all user data and sends email notification.
    Auto-deletes the file after 7 days.

    Args:
        user_id: UUID of the user
    """
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"Starting GDPR export for user {user.email}")

        # Generate export using GDPR service
        service = GDPRService(user)
        export_data = service.export_user_data()

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gdpr_export_{user_id}_{timestamp}.json"
        filepath = settings.MEDIA_ROOT / 'gdpr_exports' / filename

        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"GDPR export saved to {filepath}")

        # Send email notification
        download_url = f"{settings.FRONTEND_URL}/api/v1/core/gdpr/export/download/?file={filename}"

        send_mail(
            subject='Your Data Export is Ready',
            message=f'Your GDPR data export is ready for download.\n\nDownload link: {download_url}\n\nThis link will expire in 7 days.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"GDPR export notification sent to {user.email}")

        # Schedule deletion after 7 days
        delete_gdpr_export_file.apply_async(
            args=[str(filepath)],
            eta=timezone.now() + timedelta(days=7)
        )

        return {'success': True, 'file': filename, 'size': filepath.stat().st_size}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for GDPR export")
        return {'success': False, 'error': 'User not found'}

    except Exception as e:
        logger.error(f"GDPR export failed for user {user_id}: {str(e)}")
        # Retry up to 3 times with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def delete_gdpr_export_file(filepath):
    """
    Delete a GDPR export file after expiration.

    Args:
        filepath: Path to the export file
    """
    try:
        import os
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted expired GDPR export file: {filepath}")
            return {'success': True}
        else:
            logger.warning(f"GDPR export file not found: {filepath}")
            return {'success': False, 'error': 'File not found'}
    except Exception as e:
        logger.error(f"Failed to delete GDPR export file {filepath}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=1)
def execute_gdpr_deletion(self, user_id, confirmation_token):
    """
    Execute GDPR data deletion after cooling-off period.

    This task is scheduled 72 hours after deletion request.

    Args:
        user_id: UUID of the user
        confirmation_token: Confirmation token to verify the request
    """
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"Starting GDPR deletion for user {user.email}")

        # Execute deletion using GDPR service
        service = GDPRService(user)
        result = service.delete_user_data(confirmation_token)

        if result['success']:
            logger.info(f"GDPR deletion completed for user {user_id}. Deleted: {result.get('deleted', {})}")

            # Send confirmation email to the anonymized email (if possible)
            try:
                send_mail(
                    subject='Your Account Has Been Deleted',
                    message='Your account and all associated data have been permanently deleted as per your request.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],  # Will be anonymized email
                    fail_silently=True,  # Don't fail if email can't be sent
                )
            except Exception as email_error:
                logger.warning(f"Could not send deletion confirmation email: {email_error}")

            return result
        else:
            logger.error(f"GDPR deletion failed for user {user_id}: {result.get('error')}")
            return result

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for GDPR deletion")
        return {'success': False, 'error': 'User not found'}

    except Exception as e:
        logger.error(f"GDPR deletion failed for user {user_id}: {str(e)}")
        # Don't retry deletion - it's too risky
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_gdpr_exports():
    """
    Cleanup GDPR export files older than 7 days.

    This is a safety net in case the scheduled deletion tasks fail.
    Runs daily.
    """
    try:
        import os
        from pathlib import Path

        exports_dir = settings.MEDIA_ROOT / 'gdpr_exports'
        if not exports_dir.exists():
            return {'success': True, 'deleted': 0}

        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count = 0

        for filepath in exports_dir.glob('gdpr_export_*.json'):
            # Check file modification time
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff_date:
                try:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"Cleaned up old GDPR export: {filepath.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {filepath.name}: {str(e)}")

        logger.info(f"GDPR export cleanup completed. Deleted {deleted_count} files.")
        return {'success': True, 'deleted': deleted_count}

    except Exception as e:
        logger.error(f"GDPR export cleanup failed: {str(e)}")
        return {'success': False, 'error': str(e)}

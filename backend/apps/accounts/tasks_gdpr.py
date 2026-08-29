"""
GDPR Compliance Celery Tasks
"""
import json
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_data_export(request_id):
    """
    Generate GDPR data export for user.

    Collects all user data from across the platform and packages as JSON.
    """
    from .models_gdpr import DataExportRequest
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        export_request = DataExportRequest.objects.get(id=request_id)
        export_request.status = 'processing'
        export_request.save()

        user = export_request.user

        # Collect all user data
        data = {
            'export_date': timezone.now().isoformat(),
            'user_id': str(user.id),
            'account': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            },
        }

        # Career profile
        if hasattr(user, 'career_profile'):
            profile = user.career_profile
            data['career_profile'] = {
                'career_stage': getattr(profile, 'career_stage', None),
                'cv_parsed_data': getattr(profile, 'cv_parsed_data', {}),
                'skills': [
                    s.skill.name for s in profile.career_user_skills.all()
                ] if hasattr(profile, 'career_user_skills') else [],
            }

        # Applications
        if hasattr(user, 'applications'):
            data['applications'] = [
                {
                    'job_title': app.job.title,
                    'company': app.job.company.name,
                    'applied_at': app.applied_at.isoformat(),
                    'status': app.status,
                }
                for app in user.applications.all()
            ]

        # Saved jobs
        if hasattr(user, 'saved_jobs'):
            data['saved_jobs'] = [
                {
                    'job_title': job.title,
                    'company': job.company.name,
                    'saved_at': user.saved_jobs.through.objects.get(
                        user=user, job=job
                    ).saved_at.isoformat() if hasattr(user.saved_jobs.through.objects.get(user=user, job=job), 'saved_at') else None,
                }
                for job in user.saved_jobs.all()
            ]

        # Rashid conversations
        if hasattr(user, 'rashid_conversations'):
            data['rashid_conversations'] = [
                {
                    'title': conv.title,
                    'created_at': conv.created_at.isoformat(),
                    'message_count': conv.messages.count() if hasattr(conv, 'messages') else 0,
                }
                for conv in user.rashid_conversations.all()
            ]

        # Interview sessions
        if hasattr(user, 'interview_sessions'):
            data['interview_sessions'] = [
                {
                    'type': session.interview_type,
                    'target_role': session.target_role,
                    'started_at': session.started_at.isoformat(),
                    'status': session.status,
                    'overall_score': session.overall_score,
                }
                for session in user.interview_sessions.all()
            ]

        # Cover letters
        if hasattr(user, 'coverletter_set'):
            data['cover_letters'] = [
                {
                    'job_title': cl.job.title,
                    'created_at': cl.created_at.isoformat(),
                    'tone': cl.tone,
                    'word_count': cl.word_count,
                }
                for cl in user.coverletter_set.all()
            ]

        # Notifications
        if hasattr(user, 'notifications'):
            data['notifications'] = [
                {
                    'title': notif.title,
                    'message': notif.message,
                    'created_at': notif.created_at.isoformat(),
                    'read': notif.is_read,
                }
                for notif in user.notifications.all()[:100]  # Limit to latest 100
            ]

        # Convert to JSON
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        # Save to file
        filename = f"data_export_{user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = f"gdpr_exports/{filename}"

        # Save using Django storage (works with S3 or local)
        saved_path = default_storage.save(file_path, ContentFile(json_content.encode('utf-8')))

        # Update request
        export_request.status = 'completed'
        export_request.file_path = saved_path
        export_request.file_size_bytes = len(json_content.encode('utf-8'))
        export_request.completed_at = timezone.now()
        export_request.expires_at = timezone.now() + timedelta(days=30)
        export_request.save()

        logger.info(f"Data export completed for user {user.id}: {saved_path}")

    except Exception as e:
        logger.error(f"Data export failed for request {request_id}: {e}")
        try:
            export_request.status = 'failed'
            export_request.error_message = str(e)
            export_request.save()
        except:
            pass


@shared_task
def process_account_deletion(deletion_request_id):
    """
    Anonymize user data after 30-day grace period.

    GDPR requires PII to be removed, but we keep anonymized records
    for analytics (e.g., application counts, but not identifiable info).
    """
    from .models_gdpr import AccountDeletionRequest
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        deletion_request = AccountDeletionRequest.objects.get(id=deletion_request_id)

        if deletion_request.status != 'pending':
            logger.warning(f"Deletion request {deletion_request_id} not pending, skipping")
            return

        deletion_request.status = 'processing'
        deletion_request.save()

        user = deletion_request.user

        # Anonymize PII
        user.email = f"deleted_{user.id}@anonymized.local"
        user.first_name = ""
        user.last_name = ""
        user.is_active = False
        user.save()

        # Clear profile data
        if hasattr(user, 'career_profile'):
            profile = user.career_profile
            profile.cv_parsed_data = {}
            profile.save()

        # Delete uploaded files (CV, etc.)
        # This would need to iterate through file fields

        # Delete Rashid conversation content (keep counts for analytics)
        if hasattr(user, 'rashid_conversations'):
            for conv in user.rashid_conversations.all():
                if hasattr(conv, 'messages'):
                    conv.messages.all().delete()

        # Mark deletion complete
        deletion_request.status = 'completed'
        deletion_request.completed_at = timezone.now()
        deletion_request.save()

        logger.info(f"Account deletion completed for user {user.id}")

    except Exception as e:
        logger.error(f"Account deletion failed for request {deletion_request_id}: {e}")
        try:
            deletion_request.status = 'failed'
            deletion_request.error_message = str(e)
            deletion_request.save()
        except:
            pass


@shared_task
def cleanup_expired_exports():
    """
    Delete expired data export files (runs daily via Celery Beat).

    GDPR exports are kept for 30 days, then automatically deleted.
    """
    from .models_gdpr import DataExportRequest

    now = timezone.now()
    expired = DataExportRequest.objects.filter(
        status='completed',
        expires_at__lte=now
    )

    deleted_count = 0
    for export_request in expired:
        try:
            # Delete file
            if export_request.file_path and default_storage.exists(export_request.file_path):
                default_storage.delete(export_request.file_path)

            # Mark as expired
            export_request.status = 'expired'
            export_request.file_path = ''
            export_request.save()

            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete expired export {export_request.id}: {e}")

    logger.info(f"Cleaned up {deleted_count} expired data exports")

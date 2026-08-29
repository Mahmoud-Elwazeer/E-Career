"""
Celery tasks for email campaigns and notifications.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

from .models import EmailAccount, EmailLog
from .service import email_service

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_welcome_email(user_id):
    """
    Send welcome email to a new user.
    
    Args:
        user_id: User ID to send welcome email to
    """
    try:
        user = User.objects.get(id=user_id)
        success, tracking_id = email_service.send_welcome_email(user)
        
        if success:
            logger.info(f"Welcome email sent to {user.email}")
        else:
            logger.error(f"Failed to send welcome email to {user.email}")
        
        return success
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for welcome email")
        return False
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        return False


@shared_task
def send_job_alerts():
    """
    Send job alerts to users with matching preferences.
    Runs hourly to check for new job matches.
    """
    from apps.jobs.models import Job
    from apps.profiles.models import UserProfile
    
    logger.info("Starting job alert task")
    
    # Get users with alerts enabled
    profiles = UserProfile.objects.filter(
        email_alerts=True
    ).select_related('user')
    
    if not profiles.exists():
        logger.info("No users with job alerts enabled")
        return
    
    # Get recent jobs (last 24 hours)
    recent_jobs = Job.objects.filter(
        status='active',
        posted_at__gte=timezone.now() - timedelta(hours=24)
    ).select_related('company', 'source')
    
    if not recent_jobs.exists():
        logger.info("No new jobs in last 24 hours")
        return
    
    alerts_sent = 0
    
    for profile in profiles:
        try:
            user = profile.user
            
            # Check if user already received alert recently
            last_alert = EmailLog.objects.filter(
                user=user,
                template__template_type='job_alert'
            ).first()
            
            if last_alert:
                hours_since_last = (timezone.now() - last_alert.sent_at).total_seconds() / 3600
                
                # Respect alert frequency
                frequency = getattr(profile, 'alert_frequency', 'daily')
                if frequency == 'daily' and hours_since_last < 24:
                    continue
                elif frequency == 'weekly' and hours_since_last < 168:
                    continue
            
            # Filter jobs by user preferences
            matching_jobs = []
            
            for job in recent_jobs[:50]:  # Limit to 50 jobs per check
                # Check location match
                if profile.preferred_locations:
                    job_location = job.location.lower() if job.location else ''
                    preferred = [loc.lower() for loc in profile.preferred_locations]
                    if not any(loc in job_location for loc in preferred):
                        continue
                
                # Check job type match
                if profile.preferred_type and job.employment_type:
                    if job.employment_type not in profile.preferred_type:
                        continue
                
                # Add to matches
                matching_jobs.append({
                    'id': job.id,
                    'title': job.title,
                    'company': job.company.name if job.company else 'Unknown',
                    'location': job.location,
                    'job_type': job.employment_type,
                    'salary_range': f"{job.salary_min or 0} - {job.salary_max or 0} {job.salary_currency}" if job.salary_min or job.salary_max else 'Not specified',
                    'url': f"/jobs/{job.id}/"
                })
            
            # Send alert if matches found
            if matching_jobs:
                success, _ = email_service.send_job_alert(user, matching_jobs[:10])  # Max 10 jobs per alert
                if success:
                    alerts_sent += 1
        
        except Exception as e:
            logger.error(f"Error sending job alert to user {profile.user_id}: {e}")
    
    logger.info(f"Job alerts sent: {alerts_sent}")


@shared_task
def send_weekly_digest():
    """
    Send weekly digest to subscribed users.
    Includes platform stats and personalized recommendations.
    """
    from apps.jobs.models import Job
    from apps.profiles.models import UserProfile
    
    logger.info("Starting weekly digest task")
    
    # Get users with weekly digest enabled
    profiles = UserProfile.objects.filter(
        email_alerts=True,
        alert_frequency='weekly'
    ).select_related('user')
    
    if not profiles.exists():
        logger.info("No users with weekly digest enabled")
        return
    
    # Calculate weekly stats
    week_start = timezone.now() - timedelta(days=7)
    
    stats = {
        'week_start': week_start.strftime('%Y-%m-%d'),
        'week_end': timezone.now().strftime('%Y-%m-%d'),
        'new_jobs': Job.objects.filter(
            status='active',
            posted_at__gte=week_start
        ).count(),
        'total_companies': Job.objects.filter(status='active').values('company').distinct().count(),
    }
    
    digests_sent = 0
    
    for profile in profiles:
        try:
            user = profile.user
            
            # Add user-specific stats
            user_stats = stats.copy()
            user_stats['saved_jobs'] = user.saved_jobs.count() if hasattr(user, 'saved_jobs') else 0
            user_stats['applications'] = user.applications.count() if hasattr(user, 'applications') else 0
            
            success, _ = email_service.send_weekly_digest(user, user_stats)
            if success:
                digests_sent += 1
        
        except Exception as e:
            logger.error(f"Error sending weekly digest to user {profile.user_id}: {e}")
    
    logger.info(f"Weekly digests sent: {digests_sent}")


@shared_task
def reset_email_account_counters():
    """
    Reset daily email counters for all accounts.
    Runs at midnight daily.
    """
    logger.info("Resetting email account counters")
    
    accounts = EmailAccount.objects.filter(is_active=True)
    for account in accounts:
        account.today_sent = 0
        account.last_reset = timezone.now().date()
        account.save()
    
    logger.info(f"Reset counters for {accounts.count()} email accounts")


@shared_task
def send_employer_application_notification(application_id):
    """
    Send notification to employer when new application received.
    Also creates a UserNotification record and triggers delivery.

    Args:
        application_id: Application ID
    """
    try:
        from apps.employers.models import JobApplication

        application = JobApplication.objects.select_related('job', 'job__employer').get(id=application_id)

        # Get employer
        employer = application.job.employer

        if not employer or not employer.user.email:
            logger.warning(f"No employer email for application {application_id}")
            return False

        context = {
            'job_title': application.job.title,
            'applicant_name': application.applicant.get_full_name() if hasattr(application, 'applicant') else 'Applicant',
            'application_date': application.applied_at.strftime('%Y-%m-%d'),
            'application_url': f"/employer/applications/{application.id}/"
        }

        success, _ = email_service.send_template_email(
            user=employer.user,
            template_type='employer_application',
            context_data=context
        )

        # Also create a UserNotification for the employer (notification delivery system)
        from apps.notifications.service import create_and_deliver_notification
        applicant_name = context['applicant_name']
        create_and_deliver_notification(
            user=employer.user,
            notification_type='application_update',
            title=f"New application for {application.job.title}",
            message=f"{applicant_name} applied for {application.job.title} on {context['application_date']}.",
            related_id=str(application.id),
            related_type='application',
            related_url=context['application_url'],
            priority='high',
        )

        return success

    except Exception as e:
        logger.error(f"Error sending employer application notification: {e}")
        return False


@shared_task
def send_dead_url_notification(employer_id, job_id, url):
    """
    Send notification to employer when apply URL is dead.
    
    Args:
        employer_id: Employer ID
        job_id: Job ID
        url: The dead URL
    """
    try:
        from apps.employers.models import Employer
        from apps.jobs.models import Job
        
        employer = Employer.objects.select_related('user').get(id=employer_id)
        job = Job.objects.get(id=job_id)
        
        context = {
            'job_title': job.title,
            'job_id': job.id,
            'dead_url': url,
            'job_edit_url': f"/employer/jobs/{job.id}/edit/"
        }
        
        success, _ = email_service.send_template_email(
            user=employer.user,
            template_type='employer_url_dead',
            context_data=context
        )
        
        return success
    
    except Exception as e:
        logger.error(f"Error sending dead URL notification: {e}")
        return False


@shared_task
def send_re_engagement_emails():
    """
    Send re-engagement emails to inactive users.
    Runs weekly to bring back dormant users.
    """
    from apps.profiles.models import UserProfile
    
    logger.info("Starting re-engagement email task")
    
    # Find users inactive for 30+ days
    inactive_threshold = timezone.now() - timedelta(days=30)
    
    profiles = UserProfile.objects.filter(
        user__last_login__lt=inactive_threshold
    ).select_related('user')
    
    emails_sent = 0
    
    for profile in profiles:
        try:
            user = profile.user
            
            # Check if re-engagement email sent recently
            last_re_engagement = EmailLog.objects.filter(
                user=user,
                template__template_type='re_engagement'
            ).first()
            
            if last_re_engagement and (timezone.now() - last_re_engagement.sent_at).days < 30:
                continue
            
            context = {
                'days_inactive': (timezone.now() - user.last_login).days if user.last_login else 30,
                'login_url': '/login/'
            }
            
            success, _ = email_service.send_template_email(
                user=user,
                template_type='re_engagement',
                context_data=context
            )
            
            if success:
                emails_sent += 1
        
        except Exception as e:
            logger.error(f"Error sending re-engagement email: {e}")
    
    logger.info(f"Re-engagement emails sent: {emails_sent}")

@shared_task
def send_weekly_career_digest():
    """
    F6: Send weekly career digest with matching jobs, progress, tips.
    Runs every Sunday at 9 AM.
    """
    logger.info("Starting weekly career digest task (F6)")
    
    # Get active job seekers
    users = User.objects.filter(
        role__in=['jobseeker', 'user'],
        is_active=True
    ).select_related('career_profile')
    
    digests_sent = 0
    week_start = timezone.now() - timedelta(days=7)
    
    for user in users:
        try:
            # Skip if no career profile
            if not hasattr(user, 'career_profile'):
                continue
            
            # Fetch new matching jobs this week
            from apps.vectors.matching_service import matching_service
            matching_jobs = matching_service.find_matching_jobs(user, limit=5)
            
            # Career progress stats
            progress_data = {
                'applications_this_week': user.applications.filter(applied_at__gte=week_start).count() if hasattr(user, 'applications') else 0,
                'interviews_completed': user.interview_sessions.filter(completed_at__gte=week_start).count() if hasattr(user, 'interview_sessions') else 0,
                'profile_completeness': user.career_profile.completeness_score if hasattr(user.career_profile, 'completeness_score') else 50,
            }
            
            # AI-generated skill tips
            from apps.intelligence.career_ai import career_ai_service as bedrock_service
            user_skills = [s.skill.name for s in user.career_profile.career_user_skills.all()[:10]] if hasattr(user.career_profile, 'career_user_skills') else []
            tip_prompt = f"Give 1 short career tip (max 2 sentences) for someone with skills: {', '.join(user_skills) or 'entry-level'}."
            try:
                tip_result = bedrock_service.invoke_model(prompt=tip_prompt, max_tokens=100, temperature=0.7)
                tip = tip_result if isinstance(tip_result, str) else "Keep learning and applying to jobs regularly!"
            except Exception:
                tip = "Keep learning and applying to jobs regularly!"
            
            # Send digest
            context = {
                'user_name': user.get_full_name() or user.email.split('@')[0],
                'matching_jobs': matching_jobs[:5],
                'progress': progress_data,
                'skill_tip': tip,
                'platform_url': 'https://usam.com'
            }
            
            success, _ = email_service.send_template_email(
                user=user,
                template_type='weekly_career_digest',
                context_data=context
            )
            
            if success:
                digests_sent += 1
        
        except Exception as e:
            logger.error(f"Error sending career digest to {user.id}: {e}")
    
    logger.info(f"Weekly career digests sent: {digests_sent}")
    return digests_sent

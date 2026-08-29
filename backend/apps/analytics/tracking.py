"""
Analytics Tracking Service - Phase H

Track user behavior, conversions, and generate insights.
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from apps.events.emitter import emit
from apps.events.types import *

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """
    Central analytics tracking service.
    """

    def track_page_view(self, user, page_name: str, metadata: dict = None):
        """Track page views"""
        emit(
            event_type='page_view',
            category='user',
            user=user,
            target_type='page',
            target_id=page_name,
            data=metadata or {},
            request=None
        )

    def track_job_view(self, user, job_id: str, source: str = 'search'):
        """Track job detail views"""
        emit(
            event_type=JOB_VIEWED,
            category='job',
            user=user,
            target_type='job',
            target_id=job_id,
            data={'source': source},
            request=None
        )

    def track_job_application(self, user, job_id: str, method: str = 'direct'):
        """Track job applications"""
        emit(
            event_type=JOB_APPLIED,
            category='job',
            user=user,
            target_type='job',
            target_id=job_id,
            data={'method': method},
            request=None
        )

    def track_search(self, user, query: str, filters: dict, results_count: int):
        """Track search queries"""
        emit(
            event_type=JOB_SEARCH_PERFORMED,
            category='search',
            user=user,
            target_type='search',
            target_id=query,
            data={
                'filters': filters,
                'results_count': results_count
            },
            request=None
        )

    def track_feature_usage(self, user, feature_name: str, action: str):
        """Track feature usage (Rashid, Resume Builder, etc.)"""
        emit(
            event_type='feature_used',
            category='user',
            user=user,
            target_type='feature',
            target_id=feature_name,
            data={'action': action},
            request=None
        )

    def track_conversion(self, user, conversion_type: str, value: float = 0):
        """Track conversions (signups, applications, etc.)"""
        emit(
            event_type='conversion',
            category='user',
            user=user,
            target_type='conversion',
            target_id=conversion_type,
            data={'value': value},
            request=None
        )

    def get_user_journey(self, user_id: str, days: int = 30) -> list:
        """
        Get user's journey over time.

        Returns chronological list of key events.
        """
        from apps.events.models import EventLog

        since = timezone.now() - timedelta(days=days)

        events = EventLog.objects.filter(
            user_id=user_id,
            created_at__gte=since
        ).order_by('created_at').values(
            'event_type', 'target_type', 'target_id', 'created_at', 'data'
        )

        return list(events)

    def get_conversion_funnel(self, days: int = 30) -> dict:
        """
        Calculate conversion funnel metrics.

        Returns:
            {
                'visitors': 1000,
                'signups': 200,
                'profile_completed': 150,
                'first_application': 100,
                'conversion_rate': 10.0
            }
        """
        from apps.events.models import EventLog
        from apps.accounts.models import User
        from apps.employers.models import JobApplication

        since = timezone.now() - timedelta(days=days)

        # Get unique visitors
        visitors = EventLog.objects.filter(
            event_type='page_view',
            created_at__gte=since
        ).values('user_id').distinct().count()

        # New signups
        signups = User.objects.filter(
            date_joined__gte=since
        ).count()

        # Profile completed
        profile_completed = User.objects.filter(
            date_joined__gte=since,
            career_profile__isnull=False
        ).count()

        # First application
        first_applications = JobApplication.objects.filter(
            applied_at__gte=since
        ).values('user_id').distinct().count()

        return {
            'visitors': visitors,
            'signups': signups,
            'profile_completed': profile_completed,
            'first_application': first_applications,
            'signup_rate': round((signups / visitors * 100) if visitors else 0, 2),
            'profile_completion_rate': round((profile_completed / signups * 100) if signups else 0, 2),
            'application_conversion_rate': round((first_applications / signups * 100) if signups else 0, 2)
        }

    def get_feature_usage_stats(self, days: int = 30) -> dict:
        """Get feature usage statistics"""
        from apps.events.models import EventLog

        since = timezone.now() - timedelta(days=days)

        feature_stats = EventLog.objects.filter(
            event_type='feature_used',
            created_at__gte=since
        ).values('target_id').annotate(
            usage_count=Count('id'),
            unique_users=Count('user_id', distinct=True)
        ).order_by('-usage_count')

        return {
            'features': list(feature_stats),
            'total_feature_interactions': sum(f['usage_count'] for f in feature_stats)
        }

    def get_retention_cohorts(self) -> list:
        """
        Calculate user retention by signup cohort.

        Returns list of cohorts with retention rates.
        """
        from apps.accounts.models import User
        from apps.events.models import EventLog

        cohorts = []

        # Get cohorts by month for last 6 months
        for months_ago in range(6):
            cohort_start = timezone.now() - timedelta(days=30 * (months_ago + 1))
            cohort_end = timezone.now() - timedelta(days=30 * months_ago)

            # Users who signed up in this cohort
            cohort_users = User.objects.filter(
                date_joined__gte=cohort_start,
                date_joined__lt=cohort_end
            ).values_list('id', flat=True)

            cohort_size = len(cohort_users)

            if cohort_size == 0:
                continue

            # Check retention at 7, 14, 30 days
            retention = {}
            for day in [7, 14, 30]:
                check_date = cohort_start + timedelta(days=day)
                if check_date > timezone.now():
                    retention[f'day_{day}'] = None
                    continue

                active_users = EventLog.objects.filter(
                    user_id__in=cohort_users,
                    created_at__date=check_date.date()
                ).values('user_id').distinct().count()

                retention[f'day_{day}'] = round((active_users / cohort_size * 100), 2)

            cohorts.append({
                'cohort_month': cohort_start.strftime('%Y-%m'),
                'cohort_size': cohort_size,
                'retention': retention
            })

        return cohorts

    def get_job_market_insights(self, days: int = 30) -> dict:
        """
        Generate job market insights.

        Returns:
            {
                'top_skills': [...],
                'trending_roles': [...],
                'avg_salary_by_level': {...},
                'remote_job_percentage': 45.5
            }
        """
        from apps.jobs.models import Job
        from apps.skills.models import Skill

        since = timezone.now() - timedelta(days=days)

        active_jobs = Job.objects.filter(
            status='active',
            posted_at__gte=since.date()
        )

        # Top skills in demand
        top_skills = Skill.objects.filter(
            jobs__in=active_jobs
        ).annotate(
            job_count=Count('jobs')
        ).order_by('-job_count')[:10]

        # Remote job percentage
        total_jobs = active_jobs.count()
        remote_jobs = active_jobs.filter(work_arrangement='remote').count()
        remote_percentage = (remote_jobs / total_jobs * 100) if total_jobs else 0

        # Average salary by experience level
        salary_by_level = active_jobs.filter(
            salary_max__gt=0
        ).values('experience_level').annotate(
            avg_salary=Avg('salary_max'),
            job_count=Count('id')
        ).order_by('-avg_salary')

        return {
            'top_skills': [
                {'skill': skill.name, 'demand': skill.job_count}
                for skill in top_skills
            ],
            'remote_job_percentage': round(remote_percentage, 1),
            'avg_salary_by_level': list(salary_by_level),
            'total_active_jobs': total_jobs
        }


# Singleton instance
analytics_tracker = AnalyticsTracker()

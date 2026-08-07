"""
Job Matching for Email Alerts

This module provides functions to match jobs with user preferences
for email alert generation.
"""

from django.utils import timezone
from datetime import timedelta
import logging

from apps.jobs.models import Job

logger = logging.getLogger(__name__)


def get_matching_jobs_for_user(user, since_hours=24, limit=5):
    """
    Find jobs posted in last N hours that match user's alert criteria.
    
    Args:
        user: User instance with profile preferences
        since_hours: Number of hours to look back for new jobs
        limit: Maximum number of jobs to return
        
    Returns:
        List of matching jobs with match scores
    """
    from apps.profiles.models import UserProfile
    
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return []
    
    # Get jobs posted in the last N hours
    since = timezone.now() - timedelta(hours=since_hours)
    jobs = Job.objects.filter(
        is_active=True,
        posted_at__gte=since
    ).select_related('company', 'source')
    
    if not jobs.exists():
        return []
    
    matching_jobs = []
    
    # Get user preferences
    preferred_locations = getattr(profile, 'preferred_locations', []) or []
    preferred_type = getattr(profile, 'preferred_type', None)
    saved_searches = getattr(profile, 'saved_searches', []) or []
    
    for job in jobs:
        score = 0
        
        # Location match
        if preferred_locations:
            job_location = job.location.lower() if job.location else ''
            for loc in preferred_locations:
                if loc.lower() in job_location:
                    score += 30
                    break
        
        # Job type match
        if preferred_type and job.employment_type:
            if job.employment_type in preferred_type:
                score += 25
        
        # Skills match (if available)
        if profile.skills:
            job_skills = list(job.tags.values_list('name', flat=True)) if job.tags.exists() else []
            for skill in profile.skills:
                if any(skill.lower() in js.lower() for js in job_skills):
                    score += 15
        
        # Salary match (if user has salary preference)
        if profile.min_salary and job.salary_min:
            if job.salary_min >= profile.min_salary:
                score += 20
        
        # Add to matches if score is positive
        if score > 0:
            matching_jobs.append({
                'id': job.id,
                'uuid': str(job.uuid),
                'title': job.title,
                'company': job.company.name if job.company else 'Unknown',
                'company_logo': job.company.logo.url if job.company and job.company.logo else None,
                'location': job.location,
                'country': job.country,
                'employment_type': job.employment_type,
                'work_arrangement': job.work_arrangement,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'salary_currency': job.salary_currency,
                'posted_at': job.posted_at,
                'match_score': min(score, 100),
                'url': f"/jobs/{job.id}/",
            })
    
    # Sort by match score and limit
    matching_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    return matching_jobs[:limit]


def get_matching_jobs_for_alert(user, limit=5):
    """
    Get matching jobs for a job alert email.
    
    Args:
        user: User instance
        limit: Maximum number of jobs to return
        
    Returns:
        List of matching jobs with match scores
    """
    return get_matching_jobs_for_user(user, since_hours=24, limit=limit)


def get_weekly_job_summary(user):
    """
    Get a summary of jobs posted this week for weekly digest.
    
    Args:
        user: User instance
        
    Returns:
        Dict with weekly stats and top jobs
    """
    from apps.profiles.models import UserProfile
    
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return {'jobs': [], 'stats': {}}
    
    week_start = timezone.now() - timedelta(days=7)
    
    # Get all jobs posted this week
    weekly_jobs = Job.objects.filter(
        is_active=True,
        posted_at__gte=week_start
    ).select_related('company')
    
    # Get matching jobs for user
    matching_jobs = get_matching_jobs_for_user(user, since_hours=168, limit=10)
    
    stats = {
        'week_start': week_start.strftime('%Y-%m-%d'),
        'total_jobs_this_week': weekly_jobs.count(),
        'matching_jobs': len(matching_jobs),
        'new_companies': weekly_jobs.values('company').distinct().count(),
    }
    
    return {
        'jobs': matching_jobs,
        'stats': stats,
    }
"""
Custom admin views for scraper management.
Phase 3C: Admin Dashboard Extensions
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
try:
    from unfold.views import UnfoldDashboardView
except ImportError:
    pass


@staff_member_required
def scraper_dashboard(request):
    """
    Scraper management dashboard.
    Shows scraper health, job stats, and source status.
    """
    from apps.jobs.models import Job, Source
    from apps.core.models import PipelineHealth
    
    # Get sources with stats
    sources = Source.objects.annotate(
        total_jobs=Count('jobs'),
        active_jobs=Count('jobs', filter=Q(jobs__status='active')),
        jobs_today=Count('jobs', filter=Q(jobs__created_at__date=timezone.now().date()))
    )
    
    # Get recent scrape stats
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    
    scrape_stats = {
        'total_jobs': Job.objects.count(),
        'active_jobs': Job.objects.filter(status='active').count(),
        'jobs_this_week': Job.objects.filter(posted_at__gte=week_ago).count(),
        'scam_jobs_blocked': Job.objects.filter(is_legitimate=False).count(),
    }
    
    # Scraper health
    scraper_health = []
    for source in sources:
        last_job = source.jobs.order_by('-created_at').first()
        
        status = 'healthy'
        if not last_job:
            status = 'no_data'
        elif last_job.created_at < timezone.now() - timedelta(days=2):
            status = 'stale'
        
        scraper_health.append({
            'source': source,
            'status': status,
            'last_scrape': last_job.created_at if last_job else None
        })
    
    # Pipeline health
    pipeline_health = PipelineHealth.objects.all().order_by('task_name')
    
    context = {
        'sources': sources,
        'scrape_stats': scrape_stats,
        'scraper_health': scraper_health,
        'pipeline_health': pipeline_health,
        'title': 'Scraper Management Dashboard',
    }
    
    return render(request, 'admin/scraper_dashboard.html', context)


@staff_member_required
def health_monitor(request):
    """
    System health monitoring dashboard.
    Checks database, Redis, Celery, and other services.
    """
    from django.db import connection
    from django.core.cache import cache
    import redis
    from celery import current_app
    
    checks = []
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks.append({
            'name': 'Database',
            'status': 'healthy',
            'message': 'PostgreSQL is responding',
            'icon': 'database'
        })
    except Exception as e:
        checks.append({
            'name': 'Database',
            'status': 'error',
            'message': str(e),
            'icon': 'database'
        })
    
    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks.append({
                'name': 'Redis',
                'status': 'healthy',
                'message': 'Redis is responding',
                'icon': 'storage'
            })
        else:
            raise Exception('Cache write/read failed')
    except Exception as e:
        checks.append({
            'name': 'Redis',
            'status': 'error',
            'message': str(e),
            'icon': 'storage'
        })
    
    # Celery check
    try:
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            worker_count = len(stats)
            checks.append({
                'name': 'Celery',
                'status': 'healthy',
                'message': f'{worker_count} workers active',
                'icon': 'schedule'
            })
        else:
            checks.append({
                'name': 'Celery',
                'status': 'warning',
                'message': 'No workers detected',
                'icon': 'schedule'
            })
    except Exception as e:
        checks.append({
            'name': 'Celery',
            'status': 'error',
            'message': str(e),
            'icon': 'schedule'
        })
    
    # Email accounts check
    try:
        from apps.emails.models import EmailAccount
        email_accounts = EmailAccount.objects.filter(is_active=True)
        available_accounts = [acc for acc in email_accounts if acc.today_sent < acc.daily_limit]
        
        if len(available_accounts) > 0:
            checks.append({
                'name': 'Email Accounts',
                'status': 'healthy',
                'message': f'{len(available_accounts)}/{len(email_accounts)} accounts available',
                'icon': 'email'
            })
        else:
            checks.append({
                'name': 'Email Accounts',
                'status': 'warning',
                'message': 'No email accounts available',
                'icon': 'email'
            })
    except Exception as e:
        checks.append({
            'name': 'Email Accounts',
            'status': 'warning',
            'message': 'Email system not configured',
            'icon': 'email'
        })
    
    # Overall status
    has_error = any(check['status'] == 'error' for check in checks)
    has_warning = any(check['status'] == 'warning' for check in checks)
    
    overall_status = 'healthy'
    if has_error:
        overall_status = 'error'
    elif has_warning:
        overall_status = 'warning'
    
    context = {
        'checks': checks,
        'overall_status': overall_status,
        'title': 'System Health Monitor',
    }
    
    return render(request, 'admin/health_monitor.html', context)
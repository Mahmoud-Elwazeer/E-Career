"""
Custom admin dashboard with analytics for django-unfold.
Phase 3C: Admin Dashboard Extensions
"""

from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


def dashboard_callback(request, context):
    """
    Custom dashboard data for admin homepage.
    Provides KPIs, charts, and progress indicators.
    """
    from apps.jobs.models import Job, Company
    from apps.accounts.models import User
    from apps.rashid.models import RashidConversation, RashidUsage
    from apps.emails.models import EmailLog
    from apps.employers.models import EmployerProfile, JobPosting
    from apps.analytics.models import JobView, JobClick
    
    # Calculate time ranges
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Job stats
    total_jobs = Job.objects.filter(status='active').count()
    jobs_this_week = Job.objects.filter(posted_at__gte=week_ago, status='active').count()
    jobs_this_month = Job.objects.filter(posted_at__gte=month_ago, status='active').count()
    pending_jobs = JobPosting.objects.filter(status='pending_review').count()
    
    # User stats
    total_users = User.objects.filter(is_active=True).count()
    users_this_week = User.objects.filter(date_joined__gte=week_ago).count()
    employer_pending = EmployerProfile.objects.filter(is_verified=False).count()
    
    # Rashid AI stats
    total_conversations = RashidConversation.objects.count()
    active_conversations = RashidConversation.objects.filter(is_active=True).count()
    conversations_this_week = RashidConversation.objects.filter(started_at__gte=week_ago).count()
    
    # Token usage this week
    token_usage = RashidUsage.objects.filter(date__gte=week_ago.date()).aggregate(
        total=Sum('tokens_used')
    )
    tokens_this_week = token_usage['total'] or 0
    
    # Email stats
    emails_sent_today = EmailLog.objects.filter(sent_at__date=today.date()).count()
    emails_sent_this_week = EmailLog.objects.filter(sent_at__gte=week_ago).count()
    
    # Email open rate
    email_stats = EmailLog.objects.filter(sent_at__gte=week_ago).aggregate(
        opened=Count('id', filter=Q(opened=True)),
        total=Count('id')
    )
    open_rate = 0
    if email_stats['total'] and email_stats['total'] > 0:
        open_rate = (email_stats['opened'] / email_stats['total']) * 100
    
    # Analytics stats
    views_this_week = JobView.objects.filter(viewed_at__gte=week_ago).count()
    clicks_this_week = JobClick.objects.filter(clicked_at__gte=week_ago).count()
    
    # Company stats
    total_companies = Company.objects.filter(is_active=True).count()
    
    context.update({
        "kpis": [
            {
                "title": "Active Jobs",
                "metric": total_jobs,
                "footer": f"+{jobs_this_week} this week",
                "icon": "work",
            },
            {
                "title": "Total Users",
                "metric": total_users,
                "footer": f"+{users_this_week} this week",
                "icon": "people",
            },
            {
                "title": "Rashid Conversations",
                "metric": total_conversations,
                "footer": f"{active_conversations} active",
                "icon": "smart_toy",
            },
            {
                "title": "Email Open Rate",
                "metric": f"{open_rate:.1f}%",
                "footer": f"{emails_sent_this_week} sent this week",
                "icon": "mail",
            },
        ],
        "progress": [
            {
                "title": "Pending Job Approvals",
                "description": "Jobs awaiting review",
                "value": pending_jobs,
                "color": "warning" if pending_jobs > 0 else "success",
            },
            {
                "title": "Pending Employer Verifications",
                "description": "Employers awaiting approval",
                "value": employer_pending,
                "color": "warning" if employer_pending > 0 else "success",
            },
        ],
        "recent_activity": {
            "jobs_this_week": jobs_this_week,
            "users_this_week": users_this_week,
            "conversations_this_week": conversations_this_week,
            "tokens_this_week": tokens_this_week,
            "views_this_week": views_this_week,
            "clicks_this_week": clicks_this_week,
            "companies": total_companies,
        },
    })
    
    return context


def environment_callback(request):
    """
    Display environment badge in admin header.
    """
    import os
    env = os.getenv('DJANGO_ENV', 'development')
    
    return {
        "development": {"name": "Development", "color": "yellow"},
        "staging": {"name": "Staging", "color": "orange"},
        "production": {"name": "Production", "color": "red"},
    }.get(env, {"name": env.title(), "color": "gray"})


def get_pending_jobs_count():
    """Badge count for pending job approvals."""
    from apps.employers.models import JobPosting
    return JobPosting.objects.filter(status='pending_review').count()


def get_pending_verifications_count():
    """Badge count for pending employer verifications."""
    from apps.employers.models import EmployerProfile
    return EmployerProfile.objects.filter(is_verified=False).count()


def get_active_conversations_count():
    """Badge count for active Rashid conversations."""
    from apps.rashid.models import RashidConversation
    return RashidConversation.objects.filter(is_active=True).count()


# Unfold sidebar navigation configuration
UNFOLD_SIDEBAR = {
    "show_search": True,
    "show_all_applications": True,
    "navigation": [
        {
            "title": _("Dashboard"),
            "separator": True,
            "items": [
                {
                    "title": _("Overview"),
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                },
            ],
        },
        {
            "title": _("Jobs & Companies"),
            "separator": True,
            "items": [
                {
                    "title": _("Jobs"),
                    "icon": "work",
                    "link": reverse_lazy("admin:jobs_job_changelist"),
                },
                {
                    "title": _("Companies"),
                    "icon": "business",
                    "link": reverse_lazy("admin:jobs_company_changelist"),
                },
                {
                    "title": _("Sources"),
                    "icon": "source",
                    "link": reverse_lazy("admin:jobs_source_changelist"),
                },
                {
                    "title": _("Tags"),
                    "icon": "label",
                    "link": reverse_lazy("admin:jobs_tag_changelist"),
                },
            ],
        },
        {
            "title": _("Users & Profiles"),
            "separator": True,
            "items": [
                {
                    "title": _("Users"),
                    "icon": "people",
                    "link": reverse_lazy("admin:accounts_user_changelist"),
                },
                {
                    "title": _("User Profiles"),
                    "icon": "person",
                    "link": reverse_lazy("admin:users_userprofile_changelist"),
                },
                {
                    "title": _("Saved Jobs"),
                    "icon": "bookmark",
                    "link": reverse_lazy("admin:users_savedjob_changelist"),
                },
                {
                    "title": _("Alerts"),
                    "icon": "notifications",
                    "link": reverse_lazy("admin:users_alert_changelist"),
                },
            ],
        },
        {
            "title": _("Rashid AI"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Configuration"),
                    "icon": "settings",
                    "link": reverse_lazy("admin:rashid_rashidconfig_changelist"),
                },
                {
                    "title": _("Profiles"),
                    "icon": "person_outline",
                    "link": reverse_lazy("admin:rashid_rashidprofile_changelist"),
                },
                {
                    "title": _("Conversations"),
                    "icon": "chat",
                    "link": reverse_lazy("admin:rashid_rashidconversation_changelist"),
                },
                {
                    "title": _("Story Bank"),
                    "icon": "auto_stories",
                    "link": reverse_lazy("admin:rashid_rashidstorybank_changelist"),
                },
                {
                    "title": _("Usage Stats"),
                    "icon": "analytics",
                    "link": reverse_lazy("admin:rashid_rashidusage_changelist"),
                },
            ],
        },
        {
            "title": _("Email System"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Email Accounts"),
                    "icon": "email",
                    "link": reverse_lazy("admin:emails_emailaccount_changelist"),
                },
                {
                    "title": _("Templates"),
                    "icon": "description",
                    "link": reverse_lazy("admin:emails_emailtemplate_changelist"),
                },
                {
                    "title": _("Email Logs"),
                    "icon": "history",
                    "link": reverse_lazy("admin:emails_emaillog_changelist"),
                },
            ],
        },
        {
            "title": _("Employers"),
            "separator": True,
            "items": [
                {
                    "title": _("Employer Profiles"),
                    "icon": "business_center",
                    "link": reverse_lazy("admin:employers_employerprofile_changelist"),
                    "badge": get_pending_verifications_count,
                },
                {
                    "title": _("Job Postings"),
                    "icon": "post_add",
                    "link": reverse_lazy("admin:employers_jobposting_changelist"),
                    "badge": get_pending_jobs_count,
                },
                {
                    "title": _("Applications"),
                    "icon": "assignment",
                    "link": reverse_lazy("admin:employers_jobapplication_changelist"),
                },
            ],
        },
        {
            "title": _("Analytics"),
            "separator": True,
            "items": [
                {
                    "title": _("Job Views"),
                    "icon": "visibility",
                    "link": reverse_lazy("admin:analytics_jobview_changelist"),
                },
                {
                    "title": _("Job Clicks"),
                    "icon": "touch_app",
                    "link": reverse_lazy("admin:analytics_jobclick_changelist"),
                },
                {
                    "title": _("Search Logs"),
                    "icon": "search",
                    "link": reverse_lazy("admin:analytics_searchlog_changelist"),
                },
            ],
        },
        {
            "title": _("System"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Feature Flags"),
                    "icon": "flag",
                    "link": reverse_lazy("admin:core_featureflag_changelist"),
                },
                {
                    "title": _("Activity Log"),
                    "icon": "history",
                    "link": reverse_lazy("admin:core_activitylog_changelist"),
                },
                {
                    "title": _("Pipeline Health"),
                    "icon": "monitor_heart",
                    "link": reverse_lazy("admin:core_pipelinehealth_changelist"),
                },
                {
                    "title": _("Platform Config"),
                    "icon": "settings_applications",
                    "link": reverse_lazy("admin:core_platformconfig_changelist"),
                },
                {
                    "title": _("Media"),
                    "icon": "perm_media",
                    "link": reverse_lazy("admin:core_media_changelist"),
                },
            ],
        },
    ],
}
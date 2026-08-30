> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 3C: Admin Dashboard Extensions

> **Dependencies:** All previous phases  
> **Duration:** 4-6 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Extend Django admin with django-unfold for comprehensive platform management:
- Modern UI with django-unfold
- Rashid configuration panel
- Scraper management dashboard
- Email campaign analytics
- Pipeline health monitoring
- Feature flags management
- Custom dashboards and reports

---

## 📦 Dependencies

```bash
pip install django-unfold
pip install django-admin-charts  # For charts
pip install django-import-export  # For CSV export
```

---

## 🔧 Implementation

### Step 1: Install and Configure Unfold

**Update:** `backend/ecareer/settings.py`

```python
INSTALLED_APPS = [
    # Unfold must be BEFORE django.contrib.admin
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # ... rest of your apps
]

# Unfold configuration
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "E-Career Admin",
    "SITE_HEADER": "E-Career Platform",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("logo-light.svg"),
        "dark": lambda request: static("logo-dark.svg"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("logo-light.svg"),
        "dark": lambda request: static("logo-dark.svg"),
    },
    "SITE_SYMBOL": "📊",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "ecareer.settings.environment_callback",
    "DASHBOARD_CALLBACK": "ecareer.admin_dashboard.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "ar": "🇪🇬",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Dashboard"),
                "separator": True,
                "items": [
                    {
                        "title": _("Overview"),
                        "icon": "home",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Analytics"),
                        "icon": "bar_chart",
                        "link": reverse_lazy("admin:analytics"),
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
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:jobs_category_changelist"),
                    },
                    {
                        "title": _("Scrapers"),
                        "icon": "sync",
                        "link": reverse_lazy("admin:scraper-dashboard"),
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
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("User Profiles"),
                        "icon": "person",
                        "link": reverse_lazy("admin:profiles_userprofile_changelist"),
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
                        "title": _("Conversations"),
                        "icon": "chat",
                        "link": reverse_lazy("admin:rashid_conversation_changelist"),
                        "badge": "rashid.admin.get_active_conversations_count",
                    },
                    {
                        "title": _("Analytics"),
                        "icon": "analytics",
                        "link": reverse_lazy("admin:rashid-analytics"),
                    },
                ],
            },
            {
                "title": _("Email System"),
                "separator": True,
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
                        "title": _("Campaigns"),
                        "icon": "campaign",
                        "link": reverse_lazy("admin:emails_emailcampaign_changelist"),
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
                        "badge": "employers.admin.get_pending_verifications_count",
                    },
                    {
                        "title": _("Job Posts"),
                        "icon": "post_add",
                        "link": reverse_lazy("admin:employers_employerjobpost_changelist"),
                        "badge": "employers.admin.get_pending_jobs_count",
                    },
                    {
                        "title": _("Applications"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:employers_jobapplication_changelist"),
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
                        "link": reverse_lazy("admin:system_featureflag_changelist"),
                    },
                    {
                        "title": _("Health Monitor"),
                        "icon": "monitor_heart",
                        "link": reverse_lazy("admin:health-monitor"),
                    },
                    {
                        "title": _("Celery Tasks"),
                        "icon": "schedule",
                        "link": reverse_lazy("admin:celery-tasks"),
                    },
                ],
            },
        ],
    },
}


def environment_callback(request):
    """Display environment badge"""
    import os
    env = os.getenv('DJANGO_ENV', 'development')
    
    return {
        "development": {"name": "Development", "color": "yellow"},
        "staging": {"name": "Staging", "color": "orange"},
        "production": {"name": "Production", "color": "red"},
    }.get(env, {"name": env.title(), "color": "gray"})
```

### Step 2: Custom Admin Dashboard

**File:** `backend/ecareer/admin_dashboard.py`

```python
"""
Custom admin dashboard with analytics
"""

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from unfold.decorators import display

def dashboard_callback(request, context):
    """Custom dashboard data"""
    from jobs.models import Job
    from profiles.models import UserProfile
    from rashid.models import Conversation
    from emails.models import EmailLog
    
    # Calculate stats
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Job stats
    total_jobs = Job.objects.filter(is_active=True).count()
    jobs_this_week = Job.objects.filter(posted_date__gte=week_ago).count()
    jobs_this_month = Job.objects.filter(posted_date__gte=month_ago).count()
    
    # User stats
    total_users = UserProfile.objects.count()
    users_this_week = UserProfile.objects.filter(created_at__gte=week_ago).count()
    complete_profiles = UserProfile.objects.filter(is_complete=True).count()
    
    # Rashid stats
    total_conversations = Conversation.objects.count()
    active_conversations = Conversation.objects.filter(is_active=True).count()
    conversations_this_week = Conversation.objects.filter(created_at__gte=week_ago).count()
    
    # Email stats
    emails_sent_today = EmailLog.objects.filter(sent_at__date=today.date()).count()
    emails_sent_this_week = EmailLog.objects.filter(sent_at__gte=week_ago).count()
    email_open_rate = EmailLog.objects.filter(
        sent_at__gte=week_ago
    ).aggregate(
        opened=Count('id', filter=Q(opened_at__isnull=False)),
        total=Count('id')
    )
    
    open_rate = 0
    if email_open_rate['total'] > 0:
        open_rate = (email_open_rate['opened'] / email_open_rate['total']) * 100
    
    context.update({
        "kpis": [
            {
                "title": "Active Jobs",
                "metric": total_jobs,
                "footer": f"+{jobs_this_week} this week",
                "chart": True,
            },
            {
                "title": "Total Users",
                "metric": total_users,
                "footer": f"+{users_this_week} this week",
            },
            {
                "title": "Rashid Conversations",
                "metric": total_conversations,
                "footer": f"{active_conversations} active",
            },
            {
                "title": "Email Open Rate",
                "metric": f"{open_rate:.1f}%",
                "footer": f"{emails_sent_this_week} sent this week",
            },
        ],
        "progress": [
            {
                "title": "Profile Completion",
                "description": "Users with complete profiles",
                "value": (complete_profiles / total_users * 100) if total_users > 0 else 0,
            },
        ],
    })
    
    return context
```

### Step 3: Enhanced Admin for Jobs

**File:** `backend/jobs/admin.py` (update with unfold)

```python
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.utils.html import format_html
from django.db.models import Count
from .models import Job, Company, Category, Source

@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = [
        'title', 'company_link', 'category', 'location',
        'workplace_badge', 'posted_date', 'is_active_badge',
        'legitimacy_badge', 'view_count', 'application_count'
    ]
    
    list_filter = [
        'is_active', 'is_legitimate', 'workplace_type',
        'employment_type', 'experience_level', 'posted_date'
    ]
    
    search_fields = ['title', 'company__name', 'location', 'description']
    
    readonly_fields = ['slug', 'view_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'category', 'source', 'slug')
        }),
        ('Description', {
            'fields': ('description', 'requirements', 'responsibilities', 'benefits')
        }),
        ('Classification', {
            'fields': (
                'location', 'workplace_type', 'employment_type',
                'experience_level', 'education_level'
            )
        }),
        ('Salary', {
            'fields': (
                'salary_min', 'salary_max', 'salary_currency', 'salary_period'
            )
        }),
        ('Application', {
            'fields': ('apply_url', 'application_email')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'posted_date', 'expires_at')
        }),
        ('Legitimacy', {
            'fields': ('is_legitimate', 'legitimacy_score', 'legitimacy_flags')
        }),
        ('Metadata', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_jobs', 'deactivate_jobs', 'mark_as_scam']
    
    @display(description="Company", ordering="company__name")
    def company_link(self, obj):
        return format_html(
            '<a href="/admin/jobs/company/{}/change/">{}</a>',
            obj.company.id,
            obj.company.name
        )
    
    @display(description="Workplace", ordering="workplace_type")
    def workplace_badge(self, obj):
        colors = {
            'remote': 'green',
            'onsite': 'blue',
            'hybrid': 'purple'
        }
        color = colors.get(obj.workplace_type, 'gray')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_workplace_type_display()
        )
    
    @display(description="Active", boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    @display(description="Legitimacy", ordering="legitimacy_score")
    def legitimacy_badge(self, obj):
        if not obj.is_legitimate:
            return format_html(
                '<span class="badge bg-red">Scam ({}%)</span>',
                obj.legitimacy_score
            )
        elif obj.legitimacy_score < 70:
            return format_html(
                '<span class="badge bg-yellow">Suspicious ({}%)</span>',
                obj.legitimacy_score
            )
        else:
            return format_html(
                '<span class="badge bg-green">Legitimate ({}%)</span>',
                obj.legitimacy_score
            )
    
    @display(description="Applications")
    def application_count(self, obj):
        return obj.applications.count()
    
    def activate_jobs(self, request, queryset):
        queryset.update(is_active=True)
    activate_jobs.short_description = "Activate selected jobs"
    
    def deactivate_jobs(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_jobs.short_description = "Deactivate selected jobs"
    
    def mark_as_scam(self, request, queryset):
        queryset.update(is_legitimate=False, legitimacy_score=0, is_active=False)
    mark_as_scam.short_description = "Mark as scam"


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ['name', 'industry', 'size', 'location', 'website', 'job_count']
    list_filter = ['industry', 'size']
    search_fields = ['name', 'website']
    readonly_fields = ['slug', 'created_at']
    
    @display(description="Active Jobs")
    def job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'job_count']
    search_fields = ['name']
    readonly_fields = ['slug']
    
    @display(description="Jobs")
    def job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    list_display = ['name', 'type', 'icon', 'is_active', 'job_count']
    list_filter = ['type', 'is_active']
    
    @display(description="Jobs")
    def job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()
```

### Step 4: Rashid Admin Panel

**File:** `backend/rashid/admin.py` (update)

```python
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.utils.html import format_html
from .models import RashidConfig, Conversation, Message, UserOnboarding

@admin.register(RashidConfig)
class RashidConfigAdmin(ModelAdmin):
    list_display = ['personality', 'dialect', 'is_active', 'updated_at']
    list_filter = ['personality', 'dialect', 'is_active']
    
    fieldsets = (
        ('Basic Settings', {
            'fields': ('personality', 'dialect', 'is_active')
        }),
        ('System Prompt', {
            'fields': ('system_prompt_template', 'greeting_message')
        }),
        ('AI Parameters', {
            'fields': ('max_tokens_per_response', 'temperature')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active config
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Conversation)
class ConversationAdmin(ModelAdmin):
    list_display = ['user', 'mode', 'title_preview', 'message_count', 'is_active', 'created_at']
    list_filter = ['mode', 'is_active', 'created_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    @display(description="Title")
    def title_preview(self, obj):
        return obj.title[:50] if obj.title else f"Conversation {obj.id}"
    
    def has_change_permission(self, request, obj=None):
        # Admin can view but not edit conversations (privacy)
        return False


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['conversation', 'role', 'token_count', 'latency_ms', 'created_at']
    list_filter = ['role', 'created_at']
    readonly_fields = ['id', 'conversation', 'role', 'content', 'created_at']
    
    @display(description="Content Preview")
    def content_preview(self, obj):
        # Show that message is encrypted
        return format_html(
            '<span class="text-gray-500">[Encrypted - {} characters]</span>',
            len(obj.content) if obj.content else 0
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


def get_active_conversations_count():
    """Badge count for active conversations"""
    return Conversation.objects.filter(is_active=True).count()
```

### Step 5: Scraper Dashboard View

**File:** `backend/scrapers/admin_views.py`

```python
"""
Custom admin views for scraper management
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job, Source

@staff_member_required
def scraper_dashboard(request):
    """Scraper management dashboard"""
    
    # Get sources with stats
    sources = Source.objects.annotate(
        total_jobs=Count('jobs'),
        active_jobs=Count('jobs', filter=Q(jobs__is_active=True)),
        jobs_today=Count('jobs', filter=Q(jobs__created_at__date=timezone.now().date()))
    )
    
    # Get recent scrape stats
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    
    scrape_stats = {
        'total_jobs': Job.objects.count(),
        'active_jobs': Job.objects.filter(is_active=True).count(),
        'jobs_this_week': Job.objects.filter(posted_date__gte=week_ago).count(),
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
    
    context = {
        'sources': sources,
        'scrape_stats': scrape_stats,
        'scraper_health': scraper_health,
    }
    
    return render(request, 'admin/scraper_dashboard.html', context)
```

**Update:** `backend/ecareer/urls.py`

```python
from scrapers.admin_views import scraper_dashboard

urlpatterns = [
    # ... existing
    path('admin/scraper-dashboard/', scraper_dashboard, name='scraper-dashboard'),
]
```

### Step 6: Feature Flags Model

**File:** `backend/system/models.py`

```python
from django.db import models

class FeatureFlag(models.Model):
    """Feature flags for A/B testing and gradual rollouts"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_enabled = models.BooleanField(default=False)
    
    # Rollout percentage (0-100)
    rollout_percentage = models.IntegerField(default=0)
    
    # Target specific users
    allowed_users = models.ManyToManyField('auth.User', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({'ON' if self.is_enabled else 'OFF'})"
    
    def is_enabled_for_user(self, user):
        """Check if feature is enabled for specific user"""
        if not self.is_enabled:
            return False
        
        # If user is in allowed list, always enable
        if self.allowed_users.filter(id=user.id).exists():
            return True
        
        # Check rollout percentage
        if self.rollout_percentage >= 100:
            return True
        elif self.rollout_percentage <= 0:
            return False
        
        # Hash user ID for consistent rollout
        import hashlib
        hash_value = int(hashlib.md5(str(user.id).encode()).hexdigest(), 16)
        return (hash_value % 100) < self.rollout_percentage
```

**File:** `backend/system/admin.py`

```python
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import FeatureFlag

@admin.register(FeatureFlag)
class FeatureFlagAdmin(ModelAdmin):
    list_display = ['name', 'is_enabled', 'rollout_percentage', 'updated_at']
    list_filter = ['is_enabled']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Flag Details', {
            'fields': ('name', 'description')
        }),
        ('Activation', {
            'fields': ('is_enabled', 'rollout_percentage')
        }),
        ('Targeting', {
            'fields': ('allowed_users',)
        }),
    )
```

### Step 7: Health Monitor View

**File:** `backend/system/health_monitor.py`

```python
"""
System health monitoring dashboard
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.core.cache import cache
import redis
from celery import current_app

@staff_member_required
def health_monitor(request):
    """System health monitoring dashboard"""
    
    checks = []
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks.append({
            'name': 'Database',
            'status': 'healthy',
            'message': 'PostgreSQL is responding'
        })
    except Exception as e:
        checks.append({
            'name': 'Database',
            'status': 'error',
            'message': str(e)
        })
    
    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks.append({
                'name': 'Redis',
                'status': 'healthy',
                'message': 'Redis is responding'
            })
        else:
            raise Exception('Cache write/read failed')
    except Exception as e:
        checks.append({
            'name': 'Redis',
            'status': 'error',
            'message': str(e)
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
                'message': f'{worker_count} workers active'
            })
        else:
            checks.append({
                'name': 'Celery',
                'status': 'warning',
                'message': 'No workers detected'
            })
    except Exception as e:
        checks.append({
            'name': 'Celery',
            'status': 'error',
            'message': str(e)
        })
    
    # AWS Bedrock check
    try:
        from ai.bedrock_service import bedrock_service
        response = bedrock_service.invoke_model("test", max_tokens=10)
        if response:
            checks.append({
                'name': 'AWS Bedrock',
                'status': 'healthy',
                'message': 'AI service is responding'
            })
    except Exception as e:
        checks.append({
            'name': 'AWS Bedrock',
            'status': 'error',
            'message': str(e)
        })
    
    # Email accounts check
    from emails.models import EmailAccount
    email_accounts = EmailAccount.objects.filter(is_active=True)
    available_accounts = [acc for acc in email_accounts if acc.can_send()]
    
    if len(available_accounts) > 0:
        checks.append({
            'name': 'Email Accounts',
            'status': 'healthy',
            'message': f'{len(available_accounts)}/{len(email_accounts)} accounts available'
        })
    else:
        checks.append({
            'name': 'Email Accounts',
            'status': 'warning',
            'message': 'No email accounts available'
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
        'overall_status': overall_status
    }
    
    return render(request, 'admin/health_monitor.html', context)
```

---

## 🎨 Templates

### Step 8: Admin Templates

**File:** `backend/templates/admin/scraper_dashboard.html`

```html
{% extends "unfold/layouts/base_simple.html" %}
{% load i18n %}

{% block content %}
<div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Scraper Management Dashboard</h1>
    
    <!-- Stats Grid -->
    <div class="grid grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-sm text-gray-600">Total Jobs</div>
            <div class="text-3xl font-bold">{{ scrape_stats.total_jobs }}</div>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-sm text-gray-600">Active Jobs</div>
            <div class="text-3xl font-bold text-green-600">{{ scrape_stats.active_jobs }}</div>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-sm text-gray-600">This Week</div>
            <div class="text-3xl font-bold text-blue-600">{{ scrape_stats.jobs_this_week }}</div>
        </div>
        
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-sm text-gray-600">Scams Blocked</div>
            <div class="text-3xl font-bold text-red-600">{{ scrape_stats.scam_jobs_blocked }}</div>
        </div>
    </div>
    
    <!-- Scraper Health -->
    <div class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b">
            <h2 class="text-xl font-semibold">Scraper Health</h2>
        </div>
        
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left">Source</th>
                    <th class="px-6 py-3 text-left">Status</th>
                    <th class="px-6 py-3 text-right">Total Jobs</th>
                    <th class="px-6 py-3 text-right">Active Jobs</th>
                    <th class="px-6 py-3 text-right">Today</th>
                    <th class="px-6 py-3 text-left">Last Scrape</th>
                </tr>
            </thead>
            <tbody class="divide-y">
                {% for item in scraper_health %}
                <tr>
                    <td class="px-6 py-4">{{ item.source.name }}</td>
                    <td class="px-6 py-4">
                        {% if item.status == 'healthy' %}
                        <span class="px-2 py-1 bg-green-100 text-green-800 rounded">Healthy</span>
                        {% elif item.status == 'stale' %}
                        <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">Stale</span>
                        {% else %}
                        <span class="px-2 py-1 bg-red-100 text-red-800 rounded">No Data</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-right">{{ item.source.total_jobs }}</td>
                    <td class="px-6 py-4 text-right">{{ item.source.active_jobs }}</td>
                    <td class="px-6 py-4 text-right">{{ item.source.jobs_today }}</td>
                    <td class="px-6 py-4">{{ item.last_scrape|timesince }} ago</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

---

## ✅ Phase 3C Verification

### Tests

```bash
# Access admin
python manage.py createsuperuser
# Visit http://localhost:8000/admin/

# Test dashboards
# - Visit /admin/ for overview
# - Visit /admin/scraper-dashboard/ for scraper stats
# - Visit /admin/health-monitor/ for health checks
```

### Success Criteria

- [ ] Django Unfold installed and working
- [ ] Custom dashboard displays KPIs
- [ ] Scraper dashboard shows health status
- [ ] Rashid config panel works
- [ ] Email campaign analytics visible
- [ ] Feature flags functional
- [ ] Health monitor checks all services
- [ ] Modern, responsive UI
- [ ] All admin actions work correctly

---

**Phase 3C Complete! ✅**

## 🎉 ALL PHASES COMPLETE!

You now have all 11 implementation phases:
- **Phase 1:** Foundation (Database, Scraping, Job Pages)
- **Phase 2:** AI Layer (Profiles, Rashid Core, Tools, Emails)
- **Phase 3:** Advanced (Employer Portal, Recommendations, Admin Dashboard)

Ready for GLM execution! Start with `PHASE_1A_DATABASE.md`.

"""
Analytics Dashboard Views - Phase H

Admin dashboard for business intelligence and insights.
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .tracking import analytics_tracker


@staff_member_required
def analytics_dashboard(request):
    """
    Main analytics dashboard.

    URL: /admin/analytics/dashboard/
    """
    # Get query parameters
    days = int(request.GET.get('days', 30))

    # Fetch analytics data
    context = {
        'days': days,
        'funnel': analytics_tracker.get_conversion_funnel(days=days),
        'features': analytics_tracker.get_feature_usage_stats(days=days),
        'retention': analytics_tracker.get_retention_cohorts(),
        'market_insights': analytics_tracker.get_job_market_insights(days=days),
    }

    return render(request, 'analytics/dashboard.html', context)


@staff_member_required
def user_journey_view(request, user_id):
    """
    Individual user journey visualization.

    URL: /admin/analytics/user/<user_id>/
    """
    days = int(request.GET.get('days', 30))

    context = {
        'user_id': user_id,
        'journey': analytics_tracker.get_user_journey(user_id, days=days),
        'days': days,
    }

    return render(request, 'analytics/user_journey.html', context)

"""
AI Cost Dashboard - Track Bedrock/AI usage and costs
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from apps.events.models import EventLog as Event
from apps.rashid.models import RashidUsage


@staff_member_required
def ai_cost_dashboard(request):
    """
    Admin dashboard showing AI usage and costs across all features.

    Metrics:
    - Total spend (daily, weekly, monthly)
    - Cost by feature (Rashid, cover letters, CV tailor, etc.)
    - Token usage trends
    - Top users by spend
    - Model usage breakdown (Haiku vs Sonnet)
    """
    now = timezone.now()

    # Date ranges
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # Query AI model events
    ai_events = Event.objects.filter(event_type='ai_model_called')

    # Aggregate costs from events (stored in metadata)
    def extract_cost(events):
        """Extract cost_usd from event metadata."""
        total = 0
        for event in events:
            if event.metadata and 'cost_usd' in event.metadata:
                total += float(event.metadata.get('cost_usd', 0))
        return total

    # Today's costs
    today_events = ai_events.filter(created_at__gte=today_start)
    today_cost = extract_cost(today_events)
    today_calls = today_events.count()

    # This week
    week_events = ai_events.filter(created_at__gte=week_start)
    week_cost = extract_cost(week_events)
    week_calls = week_events.count()

    # This month
    month_events = ai_events.filter(created_at__gte=month_start)
    month_cost = extract_cost(month_events)
    month_calls = month_events.count()

    # Rashid chat costs (separate model)
    rashid_today = RashidUsage.objects.filter(created_at__gte=today_start)
    rashid_week = RashidUsage.objects.filter(created_at__gte=week_start)
    rashid_month = RashidUsage.objects.filter(created_at__gte=month_start)

    rashid_today_cost = sum([
        (u.input_tokens * 0.003 / 1000) + (u.output_tokens * 0.015 / 1000)
        for u in rashid_today
    ])
    rashid_week_cost = sum([
        (u.input_tokens * 0.003 / 1000) + (u.output_tokens * 0.015 / 1000)
        for u in rashid_week
    ])
    rashid_month_cost = sum([
        (u.input_tokens * 0.003 / 1000) + (u.output_tokens * 0.015 / 1000)
        for u in rashid_month
    ])

    # Cost by feature (from event metadata - operation field)
    feature_costs = {}
    for event in month_events:
        if event.metadata:
            operation = event.metadata.get('operation', 'unknown')
            cost = float(event.metadata.get('cost_usd', 0))
            feature_costs[operation] = feature_costs.get(operation, 0) + cost

    # Add Rashid
    feature_costs['rashid_chat'] = rashid_month_cost

    # Sort by cost descending
    feature_costs_sorted = sorted(feature_costs.items(), key=lambda x: x[1], reverse=True)

    # Model breakdown (from event metadata)
    model_usage = {}
    for event in month_events:
        if event.metadata:
            model = event.metadata.get('model', 'unknown')
            model_usage[model] = model_usage.get(model, 0) + 1

    # Top users by cost (from Rashid + events with user_id)
    user_costs = {}

    # Rashid users
    for usage in rashid_month:
        if usage.user_id:
            cost = (usage.input_tokens * 0.003 / 1000) + (usage.output_tokens * 0.015 / 1000)
            user_costs[usage.user.email if usage.user else 'Anonymous'] = \
                user_costs.get(usage.user.email if usage.user else 'Anonymous', 0) + cost

    # Event users (harder to extract - would need to parse metadata)
    # For now, Rashid is our main cost driver

    top_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)[:10]

    # Daily trend (last 30 days)
    daily_costs = []
    for i in range(30, -1, -1):
        day_start = now - timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        day_events = ai_events.filter(created_at__gte=day_start, created_at__lt=day_end)
        day_cost = extract_cost(day_events)

        day_rashid = RashidUsage.objects.filter(created_at__gte=day_start, created_at__lt=day_end)
        day_rashid_cost = sum([
            (u.input_tokens * 0.003 / 1000) + (u.output_tokens * 0.015 / 1000)
            for u in day_rashid
        ])

        daily_costs.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'cost': round(day_cost + day_rashid_cost, 4),
            'calls': day_events.count() + day_rashid.count()
        })

    context = {
        'today_cost': round(today_cost + rashid_today_cost, 4),
        'today_calls': today_calls + rashid_today.count(),
        'week_cost': round(week_cost + rashid_week_cost, 4),
        'week_calls': week_calls + rashid_week.count(),
        'month_cost': round(month_cost + rashid_month_cost, 4),
        'month_calls': month_calls + rashid_month.count(),
        'feature_costs': feature_costs_sorted,
        'model_usage': sorted(model_usage.items(), key=lambda x: x[1], reverse=True),
        'top_users': top_users,
        'daily_costs': daily_costs,
    }

    return render(request, 'monitoring/ai_cost_dashboard.html', context)

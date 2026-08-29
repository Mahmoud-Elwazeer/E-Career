"""Intelligence Layer URL Configuration."""
from django.urls import path
from . import views

app_name = "intelligence"

urlpatterns = [
    # Rashid AI Agent
    path("rashid/chat/", views.chat_with_rashid, name="rashid-chat"),

    # Trend Detection
    path("trends/emerging/", views.get_emerging_skills, name="emerging-skills"),
    path("trends/declining/", views.get_declining_skills, name="declining-skills"),

    # Research
    path("research/", views.start_research, name="start-research"),

    # Email Verification
    path("verify-email/", views.verify_email_address, name="verify-email"),

    # Knowledge Graph (Phase 4)
    path("graph/skill/<str:skill_name>/", views.skill_neighborhood, name="skill-graph"),
    path("graph/role/<str:role_title>/skills/", views.role_skills_graph, name="role-skills-graph"),
    path("graph/role/<str:role_title>/paths/", views.career_path_graph, name="career-path-graph"),
    path("graph/skill-gaps/", views.user_skill_gaps, name="user-skill-gaps"),

    # Content Pipeline (Phase 3)
    path("content/generate/", views.generate_content, name="generate-content"),

    # Web Extraction (Phase 3)
    path("extract/", views.extract_from_url, name="extract-from-url"),

    # Admin: Health & Monitoring
    path("health/", views.intelligence_health, name="health"),
    path("admin/trends/", views.admin_trends_dashboard, name="admin-trends"),

    # Admin: Marketing Intelligence (Phase 4)
    path("admin/metrics/", views.platform_metrics, name="platform-metrics"),
    path("admin/market-gaps/", views.market_gaps, name="market-gaps"),
    path("admin/content-opportunities/", views.content_opportunities, name="content-opportunities"),
    path("admin/industry-breakdown/", views.industry_breakdown, name="industry-breakdown"),
    path("admin/location-insights/", views.location_insights, name="location-insights"),
]

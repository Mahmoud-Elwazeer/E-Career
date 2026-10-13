from django.urls import path

from . import views, admin_views

app_name = "legal"

urlpatterns = [
    # Public policy serving
    path("policies/", views.policy_list, name="policy-list"),
    path("policies/<slug:slug>/", views.policy_detail, name="policy-detail"),
    path("policies/<slug:slug>/accept/", views.policy_accept, name="policy-accept"),

    # Consent purposes
    path("consent-purposes/", views.consent_purpose_list, name="consent-purposes"),
    path("consent/", views.consent_set, name="consent-set"),

    # Marketing preference (separate from transactional notifications)
    path("marketing-preference/", views.MarketingPreferenceView.as_view(), name="marketing-preference"),

    # Cookie consent
    path("cookie-categories/", views.cookie_category_list, name="cookie-categories"),
    path("cookie-consent/", views.cookie_consent_record, name="cookie-consent-record"),
    path("cookie-consent/me/", views.cookie_consent_me, name="cookie-consent-me"),

    # Privacy Center / DSR
    path("privacy-requests/", views.PrivacyRequestListCreateView.as_view(), name="privacy-requests"),
    path("privacy-requests/<uuid:uuid>/", views.PrivacyRequestDetailView.as_view(), name="privacy-request-detail"),

    # Public legal-entity + AI disclosure registers
    path("entity/", views.legal_entity_public, name="legal-entity-public"),
    path("ai-disclosures/", views.ai_disclosure_list, name="ai-disclosures"),

    # ── Admin Legal Control Plane (IsAdminRole) ─────────────────────────────
    path("admin/documents/", admin_views.AdminPolicyDocumentListView.as_view(), name="admin-documents"),
    path("admin/versions/", admin_views.AdminPolicyVersionListCreateView.as_view(), name="admin-versions"),
    path("admin/versions/<uuid:uuid>/", admin_views.AdminPolicyVersionDetailView.as_view(), name="admin-version-detail"),
    path("admin/versions/<uuid:uuid>/transition/", admin_views.policy_version_transition, name="admin-version-transition"),

    path("admin/cookie-categories/", admin_views.AdminCookieCategoryListView.as_view(), name="admin-cookie-categories"),
    path("admin/cookie-categories/<uuid:uuid>/", admin_views.AdminCookieCategoryDetailView.as_view(), name="admin-cookie-category-detail"),

    path("admin/retention/", admin_views.AdminRetentionPolicyListView.as_view(), name="admin-retention"),
    path("admin/retention/<uuid:uuid>/", admin_views.AdminRetentionPolicyDetailView.as_view(), name="admin-retention-detail"),

    path("admin/processors/", admin_views.AdminProcessorListView.as_view(), name="admin-processors"),
    path("admin/processors/<uuid:uuid>/", admin_views.AdminProcessorDetailView.as_view(), name="admin-processor-detail"),

    path("admin/transfers/", admin_views.AdminDataTransferListView.as_view(), name="admin-transfers"),
    path("admin/transfers/<uuid:uuid>/", admin_views.AdminDataTransferDetailView.as_view(), name="admin-transfer-detail"),

    path("admin/jurisdictions/", admin_views.AdminJurisdictionProfileListView.as_view(), name="admin-jurisdictions"),
    path("admin/jurisdictions/<uuid:uuid>/", admin_views.AdminJurisdictionProfileDetailView.as_view(), name="admin-jurisdiction-detail"),

    path("admin/entity/", admin_views.legal_entity_config, name="admin-entity"),

    path("admin/ai-disclosures/", admin_views.AdminAIProcessingDisclosureListView.as_view(), name="admin-ai-disclosures"),
    path("admin/ai-disclosures/<uuid:uuid>/", admin_views.AdminAIProcessingDisclosureDetailView.as_view(), name="admin-ai-disclosure-detail"),

    path("admin/incidents/", admin_views.AdminIncidentListView.as_view(), name="admin-incidents"),
    path("admin/incidents/<uuid:uuid>/", admin_views.AdminIncidentDetailView.as_view(), name="admin-incident-detail"),

    path("admin/holds/", admin_views.AdminLegalHoldListView.as_view(), name="admin-holds"),
    path("admin/holds/<uuid:uuid>/release/", admin_views.legal_hold_release, name="admin-hold-release"),

    path("admin/privacy-requests/", admin_views.AdminPrivacyRequestListView.as_view(), name="admin-privacy-requests"),
    path("admin/privacy-requests/<uuid:uuid>/transition/", admin_views.admin_privacy_request_transition, name="admin-privacy-request-transition"),
]

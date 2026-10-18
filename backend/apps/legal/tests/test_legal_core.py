"""
Core backend tests for the Legal/Privacy/Consent domain.

Covers directive-mandated behaviors:
  - Policy versioning never overwrites; activation retires the prior version
  - Terms acceptance and other consent purposes are independently tracked/withdrawable
  - Cookie consent works anonymously and always keeps "necessary" on
  - Talent Pool / marketing consent are separate ConsentPurposes from Terms
  - DSR (Privacy Request) lifecycle + admin-only transitions
  - Admin Legal Control Plane is admin-gated (RBAC)
  - AI disclosures cannot be marked as making the final hiring decision
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.legal.models import (
    PolicyDocument, PolicyVersion, ConsentPurpose, ConsentRecord, CookieCategory,
    CookieConsent, PrivacyRequest, AIProcessingDisclosure,
)
from apps.legal import services
from django.utils import timezone

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="legal-user@test.com", password="pw12345x")


@pytest.fixture
def admin_user():
    return User.objects.create_user(email="legal-admin@test.com", password="pw12345x", role="admin")


@pytest.fixture
def auth_client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def admin_client(admin_user):
    c = APIClient()
    c.force_authenticate(user=admin_user)
    return c


@pytest.fixture
def terms_doc():
    return PolicyDocument.objects.create(slug="terms", doc_type=PolicyDocument.DocType.TERMS, title="Terms of Service")


def _approved_version(doc, label="2026.1", **kwargs):
    return PolicyVersion.objects.create(
        document=doc, version_label=label, locale="en", jurisdiction="OTHER",
        status=PolicyVersion.Status.APPROVED, content_markdown="# Terms\nSome text.", **kwargs,
    )


# ── Policy lifecycle ──────────────────────────────────────────────────────────

def test_activate_version_retires_previous_active(terms_doc):
    v1 = _approved_version(terms_doc, "2026.1")
    services.activate_version(version=v1)
    v1.refresh_from_db()
    assert v1.status == PolicyVersion.Status.ACTIVE

    v2 = _approved_version(terms_doc, "2026.2")
    services.activate_version(version=v2)
    v1.refresh_from_db()
    v2.refresh_from_db()
    assert v1.status == PolicyVersion.Status.RETIRED
    assert v1.retired_at is not None
    assert v2.status == PolicyVersion.Status.ACTIVE
    # v1's content is untouched — never overwritten.
    assert v1.content_markdown == "# Terms\nSome text."


def test_activate_version_rejects_draft(terms_doc):
    draft = PolicyVersion.objects.create(
        document=terms_doc, version_label="2026.1", locale="en",
        status=PolicyVersion.Status.DRAFT, content_markdown="draft",
    )
    with pytest.raises(ValueError):
        services.activate_version(version=draft)


def test_activate_version_blocks_unresolved_marker_by_default(terms_doc):
    """Directive-critical safety gate: a version whose content still
    contains the 'REQUIRES LEGAL REVIEW' placeholder can never be activated
    through the normal path — this is the single real chokepoint enforcing
    item 29/30 (public legal content must never show internal markers)."""
    v1 = _approved_version(terms_doc)
    v1.content_markdown = "# Terms\n**REQUIRES LEGAL REVIEW / CONFIGURATION**"
    v1.save(update_fields=["content_markdown"])
    with pytest.raises(services.ActivationBlocked):
        services.activate_version(version=v1)
    v1.refresh_from_db()
    assert v1.status == PolicyVersion.Status.APPROVED  # never activated


def test_activate_version_allows_unresolved_marker_only_with_explicit_bypass(terms_doc):
    v1 = _approved_version(terms_doc)
    v1.content_markdown = "# Terms\n**REQUIRES LEGAL REVIEW / CONFIGURATION**"
    v1.save(update_fields=["content_markdown"])
    services.activate_version(version=v1, allow_unresolved_markers=True)
    v1.refresh_from_db()
    assert v1.status == PolicyVersion.Status.ACTIVE


def test_activate_version_writes_activity_log_entry(terms_doc, admin_user):
    from apps.core.models import ActivityLog

    v1 = _approved_version(terms_doc, "2026.1")
    services.activate_version(version=v1, approver=admin_user)

    entry = ActivityLog.objects.filter(action="legal.policy_activate").latest("created_at")
    assert entry.user_id == admin_user.id
    assert entry.target_type == "PolicyVersion"
    assert entry.target_id == str(v1.uuid)
    assert entry.metadata["document_slug"] == "terms"
    assert entry.metadata["version_label"] == "2026.1"
    assert entry.metadata["previous_active_version_label"] is None

    v2 = _approved_version(terms_doc, "2026.2", material_change=True)
    services.activate_version(version=v2, approver=admin_user)
    entry2 = ActivityLog.objects.filter(action="legal.policy_activate").latest("created_at")
    assert entry2.metadata["previous_active_version_label"] == "2026.1"
    assert entry2.metadata["material_change"] is True
    assert entry2.metadata["reacceptance_required"] is True


def test_public_policy_endpoint_returns_active_version(terms_doc):
    v1 = _approved_version(terms_doc)
    services.activate_version(version=v1)
    resp = APIClient().get("/api/v1/legal/policies/terms/")
    assert resp.status_code == 200
    assert resp.json()["data"]["version_label"] == "2026.1"


def test_public_policy_endpoint_404_when_no_active_version(terms_doc):
    resp = APIClient().get("/api/v1/legal/policies/terms/")
    assert resp.status_code == 404


def test_policy_accept_requires_auth(terms_doc):
    v1 = _approved_version(terms_doc)
    services.activate_version(version=v1)
    resp = APIClient().post("/api/v1/legal/policies/terms/accept/")
    assert resp.status_code == 401


def test_policy_accept_creates_acceptance_record(terms_doc, auth_client, user):
    v1 = _approved_version(terms_doc)
    services.activate_version(version=v1)
    resp = auth_client.post("/api/v1/legal/policies/terms/accept/", {"method": "signup"}, format="json")
    assert resp.status_code == 201
    assert user.legal_acceptances.filter(policy_version=v1).exists()


def test_needs_reacceptance_true_before_accept_false_after(terms_doc, user):
    v1 = _approved_version(terms_doc)
    services.activate_version(version=v1)
    assert services.needs_reacceptance(user, "terms") is True
    services.record_acceptance(user=user, policy_version=v1, method="signup")
    assert services.needs_reacceptance(user, "terms") is False


def test_policy_accept_binds_to_whichever_version_is_active_at_submit_time_not_a_stale_one(
    terms_doc, auth_client, user,
):
    """Race-condition guard: the backend must resolve 'the active version' at
    the moment /policies/<slug>/accept/ is called, never trust a version id
    supplied by (or rendered earlier on) the frontend. Simulates a user who
    loaded the signup page while v1 was active, then an admin activates v2
    before the user actually submits — the acceptance must bind to v2."""
    v1 = _approved_version(terms_doc, "2026.1")
    services.activate_version(version=v1)

    # User "loads the page" seeing v1 as active (not actually calling accept yet).
    assert services.get_active_version("terms").version_label == "2026.1"

    # Admin activates a new version before the user's accept request lands.
    v2 = _approved_version(terms_doc, "2026.2")
    services.activate_version(version=v2)

    # The user's (delayed) accept request now resolves to whatever is ACTUALLY
    # active server-side — v2, never the stale v1 the page originally showed.
    resp = auth_client.post("/api/v1/legal/policies/terms/accept/", {"method": "signup"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["policy_version"] == v2.pk
    assert not user.legal_acceptances.filter(policy_version=v1).exists()
    assert user.legal_acceptances.filter(policy_version=v2).exists()


def test_policy_version_update_preserves_old_acceptance_and_tracks_new_separately(terms_doc, user):
    """v1 active + accepted -> v2 activates -> v1's acceptance record remains
    historically intact (never overwritten/deleted) -> needs_reacceptance
    becomes True for v2 -> accepting v2 creates a SEPARATE acceptance row,
    v1's row is untouched."""
    v1 = _approved_version(terms_doc, "2026.1")
    services.activate_version(version=v1)
    v1_acceptance = services.record_acceptance(user=user, policy_version=v1, method="signup")
    assert services.needs_reacceptance(user, "terms") is False

    v2 = _approved_version(terms_doc, "2026.2", material_change=True)
    services.activate_version(version=v2)

    # Old acceptance untouched.
    v1_acceptance.refresh_from_db()
    assert v1_acceptance.policy_version_id == v1.id
    assert user.legal_acceptances.filter(policy_version=v1).count() == 1

    # System can determine re-acknowledgement is now required.
    assert services.needs_reacceptance(user, "terms") is True

    # Accepting v2 creates a NEW, separate row — v1's row is never mutated.
    v2_acceptance = services.record_acceptance(user=user, policy_version=v2, method="reacceptance_prompt")
    assert v2_acceptance.pk != v1_acceptance.pk
    assert user.legal_acceptances.filter(policy_version=v1).count() == 1
    assert user.legal_acceptances.filter(policy_version=v2).count() == 1
    assert services.needs_reacceptance(user, "terms") is False


# ── Admin version editing rules ───────────────────────────────────────────────

def test_admin_can_preview_a_draft_version_never_public(terms_doc, admin_client):
    """Safe Draft Preview: an admin can read a DRAFT version's content via
    the dedicated preview endpoint — this must never be reachable by the
    public policy_detail endpoint, which only resolves ACTIVE versions."""
    draft = PolicyVersion.objects.create(
        document=terms_doc, version_label="2026.2", locale="en",
        status=PolicyVersion.Status.DRAFT, content_markdown="unpublished draft text",
    )
    resp = admin_client.get(f"/api/v1/legal/admin/versions/{draft.uuid}/preview/")
    assert resp.status_code == 200
    assert resp.json()["data"]["content_markdown"] == "unpublished draft text"

    # Public route must 404 — no ACTIVE version exists for this document.
    public_resp = APIClient().get("/api/v1/legal/policies/terms/")
    assert public_resp.status_code == 404


def test_non_admin_cannot_preview_draft_version(terms_doc, auth_client):
    draft = PolicyVersion.objects.create(
        document=terms_doc, version_label="2026.2", locale="en",
        status=PolicyVersion.Status.DRAFT, content_markdown="unpublished draft text",
    )
    resp = auth_client.get(f"/api/v1/legal/admin/versions/{draft.uuid}/preview/")
    assert resp.status_code == 403


def test_non_draft_version_content_is_frozen(terms_doc, admin_client):
    v1 = _approved_version(terms_doc)
    resp = admin_client.patch(f"/api/v1/legal/admin/versions/{v1.uuid}/",
                              {"content_markdown": "changed"}, format="json")
    assert resp.status_code == 409


def test_draft_version_content_is_editable(terms_doc, admin_client):
    draft = PolicyVersion.objects.create(
        document=terms_doc, version_label="2026.1", locale="en",
        status=PolicyVersion.Status.DRAFT, content_markdown="draft",
    )
    resp = admin_client.patch(f"/api/v1/legal/admin/versions/{draft.uuid}/",
                              {"content_markdown": "edited draft"}, format="json")
    assert resp.status_code == 200
    draft.refresh_from_db()
    assert draft.content_markdown == "edited draft"


def test_admin_endpoints_require_admin_role(terms_doc, auth_client):
    resp = auth_client.get("/api/v1/legal/admin/versions/")
    assert resp.status_code == 403


# ── Consent purposes (separate from Terms) ───────────────────────────────────

@pytest.fixture
def talent_pool_purpose():
    return ConsentPurpose.objects.create(
        key="talent_pool", category=ConsentPurpose.Category.TALENT_POOL,
        label="Talent Pool visibility", is_required=False,
    )


@pytest.fixture
def marketing_purpose():
    return ConsentPurpose.objects.create(
        key="marketing_emails", category=ConsentPurpose.Category.MARKETING_EMAIL,
        label="Marketing emails", is_required=False,
    )


def test_consent_grant_and_withdraw_append_new_rows_never_mutate(user, talent_pool_purpose):
    services.set_consent(user=user, purpose_key="talent_pool", granted=True, method="settings")
    assert services.current_consent_status(user, "talent_pool") is True

    services.set_consent(user=user, purpose_key="talent_pool", granted=False, method="settings")
    assert services.current_consent_status(user, "talent_pool") is False

    # Both events are preserved — withdrawal never deleted/mutated the grant.
    history = ConsentRecord.objects.filter(user=user, purpose=talent_pool_purpose).order_by("created_at")
    assert list(history.values_list("status", flat=True)) == ["granted", "withdrawn"]


def test_consent_purposes_are_independent(user, talent_pool_purpose, marketing_purpose):
    services.set_consent(user=user, purpose_key="talent_pool", granted=True)
    # Marketing was never touched — defaults to not granted, independent of talent_pool.
    assert services.current_consent_status(user, "marketing_emails") is False
    assert services.current_consent_status(user, "talent_pool") is True


def test_required_purpose_cannot_be_withdrawn(user):
    ConsentPurpose.objects.create(
        key="necessary_thing", category=ConsentPurpose.Category.OTHER,
        label="Necessary thing", is_required=True,
    )
    with pytest.raises(ValueError):
        services.set_consent(user=user, purpose_key="necessary_thing", granted=False)


def test_consent_api_grant_withdraw(auth_client, talent_pool_purpose):
    resp = auth_client.post("/api/v1/legal/consent/", {"purpose": "talent_pool", "granted": True}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "granted"


# ── Cookie consent ────────────────────────────────────────────────────────────

def test_cookie_consent_works_anonymously_without_auth():
    resp = APIClient().post(
        "/api/v1/legal/cookie-consent/",
        {"action": "reject_non_essential", "categories": {"functional": False, "analytics": False, "marketing": False}},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    # Necessary is forced True regardless of what the client sent (or omitted).
    assert data["categories"]["necessary"] is True


def test_cookie_consent_accept_all(auth_client):
    resp = auth_client.post(
        "/api/v1/legal/cookie-consent/",
        {"action": "accept_all", "categories": {"functional": True, "analytics": True, "marketing": True}},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["action"] == "accept_all"


def test_sync_anonymous_cookie_consent_carries_choice_forward_on_login(user):
    """Directive item 6: a user's anonymous cookie choice should carry
    forward to their account at login — but must never broaden it."""
    anon = CookieConsent.objects.create(
        session_key="anon-session-abc", action=CookieConsent.Action.REJECT_NON_ESSENTIAL,
        categories={"necessary": True, "functional": False, "analytics": False, "marketing": False},
    )
    carried = services.sync_anonymous_cookie_consent_to_user(user=user, session_key="anon-session-abc")
    assert carried is not None
    assert carried.user_id == user.id
    assert carried.action == CookieConsent.Action.REJECT_NON_ESSENTIAL
    assert carried.categories == anon.categories  # copied verbatim, never broadened
    assert carried.carried_over_from_session_key == "anon-session-abc"
    assert carried.session_key == ""  # now owned by the user, not the anon session


def test_sync_anonymous_cookie_consent_noop_without_session_key(user):
    assert services.sync_anonymous_cookie_consent_to_user(user=user, session_key=None) is None
    assert services.sync_anonymous_cookie_consent_to_user(user=user, session_key="") is None
    assert not CookieConsent.objects.filter(user=user).exists()


def test_sync_anonymous_cookie_consent_noop_when_no_matching_anonymous_row(user):
    assert services.sync_anonymous_cookie_consent_to_user(
        user=user, session_key="nonexistent-session",
    ) is None
    assert not CookieConsent.objects.filter(user=user).exists()


def test_sync_anonymous_cookie_consent_never_overwrites_existing_user_choice(user):
    """If the user already has their own authenticated-session consent
    choice (e.g. from a previous login), carryover must never clobber it —
    even if a DIFFERENT anonymous session_key is passed in later."""
    existing = CookieConsent.objects.create(
        user=user, action=CookieConsent.Action.ACCEPT_ALL,
        categories={"necessary": True, "functional": True, "analytics": True, "marketing": True},
    )
    CookieConsent.objects.create(
        session_key="other-anon-session", action=CookieConsent.Action.REJECT_NON_ESSENTIAL,
        categories={"necessary": True, "functional": False, "analytics": False, "marketing": False},
    )
    result = services.sync_anonymous_cookie_consent_to_user(user=user, session_key="other-anon-session")
    assert result is None
    assert CookieConsent.objects.filter(user=user).count() == 1
    assert CookieConsent.objects.get(user=user).pk == existing.pk


def test_open_export_privacy_request_triggers_legacy_export(user):
    """Directive item 7: apps.legal.PrivacyRequest is canonical governance —
    opening an EXPORT request must trigger the REAL existing executor in
    apps.accounts (not a second, parallel implementation), and the legacy
    row must be linked back to this ticket."""
    from apps.accounts.models_gdpr import DataExportRequest

    req = services.open_privacy_request(user=user, request_type="export", jurisdiction="EG")
    export_request = DataExportRequest.objects.get(user=user)
    assert export_request.privacy_request_id == req.id
    assert req.events.filter(event_type="export_triggered").exists()


def test_open_export_privacy_request_reuses_in_flight_export(user):
    from apps.accounts.models_gdpr import DataExportRequest

    DataExportRequest.objects.create(user=user, status="processing")
    req = services.open_privacy_request(user=user, request_type="export", jurisdiction="EG")
    assert DataExportRequest.objects.filter(user=user).count() == 1
    assert req.events.filter(event_type="export_reused_existing").exists()


def test_open_delete_privacy_request_schedules_legacy_deletion(user):
    """Opening a DELETE request must schedule the real 30-day-grace legacy
    deletion flow, linked back to the PrivacyRequest ticket — never execute
    immediately."""
    from apps.accounts.models_gdpr import AccountDeletionRequest

    req = services.open_privacy_request(user=user, request_type="delete", jurisdiction="EG")
    deletion_request = AccountDeletionRequest.objects.get(user=user)
    assert deletion_request.privacy_request_id == req.id
    assert deletion_request.status == "pending"
    assert deletion_request.scheduled_for > timezone.now()
    assert req.events.filter(event_type="deletion_scheduled").exists()


def test_open_delete_privacy_request_reuses_existing_pending_deletion(user):
    from apps.accounts.models_gdpr import AccountDeletionRequest

    existing = AccountDeletionRequest.objects.create(
        user=user, scheduled_for=timezone.now() + timezone.timedelta(days=30),
    )
    req = services.open_privacy_request(user=user, request_type="delete", jurisdiction="EG")
    assert AccountDeletionRequest.objects.filter(user=user).count() == 1
    existing.refresh_from_db()
    assert existing.privacy_request_id == req.id
    assert req.events.filter(event_type="deletion_reused_existing").exists()


def test_login_carries_forward_anonymous_cookie_consent():
    """End-to-end: a visitor records a cookie choice anonymously, then logs
    in — the choice should now be visible as THEIR consent via
    GET /legal/cookie-consent/me/, without ever having to choose again."""
    user = User.objects.create_user(email="cookie-carryover@test.com", password="pw12345x")
    anon_client = APIClient()

    # Visitor records a choice anonymously (forces a session to exist).
    resp = anon_client.post(
        "/api/v1/legal/cookie-consent/",
        {"action": "reject_non_essential", "categories": {"functional": False, "analytics": False}},
        format="json",
    )
    assert resp.status_code == 201
    session_key = anon_client.session.session_key
    assert session_key  # the cookie-consent endpoint force-saves a session

    # Same browser (same session cookie) now logs in.
    login_resp = anon_client.post(
        "/api/v1/auth/login/", {"email": user.email, "password": "pw12345x"}, format="json",
    )
    assert login_resp.status_code == 200

    carried = CookieConsent.objects.filter(user=user).first()
    assert carried is not None
    assert carried.action == "reject_non_essential"
    assert carried.carried_over_from_session_key == session_key


def test_can_send_marketing_false_with_no_preference_row(user):
    """Directive item 11: default is opt-OUT, never opt-in-by-absence."""
    assert services.can_send_marketing(user, "email") is False
    assert services.can_send_marketing(user, "sms") is False


def test_can_send_marketing_true_when_opted_in(user):
    from apps.legal.models import MarketingPreference
    MarketingPreference.objects.create(user=user, email_marketing_opt_in=True, sms_marketing_opt_in=False)
    assert services.can_send_marketing(user, "email") is True
    assert services.can_send_marketing(user, "sms") is False


def test_can_send_marketing_false_when_unsubscribed_even_if_opted_in_flag_still_true(user):
    """An explicit unsubscribe is an absolute stop on every channel, even
    if a channel-specific boolean was somehow left True."""
    from apps.legal.models import MarketingPreference
    from django.utils import timezone as _tz
    MarketingPreference.objects.create(
        user=user, email_marketing_opt_in=True, sms_marketing_opt_in=True,
        unsubscribed_at=_tz.now(),
    )
    assert services.can_send_marketing(user, "email") is False
    assert services.can_send_marketing(user, "sms") is False


def test_can_send_marketing_false_for_inactive_user(user):
    from apps.legal.models import MarketingPreference
    MarketingPreference.objects.create(user=user, email_marketing_opt_in=True)
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert services.can_send_marketing(user, "email") is False


def test_can_send_marketing_rejects_unknown_channel(user):
    with pytest.raises(ValueError):
        services.can_send_marketing(user, "push")


def test_cookie_categories_public_endpoint_lists_necessary_as_essential():
    CookieCategory.objects.create(key="necessary", label="Strictly necessary", is_essential=True)
    CookieCategory.objects.create(key="analytics", label="Analytics", is_essential=False)
    resp = APIClient().get("/api/v1/legal/cookie-categories/")
    assert resp.status_code == 200
    necessary = next(c for c in resp.json()["data"] if c["key"] == "necessary")
    assert necessary["is_essential"] is True


# ── DSR / Privacy Requests ────────────────────────────────────────────────────

def test_open_privacy_request_and_owner_scoped_list(auth_client, user):
    resp = auth_client.post(
        "/api/v1/legal/privacy-requests/",
        {"request_type": "export", "details": "please export my data", "jurisdiction": "EG"},
        format="json",
    )
    assert resp.status_code == 201
    req_uuid = resp.json()["data"]["uuid"]

    # Owner can list/see their own request.
    listing = auth_client.get("/api/v1/legal/privacy-requests/")
    assert listing.status_code == 200

    detail = auth_client.get(f"/api/v1/legal/privacy-requests/{req_uuid}/")
    assert detail.status_code == 200

    # A different user cannot see it.
    other = User.objects.create_user(email="other-legal@test.com", password="pw12345x")
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    assert other_client.get(f"/api/v1/legal/privacy-requests/{req_uuid}/").status_code == 404


def test_dsr_due_at_computed_from_jurisdiction_profile(user):
    from apps.legal.models import JurisdictionPolicyProfile
    JurisdictionPolicyProfile.objects.create(jurisdiction="EG", dsr_sla_days=6)
    req = services.open_privacy_request(user=user, request_type="access", jurisdiction="EG")
    assert req.due_at is not None


def test_dsr_due_at_null_when_sla_not_configured(user):
    req = services.open_privacy_request(user=user, request_type="access", jurisdiction="OTHER")
    assert req.due_at is None


def test_admin_can_transition_dsr_and_event_is_logged(admin_client, user):
    req = services.open_privacy_request(user=user, request_type="delete", jurisdiction="EG")
    resp = admin_client.post(
        f"/api/v1/legal/admin/privacy-requests/{req.uuid}/transition/",
        {"status": "completed", "note": "Deleted scoped data."},
        format="json",
    )
    assert resp.status_code == 200
    req.refresh_from_db()
    assert req.status == "completed"
    assert req.events.filter(event_type="status:completed").exists()


def test_non_admin_cannot_access_dsr_admin_queue(auth_client):
    resp = auth_client.get("/api/v1/legal/admin/privacy-requests/")
    assert resp.status_code == 403


# ── AI disclosure guardrail ──────────────────────────────────────────────────

def test_ai_disclosure_cannot_claim_final_decision(admin_client):
    resp = admin_client.post(
        "/api/v1/legal/admin/ai-disclosures/",
        {
            "feature_key": "bad_feature", "feature_label": "Bad feature",
            "description": "x", "makes_final_decision": True,
        },
        format="json",
    )
    assert resp.status_code == 400


def test_ai_disclosure_public_list(admin_client):
    AIProcessingDisclosure.objects.create(
        feature_key="rasheed", feature_label="Rasheed", description="Chat assistant.",
    )
    resp = APIClient().get("/api/v1/legal/ai-disclosures/")
    assert resp.status_code == 200
    assert any(d["feature_key"] == "rasheed" for d in resp.json()["data"])


# ── Legal entity config: unconfigured by default ─────────────────────────────

def test_legal_entity_config_starts_unconfigured():
    resp = APIClient().get("/api/v1/legal/entity/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_configured"] is False
    assert data["legal_entity_name"] == ""


def test_admin_can_configure_legal_entity(admin_client):
    resp = admin_client.patch(
        "/api/v1/legal/admin/entity/",
        {"legal_entity_name": "USAM Test Co.", "registered_address": "Cairo, Egypt",
         "privacy_contact_email": "privacy@example.com"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_configured"] is True

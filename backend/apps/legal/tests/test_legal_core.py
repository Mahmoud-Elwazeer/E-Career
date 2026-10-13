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


# ── Admin version editing rules ───────────────────────────────────────────────

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

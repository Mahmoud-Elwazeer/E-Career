"""
First-launch legal flow — end-to-end test (directive item 23).

Simulates the exact sequence a brand-new deployment goes through:
  1. Fresh seed via `manage.py seed_legal` (default — no --activate-drafts).
  2. Confirm nothing is public yet (DRAFT only, legal_readiness reports
     CONFIGURATION_REQUIRED, not READY).
  3. An admin configures the legal entity.
  4. An admin reviews + edits a draft to resolve the unresolved marker
     (simulating real legal review — the seeded text is never activated
     verbatim since it would still contain "REQUIRES LEGAL REVIEW").
  5. Admin promotes the version through the real lifecycle: DRAFT -> IN_REVIEW
     -> APPROVED -> ACTIVE (via the same services.activate_version used by
     the Admin Legal Control Plane).
  6. The policy is now genuinely public (policy_detail serves it).
  7. A new user signs up and the frontend's real signup-consent flow
     (policy_accept) successfully binds their acceptance to the version
     that is now active.

This is the one test that exercises the WHOLE pipeline end-to-end rather
than any single piece in isolation — it would have caught the original
directive-critical bug (seed_legal silently auto-activating unreviewed
text) if it had existed before this hardening pass.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.legal.models import PolicyDocument, PolicyVersion, LegalEntityConfig
from apps.legal import services
from apps.legal.readiness_service import check_legal_readiness, UNRESOLVED_MARKER

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_first_launch_legal_flow_end_to_end():
    # ── 1. Fresh seed ────────────────────────────────────────────────────
    call_command("seed_legal")

    terms = PolicyDocument.objects.get(slug="terms")
    privacy = PolicyDocument.objects.get(slug="privacy")
    assert terms.live_version is None
    assert privacy.live_version is None

    # ── 2. Readiness correctly reports CONFIGURATION_REQUIRED, not READY ──
    report = check_legal_readiness()
    assert report.overall_state == "CONFIGURATION_REQUIRED"

    # ── 3. Admin configures the legal entity ────────────────────────────
    admin = User.objects.create_user(email="launch-admin@test.com", password="pw12345x", role="admin")
    admin_client = APIClient()
    admin_client.force_authenticate(user=admin)

    entity_resp = admin_client.patch(
        "/api/v1/legal/admin/entity/",
        {
            "legal_entity_name": "USAM Career Technologies LLC",
            "registered_address": "123 Example Street, Cairo, Egypt",
            "privacy_contact_email": "privacy@example.com",
            "default_refund_window_days": 14,
        },
        format="json",
    )
    assert entity_resp.status_code == 200
    assert LegalEntityConfig.load().is_configured is True

    # ── 4. Admin reviews and resolves the draft's unresolved marker ──────
    # Real legal review replaces placeholder text — simulating that here by
    # editing the seeded draft's content before promoting it.
    terms_draft = terms.versions.filter(status=PolicyVersion.Status.DRAFT).first()
    assert terms_draft is not None
    assert UNRESOLVED_MARKER in terms_draft.content_markdown  # confirms the seed is realistic

    edit_resp = admin_client.patch(
        f"/api/v1/legal/admin/versions/{terms_draft.uuid}/",
        {"content_markdown": terms_draft.content_markdown.replace(
            UNRESOLVED_MARKER, "USAM Career Technologies LLC",
        )},
        format="json",
    )
    assert edit_resp.status_code == 200

    privacy_draft = privacy.versions.filter(status=PolicyVersion.Status.DRAFT).first()
    admin_client.patch(
        f"/api/v1/legal/admin/versions/{privacy_draft.uuid}/",
        {"content_markdown": privacy_draft.content_markdown.replace(
            UNRESOLVED_MARKER, "USAM Career Technologies LLC",
        )},
        format="json",
    )

    # ── 5. Promote through the real lifecycle: DRAFT -> IN_REVIEW -> APPROVED -> ACTIVE
    for draft_uuid in (terms_draft.uuid, privacy_draft.uuid):
        review_resp = admin_client.post(
            f"/api/v1/legal/admin/versions/{draft_uuid}/transition/",
            {"status": "in_review"}, format="json",
        )
        assert review_resp.status_code == 200
        approve_resp = admin_client.post(
            f"/api/v1/legal/admin/versions/{draft_uuid}/transition/",
            {"status": "approved"}, format="json",
        )
        assert approve_resp.status_code == 200
        activate_resp = admin_client.post(
            f"/api/v1/legal/admin/versions/{draft_uuid}/transition/",
            {"status": "active"}, format="json",
        )
        assert activate_resp.status_code == 200, activate_resp.json()

    terms.refresh_from_db()
    privacy.refresh_from_db()
    assert terms.live_version is not None
    assert privacy.live_version is not None
    assert UNRESOLVED_MARKER not in terms.live_version.content_markdown

    # ── 6. The policy is now genuinely public ────────────────────────────
    public_resp = APIClient().get("/api/v1/legal/policies/terms/")
    assert public_resp.status_code == 200
    assert "USAM Career Technologies LLC" in public_resp.json()["data"]["content_markdown"]

    # ── 7. A brand-new user signs up and their acceptance binds correctly ─
    new_user = User.objects.create_user(email="first-real-user@test.com", password="pw12345x")
    user_client = APIClient()
    user_client.force_authenticate(user=new_user)

    accept_terms_resp = user_client.post(
        "/api/v1/legal/policies/terms/accept/", {"method": "signup"}, format="json",
    )
    accept_privacy_resp = user_client.post(
        "/api/v1/legal/policies/privacy/accept/", {"method": "signup"}, format="json",
    )
    assert accept_terms_resp.status_code == 201
    assert accept_privacy_resp.status_code == 201

    assert new_user.legal_acceptances.filter(policy_version=terms.live_version).exists()
    assert new_user.legal_acceptances.filter(policy_version=privacy.live_version).exists()
    assert services.needs_reacceptance(new_user, "terms") is False
    assert services.needs_reacceptance(new_user, "privacy") is False

    # ── Final check: readiness for THESE two documents is now clean ──────
    final_report = check_legal_readiness()
    terms_check = next(c for c in final_report.checks if c.key == "document.terms")
    privacy_check = next(c for c in final_report.checks if c.key == "document.privacy")
    assert terms_check.state == "READY"
    assert privacy_check.state == "READY"

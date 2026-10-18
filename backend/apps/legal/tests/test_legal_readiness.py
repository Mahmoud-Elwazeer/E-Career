"""
legal_readiness command / readiness_service — tests.

Covers the directive-critical invariant: readiness reporting must never
silently claim READY while an unreviewed marker is live, and must correctly
classify every known gap into CONFIGURATION_REQUIRED vs LEGAL_REVIEW_REQUIRED
vs BLOCKED vs READY.
"""
import json

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.legal import services
from apps.legal.models import (
    PolicyDocument, PolicyVersion, LegalEntityConfig, JurisdictionPolicyProfile,
    RetentionPolicy, ProcessorRecord,
)
from apps.legal.readiness_service import (
    check_legal_readiness, UNRESOLVED_MARKER, UNRESOLVED_MARKER_AR,
    scan_version_for_placeholders, scan_active_versions_for_placeholders,
)

pytestmark = pytest.mark.django_db


@override_settings(DEBUG=True)
def _activate_everything():
    """Seed + activate drafts + resolve every legal-review gap, simulating
    a fully-configured, legally-reviewed launch state. DEBUG=True satisfies
    the --activate-drafts production guard added in the 2026-09-21
    acceptance pass (pytest-django forces DEBUG=False by default, so every
    caller of this helper needs this override active for the duration of
    the seed call — applying it directly to this helper function, rather
    than to each test, keeps that single reusable)."""
    call_command("seed_legal", "--activate-drafts")

    cfg = LegalEntityConfig.load()
    cfg.legal_entity_name = "USAM Career Technologies LLC"
    cfg.registered_address = "123 Example Street, Cairo, Egypt"
    cfg.privacy_contact_email = "privacy@example.com"
    cfg.default_refund_window_days = 14
    cfg.save()

    for j in JurisdictionPolicyProfile.objects.all():
        j.minor_age_threshold = 18
        j.requires_legal_review = False
        j.save()

    RetentionPolicy.objects.update(requires_legal_review=False, retention_period_days=365)
    ProcessorRecord.objects.update(dpa_signed=True)

    # Strip the unresolved marker (English AND Arabic — continuation pass
    # seeds both locales) from every ACTIVE version's content for this
    # simulation (a real admin would publish reviewed, marker-free text).
    for version in PolicyVersion.objects.filter(status=PolicyVersion.Status.ACTIVE):
        content = version.content_markdown.replace(UNRESOLVED_MARKER, "Reviewed")
        content = content.replace(UNRESOLVED_MARKER_AR, "تمت المراجعة")
        version.content_markdown = content
        version.save(update_fields=["content_markdown"])


def test_fresh_seed_without_activation_reports_configuration_required():
    """Right after a plain `seed_legal` (no --activate-drafts), nothing is
    public yet — readiness must report CONFIGURATION_REQUIRED, not BLOCKED
    (nothing unsafe is live) and not READY (core documents aren't active)."""
    call_command("seed_legal")
    report = check_legal_readiness()
    assert report.overall_state == "CONFIGURATION_REQUIRED"
    doc_checks = [c for c in report.checks if c.key.startswith("document.")]
    assert all(c.state == "CONFIGURATION_REQUIRED" for c in doc_checks)


@override_settings(DEBUG=True)
def test_activated_seed_with_unresolved_marker_is_blocked():
    """If drafts get force-activated via --activate-drafts (test/staging
    convenience) WITHOUT stripping the seeded 'REQUIRES LEGAL REVIEW' marker,
    readiness must report BLOCKED — this is the exact unsafe state the
    directive says must never be presented as launch-ready."""
    call_command("seed_legal", "--activate-drafts")
    report = check_legal_readiness()
    assert report.overall_state == "BLOCKED"
    blocked = [c for c in report.checks if c.state == "BLOCKED"]
    assert blocked, "Expected at least one BLOCKED check for the unresolved marker."
    assert any("terms" in c.key for c in blocked)


def test_fully_configured_and_reviewed_state_reports_ready():
    _activate_everything()
    report = check_legal_readiness()
    assert report.overall_state == "READY"


def test_legal_review_required_when_minor_age_threshold_unconfirmed():
    _activate_everything()
    profile = JurisdictionPolicyProfile.objects.get(jurisdiction="EG")
    profile.minor_age_threshold = None
    profile.save()
    report = check_legal_readiness()
    assert report.overall_state == "LEGAL_REVIEW_REQUIRED"


def test_legal_review_required_when_retention_policy_unreviewed():
    _activate_everything()
    RetentionPolicy.objects.update(requires_legal_review=True)
    report = check_legal_readiness()
    assert report.overall_state == "LEGAL_REVIEW_REQUIRED"


def test_configuration_required_when_legal_entity_blank():
    _activate_everything()
    cfg = LegalEntityConfig.load()
    cfg.legal_entity_name = ""
    cfg.save()
    report = check_legal_readiness()
    assert report.overall_state == "CONFIGURATION_REQUIRED"


def test_json_output_is_valid_and_never_exposes_secrets():
    call_command("seed_legal")
    out = []

    class _Capture:
        def write(self, s):
            out.append(s)

    call_command("legal_readiness", "--json", stdout=_Capture())
    payload = json.loads("".join(out))
    assert "overall_state" in payload
    assert isinstance(payload["checks"], list)
    serialized = json.dumps(payload).lower()
    for forbidden in ("secret", "api_key", "password", "token"):
        assert forbidden not in serialized


@override_settings(DEBUG=True)
def test_scan_version_for_placeholders_detects_bracket_todo_and_example_content(settings):
    doc = PolicyDocument.objects.create(slug="x", doc_type=PolicyDocument.DocType.TERMS, title="X")
    version = PolicyVersion.objects.create(
        document=doc, version_label="1", locale="en", status=PolicyVersion.Status.DRAFT,
        content_markdown="Contact [Insert Company Name Here] at legal@example.com. TODO: fix this.",
    )
    findings = scan_version_for_placeholders(version)
    joined = " | ".join(findings)
    assert "bracket_placeholder" in joined
    assert "example_email" in joined
    assert "todo_fixme" in joined


def test_scan_version_for_placeholders_clean_content_has_no_findings():
    doc = PolicyDocument.objects.create(slug="y", doc_type=PolicyDocument.DocType.PRIVACY, title="Y")
    version = PolicyVersion.objects.create(
        document=doc, version_label="1", locale="en", status=PolicyVersion.Status.DRAFT,
        content_markdown="# Privacy Policy\nThis is real, reviewed content with no placeholders.",
    )
    assert scan_version_for_placeholders(version) == []


def test_scan_version_for_placeholders_never_flags_a_real_markdown_cross_link():
    """Regression guard: a real internal cross-link whose link text happens
    to start with a word like "Your" (e.g. the real seeded "[Your Data
    Rights](/legal/data-rights)" link) must never be mistaken for a
    template placeholder — this exact false positive was found and fixed
    during this pass."""
    doc = PolicyDocument.objects.create(slug="z", doc_type=PolicyDocument.DocType.DATA_RIGHTS, title="Z")
    version = PolicyVersion.objects.create(
        document=doc, version_label="1", locale="en", status=PolicyVersion.Status.DRAFT,
        content_markdown="See [Your Data Rights](/legal/data-rights) and [Company Name Inc.](https://example-registry.gov) for details.",
    )
    assert scan_version_for_placeholders(version) == []


@override_settings(DEBUG=True)
def test_scan_active_versions_for_placeholders_only_checks_active_not_draft():
    """DRAFT content is expected to contain placeholders — the directive's
    own seeded text does, pending legal review. Only ACTIVE versions matter
    for this scan."""
    call_command("seed_legal")  # creates DRAFTs with real "REQUIRES LEGAL REVIEW" markers
    assert scan_active_versions_for_placeholders() == {}  # nothing ACTIVE yet, so nothing flagged


def test_placeholder_scan_blocks_readiness_when_an_active_version_has_a_leftover_placeholder():
    """Simulates the one gap activation-time blocking alone can't catch: a
    placeholder typed directly into an already-ACTIVE version's content via
    a later edit (editing content and activating are separate admin
    actions) — the independent after-the-fact scan must catch it."""
    _activate_everything()
    terms = PolicyDocument.objects.get(slug="terms")
    active = terms.live_version
    active.content_markdown += "\nContact us at support@example.com for more info."
    active.save(update_fields=["content_markdown"])

    report = check_legal_readiness()
    assert report.overall_state == "BLOCKED"
    placeholder_check = next(c for c in report.checks if c.key == "placeholder_scan")
    assert placeholder_check.state == "BLOCKED"


@override_settings(DEBUG=True)
def test_readiness_check_never_mutates_data():
    call_command("seed_legal", "--activate-drafts")
    before = list(PolicyVersion.objects.values_list("uuid", "status", "content_markdown"))
    check_legal_readiness()
    after = list(PolicyVersion.objects.values_list("uuid", "status", "content_markdown"))
    assert before == after

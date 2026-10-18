"""
seed_legal management command — end-to-end smoke test.

Confirms the full seed runs cleanly (idempotent, no crashes) and populates
every table the Legal Center / Admin Legal Control Plane / Privacy Center
depend on, including the processor register (previously unseeded).
"""
import pytest
from django.core.management import call_command

from apps.legal.models import (
    PolicyDocument, PolicyVersion, ConsentPurpose, CookieCategory,
    JurisdictionPolicyProfile, LegalEntityConfig, AIProcessingDisclosure,
    RetentionPolicy, ProcessorRecord,
)

pytestmark = pytest.mark.django_db


def test_seed_legal_runs_cleanly_and_is_idempotent():
    call_command("seed_legal")
    call_command("seed_legal")  # second run must not crash or duplicate


def test_seed_legal_default_behavior_creates_drafts_never_auto_publishes():
    """Directive-critical: seeding must NOT silently publish unreviewed
    legal text. Default (no --activate-drafts) creates DRAFT versions only
    — no document has a live/ACTIVE version, and the public endpoint
    correctly reports nothing active yet."""
    call_command("seed_legal")
    docs = PolicyDocument.objects.filter(is_active=True)
    # terms, privacy, cookies, refunds, payment-security, security,
    # ai-disclosure, acceptable-use, data-rights, subprocessors,
    # international-transfers, candidate-privacy, business-terms
    assert docs.count() == 13
    for doc in docs:
        assert doc.live_version is None, (
            f"{doc.slug} has a live ACTIVE version right after seeding — "
            f"this means seed_legal silently published unreviewed text."
        )
        version = doc.versions.filter(locale="en").first()
        assert version is not None
        assert version.status == PolicyVersion.Status.DRAFT
        # Every document must also get an Arabic draft seeded, flagged as
        # an unreviewed machine translation (continuation pass).
        ar_version = doc.versions.filter(locale="ar").first()
        assert ar_version is not None, f"{doc.slug} has no Arabic (ar) draft seeded."
        assert ar_version.is_machine_translated is True
        assert ar_version.status == PolicyVersion.Status.DRAFT


def test_seed_legal_activate_drafts_flag_publishes_for_staging_convenience():
    """The --activate-drafts flag exists ONLY for test/staging convenience
    and must be explicitly passed — never the default."""
    call_command("seed_legal", "--activate-drafts")
    docs = PolicyDocument.objects.filter(is_active=True)
    assert docs.count() == 13
    for doc in docs:
        assert doc.live_version is not None


def test_seed_legal_never_touches_an_existing_active_version_on_rerun():
    """Re-running seed_legal must NEVER replace/retire an already-ACTIVE
    production policy — the real non-negotiable this gap-fix protects."""
    call_command("seed_legal", "--activate-drafts")
    terms_doc = PolicyDocument.objects.get(slug="terms")
    active_before = terms_doc.live_version
    assert active_before is not None
    original_content = active_before.content_markdown

    # Simulate an admin having since activated a newer v2 that supersedes
    # the seed's own text — re-running seed_legal must not touch it.
    call_command("seed_legal")  # no --activate-drafts this time
    terms_doc.refresh_from_db()
    active_after = terms_doc.live_version
    assert active_after is not None
    assert active_after.pk == active_before.pk
    assert active_after.content_markdown == original_content
    assert active_after.status == PolicyVersion.Status.ACTIVE  # never retired by reseeding


def test_seed_legal_populates_processor_register_from_real_integrations_only():
    call_command("seed_legal")
    names = set(ProcessorRecord.objects.values_list("name", flat=True))
    # Confirmed-by-code vendors only.
    assert "Amazon Web Services (AWS)" in names
    assert "Stripe, Inc." in names
    assert "Typesense" in names
    assert "Sentry" in names
    # dpa_signed must never default to a fabricated True/False — stays
    # unknown (NULL) until legal confirms it.
    for proc in ProcessorRecord.objects.all():
        assert proc.dpa_signed is None


def test_seed_legal_processor_register_distinguishes_model_path_from_direct_processor():
    """Directive item 21: Anthropic must be represented as a model path
    routed through AWS Bedrock infrastructure, never implied to be a
    direct, separately-contracted processor of USAM's data."""
    call_command("seed_legal")
    anthropic = ProcessorRecord.objects.filter(name__icontains="Anthropic").first()
    assert anthropic is not None
    assert "model_path_via_infrastructure" in anthropic.notes
    assert "NOT a direct API relationship" in anthropic.name or "via AWS Bedrock" in anthropic.name
    assert anthropic.dpa_signed is None  # no direct USAM-Anthropic DPA to confirm or deny

    aws = ProcessorRecord.objects.filter(name__icontains="Amazon Web Services").first()
    assert aws is not None
    assert "cloud_infrastructure" in aws.notes

    typesense = ProcessorRecord.objects.filter(name="Typesense").first()
    assert typesense is not None
    assert "self_hosted_infrastructure" in typesense.notes


def test_seed_legal_leaves_legal_entity_unconfigured():
    call_command("seed_legal")
    cfg = LegalEntityConfig.load()
    assert cfg.is_configured is False
    assert cfg.legal_entity_name == ""


def test_seed_legal_leaves_minor_age_threshold_unconfirmed_for_both_jurisdictions():
    call_command("seed_legal")
    for j in JurisdictionPolicyProfile.objects.all():
        assert j.minor_age_threshold is None


def test_seed_legal_populates_consent_purposes_and_cookie_categories():
    call_command("seed_legal")
    assert ConsentPurpose.objects.count() >= 7
    assert CookieCategory.objects.filter(key="necessary", is_essential=True).exists()


def test_seed_legal_ai_disclosures_never_claim_final_decision():
    call_command("seed_legal")
    assert AIProcessingDisclosure.objects.count() >= 4
    assert not AIProcessingDisclosure.objects.filter(makes_final_decision=True).exists()

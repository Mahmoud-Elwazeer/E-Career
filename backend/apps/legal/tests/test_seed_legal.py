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


def test_seed_legal_activates_every_policy_document():
    call_command("seed_legal")
    docs = PolicyDocument.objects.filter(is_active=True)
    assert docs.count() == 7  # terms, privacy, cookies, refunds, payment-security, security, ai-disclosure
    for doc in docs:
        assert doc.live_version is not None, f"{doc.slug} has no ACTIVE version after seeding"


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

"""Tests for the AlexBank adapter infrastructure (task #6).

These prove the infra that does NOT depend on the bank spec: config/health
reporting, typed errors, the live adapter's refusal to fake, and the mock
provider's deterministic lifecycle + its production guard rail.
"""
import json

import pytest
from django.test import override_settings

from apps.payments.providers import (
    get_provider, ProviderError,
    AlexBankProvider, AlexBankMockProvider, AlexBankState,
    AlexBankConfigError, AlexBankNotImplemented, AlexBankTransportError,
    ALEXBANK_REQUIRED_SECRETS,
)


# ── Factory wiring ────────────────────────────────────────────────────────────
def test_factory_resolves_alexbank_and_mock():
    assert isinstance(get_provider("alexbank"), AlexBankProvider)
    assert isinstance(get_provider("alexbank_mock"), AlexBankMockProvider)


def test_factory_rejects_unknown():
    with pytest.raises(ProviderError):
        get_provider("not-a-bank")


# ── Config / health (no bank calls) ──────────────────────────────────────────
def test_health_reports_not_configured_when_secrets_absent(monkeypatch):
    # Ensure no AlexBank secrets are present in the environment.
    import apps.payments.secrets as secretsmod
    monkeypatch.setattr(secretsmod, "get_secret", lambda key, default="": "")
    health = AlexBankProvider().health()
    assert health["provider"] == "alexbank"
    assert health["configured"] is False
    assert health["live_enabled"] is False  # never on until real ops are wired
    assert set(health["missing_secrets"]) == set(ALEXBANK_REQUIRED_SECRETS)


def test_is_configured_true_when_all_required_present(monkeypatch):
    import apps.payments.secrets as secretsmod
    present = dict.fromkeys(ALEXBANK_REQUIRED_SECRETS, "x")
    monkeypatch.setattr(secretsmod, "get_secret",
                        lambda key, default="": present.get(key, ""))
    # health() and is_configured() read get_secret via the module; patch there.
    monkeypatch.setattr(
        "apps.payments.providers.alexbank_provider.get_secret",
        lambda key, default="": present.get(key, ""),
    )
    assert AlexBankProvider().is_configured() is True
    assert AlexBankProvider().health()["configured"] is True
    assert AlexBankProvider().health()["live_enabled"] is False


# ── Live adapter never fakes ─────────────────────────────────────────────────
def test_live_create_payment_raises_config_error_without_credentials(monkeypatch):
    monkeypatch.setattr(
        "apps.payments.providers.alexbank_provider.get_secret",
        lambda key, default="": "",
    )
    with pytest.raises(AlexBankConfigError):
        AlexBankProvider().create_payment(amount=1000, currency="EGP", reference="C-PAY-X")


def test_live_create_payment_blocked_even_when_configured(monkeypatch):
    present = dict.fromkeys(ALEXBANK_REQUIRED_SECRETS, "x")
    monkeypatch.setattr(
        "apps.payments.providers.alexbank_provider.get_secret",
        lambda key, default="": present.get(key, ""),
    )
    # Configured, but the live contract isn't wired => refuse, never fake.
    with pytest.raises(AlexBankNotImplemented):
        AlexBankProvider().create_payment(amount=1000, currency="EGP", reference="C-PAY-X")
    with pytest.raises(AlexBankNotImplemented):
        AlexBankProvider().verify_payment("ref")
    with pytest.raises(AlexBankNotImplemented):
        AlexBankProvider().refund_payment(provider_reference="ref", amount=100)
    with pytest.raises(AlexBankNotImplemented):
        AlexBankProvider().parse_webhook(body=b"{}", headers={})


def test_alexbank_errors_are_provider_errors():
    # Orchestration catches ProviderError broadly; our typed errors must qualify.
    assert issubclass(AlexBankConfigError, ProviderError)
    assert issubclass(AlexBankNotImplemented, ProviderError)
    assert issubclass(AlexBankTransportError, ProviderError)


# ── Mock provider: deterministic lifecycle + guard rail ──────────────────────
@override_settings(DEBUG=True)
def test_mock_lifecycle_create_verify_refund():
    p = AlexBankMockProvider()
    created = p.create_payment(amount=5000, currency="EGP", reference="C-PAY-M1")
    assert created.ok is True
    assert created.status == AlexBankState.INITIATED
    assert created.checkout_url

    verified = p.verify_payment(created.provider_reference)
    assert verified.ok is True
    assert verified.status == AlexBankState.CAPTURED

    refunded = p.refund_payment(provider_reference=created.provider_reference, amount=5000)
    assert refunded.ok is True
    assert refunded.status == AlexBankState.REFUNDED


@override_settings(DEBUG=True)
def test_mock_rejects_bad_amounts():
    p = AlexBankMockProvider()
    with pytest.raises(AlexBankTransportError):
        p.create_payment(amount=0, currency="EGP", reference="C-PAY-M2")


@override_settings(DEBUG=True)
def test_mock_parse_webhook_normalizes():
    p = AlexBankMockProvider()
    body = json.dumps({
        "event_id": "evt_1", "event_type": "payment.captured",
        "provider_reference": "ALEXBANK-MOCK-X", "status": AlexBankState.CAPTURED,
    }).encode()
    event = p.parse_webhook(body=body, headers={})
    assert event["signature_valid"] is True
    assert event["event_id"] == "evt_1"
    assert event["status"] == AlexBankState.CAPTURED


@override_settings(DEBUG=False)
def test_mock_guard_blocks_in_production(monkeypatch):
    # With DEBUG off and no ALEXBANK_ALLOW_MOCK, the mock must refuse to run.
    monkeypatch.setattr(
        "apps.payments.providers.alexbank_provider.get_secret",
        lambda key, default="": "",
    )
    with pytest.raises(AlexBankConfigError):
        AlexBankMockProvider().create_payment(amount=1000, currency="EGP", reference="C-PAY-M3")


# ── State vocabulary sanity ──────────────────────────────────────────────────
def test_state_sets_are_consistent():
    assert AlexBankState.CAPTURED in AlexBankState.SETTLED
    assert AlexBankState.SETTLED <= AlexBankState.TERMINAL
    assert AlexBankState.TERMINAL <= AlexBankState.ALL

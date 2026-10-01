"""
AlexBank (Bank of Alexandria) adapter.

Status: INFRASTRUCTURE COMPLETE, LIVE API BLOCKED on the bank's specification.

What is built here NOW (does not depend on the bank spec):
  - the full lifecycle/state vocabulary a card/bank payment moves through,
  - typed errors that separate "we are misconfigured" from "the bank failed"
    from "this isn't implemented yet",
  - config validation + a health probe that reports readiness WITHOUT calling
    the bank (so ops can see status before any contract exists),
  - a deterministic MOCK provider so the whole order->pay->verify->refund flow
    can be integration-tested against AlexBank's SHAPE today.

What is deliberately NOT built (needs the real bank contract — see
docs/ALEXBANK_INTEGRATION_CHECKLIST.md):
  - the actual request/response bodies, endpoints, auth signing, 3-D Secure
    redirect handling, webhook/callback payload parsing and settlement format.

The LIVE adapter NEVER fakes a success. Every live operation raises
AlexBankNotImplemented until the real contract is wired, so no fabricated money
movement can reach production through this adapter. Credentials resolve through
the secrets helper (AWS Secrets Manager), never hard-coded.
"""
from __future__ import annotations

from dataclasses import dataclass

from .base import PaymentProvider, ProviderResult, ProviderError
from ..secrets import get_secret


# ── Lifecycle states ─────────────────────────────────────────────────────────
class AlexBankState:
    """Normalized payment lifecycle, provider-agnostic in spirit but named here
    so the real adapter maps the bank's native statuses onto these.

    These map cleanly onto the platform's Payment.Status state machine:
        INITIATED -> created/pending
        AUTHORIZED/PENDING_3DS -> processing
        CAPTURED -> succeeded
        FAILED/CANCELLED/EXPIRED -> failed/cancelled
        REFUNDED -> refunded
    """

    INITIATED = "initiated"
    PENDING_3DS = "pending_3ds"      # customer must complete 3-D Secure
    AUTHORIZED = "authorized"        # funds held, not yet captured
    CAPTURED = "captured"            # money captured (success)
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"

    ALL = {
        INITIATED, PENDING_3DS, AUTHORIZED, CAPTURED,
        FAILED, CANCELLED, EXPIRED, REFUNDED,
    }

    # States that mean "money is in" for reconciliation.
    SETTLED = {CAPTURED}
    # Terminal states no further transition is expected from.
    TERMINAL = {CAPTURED, FAILED, CANCELLED, EXPIRED, REFUNDED}


# ── Typed errors ─────────────────────────────────────────────────────────────
class AlexBankError(ProviderError):
    """Base for all AlexBank adapter errors (subclass of ProviderError so the
    orchestration layer's existing `except ProviderError` keeps working)."""


class AlexBankConfigError(AlexBankError):
    """Credentials/configuration missing or invalid — our fault, not the bank's."""


class AlexBankTransportError(AlexBankError):
    """The bank was reached but the call failed (network, HTTP, bank error)."""


class AlexBankNotImplemented(AlexBankError):
    """A live operation was invoked before the real bank contract is wired.
    This is what guarantees the live adapter can never fake a success."""


# ── Config descriptor ────────────────────────────────────────────────────────
# The secret KEYS the live adapter needs. VALUES are supplied later by the user
# from the real bank onboarding (see the integration checklist). Listing the
# keys here does NOT invent the bank's API — it only declares what we must be
# handed before we can go live.
REQUIRED_SECRETS = ("ALEXBANK_MERCHANT_ID", "ALEXBANK_API_KEY", "ALEXBANK_BASE_URL")
OPTIONAL_SECRETS = (
    "ALEXBANK_WEBHOOK_SECRET",   # for callback signature verification
    "ALEXBANK_TERMINAL_ID",      # some acquirers scope by terminal
)


@dataclass(frozen=True)
class AlexBankConfig:
    merchant_id: str
    api_key: str
    base_url: str
    webhook_secret: str = ""
    terminal_id: str = ""

    @property
    def is_complete(self) -> bool:
        return bool(self.merchant_id and self.api_key and self.base_url)


def load_config() -> AlexBankConfig:
    """Resolve AlexBank config from the secrets helper. Does NOT contact the
    bank and never raises — call `.is_complete` to check readiness."""
    return AlexBankConfig(
        merchant_id=get_secret("ALEXBANK_MERCHANT_ID"),
        api_key=get_secret("ALEXBANK_API_KEY"),
        base_url=get_secret("ALEXBANK_BASE_URL"),
        webhook_secret=get_secret("ALEXBANK_WEBHOOK_SECRET"),
        terminal_id=get_secret("ALEXBANK_TERMINAL_ID"),
    )


class AlexBankProvider(PaymentProvider):
    """Live AlexBank adapter. Config/health are usable now; money operations
    remain blocked (raise AlexBankNotImplemented) until the bank contract lands."""

    name = "alexbank"

    # ── Config / readiness (safe to call anytime, never touches the bank) ──
    def config(self) -> AlexBankConfig:
        return load_config()

    def is_configured(self) -> bool:
        return self.config().is_complete

    def health(self) -> dict:
        """Report adapter readiness WITHOUT calling the bank.

        Returns a dict ops/admin can surface:
            configured      — all required secrets present
            live_enabled    — whether live money ops would run (always False
                              until the contract is implemented)
            missing_secrets — which required keys are absent
        """
        cfg = self.config()
        missing = [k for k in REQUIRED_SECRETS if not get_secret(k)]
        return {
            "provider": self.name,
            "configured": cfg.is_complete,
            "live_enabled": False,  # flips to True only when real ops are wired
            "missing_secrets": missing,
            "note": (
                "AlexBank adapter infrastructure is in place; live money "
                "operations are blocked pending the bank's API specification."
            ),
        }

    def _require_credentials(self) -> AlexBankConfig:
        cfg = self.config()
        if not cfg.is_complete:
            missing = [k for k in REQUIRED_SECRETS if not get_secret(k)]
            raise AlexBankConfigError(
                "AlexBank not configured. Provide "
                + ", ".join(missing)
                + " via AWS Secrets Manager."
            )
        return cfg

    # ── Money operations (blocked until the real contract is supplied) ──
    def create_payment(self, *, amount, currency, reference, metadata=None):
        self._require_credentials()
        raise AlexBankNotImplemented(
            "AlexBank create_payment awaiting the bank's payment-initiation "
            "contract. See docs/ALEXBANK_INTEGRATION_CHECKLIST.md."
        )

    def verify_payment(self, provider_reference):
        self._require_credentials()
        raise AlexBankNotImplemented(
            "AlexBank verify_payment awaiting the bank's status/query contract."
        )

    def refund_payment(self, *, provider_reference, amount):
        self._require_credentials()
        raise AlexBankNotImplemented(
            "AlexBank refund_payment awaiting the bank's refund contract."
        )

    def parse_webhook(self, *, body, headers):
        self._require_credentials()
        raise AlexBankNotImplemented(
            "AlexBank parse_webhook awaiting the bank's callback payload + "
            "signature specification."
        )


class AlexBankMockProvider(PaymentProvider):
    """Deterministic AlexBank stand-in for integration testing.

    It models the AlexBank SHAPE (lifecycle states, ProviderResult contract)
    so the order->pay->verify->refund flow can be exercised end to end before
    the real bank is wired. It is NOT the bank and performs NO real settlement.

    Guard rail: this provider is opt-in via the factory name "alexbank_mock"
    and refuses to run unless settings.DEBUG is True or
    ALEXBANK_ALLOW_MOCK is explicitly enabled, so it can never silently stand in
    for the live bank in production.
    """

    name = "alexbank_mock"

    def _guard(self):
        from django.conf import settings
        allow = bool(getattr(settings, "DEBUG", False)) or get_secret("ALEXBANK_ALLOW_MOCK") in ("1", "true", "True")
        if not allow:
            raise AlexBankConfigError(
                "AlexBankMockProvider is disabled. It is for tests/sandbox only "
                "(set DEBUG or ALEXBANK_ALLOW_MOCK). Never use it in production."
            )

    def create_payment(self, *, amount, currency, reference, metadata=None):
        self._guard()
        if int(amount) <= 0:
            raise AlexBankTransportError("Mock: amount must be positive")
        return ProviderResult(
            ok=True,
            provider_reference=f"ALEXBANK-MOCK-{reference}",
            status=AlexBankState.INITIATED,
            checkout_url=f"https://sandbox.alexbank.invalid/pay/{reference}",
            raw={"mock": True, "amount": int(amount), "currency": currency},
        )

    def verify_payment(self, provider_reference):
        self._guard()
        # Deterministic: the mock treats any created payment as captured on verify.
        return ProviderResult(
            ok=True,
            provider_reference=provider_reference,
            status=AlexBankState.CAPTURED,
            raw={"mock": True},
        )

    def refund_payment(self, *, provider_reference, amount):
        self._guard()
        if int(amount) <= 0:
            raise AlexBankTransportError("Mock: refund amount must be positive")
        return ProviderResult(
            ok=True,
            provider_reference=f"{provider_reference}-REF",
            status=AlexBankState.REFUNDED,
            raw={"mock": True, "amount": int(amount)},
        )

    def parse_webhook(self, *, body, headers):
        self._guard()
        # The mock accepts a trivial JSON body; the real adapter will verify a
        # bank signature per the spec.
        import json
        try:
            payload = json.loads(body or b"{}")
        except (ValueError, TypeError) as e:
            raise AlexBankTransportError(f"Mock: invalid webhook body: {e}") from e
        return {
            "event_id": payload.get("event_id", "mock-event"),
            "event_type": payload.get("event_type", "payment.captured"),
            "provider_reference": payload.get("provider_reference", ""),
            "status": payload.get("status", AlexBankState.CAPTURED),
            "signature_valid": True,
            "raw": payload,
        }

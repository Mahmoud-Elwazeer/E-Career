"""
PaymentProvider abstraction.

The platform never hard-codes itself against one gateway. Concrete adapters
(Stripe, AlexBank, Paymob, Fawry) implement only the operations the provider
genuinely supports. Business code depends on this interface, not the provider.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ProviderError(Exception):
    pass


@dataclass
class ProviderResult:
    """Normalized result of a provider operation."""
    ok: bool
    provider_reference: str = ""
    status: str = ""                    # provider-native status string
    # For hosted checkout flows, the URL to redirect the customer to.
    checkout_url: str = ""
    raw: dict = field(default_factory=dict)
    error: str = ""


class PaymentProvider(ABC):
    """Interface every gateway adapter implements."""

    name: str = "base"

    @abstractmethod
    def create_payment(self, *, amount: int, currency: str, reference: str,
                       metadata: dict | None = None) -> ProviderResult:
        """Create a payment/checkout session. Returns a checkout_url or ref."""

    @abstractmethod
    def verify_payment(self, provider_reference: str) -> ProviderResult:
        """Fetch the authoritative status from the provider."""

    def refund_payment(self, *, provider_reference: str, amount: int) -> ProviderResult:
        raise ProviderError(f"{self.name} does not support refunds")

    @abstractmethod
    def parse_webhook(self, *, body: bytes, headers: dict) -> dict:
        """Verify the signature and return a normalized event dict:
        {event_id, event_type, provider_reference, status, signature_valid, raw}.
        Raise ProviderError on an invalid signature."""


def get_provider(name: str) -> PaymentProvider:
    """Factory: resolve a provider adapter by name."""
    name = (name or "").lower()
    if name == "stripe":
        from .stripe_provider import StripeProvider
        return StripeProvider()
    if name == "alexbank":
        from .alexbank_provider import AlexBankProvider
        return AlexBankProvider()
    raise ProviderError(f"Unknown payment provider: {name!r}")

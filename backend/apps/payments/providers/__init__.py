"""Payment provider abstraction (directive Part XVI)."""
from .base import PaymentProvider, ProviderResult, ProviderError, get_provider

__all__ = ["PaymentProvider", "ProviderResult", "ProviderError", "get_provider"]

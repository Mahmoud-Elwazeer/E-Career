"""
AlexBank (Bank of Alexandria) adapter — SCAFFOLD.

Real AlexBank credentials + API contract will be supplied later. This adapter
establishes the integration shape now so wiring it live is a config change, not
a rewrite. Credentials resolve through the secrets helper (AWS Secrets Manager),
never hard-coded.

Until the real endpoints/credentials are provided, every operation raises
ProviderError — it NEVER fakes a success. That is deliberate: no fake money
movement can slip into production through this adapter.
"""
from __future__ import annotations

from .base import PaymentProvider, ProviderResult, ProviderError
from ..secrets import get_secret


class AlexBankProvider(PaymentProvider):
    name = "alexbank"

    def _require_credentials(self):
        merchant_id = get_secret("ALEXBANK_MERCHANT_ID")
        api_key = get_secret("ALEXBANK_API_KEY")
        base_url = get_secret("ALEXBANK_BASE_URL")
        if not (merchant_id and api_key and base_url):
            raise ProviderError(
                "AlexBank not configured. Provide ALEXBANK_MERCHANT_ID, "
                "ALEXBANK_API_KEY and ALEXBANK_BASE_URL via AWS Secrets Manager."
            )
        return merchant_id, api_key, base_url

    def create_payment(self, *, amount, currency, reference, metadata=None):
        self._require_credentials()
        # TODO: implement against the real AlexBank payment-initiation contract
        # once documentation/credentials are supplied. Intentionally not faked.
        raise ProviderError("AlexBank create_payment not yet implemented (awaiting contract)")

    def verify_payment(self, provider_reference):
        self._require_credentials()
        raise ProviderError("AlexBank verify_payment not yet implemented (awaiting contract)")

    def parse_webhook(self, *, body, headers):
        self._require_credentials()
        raise ProviderError("AlexBank parse_webhook not yet implemented (awaiting contract)")

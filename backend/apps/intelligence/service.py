"""
Centralized AI service.

All AI calls in the system go through this service.
Handles: model selection, circuit breaking, cost tracking, rate limiting.
"""
from __future__ import annotations

import structlog
from django.conf import settings
from django.core.cache import cache

from .llm_plugin import LLMPlugin, LLMRequest, LLMResponse
from .bedrock_plugin import BedrockLLMPlugin
from .circuit_breaker import ai_circuit_breaker

logger = structlog.get_logger()

FALLBACK_RESPONSE = LLMResponse(
    content="I'm temporarily unavailable. Please try again in a few minutes.",
    model="fallback",
    tokens_in=0,
    tokens_out=0,
    latency_ms=0,
    cost_usd=0.0,
    metadata={"is_fallback": True},
)

USER_DAILY_TOKEN_LIMIT = 50000


class AIService:
    """Centralized AI service with circuit breaker and cost controls."""

    def __init__(self):
        self._plugin: LLMPlugin | None = None

    @property
    def plugin(self) -> LLMPlugin:
        if self._plugin is None:
            self._plugin = BedrockLLMPlugin()
        return self._plugin

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not ai_circuit_breaker.is_available():
            logger.warning("ai_circuit_open", model=request.model)
            return FALLBACK_RESPONSE

        if request.user_id and self._is_over_limit(request.user_id):
            logger.warning("ai_user_over_limit", user_id=request.user_id)
            return LLMResponse(
                content="You've reached your daily AI usage limit. It resets tomorrow.",
                model="rate_limited",
                metadata={"is_rate_limited": True},
            )

        try:
            response = self.plugin.generate(request)
            ai_circuit_breaker.record_success()

            if request.user_id:
                self._track_user_tokens(request.user_id, response.tokens_in + response.tokens_out)

            return response

        except Exception as e:
            ai_circuit_breaker.record_failure()
            logger.error("ai_generate_failed", error=str(e), model=request.model)
            return FALLBACK_RESPONSE

    def generate_with_haiku(self, prompt: str, system: str = "", user_id: int | None = None) -> str:
        """Convenience: generate with Haiku (cheap, fast)."""
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system,
            model="haiku",
            user_id=user_id,
        )
        return self.generate(request).content

    def generate_with_sonnet(self, prompt: str, system: str = "", user_id: int | None = None) -> str:
        """Convenience: generate with Sonnet (quality, user-facing)."""
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system,
            model="sonnet",
            max_tokens=2048,
            user_id=user_id,
        )
        return self.generate(request).content

    def health_check(self) -> dict:
        return {
            "provider": "bedrock",
            "circuit_breaker": ai_circuit_breaker.state.value,
            "available": ai_circuit_breaker.is_available(),
        }

    def _is_over_limit(self, user_id: int) -> bool:
        key = f"ai_tokens_daily:{user_id}"
        used = cache.get(key, 0)
        limit = getattr(settings, "AI_USER_DAILY_TOKEN_LIMIT", USER_DAILY_TOKEN_LIMIT)
        return used >= limit

    def _track_user_tokens(self, user_id: int, tokens: int) -> None:
        key = f"ai_tokens_daily:{user_id}"
        try:
            current = cache.get(key, 0)
            cache.set(key, current + tokens, timeout=86400)
        except Exception:
            pass


_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

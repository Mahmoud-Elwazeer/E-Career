"""
AWS Bedrock LLM Plugin implementation.

Supports:
- Claude Haiku (cheap, fast, extraction tasks)
- Claude Sonnet (quality, user-facing)
- Cohere Embed v3 (embeddings)
"""
from __future__ import annotations

import json
import time
import structlog
from typing import Any

import boto3
from django.conf import settings

from .llm_plugin import LLMPlugin, LLMRequest, LLMResponse

logger = structlog.get_logger()

MODEL_COSTS = {
    "us.anthropic.claude-3-haiku-20240307-v1:0": {"input_per_1k": 0.00025, "output_per_1k": 0.00125},
    # claude-sonnet-4-20250514-v1:0 retained here only for historical cost
    # lookups against old logged usage rows; it is Legacy/access-denied in
    # Bedrock as of 2026-08-30 (see audit/LIVE_VERIFICATION_REPORT.md) and
    # must not be used as an active alias target below.
    "us.anthropic.claude-sonnet-4-20250514-v1:0": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": {"input_per_1k": 0.003, "output_per_1k": 0.015},
}

_DEFAULT_ALIASES = {
    "haiku": "us.anthropic.claude-3-haiku-20240307-v1:0",
    "sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
}

MODEL_ALIASES = getattr(settings, "BEDROCK_MODEL_ALIASES", _DEFAULT_ALIASES)


class BedrockLLMPlugin(LLMPlugin):
    """AWS Bedrock implementation of LLMPlugin."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=getattr(settings, "AWS_DEFAULT_REGION", "us-east-1"),
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", ""),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", ""),
            )
        return self._client

    def generate(self, request: LLMRequest) -> LLMResponse:
        model_id = self._resolve_model(request.model)
        start_time = time.time()

        messages = [{"role": "user", "content": request.prompt}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages,
        }

        if request.system_prompt:
            body["system"] = request.system_prompt

        try:
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
        except Exception as e:
            logger.error("bedrock_invoke_failed", model=model_id, error=str(e))
            raise

        response_body = json.loads(response["body"].read())
        content = response_body.get("content", [{}])[0].get("text", "")
        usage = response_body.get("usage", {})
        tokens_in = usage.get("input_tokens", 0)
        tokens_out = usage.get("output_tokens", 0)
        latency_ms = int((time.time() - start_time) * 1000)

        cost = self._calculate_cost(model_id, tokens_in, tokens_out)

        self._track_usage(request, model_id, tokens_in, tokens_out, latency_ms, cost)

        return LLMResponse(
            content=content,
            model=model_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=cost,
        )

    def available_models(self) -> list[str]:
        return list(MODEL_COSTS.keys())

    def health_check(self) -> bool:
        try:
            self.client.list_foundation_models(byOutputModality="TEXT")
            return True
        except Exception:
            return False

    def _resolve_model(self, model: str) -> str:
        if not model:
            return MODEL_ALIASES["haiku"]
        return MODEL_ALIASES.get(model, model)

    def _calculate_cost(self, model_id: str, tokens_in: int, tokens_out: int) -> float:
        rates = MODEL_COSTS.get(model_id, {"input_per_1k": 0.003, "output_per_1k": 0.015})
        cost = (tokens_in / 1000) * rates["input_per_1k"] + (tokens_out / 1000) * rates["output_per_1k"]
        return round(cost, 6)

    def _track_usage(self, request: LLMRequest, model_id: str, tokens_in: int, tokens_out: int, latency_ms: int, cost: float):
        from apps.events.emitter import emit
        from apps.events.types import AI_MODEL_CALLED

        emit(
            event_type=AI_MODEL_CALLED,
            category="ai",
            user=None,
            target_type="model",
            target_id=model_id,
            data={
                "model": model_id,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "user_id": request.user_id,
            },
        )

        logger.info(
            "ai_model_called",
            model=model_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=cost,
        )

"""
LLM Plugin abstraction layer.

Provides a unified interface for all AI model calls with:
- Automatic model tiering (cheapest model that works)
- Cost tracking per call
- Circuit breaker for provider outages
- Token limit enforcement per user
"""
from __future__ import annotations

import abc
import time
import structlog
from dataclasses import dataclass, field
from typing import Any

logger = structlog.get_logger()


@dataclass
class LLMRequest:
    """Represents a request to an LLM."""

    prompt: str
    system_prompt: str = ""
    model: str = ""
    max_tokens: int = 1024
    temperature: float = 0.3
    json_mode: bool = False
    user_id: int | None = None
    operation: str = ""


@dataclass
class LLMResponse:
    """Represents a response from an LLM."""

    content: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMPlugin(abc.ABC):
    """Abstract base class for LLM provider plugins."""

    @abc.abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""

    @abc.abstractmethod
    def available_models(self) -> list[str]:
        """Return list of available model IDs."""

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider is healthy."""

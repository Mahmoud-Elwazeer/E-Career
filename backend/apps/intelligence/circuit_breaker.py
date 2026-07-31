"""
Circuit breaker for AI provider outages.

If Bedrock returns 5xx > 50% in 2 minutes → stop calls.
Return graceful fallback responses.
Auto-resume after 5 minutes.
"""
from __future__ import annotations

import time
import structlog
from collections import deque
from enum import Enum

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""

    def __init__(
        self,
        failure_threshold: float = 0.5,
        window_seconds: int = 120,
        recovery_seconds: int = 300,
        min_calls: int = 5,
    ):
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.recovery_seconds = recovery_seconds
        self.min_calls = min_calls

        self._state = CircuitState.CLOSED
        self._calls: deque[tuple[float, bool]] = deque()
        self._opened_at: float = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._opened_at >= self.recovery_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open")
        return self._state

    def is_available(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        self._calls.append((time.time(), True))
        self._prune()
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            logger.info("circuit_breaker_closed")

    def record_failure(self) -> None:
        self._calls.append((time.time(), False))
        self._prune()
        self._check_threshold()

    def _prune(self) -> None:
        cutoff = time.time() - self.window_seconds
        while self._calls and self._calls[0][0] < cutoff:
            self._calls.popleft()

    def _check_threshold(self) -> None:
        if len(self._calls) < self.min_calls:
            return

        failures = sum(1 for _, success in self._calls if not success)
        failure_rate = failures / len(self._calls)

        if failure_rate >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
            logger.warning(
                "circuit_breaker_opened",
                failure_rate=round(failure_rate, 2),
                total_calls=len(self._calls),
            )


ai_circuit_breaker = CircuitBreaker()

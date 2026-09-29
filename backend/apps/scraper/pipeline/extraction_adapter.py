"""Pluggable extraction adapter contract (§16/§17).

Defines the SEAM for optional adaptive/AI extractors (Scrapling, Crawl4AI,
ScrapeGraphAI) WITHOUT importing them into the main venv. Those libraries pull
in conflicting deps (lxml / litellm vs docling in this project), so they must
run OUT-OF-PROCESS when enabled. This module ships only the contract + a
deterministic default; heavy backends are wired via subprocess/service and are
strictly opt-in.

Extraction preference order (§17) — reliability, cost, speed, explainability:
    structured ATS/API  ->  deterministic HTTP  ->  browser  ->  adaptive parser
    ->  AI extraction  ->  agentic fallback

AI is NEVER the default. The pipeline only falls through to a heavier tier when
the cheaper tier fails, and every result records which TIER produced it so the
funnel stays explainable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Protocol


class ExtractionTier(IntEnum):
    """Lower value = cheaper/more reliable/more preferred."""
    STRUCTURED_API = 0     # ATS JSON APIs (greenhouse/lever/ashby/workday/...)
    DETERMINISTIC_HTTP = 1  # plain HTTP + known selectors (iCIMS portal)
    BROWSER = 2            # headless browser for JS-only pages
    ADAPTIVE_PARSER = 3    # Scrapling-style self-healing selectors
    AI_EXTRACTION = 4      # LLM field extraction from raw HTML
    AGENTIC = 5            # multi-step agent (last resort)


@dataclass
class ExtractionResult:
    ok: bool
    tier: ExtractionTier
    jobs: List[Dict] = field(default_factory=list)
    evidence: Dict = field(default_factory=dict)  # url, status, backend, timings
    error: Optional[str] = None


class ExtractionBackend(Protocol):
    """A backend that can attempt extraction at a given tier.

    Implementations MUST NOT import heavy/conflicting deps at module import
    time — do it lazily inside `extract`, and only when actually invoked, so the
    main venv stays clean when the backend is disabled.
    """
    tier: ExtractionTier
    name: str

    def available(self) -> bool:
        """True only if the backend's runtime is actually installed/reachable."""
        ...

    def extract(self, url: str, *, hints: Optional[Dict] = None) -> ExtractionResult:
        ...


class ExtractionRouter:
    """Tries registered backends in ascending tier order until one succeeds.

    Enforces the §17 preference order and records which tier produced the
    result. Backends that are not `available()` are skipped (so an environment
    without Scrapling/Crawl4AI simply never reaches those tiers).
    """

    def __init__(self, backends: Optional[List[ExtractionBackend]] = None,
                 max_tier: ExtractionTier = ExtractionTier.BROWSER):
        # Default max_tier is BROWSER: adaptive/AI tiers are OFF unless a caller
        # explicitly raises the ceiling (opt-in), keeping AI non-default.
        self._backends = sorted(backends or [], key=lambda b: int(b.tier))
        self.max_tier = max_tier

    def register(self, backend: ExtractionBackend) -> None:
        self._backends.append(backend)
        self._backends.sort(key=lambda b: int(b.tier))

    def extract(self, url: str, *, hints: Optional[Dict] = None) -> ExtractionResult:
        attempts: List[Dict] = []
        for backend in self._backends:
            if int(backend.tier) > int(self.max_tier):
                break
            if not backend.available():
                attempts.append({"backend": backend.name, "skipped": "unavailable"})
                continue
            result = backend.extract(url, hints=hints)
            attempts.append({
                "backend": backend.name, "tier": int(backend.tier),
                "ok": result.ok, "jobs": len(result.jobs), "error": result.error,
            })
            if result.ok and result.jobs:
                result.evidence.setdefault("attempts", attempts)
                return result
        return ExtractionResult(
            ok=False, tier=self.max_tier, jobs=[],
            evidence={"attempts": attempts},
            error="no backend produced results within tier ceiling",
        )


class OutOfProcessBackend:
    """Adapter that runs a heavy extractor (Scrapling/Crawl4AI/ScrapeGraphAI) in
    a SEPARATE process/venv and exchanges JSON over stdin/stdout.

    This keeps the conflicting deps out of the Django venv. The concrete runner
    script + its own venv are provisioned separately (see §16 docs); this class
    only defines how the main process talks to it. `available()` returns False
    until such a runner is configured, so it is inert by default.
    """
    def __init__(self, name: str, tier: ExtractionTier, runner_cmd: Optional[List[str]] = None):
        self.name = name
        self.tier = tier
        self.runner_cmd = runner_cmd  # e.g. ["/opt/scrapling-venv/bin/python", "runner.py"]

    def available(self) -> bool:
        return bool(self.runner_cmd)

    def extract(self, url: str, *, hints: Optional[Dict] = None) -> ExtractionResult:
        if not self.available():
            return ExtractionResult(ok=False, tier=self.tier, error="runner not configured")
        import json
        import subprocess
        payload = json.dumps({"url": url, "hints": hints or {}})
        try:
            proc = subprocess.run(
                self.runner_cmd, input=payload, capture_output=True,
                text=True, timeout=60,
            )
            if proc.returncode != 0:
                return ExtractionResult(ok=False, tier=self.tier,
                                        error=f"runner exit {proc.returncode}: {proc.stderr[:300]}")
            data = json.loads(proc.stdout or "{}")
            return ExtractionResult(
                ok=bool(data.get("jobs")), tier=self.tier,
                jobs=data.get("jobs", []),
                evidence={"backend": self.name, **(data.get("evidence") or {})},
            )
        except (subprocess.SubprocessError, ValueError) as e:
            return ExtractionResult(ok=False, tier=self.tier, error=f"{type(e).__name__}: {e}")

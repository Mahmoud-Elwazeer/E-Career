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

import json
import subprocess
import threading
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Protocol


class _ResponseTooLarge(Exception):
    """Raised internally when an out-of-process runner's stdout exceeds
    OutOfProcessBackend.MAX_RESPONSE_BYTES (§13 resource bound)."""


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

        # §9/§13 SSRF guard: validated BEFORE a subprocess/container is ever
        # launched - the primary, always-applied enforcement point for this
        # Tier-3 adaptive path. See ssrf_guard.py's module docstring for the
        # full threat model (cloud metadata endpoint, RFC1918, loopback,
        # non-HTTP schemes) and its documented residual risk (redirect-chain
        # re-validation is NOT covered here).
        from .ssrf_guard import validate_url_safe
        safety = validate_url_safe(url)
        if not safety.safe:
            return ExtractionResult(
                ok=False, tier=self.tier,
                error=f"blocked by SSRF guard: {safety.reason}",
                evidence={"backend": self.name, "ssrf_blocked": True, "url": url},
            )

        payload = json.dumps({"url": url, "hints": hints or {}})
        try:
            # §13 resource bound: subprocess.run's capture_output buffers the
            # ENTIRE stdout in memory with no size limit - a malicious or
            # buggy runner (e.g. a page that is actually a multi-GB file
            # served with a misleading content-type) could exhaust worker
            # memory. Popen + a size-capped read loop enforces a hard ceiling
            # DURING the read, not just a check after the fact.
            proc = subprocess.Popen(
                self.runner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=False,  # binary mode - _read_bounded enforces the byte cap itself
            )
            try:
                stdout_data, stderr_data = self._read_bounded(proc, payload, timeout=60)
            except _ResponseTooLarge:
                proc.kill()
                proc.wait(timeout=5)
                return ExtractionResult(
                    ok=False, tier=self.tier,
                    error=f"runner stdout exceeded {self.MAX_RESPONSE_BYTES} byte limit",
                    evidence={"backend": self.name, "response_size_exceeded": True},
                )
            if proc.returncode != 0:
                return ExtractionResult(ok=False, tier=self.tier,
                                        error=f"runner exit {proc.returncode}: {(stderr_data or '')[:300]}")
            data = json.loads(stdout_data or "{}")
            return ExtractionResult(
                ok=bool(data.get("jobs")), tier=self.tier,
                jobs=data.get("jobs", []),
                evidence={"backend": self.name, **(data.get("evidence") or {})},
            )
        except (subprocess.SubprocessError, ValueError, OSError) as e:
            return ExtractionResult(ok=False, tier=self.tier, error=f"{type(e).__name__}: {e}")

    # 10 MB is far more than any legitimate single-page JobPosting
    # extraction response needs (even dozens of full job descriptions as
    # JSON stay well under 1 MB) - this is a hard safety ceiling, not a
    # tuned-for-throughput limit.
    MAX_RESPONSE_BYTES = 10 * 1024 * 1024

    def _read_bounded(self, proc, payload: str, *, timeout: int):
        """Write `payload` to stdin, then read stdout in a thread with a
        true streaming byte cap (kills the process the moment the cap is
        exceeded, rather than buffering an unbounded amount first via
        communicate()). stderr is read in a second thread so neither pipe
        can deadlock the other if the runner writes a lot to both.
        """
        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []
        exceeded = threading.Event()

        def _pump(stream, chunks: list, cap_bytes: Optional[int]):
            total = 0
            try:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if cap_bytes is not None:
                        total += len(chunk)
                        if total > cap_bytes:
                            exceeded.set()
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            break
            except Exception:
                pass

        proc.stdin.write(payload.encode("utf-8"))
        proc.stdin.close()

        t_out = threading.Thread(target=_pump, args=(proc.stdout, stdout_chunks, self.MAX_RESPONSE_BYTES))
        t_err = threading.Thread(target=_pump, args=(proc.stderr, stderr_chunks, self.MAX_RESPONSE_BYTES))
        t_out.start()
        t_err.start()

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            t_out.join(timeout=5)
            t_err.join(timeout=5)
            raise

        t_out.join(timeout=5)
        t_err.join(timeout=5)

        if exceeded.is_set():
            raise _ResponseTooLarge()

        stdout_data = "".join(c.decode("utf-8", errors="ignore") for c in stdout_chunks)
        stderr_data = "".join(c.decode("utf-8", errors="ignore") for c in stderr_chunks)
        return stdout_data, stderr_data

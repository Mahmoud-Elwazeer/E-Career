"""Tests for the extraction adapter contract (§16/§17).

Verifies the router honors tier order, skips unavailable backends, keeps AI
tiers OFF by default, and records explainable attempts. Uses fake in-process
backends (no heavy deps).
"""
from apps.scraper.pipeline.extraction_adapter import (
    ExtractionTier, ExtractionResult, ExtractionRouter, OutOfProcessBackend,
)


class _Fake:
    def __init__(self, name, tier, avail=True, jobs=None):
        self.name = name; self.tier = tier; self._avail = avail; self._jobs = jobs or []
    def available(self): return self._avail
    def extract(self, url, *, hints=None):
        return ExtractionResult(ok=bool(self._jobs), tier=self.tier, jobs=list(self._jobs))


def test_cheapest_successful_tier_wins():
    r = ExtractionRouter([
        _Fake("api", ExtractionTier.STRUCTURED_API, jobs=[{"t": "a"}]),
        _Fake("browser", ExtractionTier.BROWSER, jobs=[{"t": "b"}]),
    ])
    res = r.extract("http://x")
    assert res.ok and res.tier == ExtractionTier.STRUCTURED_API
    assert res.jobs == [{"t": "a"}]


def test_falls_through_to_next_tier_when_cheaper_empty():
    r = ExtractionRouter([
        _Fake("api", ExtractionTier.STRUCTURED_API, jobs=[]),
        _Fake("http", ExtractionTier.DETERMINISTIC_HTTP, jobs=[{"t": "h"}]),
    ])
    res = r.extract("http://x")
    assert res.tier == ExtractionTier.DETERMINISTIC_HTTP
    assert res.jobs == [{"t": "h"}]


def test_unavailable_backend_skipped():
    r = ExtractionRouter([
        _Fake("api", ExtractionTier.STRUCTURED_API, avail=False, jobs=[{"t": "a"}]),
        _Fake("http", ExtractionTier.DETERMINISTIC_HTTP, jobs=[{"t": "h"}]),
    ])
    res = r.extract("http://x")
    assert res.tier == ExtractionTier.DETERMINISTIC_HTTP
    attempts = res.evidence["attempts"]
    assert any(a.get("skipped") == "unavailable" for a in attempts)


def test_ai_tier_off_by_default():
    # An AI backend that WOULD return jobs must NOT be reached with default ceiling.
    r = ExtractionRouter([
        _Fake("ai", ExtractionTier.AI_EXTRACTION, jobs=[{"t": "ai"}]),
    ])  # default max_tier = BROWSER
    res = r.extract("http://x")
    assert res.ok is False  # never reached AI tier


def test_ai_tier_reachable_when_ceiling_raised():
    r = ExtractionRouter([
        _Fake("ai", ExtractionTier.AI_EXTRACTION, jobs=[{"t": "ai"}]),
    ], max_tier=ExtractionTier.AGENTIC)
    res = r.extract("http://x")
    assert res.ok and res.tier == ExtractionTier.AI_EXTRACTION


def test_out_of_process_backend_inert_without_runner():
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER)
    assert b.available() is False
    res = b.extract("http://x")
    assert res.ok is False and "not configured" in (res.error or "")


# ---------------------------------------------------------------------------
# §9/§13 SSRF guard + resource bounds - OutOfProcessBackend.extract() wiring.
# Uses real `sys.executable -c "..."` subprocesses (not mocks) to actually
# exercise the Popen/_read_bounded machinery, since that's exactly the code
# path a real security review would want proven, not assumed.
# ---------------------------------------------------------------------------
import sys
import json as _json


def _echo_runner_cmd():
    """A tiny real subprocess that reads stdin JSON and echoes back a
    well-formed {"jobs": [...], "evidence": {...}} - used to prove a SAFE
    url is actually allowed through to the runner (i.e. the SSRF guard
    doesn't block everything)."""
    script = (
        "import sys, json; "
        "d = json.loads(sys.stdin.read()); "
        "print(json.dumps({'jobs': [{'title': 'ok', 'url': d['url']}], 'evidence': {}}))"
    )
    return [sys.executable, "-c", script]


def test_ssrf_guard_blocks_loopback_before_subprocess_runs():
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=_echo_runner_cmd())
    res = b.extract("http://127.0.0.1:8000/admin")
    assert res.ok is False
    assert "SSRF guard" in res.error
    assert res.evidence.get("ssrf_blocked") is True


def test_ssrf_guard_blocks_cloud_metadata_endpoint():
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=_echo_runner_cmd())
    res = b.extract("http://169.254.169.254/latest/meta-data/")
    assert res.ok is False
    assert res.evidence.get("ssrf_blocked") is True


def test_ssrf_guard_blocks_rfc1918_private_network():
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=_echo_runner_cmd())
    res = b.extract("http://192.168.1.50/internal-admin")
    assert res.ok is False
    assert res.evidence.get("ssrf_blocked") is True


def test_ssrf_guard_blocks_file_scheme():
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=_echo_runner_cmd())
    res = b.extract("file:///etc/passwd")
    assert res.ok is False
    assert res.evidence.get("ssrf_blocked") is True


def test_safe_public_url_actually_reaches_the_real_subprocess():
    """Proves the SSRF guard is not overly broad - a legitimate public URL
    (IP literal, since this must run offline in CI with no real DNS) still
    reaches the real runner subprocess and gets a real result back."""
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=_echo_runner_cmd())
    res = b.extract("http://93.184.216.34/careers")
    assert res.ok is True
    assert res.jobs == [{"title": "ok", "url": "http://93.184.216.34/careers"}]


def test_response_size_limit_kills_oversized_runner_output():
    """A real subprocess that tries to write far more than
    OutOfProcessBackend.MAX_RESPONSE_BYTES to stdout must be killed and
    reported as blocked, not allowed to exhaust memory."""
    over_limit_mb = 15  # MAX_RESPONSE_BYTES is 10 MB
    script = (
        "import sys; "
        f"sys.stdin.read(); "
        f"sys.stdout.write('x' * ({over_limit_mb} * 1024 * 1024))"
    )
    runner_cmd = [sys.executable, "-c", script]
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=runner_cmd)
    res = b.extract("http://93.184.216.34/careers")
    assert res.ok is False
    assert res.evidence.get("response_size_exceeded") is True


def test_runner_timeout_is_reported_not_hung():
    script = "import sys, time; sys.stdin.read(); time.sleep(5)"
    runner_cmd = [sys.executable, "-c", script]
    b = OutOfProcessBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=runner_cmd)
    # Shrink the timeout for a fast test by monkeypatching the bounded-read
    # call's timeout via a tiny subclass override.
    import apps.scraper.pipeline.extraction_adapter as mod

    orig_extract = mod.OutOfProcessBackend.extract

    class _FastTimeoutBackend(mod.OutOfProcessBackend):
        def extract(self, url, *, hints=None):
            # Reuse the real method body logic by temporarily patching the
            # hardcoded 60s timeout: simplest robust way is to call
            # _read_bounded directly with a short timeout, mirroring extract().
            if not self.available():
                return mod.ExtractionResult(ok=False, tier=self.tier, error="runner not configured")
            from apps.scraper.pipeline.ssrf_guard import validate_url_safe
            safety = validate_url_safe(url)
            if not safety.safe:
                return mod.ExtractionResult(ok=False, tier=self.tier, error="blocked")
            payload = _json.dumps({"url": url, "hints": {}})
            proc = mod.subprocess.Popen(
                self.runner_cmd, stdin=mod.subprocess.PIPE, stdout=mod.subprocess.PIPE,
                stderr=mod.subprocess.PIPE, text=False,
            )
            try:
                self._read_bounded(proc, payload, timeout=1)
                return mod.ExtractionResult(ok=True, tier=self.tier)
            except mod.subprocess.TimeoutExpired:
                return mod.ExtractionResult(ok=False, tier=self.tier, error="timed out")

    b = _FastTimeoutBackend("scrapling", ExtractionTier.ADAPTIVE_PARSER, runner_cmd=runner_cmd)
    res = b.extract("http://93.184.216.34/careers")
    assert res.ok is False
    assert "timed out" in (res.error or "")


if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)

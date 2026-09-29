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

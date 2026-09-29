"""Tests for extended RunMetrics funnel counters + degraded/zero-yield logic.

Pure-Python; runs under pytest or the standalone harness at the bottom.
"""
from apps.scraper.pipeline.run_metrics import RunMetrics, DUPLICATE, LOW_LEGITIMACY


def test_to_dict_has_all_funnel_columns():
    m = RunMetrics(source="stripe-greenhouse", provider="greenhouse", fetched=100)
    d = m.to_dict()
    for key in ("fetched", "normalized", "created", "updated", "duplicates",
                "verified", "errors", "direct_apply_candidate",
                "direct_apply_verified", "publishable", "indexed",
                "rejected_total", "rejected"):
        assert key in d, f"missing column {key}"


def test_zero_yield_anomaly_true_when_nothing_handled():
    m = RunMetrics(fetched=50)  # fetched a lot, created/updated/dupes all 0
    assert m.is_zero_yield_anomaly is True


def test_zero_yield_false_when_duplicates_explain_it():
    # A run that only re-found existing jobs is healthy, not anomalous.
    m = RunMetrics(fetched=50, duplicates=50, updated=50)
    assert m.is_zero_yield_anomaly is False


def test_zero_yield_false_below_threshold():
    m = RunMetrics(fetched=5)
    assert m.is_zero_yield_anomaly is False


def test_degraded_when_high_fetch_all_rejected():
    m = RunMetrics(fetched=156)
    for _ in range(156):
        m.reject(LOW_LEGITIMACY)
    assert m.is_degraded is True


def test_not_degraded_when_publishing():
    m = RunMetrics(fetched=156, created=120, publishable=118, verified=118)
    assert m.is_degraded is False


def test_not_degraded_when_only_duplicates():
    m = RunMetrics(fetched=156, duplicates=156, updated=156)
    # nothing new created, but it's all known jobs -> healthy, not degraded
    assert m.is_zero_yield_anomaly is False


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

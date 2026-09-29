"""Tests for the Eightfold connector (§10) using a REAL captured Netflix payload.

The network call is stubbed with a fixture captured live from
explore.jobs.netflix.net on 2026-09-29, so the parse contract is verified
offline and deterministically.
"""
import json
import os

from apps.scraper.ats import eightfold

_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_eightfold.json")


class _Resp:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        pass
    def json(self):
        return self._payload


class _FakeRequests:
    """Returns the fixture on page 1, then an empty page to end pagination."""
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
    def get(self, url, **kw):
        self.calls += 1
        if self.calls == 1:
            return _Resp(self.payload)
        return _Resp({"positions": [], "count": self.payload.get("count")})


def _install_fake(monkeypatch_target):
    with open(_FIXTURE, encoding="utf-8") as fh:
        payload = json.load(fh)
    eightfold.requests = _FakeRequests(payload)
    return payload


def test_eightfold_parses_netflix_positions():
    payload = _install_fake(eightfold)
    jobs = eightfold.fetch_eightfold_jobs("netflix")
    assert len(jobs) == len(payload["positions"])
    j = jobs[0]
    assert j["ats_platform"] == "eightfold"
    assert j["title"]
    assert j["ats_job_id"]


def test_eightfold_apply_urls_are_direct_employer():
    _install_fake(eightfold)
    jobs = eightfold.fetch_eightfold_jobs("netflix")
    # every apply url must be on Netflix's own eightfold host (moat-compliant)
    assert all("netflix.net" in (j["direct_apply_url"] or "") for j in jobs)
    assert all("linkedin" not in (j["direct_apply_url"] or "").lower() for j in jobs)


def test_eightfold_unknown_tenant_returns_empty():
    jobs = eightfold.fetch_eightfold_jobs("totally-unknown-tenant")
    assert jobs == []


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

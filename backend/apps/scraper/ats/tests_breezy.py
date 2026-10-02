"""Tests for the Breezy HR connector using a trimmed REAL payload shape.

Fixture mirrors a real company board (zero-hash.breezy.hr) captured live
2026-10-03 (full response: 25 real positions; fixture trims to 2 real
positions + 1 synthetic missing-url entry to prove skip behavior).
"""
import json
import os

from apps.scraper.ats import breezy as bz

_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_breezy.json")


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeRequests:
    def __init__(self, payload):
        self.payload = payload

    def get(self, url, **kw):
        return _Resp(self.payload)

    class RequestException(Exception):
        pass


def _install():
    with open(_FIXTURE, encoding="utf-8") as fh:
        payload = json.load(fh)
    bz.requests = _FakeRequests(payload)
    return payload


def test_parses_real_shaped_positions_and_skips_missing_url():
    payload = _install()
    jobs = bz.fetch_breezy_jobs("zero-hash")
    # 3 entries in fixture, 1 has an empty url and must be skipped.
    assert len(payload) == 3
    assert len(jobs) == 2
    assert jobs[0]["ats_platform"] == "breezy"
    assert jobs[0]["title"] == "Chief Compliance Officer"
    assert jobs[0]["ats_job_id"] == "05c2e3ac74c6"


def test_apply_url_is_employer_subdomain_detail_page():
    _install()
    jobs = bz.fetch_breezy_jobs("zero-hash")
    for j in jobs:
        url = j["direct_apply_url"]
        assert url.startswith("https://zero-hash.breezy.hr/p/")


def test_remote_flag_and_location_mapped():
    _install()
    jobs = bz.fetch_breezy_jobs("zero-hash")
    london_job = next(j for j in jobs if j["ats_job_id"] == "05c2e3ac74c6")
    assert london_job["remote_type"] == "remote"
    assert london_job["location"] == "London, GB"


def test_employment_type_lowercased():
    _install()
    jobs = bz.fetch_breezy_jobs("zero-hash")
    assert jobs[0]["employment_type"] == "fulltime"


def test_non_list_payload_returns_empty():
    bz.requests = _FakeRequests({"not": "a list"})
    jobs = bz.fetch_breezy_jobs("whatever")
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

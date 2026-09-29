"""Tests for the rewritten (browser-free) Workday connector (§11).

Uses a REAL captured NVIDIA CXS payload (2026-09-29) stubbed over requests.post,
so the parse + pagination contract is verified offline.
"""
import json
import os

from apps.scraper.ats import workday

_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_workday.json")


class _Resp:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        pass
    def json(self):
        return self._payload


class _FakeRequests:
    """Page 1 returns the fixture; page 2 returns empty to end pagination."""
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
        self.last_json = None
    def post(self, url, **kw):
        self.calls += 1
        self.last_json = kw.get("json")
        if self.calls == 1:
            return _Resp(self.payload)
        return _Resp({"total": self.payload.get("total"), "jobPostings": []})
    # expose RequestException so `except requests.RequestException` still works
    class RequestException(Exception):
        pass


def _install():
    with open(_FIXTURE, encoding="utf-8") as fh:
        payload = json.load(fh)
    fake = _FakeRequests(payload)
    workday.requests = fake
    return payload, fake


def test_workday_parses_nvidia_postings():
    payload, _ = _install()
    jobs = workday.fetch_workday_jobs("nvidia")
    assert len(jobs) == len(payload["jobPostings"])
    j = jobs[0]
    assert j["ats_platform"] == "workday"
    assert j["title"]
    # req id extracted from bulletFields / externalPath
    assert j["ats_job_id"]


def test_workday_apply_urls_are_employer_host():
    _install()
    jobs = workday.fetch_workday_jobs("nvidia")
    assert all("nvidia.wd5.myworkdayjobs.com" in (j["direct_apply_url"] or "") for j in jobs)
    assert all("linkedin" not in (j["direct_apply_url"] or "").lower() for j in jobs)


def test_workday_uses_limit_20():
    _, fake = _install()
    workday.fetch_workday_jobs("nvidia")
    # never asks for more than Workday's server-side cap of 20
    assert fake.last_json["limit"] == 20


def test_workday_unknown_tenant_returns_empty():
    jobs = workday.fetch_workday_jobs("totally-unknown")
    assert jobs == []


def test_posted_on_parsing():
    assert workday.WorkdayScraper._parse_posted("Posted Today")
    assert workday.WorkdayScraper._parse_posted("Posted 3 Days Ago")
    assert workday.WorkdayScraper._parse_posted("nonsense") is None


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

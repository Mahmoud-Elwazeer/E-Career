"""Tests for the Personio connector using a trimmed REAL feed shape.

Fixture mirrors a real company board (f24.jobs.personio.de/xml) captured
live 2026-10-02 (full feed: 9 real positions; fixture trims to 2
representative positions - one with salary data, one without, one with
"Remote" in the office field).
"""
import os

from apps.scraper.ats import personio as ps

_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_personio.xml")


class _Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class _FakeRequests:
    def __init__(self, content):
        self.content = content

    def get(self, url, **kw):
        return _Resp(self.content)

    class RequestException(Exception):
        pass


def _install():
    with open(_FIXTURE, "rb") as fh:
        content = fh.read()
    ps.requests = _FakeRequests(content)
    return content


def test_parses_real_shaped_positions():
    _install()
    jobs = ps.fetch_personio_jobs("f24")
    assert len(jobs) == 2
    assert jobs[0]["ats_platform"] == "personio"
    assert jobs[0]["title"] == "Junior Full Stack Engineer - Suite"
    assert jobs[0]["ats_job_id"] == "2676311"


def test_apply_url_built_from_job_id():
    _install()
    jobs = ps.fetch_personio_jobs("f24")
    job = next(j for j in jobs if j["ats_job_id"] == "2676311")
    assert job["direct_apply_url"] == "https://f24.jobs.personio.de/job/2676311"


def test_salary_extracted_when_present():
    _install()
    jobs = ps.fetch_personio_jobs("f24")
    job = next(j for j in jobs if j["ats_job_id"] == "2676311")
    assert job["salary_min"] == 22971.0
    assert job["salary_max"] == 26971.0
    assert job["salary_currency"] == "EUR"


def test_missing_salary_handled_gracefully():
    _install()
    jobs = ps.fetch_personio_jobs("f24")
    job = next(j for j in jobs if j["ats_job_id"] == "1316737")
    assert job["salary_min"] is None
    assert job["salary_max"] is None


def test_remote_office_maps_to_remote_type():
    _install()
    jobs = ps.fetch_personio_jobs("f24")
    job = next(j for j in jobs if j["ats_job_id"] == "1316737")
    assert job["remote_type"] == "remote"
    job2 = next(j for j in jobs if j["ats_job_id"] == "2676311")
    assert job2["remote_type"] == "onsite"


def test_description_includes_job_description_sections():
    _install()
    jobs = ps.fetch_personio_jobs("f24")
    job = next(j for j in jobs if j["ats_job_id"] == "2676311")
    assert "About the job" in job["description"]
    assert "Junior Software Engineer" in job["description"]


def test_malformed_xml_returns_empty_not_crash():
    ps.requests = _FakeRequests(b"<not valid xml")
    jobs = ps.fetch_personio_jobs("f24")
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

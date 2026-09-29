"""Tests for the rewritten iCIMS connector (Phase A). Offline via mocked HTTP."""
from unittest.mock import patch, MagicMock

from apps.scraper.ats.icims import IcimsScraper


def test_tenant_normalization():
    assert IcimsScraper("rambus")._tenant() == "rambus"
    assert IcimsScraper("careers-rambus.icims.com")._tenant() == "rambus"
    assert IcimsScraper("Careers-RAMBUS")._tenant() == "rambus"


SAMPLE_HTML = """
<html><body>
  <a href="/jobs/12345/software-engineer/job">Software Engineer</a>
  <a href="/jobs/12345/software-engineer/job">Software Engineer (dup)</a>
  <a href="/jobs/67890/data-analyst/job">Data Analyst</a>
  <a href="/about">About</a>
</body></html>
"""


def test_fetch_parses_tenant_jobs_and_builds_direct_apply_urls():
    resp = MagicMock()
    resp.text = SAMPLE_HTML
    resp.raise_for_status = MagicMock()

    # First page returns jobs; second page empty → loop stops.
    empty = MagicMock()
    empty.text = "<html><body></body></html>"
    empty.raise_for_status = MagicMock()

    with patch("apps.scraper.ats.icims.requests.get", side_effect=[resp, empty]):
        jobs = IcimsScraper("rambus").fetch_jobs()

    assert len(jobs) == 2  # dedup within page by job id
    titles = {j["title"] for j in jobs}
    assert "Software Engineer" in titles and "Data Analyst" in titles
    for j in jobs:
        # Direct-apply URL must be on the real tenant domain (moat-compliant).
        assert j["direct_apply_url"].startswith("https://careers-rambus.icims.com/jobs/")
        assert j["ats_platform"] == "icims"


def test_fetch_handles_request_error_gracefully():
    import requests as _rq
    with patch("apps.scraper.ats.icims.requests.get", side_effect=_rq.RequestException("boom")):
        jobs = IcimsScraper("rambus").fetch_jobs()
    assert jobs == []

"""Standalone tests for scrapling_runner.py's HTML extraction logic.

Deliberately has NO Django imports and does NOT require the main backend
venv's dependencies beyond pytest - the extraction logic itself
(extract_jobs_from_html) has zero dependency on Scrapling being importable
(it only re-raises an empty list if Scrapling isn't installed, see the
try/except ImportError guard), so these tests run in the main CI/test
environment without needing the isolated Scrapling venv at all. Only the
`run()`/`main()` functions (which actually invoke Scrapling's Fetcher) need
the isolated venv - those are exercised manually against real pages, not in
automated CI (see the module docstring in scrapling_runner.py for the
real-page verification done during development).

Run directly: pytest apps/scraper/extraction_runners/tests_scrapling_runner.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from scrapling_runner import extract_jobs_from_html, _extract_jsonld_location


JSONLD_FIXTURE = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "JobPosting",
  "title": "Senior Software Engineer",
  "description": "We are looking for a senior engineer to join our platform team.",
  "datePosted": "2026-09-15",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Acme Robotics"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Austin",
      "addressRegion": "TX",
      "addressCountry": "US"
    }
  },
  "url": "https://acmerobotics.example.com/careers/senior-engineer-442"
}
</script>
</head>
<body><h1>Senior Software Engineer</h1></body>
</html>
"""

MICRODATA_FIXTURE = """
<html><body>
<div itemscope itemtype="https://schema.org/JobPosting">
  <h2 itemprop="title">Backend Engineer</h2>
  <span itemprop="name">Beta Corp</span>
</div>
</body></html>
"""

NO_STRUCTURED_DATA_FIXTURE = """
<html><body>
<div class="jobCard_abc123">
  <span class="jobTitle_xyz789">Platform Engineer</span>
</div>
</body></html>
"""

MULTIPLE_JOBS_JSONLD_FIXTURE = """
<html><head>
<script type="application/ld+json">
[
  {"@type": "JobPosting", "title": "Frontend Engineer", "hiringOrganization": {"name": "Gamma Inc"}, "url": "https://gamma.example.com/jobs/1"},
  {"@type": "JobPosting", "title": "Backend Engineer", "hiringOrganization": {"name": "Gamma Inc"}, "url": "https://gamma.example.com/jobs/2"}
]
</script>
</head><body></body></html>
"""


def test_jsonld_jobposting_extracted_correctly():
    jobs = extract_jobs_from_html(JSONLD_FIXTURE, "https://acmerobotics.example.com/careers")
    assert len(jobs) == 1
    job = jobs[0]
    assert job["title"] == "Senior Software Engineer"
    assert job["company"] == "Acme Robotics"
    assert job["location"] == "Austin, TX, US"
    assert job["direct_apply_url"] == "https://acmerobotics.example.com/careers/senior-engineer-442"
    assert job["posted_at"] == "2026-09-15"
    assert job["raw_data"]["extraction_method"] == "jsonld_jobposting"


def test_jsonld_array_of_jobpostings_all_extracted():
    jobs = extract_jobs_from_html(MULTIPLE_JOBS_JSONLD_FIXTURE, "https://gamma.example.com/careers")
    assert len(jobs) == 2
    titles = {j["title"] for j in jobs}
    assert titles == {"Frontend Engineer", "Backend Engineer"}


def test_microdata_jobposting_used_as_fallback_when_no_jsonld():
    jobs = extract_jobs_from_html(MICRODATA_FIXTURE, "https://betacorp.example.com/careers")
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    assert jobs[0]["company"] == "Beta Corp"
    assert jobs[0]["raw_data"]["extraction_method"] == "microdata_jobposting"


def test_jsonld_preferred_over_microdata_when_both_present():
    """If a page somehow has both, JSON-LD wins (checked first, returns early)."""
    combined = JSONLD_FIXTURE.replace("</head>", "</head>") + MICRODATA_FIXTURE
    jobs = extract_jobs_from_html(combined, "https://x.example.com")
    assert len(jobs) == 1
    assert jobs[0]["raw_data"]["extraction_method"] == "jsonld_jobposting"


def test_no_structured_data_returns_empty_not_fabricated():
    """Honest finding (confirmed live against notion.com/careers, a real
    production React/Next.js careers page): many real careers pages render
    job listings as plain HTML with CSS-module-hashed class names and NO
    schema.org markup at all (neither JSON-LD nor microdata). This adapter
    deliberately returns [] rather than guessing from hashed/unstable class
    names - a false "0 jobs found" is far safer for this platform's
    direct-apply moat than fabricating low-confidence records from
    unrecognized markup. Per-site custom selectors are a Tier 1
    (DETERMINISTIC_HTTP) concern, not this generic adaptive tier."""
    jobs = extract_jobs_from_html(NO_STRUCTURED_DATA_FIXTURE, "https://unknown.example.com/careers")
    assert jobs == []


def test_malformed_jsonld_does_not_crash():
    bad_html = '<script type="application/ld+json">{not valid json</script>'
    jobs = extract_jobs_from_html(bad_html, "https://x.example.com")
    assert jobs == []


def test_jsonld_location_handles_list_of_places():
    item = {"jobLocation": [{"address": {"addressLocality": "Cairo", "addressCountry": "Egypt"}}]}
    assert _extract_jsonld_location(item) == "Cairo, Egypt"


def test_jsonld_location_handles_missing_location():
    assert _extract_jsonld_location({}) == ""


# ---------------------------------------------------------------------------
# §9/§13 SSRF guard - this standalone script's own defense-in-depth copy
# (duplicated from apps/scraper/pipeline/ssrf_guard.py by design, since this
# script must stay dependency-free - see its module docstring).
# ---------------------------------------------------------------------------
from scrapling_runner import is_url_safe, run as _runner_run  # noqa: E402


def test_is_url_safe_allows_public_ip_literal():
    safe, reason = is_url_safe("http://93.184.216.34/careers")
    assert safe is True


def test_is_url_safe_blocks_loopback():
    safe, reason = is_url_safe("http://127.0.0.1:8000/admin")
    assert safe is False
    assert "blocked" in reason.lower() or "127.0.0.1" in reason


def test_is_url_safe_blocks_metadata_ip():
    safe, reason = is_url_safe("http://169.254.169.254/latest/meta-data/")
    assert safe is False


def test_is_url_safe_blocks_rfc1918():
    safe, reason = is_url_safe("http://192.168.1.1/internal")
    assert safe is False


def test_is_url_safe_blocks_file_scheme():
    safe, reason = is_url_safe("file:///etc/passwd")
    assert safe is False
    assert "scheme" in reason


def test_is_url_safe_blocks_localhost_hostname():
    safe, reason = is_url_safe("http://localhost/x")
    assert safe is False


def test_run_blocks_unsafe_url_before_any_fetch_attempt():
    """run() must short-circuit on the SSRF check BEFORE importing/invoking
    Scrapling's Fetcher at all - proven by the fact this returns the SSRF
    error even in an environment where scrapling isn't installed (which
    would otherwise surface as a different 'scrapling not installed'
    error first if the check order were wrong)."""
    result = _runner_run("http://127.0.0.1:9999/internal", {})
    assert result["jobs"] == []
    assert result["evidence"].get("ssrf_blocked") is True

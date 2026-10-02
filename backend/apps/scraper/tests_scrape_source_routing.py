"""Tests proving tasks.scrape_source() is wired through StrategyRouter (§1/§2).

Covers:
  1. Zero behavior change for a Source with a KNOWN ats_platform (e.g.
     greenhouse) - must route Tier.STRUCTURED and call the exact same
     connector function as before, with the exact same company_slug.
  2. A Source with an UNKNOWN platform must NOT silently return [] anymore -
     it must be routed to the adaptive fallback (Tier.ADAPTIVE), which first
     attempts source discovery and only then the out-of-process Scrapling
     runner (both exercised here via mocks/fakes, no real network calls).
  3. Source discovery finding a KNOWN ATS for an "unknown" source must result
     in that structured connector being called, not Scrapling.
"""
from unittest.mock import patch, MagicMock

import pytest

from apps.scraper import tasks
from apps.scraper.pipeline.source_discovery import DiscoveryResult


class _FakeSource:
    """Minimal stand-in for apps.jobs.models.Source (avoid DB in these tests)."""

    def __init__(self, slug, ats_platform, url="https://example.com/careers",
                 requires_playwright=False, type="scraper"):
        self.slug = slug
        self.ats_platform = ats_platform
        self.url = url
        self.requires_playwright = requires_playwright
        self.type = type


def test_known_platform_routes_structured_and_calls_existing_connector():
    """A greenhouse source must still call fetch_greenhouse_jobs with the
    stripped slug - the EXACT pre-refactor behavior - because 'greenhouse' is
    in StrategyRouter.STRUCTURED_ATS."""
    source = _FakeSource(slug="stripe-greenhouse", ats_platform="greenhouse")

    with patch("apps.scraper.ats.greenhouse.fetch_greenhouse_jobs") as mock_fetch:
        mock_fetch.return_value = [{"title": "Engineer"}]
        jobs = tasks.scrape_source(source)

    mock_fetch.assert_called_once_with("stripe")
    assert jobs == [{"title": "Engineer"}]


def test_unknown_platform_does_not_silently_return_empty():
    """Previously: unknown platform -> logged a warning and returned [] with
    no further attempt. Now: it must be routed to the adaptive fallback,
    which should at least ATTEMPT source discovery (even if that discovery
    finds nothing and the final result is still [])."""
    source = _FakeSource(slug="some-unknown-co", ats_platform="totally_unknown_platform")

    with patch(
        "apps.scraper.pipeline.source_discovery.discover_ats"
    ) as mock_discover, patch("requests.get") as mock_get:
        mock_discover.return_value = DiscoveryResult(slug="some-unknown-co", healthy=False)
        jobs = tasks.scrape_source(source)

    assert mock_discover.called, "adaptive fallback must attempt source discovery first"
    assert jobs == []


def test_unknown_platform_discovers_known_ats_and_uses_structured_connector():
    """If source discovery finds the company is actually on a known structured
    ATS (e.g. the seed data is stale / employer migrated), the structured
    connector must be used - NOT the Scrapling adaptive runner."""
    source = _FakeSource(slug="migrated-co", ats_platform="")

    discovery_result = DiscoveryResult(
        slug="migrated-co", provider="ashby", tenant="migrated-co",
        endpoint="https://api.ashbyhq.com/posting-api/job-board/migrated-co",
        job_count=3, healthy=True,
    )

    with patch(
        "apps.scraper.pipeline.source_discovery.discover_ats",
        return_value=discovery_result,
    ), patch("apps.scraper.ats.ashby.fetch_ashby_jobs") as mock_ashby:
        mock_ashby.return_value = [{"title": "PM"}, {"title": "Eng"}, {"title": "Designer"}]
        jobs = tasks.scrape_source(source)

    mock_ashby.assert_called_once_with("migrated-co")
    assert len(jobs) == 3


def test_adaptive_runner_falls_through_to_scrapling_when_no_runner_configured():
    """With SCRAPLING_RUNNER_PYTHON unset (the default), the adaptive runner
    must degrade gracefully to [] rather than erroring."""
    source = _FakeSource(slug="no-ats-co", ats_platform="")

    discovery_result = DiscoveryResult(slug="no-ats-co", healthy=False)

    with patch(
        "apps.scraper.pipeline.source_discovery.discover_ats",
        return_value=discovery_result,
    ), patch("django.conf.settings.SCRAPLING_RUNNER_PYTHON", "", create=True):
        jobs = tasks.scrape_source(source)

    assert jobs == []


def test_adaptive_runner_invokes_scrapling_backend_when_configured():
    """When SCRAPLING_RUNNER_PYTHON IS configured, the adaptive fallback must
    invoke OutOfProcessBackend.extract() exactly once (mocked - no real
    subprocess) and return its jobs."""
    source = _FakeSource(slug="no-ats-co", ats_platform="", url="https://no-ats-co.example/careers")

    discovery_result = DiscoveryResult(slug="no-ats-co", healthy=False)

    fake_extraction_result = MagicMock(ok=True, jobs=[{"title": "Found via Scrapling"}], error=None)

    with patch(
        "apps.scraper.pipeline.source_discovery.discover_ats",
        return_value=discovery_result,
    ), patch("django.conf.settings.SCRAPLING_RUNNER_PYTHON", "/fake/venv/bin/python", create=True), patch(
        "apps.scraper.pipeline.extraction_adapter.OutOfProcessBackend"
    ) as MockBackend:
        instance = MockBackend.return_value
        instance.available.return_value = True
        instance.extract.return_value = fake_extraction_result

        jobs = tasks.scrape_source(source)

    instance.extract.assert_called_once_with("https://no-ats-co.example/careers")
    assert jobs == [{"title": "Found via Scrapling"}]

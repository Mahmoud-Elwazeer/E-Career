"""Tests for the scraping Strategy Router (Phase A).

Pure/offline: uses lightweight fake source objects and injected runners, so no
DB, network, or heavy libs are needed. Verifies deterministic tier selection and
that the router delegates to the correct runner (and never duplicates connector
logic — Tier 0 always goes through the injected structured runner).
"""
from types import SimpleNamespace

from apps.scraper.strategy_router import (
    StrategyRouter,
    Tier,
    decide_route,
)


def _source(**kw):
    base = dict(slug="acme-greenhouse", ats_platform="greenhouse", type="ats",
                requires_playwright=False)
    base.update(kw)
    return SimpleNamespace(**base)


def test_known_ats_routes_to_structured():
    d = decide_route(_source(slug="stripe-lever", ats_platform="lever"))
    assert d.tier == Tier.STRUCTURED
    assert d.company_slug == "stripe"  # platform suffix stripped
    assert d.platform == "lever"


def test_all_supported_ats_route_structured():
    for plat in ["greenhouse", "lever", "ashby", "workday", "icims", "oracle", "sap",
                 "smartrecruiters", "workable", "teamtailor", "bamboohr"]:
        d = decide_route(_source(slug=f"x-{plat}", ats_platform=plat))
        assert d.tier == Tier.STRUCTURED, plat


def test_playwright_flag_routes_browser():
    d = decide_route(_source(slug="foo", ats_platform="", type="careers_page",
                             requires_playwright=True))
    assert d.tier == Tier.BROWSER


def test_static_career_page_routes_http():
    d = decide_route(_source(slug="foo", ats_platform="", type="careers_page"))
    assert d.tier == Tier.HTTP


def test_unknown_layout_routes_adaptive():
    d = decide_route(_source(slug="foo", ats_platform="", type="unknown"))
    assert d.tier == Tier.ADAPTIVE


def test_router_delegates_structured_to_injected_runner():
    calls = {}

    def structured(platform, slug):
        calls["structured"] = (platform, slug)
        return [{"title": "Job A"}]

    router = StrategyRouter(structured_runner=structured)
    jobs, decision = router.run(_source(slug="acme-ashby", ats_platform="ashby"))
    assert jobs == [{"title": "Job A"}]
    assert decision.tier == Tier.STRUCTURED
    assert calls["structured"] == ("ashby", "acme")


def test_router_degrades_when_optional_runner_absent():
    # ADAPTIVE tier with no adaptive runner injected → graceful empty, no crash.
    router = StrategyRouter(structured_runner=lambda p, s: [])
    jobs, decision = router.run(_source(slug="foo", ats_platform="", type="unknown"))
    assert jobs == []
    assert decision.tier == Tier.ADAPTIVE


def test_router_uses_http_runner_when_provided():
    router = StrategyRouter(
        structured_runner=lambda p, s: [],
        http_runner=lambda src: [{"title": "HTTP job"}],
    )
    jobs, decision = router.run(_source(slug="foo", ats_platform="", type="careers_page"))
    assert jobs == [{"title": "HTTP job"}]
    assert decision.tier == Tier.HTTP

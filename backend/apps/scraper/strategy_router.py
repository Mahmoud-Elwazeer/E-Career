"""Scraping Strategy Router (Phase A).

A thin, testable abstraction over the existing crawler stack that makes the
tiered acquisition strategy EXPLICIT and documents where each tier lives. It
does NOT replace the working orchestrator/connectors — it routes a Source to
the correct tier and records which tier handled it, so behaviour is observable
and optional/heavy libraries stay out of the main runtime.

Tiers (cheap → expensive):
  TIER 0  STRUCTURED   official/public ATS API, JSON feed, RSS, JSON-LD, sitemap
  TIER 1  HTTP         fast deterministic HTTP + HTML parse (unknown career page)
  TIER 2  BROWSER      JS-rendered page (Playwright / Scrapling DynamicFetcher)
  TIER 3  ADAPTIVE     adaptive selectors (Scrapling) — out-of-process/optional
  TIER 4  AI           schema-guided LLM extraction (Crawl4AI/Bedrock) — optional
  TIER 5  AGENTIC      controlled agentic browser — last resort, NOT normal path

Routing rule (deterministic, cheapest capable tier first):
  if source has a known ATS platform with a real connector -> TIER 0
  elif source is a static career page                       -> TIER 1
  elif source requires JS rendering                         -> TIER 2
  else                                                       -> ADAPTIVE/AI (opt)

The router returns a decision (which tier + why); the caller executes it. TIER 0
delegates to the EXISTING connector dispatch so we never duplicate that logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Optional

import structlog

logger = structlog.get_logger()


class Tier(IntEnum):
    STRUCTURED = 0
    HTTP = 1
    BROWSER = 2
    ADAPTIVE = 3
    AI = 4
    AGENTIC = 5


# ATS platforms that have a REAL structured connector today (Tier 0).
# Keep in sync with the connector dispatch in tasks.py / orchestrator.py.
STRUCTURED_ATS = {
    "greenhouse",
    "lever",
    "ashby",
    "bamboohr",
    "smartrecruiters",
    "workable",
    "teamtailor",
    "workday",   # Tier-2 under the hood (Playwright) but dispatched structurally
    "icims",
    "oracle",
    "sap",
    "recruitee",
    "eightfold",
    "personio",
    "jobvite",  # DISCOVERY_UNSUPPORTED stub (see ats/jobvite.py) - routes
                # structurally like oracle/sap, honestly returns [] until
                # per-tenant credentials exist.
    "breezy",   # public unauthenticated JSON feed at {slug}.breezy.hr/json,
                # verified live 2026-10-03 (see ats/breezy.py).
}


@dataclass
class RouteDecision:
    tier: Tier
    reason: str
    company_slug: str
    platform: str


def _company_slug(source) -> str:
    platform = (getattr(source, "ats_platform", "") or "").lower()
    slug = getattr(source, "slug", "") or ""
    if platform and slug.endswith(f"-{platform}"):
        slug = slug[: -len(f"-{platform}")]
    return slug


def decide_route(source) -> RouteDecision:
    """Classify a Source into the cheapest capable acquisition tier."""
    platform = (getattr(source, "ats_platform", "") or "").lower()
    slug = _company_slug(source)

    if platform in STRUCTURED_ATS:
        return RouteDecision(
            tier=Tier.STRUCTURED,
            reason=f"known structured ATS connector: {platform}",
            company_slug=slug,
            platform=platform,
        )

    # requires_playwright is an existing Source flag for JS-heavy pages.
    if getattr(source, "requires_playwright", False):
        return RouteDecision(
            tier=Tier.BROWSER,
            reason="source flagged requires_playwright",
            company_slug=slug,
            platform=platform or "generic",
        )

    source_type = (getattr(source, "type", "") or "").lower()
    if source_type in ("careers_page", "html", "career_page"):
        return RouteDecision(
            tier=Tier.HTTP,
            reason="static career page (HTTP tier)",
            company_slug=slug,
            platform=platform or "generic",
        )

    # Unknown structure → adaptive/AI, which are OPTIONAL out-of-process tiers.
    return RouteDecision(
        tier=Tier.ADAPTIVE,
        reason="unknown layout → adaptive/AI fallback (optional service)",
        company_slug=slug,
        platform=platform or "generic",
    )


class StrategyRouter:
    """Routes a source to a tier and executes via an injected structured runner.

    The structured runner is the EXISTING connector dispatch (passed in) so this
    router adds routing/observability without duplicating connector logic. Higher
    tiers (adaptive/AI/agentic) are optional and only invoked if a runner for
    them is provided (they may live out-of-process to avoid dep conflicts).
    """

    def __init__(
        self,
        structured_runner: Callable[[str, str], list],
        http_runner: Optional[Callable[[object], list]] = None,
        browser_runner: Optional[Callable[[object], list]] = None,
        adaptive_runner: Optional[Callable[[object], list]] = None,
        ai_runner: Optional[Callable[[object], list]] = None,
    ):
        self._structured = structured_runner
        self._http = http_runner
        self._browser = browser_runner
        self._adaptive = adaptive_runner
        self._ai = ai_runner

    def run(self, source) -> tuple[list, RouteDecision]:
        decision = decide_route(source)
        logger.info(
            "scrape_route_selected",
            source=getattr(source, "slug", "?"),
            tier=decision.tier.name,
            reason=decision.reason,
        )
        jobs = self._execute(source, decision)
        logger.info(
            "scrape_route_result",
            source=getattr(source, "slug", "?"),
            tier=decision.tier.name,
            jobs_found=len(jobs) if jobs else 0,
        )
        return jobs or [], decision

    def _execute(self, source, decision: RouteDecision) -> list:
        if decision.tier == Tier.STRUCTURED:
            return self._structured(decision.platform, decision.company_slug)
        if decision.tier == Tier.HTTP and self._http:
            return self._http(source)
        if decision.tier == Tier.BROWSER and self._browser:
            return self._browser(source)
        if decision.tier == Tier.ADAPTIVE and self._adaptive:
            return self._adaptive(source)
        if decision.tier == Tier.AI and self._ai:
            return self._ai(source)
        # No runner available for the chosen optional tier → degrade gracefully.
        logger.warning(
            "scrape_route_no_runner",
            source=getattr(source, "slug", "?"),
            tier=decision.tier.name,
        )
        return []

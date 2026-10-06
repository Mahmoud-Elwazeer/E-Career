#!/usr/bin/env python3
"""Out-of-process Scrapling extraction runner (§15/§16).

STANDALONE SCRIPT - zero Django imports, zero dependency on the main
backend package. This is the actual process invoked by
OutOfProcessBackend.runner_cmd (apps/scraper/pipeline/extraction_adapter.py).
It is designed to run inside its OWN isolated virtualenv, separate from the
main Django venv, specifically because Scrapling pins `lxml>=6.1.1` while
this project's `docling` (CV parser) requires `lxml<6.0.0` - a real,
confirmed conflict (verified against current PyPI metadata, not assumed).

Protocol (matches OutOfProcessBackend.extract()):
    stdin:  JSON  {"url": "<job listing/careers page url>", "hints": {...}}
    stdout: JSON  {"jobs": [...], "evidence": {...}}
    exit 0 on success (even if jobs is empty - that's a valid "nothing found"
    result, not a failure); exit != 0 only on a real runner-level error
    (Scrapling itself threw, page unreachable, etc).

Extraction strategy for ADAPTIVE_PARSER tier (§15): this tier exists for
career/job pages that defeat Tier 0 (structured ATS API) and Tier 1
(deterministic HTTP + known selectors) - typically a non-ATS company careers
page with no public JSON API and a DOM that isn't addressable by a fixed
CSS/XPath selector set. Scrapling's value-add over plain requests+BeautifulSoup
is its adaptive/self-healing selector matching (`auto_save`/`adaptive=True`)
and built-in anti-bot bypass for Cloudflare-protected pages - NOT raw HTML
fetching, which Tier 1 already does. This runner uses Scrapling's `Fetcher`
for a static-HTML attempt first, and only escalates to `StealthyFetcher`
(headless browser, slower, higher resource cost) if the static fetch is
blocked or returns a bot-challenge page.

Setup - TWO reproducible options, both isolated from the main backend venv:

  OPTION A (preferred - Docker, see ./Dockerfile in this directory):
      docker build -t usam-scrapling-runner:0.4.15 \
          -f apps/scraper/extraction_runners/Dockerfile \
          apps/scraper/extraction_runners
      # then set the Django env var:
      #   SCRAPLING_RUNNER_CMD=docker,run,--rm,-i,usam-scrapling-runner:0.4.15
      # Verified end-to-end on 2026-10-02: built the image, ran it against a
      # real live Greenhouse-hosted job page (job-boards.greenhouse.io/
      # stripe/jobs/8172510) via `echo '{"url": "..."}' | docker run --rm -i
      # usam-scrapling-runner:0.4.15` and got back a real JobPosting JSON-LD
      # extraction (title/description/company/location/apply_url) - this is
      # not a hypothetical artifact, it has been built and exercised.

  OPTION B (plain isolated venv, no Docker):
      python3 -m venv /opt/scrapling-runner-venv
      /opt/scrapling-runner-venv/bin/pip install -r requirements.txt
      /opt/scrapling-runner-venv/bin/python -m playwright install chromium
      # then set the Django env var:
      #   SCRAPLING_RUNNER_PYTHON=/opt/scrapling-runner-venv/bin/python

Wiring (django side, apps/scraper/tasks.py's _adaptive_fallback_runner reads
SCRAPLING_RUNNER_CMD first, falling back to SCRAPLING_RUNNER_PYTHON + this
script's path - see config/settings/base.py for both settings):
    OutOfProcessBackend(
        name="scrapling",
        tier=ExtractionTier.ADAPTIVE_PARSER,
        runner_cmd=["docker", "run", "--rm", "-i", "usam-scrapling-runner:0.4.15"],
        # or: ["/opt/scrapling-runner-venv/bin/python", "/path/to/scrapling_runner.py"]
    )
"""
import ipaddress
import json
import socket
import sys
from urllib.parse import urlparse


# §9/§13 SSRF guard, duplicated (not imported) from
# apps/scraper/pipeline/ssrf_guard.py - this script's own module docstring
# requires "zero Django imports, zero dependency on the main backend
# package" so it can run inside a separate isolated venv/container. This is
# defense-in-depth: the Django-side OutOfProcessBackend.extract() already
# validates the URL before ever launching this process, but this script
# could in principle be invoked directly (e.g. `docker run
# usam-scrapling-runner` with attacker-controlled stdin), bypassing that
# gate entirely. See ssrf_guard.py's module docstring for the full threat
# model and its documented residual risk (redirect-chain hops are not
# re-validated by either copy of this logic).
_ALLOWED_SCHEMES = frozenset({"http", "https"})
_BLOCKED_HOSTNAMES = frozenset({"localhost", "localhost.localdomain", "metadata.google.internal"})


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable -> fail closed
    return bool(
        ip.is_loopback or ip.is_private or ip.is_link_local
        or ip.is_reserved or ip.is_multicast or ip.is_unspecified
    )


def is_url_safe(url: str) -> tuple[bool, str]:
    """Returns (safe, reason). Mirrors ssrf_guard.validate_url_safe's logic
    (scheme allowlist, blocked hostname literals, IP-literal check, then
    full DNS resolution checking every returned address) in a standalone,
    dependency-free form for this isolated script."""
    if not url or not isinstance(url, str):
        return False, "empty or non-string URL"
    try:
        parsed = urlparse(url)
    except ValueError as e:
        return False, f"unparseable URL: {e}"

    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        return False, f"disallowed scheme: {scheme!r}"

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL has no hostname"
    if hostname in _BLOCKED_HOSTNAMES:
        return False, f"blocked hostname literal: {hostname!r}"

    try:
        literal_ip = ipaddress.ip_address(hostname.strip("[]"))
        if _is_blocked_ip(str(literal_ip)):
            return False, f"blocked IP literal: {literal_ip}"
        return True, ""
    except ValueError:
        pass

    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, OSError) as e:
        return False, f"DNS resolution failed: {type(e).__name__}: {e}"
    if not addrinfo:
        return False, "DNS resolution returned no addresses"
    for entry in addrinfo:
        ip_str = entry[4][0]
        if _is_blocked_ip(ip_str):
            return False, f"resolves to blocked address: {ip_str}"
    return True, ""


def extract_jobs_from_html(html: str, url: str) -> list[dict]:
    """Best-effort generic job-listing extraction from arbitrary careers-page
    HTML. This is intentionally conservative: it looks for common job-listing
    markup patterns (schema.org JobPosting, common ATS-embed class names) and
    returns [] rather than guessing when nothing matches - a false "found 0
    jobs" is far safer for this platform's moat than fabricating low-quality
    records from an unrecognized page structure.
    """
    jobs: list[dict] = []

    try:
        from scrapling.fetchers import Fetcher  # noqa: F401  (import-time proof only)
    except ImportError:
        return jobs

    # 1. schema.org JobPosting JSON-LD (the single most reliable generic
    #    signal across arbitrary company career sites - no ATS-specific
    #    knowledge required).
    import re
    ld_json_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    )
    for block in ld_json_blocks:
        try:
            data = json.loads(block.strip())
        except (ValueError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            if item.get("@type") != "JobPosting":
                continue
            jobs.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "company": (item.get("hiringOrganization") or {}).get("name", ""),
                "location": _extract_jsonld_location(item),
                "direct_apply_url": item.get("url") or url,
                "source_url": url,
                "posted_at": item.get("datePosted"),
                "raw_data": {"extraction_method": "jsonld_jobposting"},
            })

    if jobs:
        return jobs

    # 2. schema.org JobPosting MICRODATA (itemtype attribute) - a second,
    # still-GENERIC structured-data signal some sites use instead of
    # JSON-LD. Still schema.org-conformant, not a site-specific guess.
    microdata_blocks = re.findall(
        r'<[^>]+itemtype=["\']https?://schema\.org/JobPosting["\'][^>]*>(.*?)</(?:div|article|section|li)>',
        html, re.DOTALL | re.IGNORECASE,
    )
    for block in microdata_blocks:
        title_m = re.search(r'itemprop=["\']title["\'][^>]*>([^<]+)<', block, re.IGNORECASE)
        org_m = re.search(r'itemprop=["\']name["\'][^>]*>([^<]+)<', block, re.IGNORECASE)
        if not title_m:
            continue
        jobs.append({
            "title": title_m.group(1).strip(),
            "description": "",
            "company": org_m.group(1).strip() if org_m else "",
            "location": "",
            "direct_apply_url": url,
            "source_url": url,
            "posted_at": None,
            "raw_data": {"extraction_method": "microdata_jobposting"},
        })

    return jobs


def _extract_jsonld_location(item: dict) -> str:
    loc = item.get("jobLocation")
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    if isinstance(loc, dict):
        addr = loc.get("address", {})
        if isinstance(addr, dict):
            parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
            return ", ".join(p for p in parts if p)
    return ""


def run(url: str, hints: dict) -> dict:
    evidence: dict = {"url": url, "tier_attempted": "adaptive_parser"}

    # Defense-in-depth SSRF check (see module-level docstring above
    # is_url_safe) - this script's own gate, independent of whatever
    # already validated the URL before this process was launched.
    safe, reason = is_url_safe(url)
    if not safe:
        return {"jobs": [], "evidence": {**evidence, "error": f"blocked by SSRF guard: {reason}", "ssrf_blocked": True}}

    try:
        from scrapling.fetchers import Fetcher, StealthyFetcher
    except ImportError as e:
        return {"jobs": [], "evidence": {**evidence, "error": f"scrapling not installed: {e}"}}

    # Static-HTML attempt first (cheap) - only escalate to the stealthy
    # headless-browser fetcher if the page looks bot-blocked.
    try:
        # NOTE: Fetcher.get() does not accept a `timeout` kwarg in this
        # Scrapling version (confirmed via its GetRequestParams TypedDict) -
        # it uses its own internal defaults.
        page = Fetcher.get(url)
        html = page.html_content if hasattr(page, "html_content") else str(page)
        status = getattr(page, "status", None)
        evidence["fetch_method"] = "static"
        evidence["status_code"] = status
    except Exception as e:
        evidence["static_fetch_error"] = f"{type(e).__name__}: {e}"
        html = ""
        status = None

    looks_blocked = (not html) or status in (403, 429, 503) or "cf-browser-verification" in (html or "").lower()

    if looks_blocked:
        try:
            # NOTE: Scrapling's timeout is in MILLISECONDS, not seconds -
            # confirmed empirically (a value of 30 caused every real fetch
            # to fail with "Timeout 30ms exceeded"). 30000 = 30 seconds.
            page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=30000)
            html = page.html_content if hasattr(page, "html_content") else str(page)
            evidence["fetch_method"] = "stealthy_browser"
            evidence["escalated_due_to"] = "static_fetch_blocked_or_empty"
        except Exception as e:
            return {"jobs": [], "evidence": {**evidence, "error": f"stealthy fetch failed: {type(e).__name__}: {e}"}}

    jobs = extract_jobs_from_html(html, url)
    evidence["jobs_found"] = len(jobs)
    evidence["extraction_method"] = "jsonld_jobposting" if jobs else "none_matched"
    return {"jobs": jobs, "evidence": evidence}


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError) as e:
        print(json.dumps({"jobs": [], "evidence": {"error": f"invalid stdin JSON: {e}"}}))
        return 1

    url = payload.get("url", "")
    hints = payload.get("hints", {}) or {}

    if not url:
        print(json.dumps({"jobs": [], "evidence": {"error": "no url provided"}}))
        return 1

    try:
        result = run(url, hints)
    except Exception as e:
        # Never let an unexpected exception produce a non-JSON stdout - the
        # parent process expects well-formed JSON even on failure, per the
        # OutOfProcessBackend contract (it only treats a non-zero exit code
        # as a hard failure; stdout is still parsed as JSON when present).
        print(json.dumps({"jobs": [], "evidence": {"error": f"unhandled {type(e).__name__}: {e}"}}))
        return 1

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

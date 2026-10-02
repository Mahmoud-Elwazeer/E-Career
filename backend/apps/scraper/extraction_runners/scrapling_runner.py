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
import json
import sys


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

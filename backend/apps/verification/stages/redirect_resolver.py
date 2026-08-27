from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import httpx
import structlog

logger = structlog.get_logger()

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "referrer", "source", "fbclid", "gclid", "mc_cid", "mc_eid",
}


@dataclass
class RedirectResult:
    final_url: str
    chain: list[dict[str, str | int]] = field(default_factory=list)
    redirect_count: int = 0
    error: str = ""


class RedirectResolverStage:
    """Stage 2: Follow redirects to find final destination URL (SSRF-safe)."""

    MAX_REDIRECTS = 10
    TIMEOUT = 15

    def run(self, url: str) -> RedirectResult:
        if not url:
            return RedirectResult(final_url="", error="empty_url")

        from apps.core.safe_fetch import safe_fetch, SSRFBlockedError

        try:
            result = safe_fetch(
                url,
                method="HEAD",
                timeout=self.TIMEOUT,
                allow_http=True,
                max_redirects=self.MAX_REDIRECTS,
            )

            final_url = self._strip_tracking_params(result.final_url)

            return RedirectResult(
                final_url=final_url,
                chain=result.redirect_chain,
                redirect_count=max(0, len(result.redirect_chain) - 1),
                error=result.error,
            )

        except SSRFBlockedError as e:
            logger.warning("redirect_resolver_ssrf_blocked", url=url, reason=e.reason)
            return RedirectResult(
                final_url="",
                chain=[],
                redirect_count=0,
                error=f"SSRF blocked: {e.reason}",
            )

        except Exception as e:
            logger.warning("redirect_resolver_error", url=url, error=str(e))
            return RedirectResult(
                final_url=url,
                chain=[],
                redirect_count=0,
                error=str(e),
            )

    def _strip_tracking_params(self, url: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=False)
        cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
        new_query = urlencode(cleaned, doseq=True) if cleaned else ""
        return urlunparse(parsed._replace(query=new_query))

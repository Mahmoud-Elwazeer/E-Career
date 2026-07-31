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
    """Stage 2: Follow redirects to find final destination URL."""

    MAX_REDIRECTS = 10
    TIMEOUT = 15

    def run(self, url: str) -> RedirectResult:
        if not url:
            return RedirectResult(final_url="", error="empty_url")

        chain = []
        current_url = url

        try:
            with httpx.Client(
                follow_redirects=False,
                timeout=self.TIMEOUT,
                verify=False,
            ) as client:
                for i in range(self.MAX_REDIRECTS):
                    try:
                        response = client.head(current_url, follow_redirects=False)
                    except httpx.RequestError:
                        response = client.get(current_url, follow_redirects=False)

                    chain.append({
                        "url": current_url,
                        "status": response.status_code,
                    })

                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location", "")
                        if not location:
                            break
                        if location.startswith("/"):
                            parsed = urlparse(current_url)
                            location = f"{parsed.scheme}://{parsed.netloc}{location}"
                        current_url = location
                    else:
                        break

        except Exception as e:
            logger.warning("redirect_resolver_error", url=url, error=str(e))
            return RedirectResult(
                final_url=current_url,
                chain=chain,
                redirect_count=len(chain) - 1,
                error=str(e),
            )

        final_url = self._strip_tracking_params(current_url)

        return RedirectResult(
            final_url=final_url,
            chain=chain,
            redirect_count=max(0, len(chain) - 1),
        )

    def _strip_tracking_params(self, url: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=False)
        cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
        new_query = urlencode(cleaned, doseq=True) if cleaned else ""
        return urlunparse(parsed._replace(query=new_query))

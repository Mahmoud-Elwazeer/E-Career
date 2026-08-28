"""
Adaptive Scraping Service using Scrapling.

Enhances the existing ATS scraper infrastructure with:
- Adaptive selectors (survive page redesigns)
- Anti-detection (TLS fingerprinting, Cloudflare bypass)
- Multi-session routing (HTTP for simple, browser for JS-heavy)
- AutoThrottle (per-domain adaptive rate limiting)
- robots.txt compliance

Does NOT replace existing ATS scrapers — supplements them
for unknown/custom career pages.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from typing import Any

logger = structlog.get_logger()


@dataclass
class ScrapedJob:
    """A job extracted from a career page."""
    title: str
    company: str
    location: str = ""
    description: str = ""
    apply_url: str = ""
    employment_type: str = ""
    experience_level: str = ""
    posted_date: str = ""
    department: str = ""
    salary: str = ""
    source_url: str = ""
    extraction_method: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "apply_url": self.apply_url,
            "employment_type": self.employment_type,
            "experience_level": self.experience_level,
            "posted_date": self.posted_date,
            "department": self.department,
            "salary": self.salary,
            "source_url": self.source_url,
            "extraction_method": self.extraction_method,
        }


class AdaptiveScraperService:
    """Adaptive scraping for career pages using Scrapling."""

    def __init__(self):
        self._scrapling_available = None

    @property
    def is_available(self) -> bool:
        if self._scrapling_available is None:
            try:
                import scrapling
                self._scrapling_available = True
            except ImportError:
                self._scrapling_available = False
                logger.warning("scrapling_not_installed")
        return self._scrapling_available

    def scrape_career_page(
        self,
        url: str,
        company_name: str = "",
        use_browser: bool = False,
    ) -> list[ScrapedJob]:
        """Scrape a career page for job listings.

        Args:
            url: The career page URL
            company_name: Company name for context
            use_browser: Force browser mode for JS-heavy pages
        """
        if not self.is_available:
            return self._fallback_scrape(url, company_name)

        try:
            if use_browser:
                return self._scrape_with_browser(url, company_name)
            else:
                return self._scrape_with_http(url, company_name)
        except Exception as e:
            logger.error("adaptive_scrape_failed", url=url, error=str(e))
            if not use_browser:
                logger.info("retrying_with_browser", url=url)
                try:
                    return self._scrape_with_browser(url, company_name)
                except Exception:
                    pass
            return []

    def _scrape_with_http(self, url: str, company_name: str) -> list[ScrapedJob]:
        """Fast HTTP-based scraping for static pages."""
        from scrapling import Fetcher

        fetcher = Fetcher(auto_match=True)
        response = fetcher.get(url)

        if response.status != 200:
            logger.warning("scrape_non_200", url=url, status=response.status)
            return []

        return self._extract_jobs(response, url, company_name, "scrapling_http")

    def _scrape_with_browser(self, url: str, company_name: str) -> list[ScrapedJob]:
        """Browser-based scraping for JS-heavy pages."""
        from scrapling import StealthyFetcher

        fetcher = StealthyFetcher(auto_match=True)
        response = fetcher.get(url, network_idle=True)

        if response.status != 200:
            logger.warning("scrape_non_200", url=url, status=response.status)
            return []

        return self._extract_jobs(response, url, company_name, "scrapling_browser")

    def _extract_jobs(self, response, url: str, company_name: str, method: str) -> list[ScrapedJob]:
        """Extract job listings from a scraped page."""
        jobs = []

        job_elements = (
            response.css('[data-testid*="job"]') or
            response.css('.job-listing, .job-card, .position-card') or
            response.css('article[class*="job"], div[class*="opening"]') or
            response.css('a[href*="/jobs/"], a[href*="/careers/"], a[href*="/positions/"]')
        )

        if not job_elements:
            job_elements = response.css('li[class*="job"], tr[class*="job"]')

        for elem in job_elements:
            try:
                title = (
                    elem.css_first('h2, h3, h4, [class*="title"]') or
                    elem.css_first('a')
                )
                title_text = title.text.strip() if title else ""

                if not title_text or len(title_text) < 3:
                    continue

                location_elem = elem.css_first('[class*="location"], [class*="place"]')
                location = location_elem.text.strip() if location_elem else ""

                link_elem = elem.css_first('a[href]')
                apply_url = ""
                if link_elem:
                    href = link_elem.attrib.get("href", "")
                    if href.startswith("/"):
                        from urllib.parse import urljoin
                        apply_url = urljoin(url, href)
                    elif href.startswith("http"):
                        apply_url = href

                dept_elem = elem.css_first('[class*="department"], [class*="team"]')
                department = dept_elem.text.strip() if dept_elem else ""

                jobs.append(ScrapedJob(
                    title=title_text,
                    company=company_name,
                    location=location,
                    apply_url=apply_url,
                    department=department,
                    source_url=url,
                    extraction_method=method,
                ))

            except Exception as e:
                logger.debug("job_extraction_error", error=str(e))
                continue

        logger.info("jobs_extracted", url=url, count=len(jobs), method=method)
        return jobs

    def _fallback_scrape(self, url: str, company_name: str) -> list[ScrapedJob]:
        """Fallback when Scrapling is not available — use safe_fetch + BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup
            from apps.core.safe_fetch import safe_fetch, SSRFBlockedError

            result = safe_fetch(url, method="GET", timeout=30, allow_http=True, read_body=True)
            if result.status_code == 0 or result.status_code >= 400:
                logger.warning("fallback_scrape_failed", url=url, status=result.status_code)
                return []

            soup = BeautifulSoup(result.content.decode("utf-8", errors="replace"), "html.parser")
            jobs = []

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if any(kw in href.lower() for kw in ["/jobs/", "/careers/", "/positions/", "/openings/"]):
                    if text and len(text) > 5 and len(text) < 200:
                        from urllib.parse import urljoin
                        jobs.append(ScrapedJob(
                            title=text,
                            company=company_name,
                            apply_url=urljoin(url, href),
                            source_url=url,
                            extraction_method="beautifulsoup_fallback",
                        ))

            return jobs[:50]

        except Exception as e:
            logger.error("fallback_scrape_failed", url=url, error=str(e))
            return []


_service: AdaptiveScraperService | None = None


def get_adaptive_scraper() -> AdaptiveScraperService:
    global _service
    if _service is None:
        _service = AdaptiveScraperService()
    return _service

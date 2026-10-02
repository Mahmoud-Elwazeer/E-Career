"""Personio XML job feed scraper.

Verified live 2026-10-02 against a real company board (f24.jobs.personio.de):
9 real, current positions returned with full descriptions and salary data.

IMPORTANT - this is NOT a universal endpoint. Per Personio's own official
documentation (support.personio.de, "Integrate jobs from Personio via XML"),
the XML feed only exists for a company subdomain if that employer has
EXPLICITLY enabled it (Settings > Recruiting > Career Portal > Activations >
"Enable XML feed"). There is no generic unauthenticated JSON API Personio
exposes for an arbitrary tenant - confirmed via Personio's own "Summary of
career page integration options" doc, which lists four options (Link,
iframe, XML, XML+API), none of which are a public-by-default REST API.
A 404 on this endpoint for a given slug does NOT necessarily mean the
company has no Personio board - it may just mean they haven't opted into
the XML feed. Source Discovery (apps/scraper/pipeline/source_discovery.py)
should treat a 404 here as "unconfirmed", not "definitely not Personio".

Endpoint: https://{company_subdomain}.jobs.personio.de/xml?language=en
(also works on the .com domain variant: {subdomain}.jobs.personio.com/xml)

Response is XML (not JSON) with a <workzag-jobs><position>...</position></workzag-jobs>
shape. No apply URL field is included in the feed itself - the real,
confirmed-live job detail/apply page pattern is
https://{subdomain}.jobs.personio.de/job/{id}, constructed from the <id>
field (verified live: a URL built this way for a real id resolved to a real,
correct job page as the direct-apply/employer-hosted destination - moat
compliant since it's the employer's own Personio-hosted careers page, not an
aggregator).
"""
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
from .base import BaseATSScraper


class PersonioScraper(BaseATSScraper):
    """Scrapes jobs from a company's Personio XML job feed (if enabled)."""

    FEED_URL = "https://{company_subdomain}.jobs.personio.de/xml?language=en"
    JOB_URL_PATTERN = "https://{company_subdomain}.jobs.personio.de/job/{job_id}"
    HEADERS = {
        "Accept": "application/xml",
        "User-Agent": "USAM-Career-Compass/1.0",
    }

    def get_platform_name(self) -> str:
        return "personio"

    def fetch_jobs(self) -> List[Dict]:
        try:
            url = self.FEED_URL.format(company_subdomain=self.company_slug)
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as e:
            # A 404/empty response here most often means this employer has
            # not enabled the XML feed, NOT that the connector is broken -
            # see module docstring. Logged at this level only; Source
            # Discovery is responsible for marking the source UNCONFIRMED
            # rather than INVALID based on this alone.
            print(f"Personio feed unavailable for {self.company_slug}: {e}")
            return []

        jobs = []
        for position in root.findall("position"):
            job_id = (position.findtext("id") or "").strip()
            if not job_id:
                continue

            title = position.findtext("name") or ""
            office = position.findtext("office") or ""
            department = position.findtext("department") or ""
            employment_type = position.findtext("employmentType") or ""
            seniority = position.findtext("seniority") or ""

            description_parts = []
            for jd in position.findall("jobDescriptions/jobDescription"):
                section_name = jd.findtext("name") or ""
                section_value = jd.findtext("value") or ""
                if section_value.strip():
                    description_parts.append(f"<h3>{section_name}</h3>{section_value}")
            description = "".join(description_parts)

            salary_min = salary_max = None
            salary_currency = "USD"
            salary_el = position.find("salaryInformation")
            if salary_el is not None:
                try:
                    min_text = salary_el.findtext("min")
                    max_text = salary_el.findtext("max")
                    salary_min = float(min_text) if min_text else None
                    salary_max = float(max_text) if max_text else None
                except (TypeError, ValueError):
                    pass
                salary_currency = salary_el.findtext("currencyCode") or "USD"

            apply_url = self.JOB_URL_PATTERN.format(
                company_subdomain=self.company_slug, job_id=job_id,
            )

            normalized = {
                "title": title,
                "apply_url": apply_url,
                "description": description,
                "location": office,
                "id": job_id,
                "posted_at": position.findtext("createdAt") or "",
                "departments": [department] if department else [],
                "employment_type": employment_type,
                "experience_level": seniority,
                "remote_type": "remote" if "remote" in office.lower() else "onsite",
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": salary_currency,
            }
            jobs.append(self.normalize_job(normalized))

        return jobs


def fetch_personio_jobs(company_subdomain: str) -> List[Dict]:
    """Convenience function to fetch Personio jobs."""
    scraper = PersonioScraper(company_subdomain)
    return scraper.fetch_jobs()

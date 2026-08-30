"""
Crawl4AI Integration for LLM-Based Structured Web Extraction.

Uses Crawl4AI (Apache 2.0) for extracting structured data from web pages
using LLM-powered extraction strategies. Primary use cases:
- Company profile extraction from career pages
- Job requirements extraction from unstructured HTML
- Competitor analysis page extraction

Falls back to BeautifulSoup + AI prompt when Crawl4AI is not installed.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of a structured web extraction."""
    url: str
    data: Dict = field(default_factory=dict)
    raw_html: str = ""
    markdown: str = ""
    success: bool = True
    error: str = ""
    extraction_method: str = "crawl4ai"


class Crawl4AIExtractor:
    """
    Structured web extraction using Crawl4AI.

    Crawl4AI provides:
    - Browser-based rendering for JS-heavy pages
    - LLM extraction strategies (JsonCssExtractionStrategy, LLMExtractionStrategy)
    - Markdown conversion for RAG pipelines
    - Chunking strategies for large pages
    """

    def __init__(self):
        self._crawler = None

    @property
    def is_available(self) -> bool:
        try:
            import crawl4ai
            return True
        except ImportError:
            return False

    def extract_company_profile(self, url: str) -> ExtractionResult:
        """
        Extract structured company profile from a careers/about page.

        Returns company info: name, description, industry, size, culture, benefits.
        """
        schema = {
            "name": "Company name",
            "description": "Brief company description",
            "industry": "Primary industry",
            "size": "Company size (startup/small/medium/large/enterprise)",
            "founded": "Year founded",
            "headquarters": "HQ location",
            "culture_values": ["List of culture values"],
            "benefits": ["List of benefits mentioned"],
            "tech_stack": ["Technologies mentioned"],
        }

        return self._extract_with_schema(url, schema, "company_profile")

    def extract_job_details(self, url: str) -> ExtractionResult:
        """
        Extract structured job details from a job posting page.

        Returns: title, description, requirements, benefits, salary, location.
        """
        schema = {
            "title": "Job title",
            "department": "Department",
            "location": "Job location",
            "remote_type": "Remote/hybrid/onsite",
            "employment_type": "Full-time/part-time/contract",
            "experience_level": "Entry/mid/senior/lead",
            "description": "Job description",
            "responsibilities": ["List of responsibilities"],
            "requirements": ["List of requirements"],
            "nice_to_have": ["Optional qualifications"],
            "benefits": ["Benefits listed"],
            "salary_range": "Salary range if mentioned",
            "apply_url": "Direct application URL",
        }

        return self._extract_with_schema(url, schema, "job_details")

    def extract_to_markdown(self, url: str) -> ExtractionResult:
        """
        Convert a web page to clean markdown for RAG/content processing.
        """
        if self.is_available:
            return self._crawl4ai_markdown(url)
        return self._fallback_markdown(url)

    def _extract_with_schema(
        self, url: str, schema: Dict, extraction_type: str
    ) -> ExtractionResult:
        """Extract structured data using schema-guided extraction."""
        if self.is_available:
            return self._crawl4ai_extract(url, schema, extraction_type)
        return self._fallback_extract(url, schema, extraction_type)

    def _crawl4ai_extract(
        self, url: str, schema: Dict, extraction_type: str
    ) -> ExtractionResult:
        """Use Crawl4AI's LLM extraction strategy."""
        try:
            from crawl4ai import WebCrawler
            from crawl4ai.extraction_strategy import LLMExtractionStrategy

            import json

            from apps.intelligence.bedrock_plugin import MODEL_ALIASES
            haiku_id = MODEL_ALIASES.get("haiku")
            strategy = LLMExtractionStrategy(
                provider=f"bedrock/{haiku_id}",
                schema=schema,
                instruction=f"Extract {extraction_type} information from this page.",
            )

            crawler = WebCrawler()
            crawler.warmup()

            result = crawler.run(
                url=url,
                extraction_strategy=strategy,
            )

            if result.success:
                extracted = json.loads(result.extracted_content) if result.extracted_content else {}
                return ExtractionResult(
                    url=url,
                    data=extracted,
                    markdown=result.markdown or "",
                    success=True,
                    extraction_method="crawl4ai",
                )

            return ExtractionResult(
                url=url, success=False, error="Crawl4AI extraction failed"
            )

        except Exception as e:
            logger.error(f"Crawl4AI extraction failed for {url}: {e}")
            return self._fallback_extract(url, schema, extraction_type)

    def _crawl4ai_markdown(self, url: str) -> ExtractionResult:
        """Convert page to markdown using Crawl4AI."""
        try:
            from crawl4ai import WebCrawler

            crawler = WebCrawler()
            crawler.warmup()

            result = crawler.run(url=url)

            if result.success:
                return ExtractionResult(
                    url=url,
                    markdown=result.markdown or "",
                    raw_html=result.html or "",
                    success=True,
                    extraction_method="crawl4ai",
                )

            return ExtractionResult(url=url, success=False, error="Crawl failed")

        except Exception as e:
            logger.error(f"Crawl4AI markdown failed for {url}: {e}")
            return self._fallback_markdown(url)

    def _fallback_extract(
        self, url: str, schema: Dict, extraction_type: str
    ) -> ExtractionResult:
        """Fallback: fetch page, convert to text, then use AI to extract."""
        import json
        from bs4 import BeautifulSoup
        from apps.core.safe_fetch import safe_fetch, SSRFBlockedError

        try:
            result = safe_fetch(url, method="GET", timeout=30, allow_http=True, read_body=True)
            if result.status_code == 0 or result.status_code >= 400:
                return ExtractionResult(url=url, success=False, error=f"HTTP {result.status_code}")

            soup = BeautifulSoup(result.content.decode("utf-8", errors="replace"), 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)[:8000]

            from apps.intelligence.service import get_ai_service
            from apps.intelligence.llm_plugin import LLMRequest

            service = get_ai_service()
            prompt = f"""Extract {extraction_type} information from this web page content.

Return a JSON object matching this schema:
{json.dumps(schema, indent=2)}

PAGE CONTENT:
{text}

Return ONLY valid JSON."""

            response = service.generate(LLMRequest(
                prompt=prompt,
                system_prompt="You are a web data extraction expert. Extract structured data accurately.",
                model="haiku",
                max_tokens=2000,
                operation="extraction",
            ))

            json_start = response.content.find('{')
            json_end = response.content.rfind('}') + 1
            data = json.loads(response.content[json_start:json_end])

            return ExtractionResult(
                url=url,
                data=data,
                success=True,
                extraction_method="fallback_ai",
            )

        except Exception as e:
            logger.error(f"Fallback extraction failed for {url}: {e}")
            return ExtractionResult(url=url, success=False, error=str(e))

    def _fallback_markdown(self, url: str) -> ExtractionResult:
        """Fallback: simple HTML to text conversion."""
        from bs4 import BeautifulSoup
        from apps.core.safe_fetch import safe_fetch

        try:
            result = safe_fetch(url, method="GET", timeout=30, allow_http=True, read_body=True)
            if result.status_code == 0 or result.status_code >= 400:
                return ExtractionResult(url=url, success=False, error=f"HTTP {result.status_code}")

            html_text = result.content.decode("utf-8", errors="replace")
            soup = BeautifulSoup(html_text, 'html.parser')
            for tag in soup(['script', 'style']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)

            return ExtractionResult(
                url=url,
                markdown=text,
                raw_html=html_text,
                success=True,
                extraction_method="beautifulsoup",
            )

        except Exception as e:
            return ExtractionResult(url=url, success=False, error=str(e))


_extractor: Optional[Crawl4AIExtractor] = None


def get_crawl4ai_extractor() -> Crawl4AIExtractor:
    global _extractor
    if _extractor is None:
        _extractor = Crawl4AIExtractor()
    return _extractor

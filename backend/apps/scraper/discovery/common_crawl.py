"""
Company Discovery via Common Crawl

Scans Common Crawl segments for ATS URL patterns (greenhouse.io, lever.co, etc.)
and extracts company slugs.
"""
import gzip
import json
import logging
import re
import os
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime

from django.core.cache import cache

from apps.core.safe_fetch import safe_fetch

logger = logging.getLogger(__name__)


class CommonCrawlDiscovery:
    """
    Discovers companies by scanning Common Crawl segments for ATS URL patterns.
    
    Features:
    - Download relevant Common Crawl segments
    - Scan for ATS URL patterns (greenhouse.io, lever.co, etc.)
    - Extract company slugs
    - Validate discovered companies (active career page?)
    - Store in Source model with type='ats'
    """
    
    # ATS platform patterns
    ATS_PATTERNS = {
        'greenhouse': r'greenhouse\.io/(\w+)',
        'lever': r'lever\.co/(\w+)',
        'ashby': r'ashby\.com/(\w+)',
        'bamboohr': r'bamboohr\.com/(\w+)',
        'workable': r'workable\.com/(\w+)',
        'smartrecruiters': r'smartrecruiters\.com/(\w+)',
        'teamtailor': r'teamtailor\.com/(\w+)',
    }
    
    # Career page patterns
    CAREER_PAGE_PATTERNS = [
        r'/careers?',
        r'/jobs?',
        r'/work-with-us',
        r'/talent',
        r'/opportunities',
    ]
    
    # Cache timeout: 7 days
    CACHE_TIMEOUT = 60 * 60 * 24 * 7
    
    def __init__(self, output_dir: str = '/tmp/common_crawl'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def get_recent_crawl_ids(self, limit: int = 5) -> List[str]:
        """
        Get recent Common Crawl index IDs.
        
        Args:
            limit: Number of recent crawl IDs to return
            
        Returns:
            List of crawl IDs
        """
        cache_key = 'common_crawl:crawl_ids'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            result = safe_fetch(
                'https://index.commoncrawl.org/collisions.json',
                method="GET", timeout=30, read_body=True
            )
            if result.status_code == 0 or result.status_code >= 400:
                logger.error(f"Failed to get crawl IDs: HTTP {result.status_code}")
                return []

            import json as _json
            data = _json.loads(result.content)
            crawl_ids = [item['id'] for item in data.get('items', [])[:limit]]

            cache.set(cache_key, crawl_ids, self.CACHE_TIMEOUT)
            return crawl_ids

        except Exception as e:
            logger.error(f"Failed to get crawl IDs: {e}")
            return []
    
    def download_warc_file(self, warc_url: str, output_path: str) -> bool:
        """
        Download a WARC file from Common Crawl (SSRF-safe).
        Only allows downloads from commoncrawl.s3.amazonaws.com.
        """
        from urllib.parse import urlparse

        parsed = urlparse(warc_url)
        allowed_hosts = {"commoncrawl.s3.amazonaws.com", "data.commoncrawl.org"}
        if parsed.hostname not in allowed_hosts:
            logger.error(f"Blocked WARC download from non-CC host: {parsed.hostname}")
            return False

        from apps.core.safe_fetch import safe_fetch, SSRFBlockedError
        try:
            result = safe_fetch(
                warc_url, method="GET", timeout=120,
                allow_http=True, read_body=True,
                max_size=100 * 1024 * 1024,
            )
            if result.status_code == 200 and result.content:
                with open(output_path, 'wb') as f:
                    f.write(result.content)
                logger.info(f"Downloaded WARC file: {output_path}")
                return True
            return False
        except SSRFBlockedError as e:
            logger.error(f"SSRF blocked WARC download: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"Failed to download WARC file: {e}")
            return False
    
    def extract_companies_from_warc(self, warc_path: str, max_lines: int = 10000) -> List[Dict]:
        """
        Extract company information from a WARC file.
        
        Args:
            warc_path: Path to the WARC file
            max_lines: Maximum lines to process
            
        Returns:
            List of company dictionaries
        """
        companies = []
        
        try:
            with gzip.open(warc_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    
                    try:
                        record = json.loads(line)
                        companies.extend(self._process_record(record))
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to process WARC file: {e}")
        
        return companies
    
    def _process_record(self, record: Dict) -> List[Dict]:
        """Process a single WARC record."""
        companies = []
        
        # Check if this is a response record
        if record.get('type') != 'response':
            return companies
        
        # Get URL
        url = record.get('target', {}).get('url', '')
        if not url:
            return companies
        
        # Check if this is a career page
        if not self._is_career_page(url):
            return companies
        
        # Extract ATS platform and company slug
        for platform, pattern in self.ATS_PATTERNS.items():
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                company_slug = match.group(1)
                companies.append({
                    'name': self._slug_to_name(company_slug),
                    'slug': company_slug,
                    'ats_platform': platform,
                    'source_url': url,
                    'career_page_url': url,
                })
                break  # Only match one platform per URL
        
        return companies
    
    def _is_career_page(self, url: str) -> bool:
        """Check if URL is a career page."""
        parsed = urlparse(url)
        
        # Check path patterns
        for pattern in self.CAREER_PAGE_PATTERNS:
            if re.search(pattern, parsed.path, re.IGNORECASE):
                return True
        
        return False
    
    def _slug_to_name(self, slug: str) -> str:
        """Convert slug to company name."""
        # Common slug patterns
        name = slug.replace('-', ' ').replace('_', ' ').title()
        
        # Handle common suffixes
        suffixes = ['Inc', 'LLC', 'Ltd', 'Corp', 'Company', 'Corporation']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name.replace(f' {suffix}', '')
                break
        
        return name
    
    def discover_companies(self, crawl_ids: Optional[List[str]] = None, 
                          max_crawl_files: int = 3) -> List[Dict]:
        """
        Discover companies from Common Crawl.
        
        Args:
            crawl_ids: List of crawl IDs to process (uses recent if None)
            max_crawl_files: Maximum WARC files to process per crawl
            
        Returns:
            List of discovered companies
        """
        if crawl_ids is None:
            crawl_ids = self.get_recent_crawl_ids()
        
        all_companies = []
        
        for crawl_id in crawl_ids:
            logger.info(f"Processing crawl: {crawl_id}")
            
            # Get WARC files for this crawl
            warc_files = self._get_warc_files(crawl_id)
            
            for warc_url in warc_files[:max_crawl_files]:
                # Download WARC file
                warc_path = os.path.join(self.output_dir, f"{crawl_id}.warc.gz")
                
                if not os.path.exists(warc_path):
                    if not self.download_warc_file(warc_url, warc_path):
                        continue
                
                # Extract companies
                companies = self.extract_companies_from_warc(warc_path)
                all_companies.extend(companies)
        
        # Deduplicate
        unique_companies = self._deduplicate_companies(all_companies)
        
        return unique_companies
    
    def _get_warc_files(self, crawl_id: str, limit: int = 10) -> List[str]:
        """
        Get WARC file URLs for a crawl.
        
        Args:
            crawl_id: Crawl ID
            limit: Maximum number of WARC files
            
        Returns:
            List of WARC file URLs
        """
        cache_key = f'common_crawl:warc_files:{crawl_id}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            index_url = f"https://index.commoncrawl.org/CC-MAIN-{crawl_id}-index"
            result = safe_fetch(
                f"{index_url}/collisions.json", method="GET", timeout=30, read_body=True
            )
            if result.status_code == 0 or result.status_code >= 400:
                logger.error(f"Failed to get WARC files for {crawl_id}: HTTP {result.status_code}")
                return []

            import json as _json
            data = _json.loads(result.content)
            warc_files = [item.get('warc', {}).get('filename', '')
                         for item in data.get('items', [])[:limit]]

            cache.set(cache_key, warc_files, self.CACHE_TIMEOUT)
            return warc_files

        except Exception as e:
            logger.error(f"Failed to get WARC files for {crawl_id}: {e}")
            return []
    
    def _deduplicate_companies(self, companies: List[Dict]) -> List[Dict]:
        """Deduplicate companies by slug."""
        seen_slugs = set()
        unique = []
        
        for company in companies:
            slug = company.get('slug', '')
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                unique.append(company)
        
        return unique
    
    def validate_company(self, company: Dict) -> bool:
        """
        Validate that a company has an active career page (SSRF-safe).
        """
        career_url = company.get('career_page_url', '')
        if not career_url:
            return False

        from apps.core.safe_fetch import verify_url_is_live
        is_live, _ = verify_url_is_live(career_url, timeout=10, allow_http=True)
        return is_live
    
    def save_to_database(self, companies: List[Dict]) -> Dict[str, int]:
        """
        Save discovered companies to the database.
        
        Args:
            companies: List of company dictionaries
            
        Returns:
            Dict with 'created' and 'skipped' counts
        """
        from apps.jobs.models import Source
        
        created = 0
        skipped = 0
        
        for company in companies:
            try:
                # Check if source already exists
                slug = company.get('slug', '')
                ats_platform = company.get('ats_platform', '')
                
                existing = Source.objects.filter(
                    slug__iexact=slug,
                    ats_platform__iexact=ats_platform
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create new source
                source = Source.objects.create(
                    name=company.get('name', slug),
                    slug=slug,
                    url=company.get('source_url', ''),
                    career_page_url=company.get('career_page_url', ''),
                    type='ats',
                    ats_platform=ats_platform,
                    scraper_class=f'{ats_platform.capitalize()}Scraper',
                    is_active=True,
                )
                
                created += 1
                
            except Exception as e:
                logger.error(f"Failed to save company {company.get('slug')}: {e}")
                skipped += 1
        
        return {'created': created, 'skipped': skipped}


# Singleton instance
common_crawl_discovery = CommonCrawlDiscovery()


def discover_companies_from_common_crawl() -> Dict[str, int]:
    """
    Convenience function to discover companies from Common Crawl.
    
    Returns:
        Dict with 'discovered' and 'saved' counts
    """
    # Discover companies
    companies = common_crawl_discovery.discover_companies()
    
    # Save to database
    result = common_crawl_discovery.save_to_database(companies)
    
    return {
        'discovered': len(companies),
        'saved': result['created'],
        'skipped': result['skipped'],
    }
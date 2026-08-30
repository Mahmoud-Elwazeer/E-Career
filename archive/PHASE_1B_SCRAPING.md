> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 1B: Scraping Pipeline

> **Duration:** 4-6 hours  
> **Dependencies:** Phase 1A complete, Redis running  
> **Branch:** development  
> **Status:** Ready to execute

---

## 📋 Overview

Build a comprehensive job scraping pipeline that aggregates jobs from multiple ATS platforms and regional boards. **Critical rule: Only jobs with direct company apply URLs are stored.**

### What You'll Build:
- ✅ ATS API scrapers (Greenhouse, Lever, Ashby, Workday, BambooHR)
- ✅ Regional job boards (Wuzzuf, Bayt, GulfTalent via JobSpy)
- ✅ Company list import (12,000+ companies from OpenJobs)
- ✅ URL validation (blocks LinkedIn, Indeed, aggregators)
- ✅ Legitimacy checker (Block G port to Python)
- ✅ Deduplication logic
- ✅ Celery tasks and Beat scheduling

---

## 🔧 Pre-requisites

```bash
# Install scraping dependencies
pip install jobspy==1.1.82
pip install scrapy==2.11.0
pip install scrapy-playwright==0.0.34
pip install playwright==1.40.0
pip install requests==2.31.0
pip install httpx==0.27.0

# Install Playwright browsers
playwright install chromium

# Ensure Redis is running
redis-cli ping  # Should return "PONG"

# Ensure Celery worker is configured
# We'll set it up in this phase
```

---

## 📦 Step 1: Install Dependencies

**File:** `backend/requirements/base.txt`

Add these lines:

```txt
# Job scraping
jobspy==1.1.82
scrapy==2.11.0
scrapy-playwright==0.0.34
playwright==1.40.0
requests==2.31.0
httpx==0.27.0

# Task queue
celery==5.3.4
celery[redis]==5.3.4
django-celery-beat==2.5.0
redis==5.0.1
```

Install:
```bash
cd backend
pip install -r requirements/base.txt
```

---

## 🏗️ Step 2: Create Scraper App Structure

```bash
cd backend/apps
python ../manage.py startapp scraper
```

Create the following directory structure:

```
apps/scraper/
├── __init__.py
├── apps.py
├── models.py  (empty - we use existing Source model)
├── ats/
│   ├── __init__.py
│   ├── greenhouse.py
│   ├── lever.py
│   ├── ashby.py
│   ├── workday.py
│   ├── bamboohr.py
│   └── base.py
├── regional/
│   ├── __init__.py
│   ├── jobspy_wrapper.py
│   ├── wuzzuf.py
│   └── gulftalent.py
├── pipeline/
│   ├── __init__.py
│   ├── normalizer.py
│   ├── deduplicator.py
│   ├── legitimacy.py
│   ├── url_resolver.py
│   └── enricher.py
├── management/
│   └── commands/
│       ├── __init__.py
│       ├── scrape_jobs.py
│       ├── verify_apply_urls.py
│       ├── expire_old_jobs.py
│       └── import_companies.py
└── tasks.py
```

---

## 📝 Step 3: Create Core URL Validator

**File:** `backend/apps/scraper/pipeline/url_resolver.py`

```python
"""
URL validation and verification.
This is the gatekeeper - blocks all aggregator links.
"""
import requests
from urllib.parse import urlparse
from typing import Tuple


# Blocked domains - NEVER allow these as apply URLs
BLOCKED_DOMAINS = [
    # Job aggregators
    'linkedin.com',
    'indeed.com',
    'glassdoor.com',
    'ziprecruiter.com',
    'monster.com',
    'careerbuilder.com',
    'simplyhired.com',
    'jobgenie.com',
    
    # Regional aggregators
    'bayt.com',
    'wuzzuf.net',
    'gulftalent.com',
    'tanqeeb.com',
    'akhtaboot.com',
    
    # Social media
    'facebook.com',
    'twitter.com',
    'instagram.com',
]

# Allowed ATS domains
ALLOWED_ATS = [
    'greenhouse.io',
    'lever.co',
    'ashbyhq.com',
    'myworkdayjobs.com',
    'bamboohr.com',
    'icims.com',
    'jobvite.com',
    'smartrecruiters.com',
    'workable.com',
    'breezy.hr',
    'recruitee.com',
    'personio.de',
    'join.com',
]


def is_direct_company_url(url: str) -> bool:
    """
    Returns True only if URL is from:
    1. Company's own domain, OR
    2. An allowed ATS platform
    
    Returns False for aggregators like LinkedIn, Indeed, etc.
    """
    if not url:
        return False
    
    try:
        domain = urlparse(url).netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check if it's in blocked list
        for blocked in BLOCKED_DOMAINS:
            if blocked in domain:
                return False
        
        # Check if it's an allowed ATS
        for ats in ALLOWED_ATS:
            if ats in domain:
                return True
        
        # If not blocked and not ATS, assume it's company's own domain
        # (We trust companies to use their own domains)
        return True
        
    except Exception:
        return False


def verify_url_live(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """
    Checks if URL is accessible.
    Returns (is_live, status_code).
    """
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; JobsBot/1.0; +https://jobs.usamif.com)'
            }
        )
        return response.status_code < 400, response.status_code
    except requests.RequestException:
        # Try GET if HEAD fails
        try:
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; JobsBot/1.0; +https://jobs.usamif.com)'
                }
            )
            return response.status_code < 400, response.status_code
        except Exception:
            return False, 0


def extract_domain(url: str) -> str:
    """Extract clean domain from URL"""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ''
```

---

## 🔌 Step 4: Create ATS API Scrapers

### 4.1 Base Scraper Class

**File:** `backend/apps/scraper/ats/base.py`

```python
"""Base class for all ATS scrapers"""
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class BaseATSScraper(ABC):
    """
    Base class for all ATS API scrapers.
    Each ATS scraper must implement fetch_jobs().
    """
    
    def __init__(self, company_slug: str):
        self.company_slug = company_slug
    
    @abstractmethod
    def fetch_jobs(self) -> List[Dict]:
        """
        Fetch jobs from ATS API.
        Must return list of normalized job dicts.
        """
        pass
    
    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normalize raw ATS data to our standard format.
        Override in subclass if needed.
        """
        return {
            'title': raw_job.get('title', ''),
            'company_slug': self.company_slug,
            'direct_apply_url': raw_job.get('apply_url', ''),
            'description': raw_job.get('description', ''),
            'location': raw_job.get('location', ''),
            'employment_type': raw_job.get('employment_type'),
            'experience_level': raw_job.get('experience_level'),
            'remote_type': raw_job.get('remote_type'),
            'salary_min': raw_job.get('salary_min'),
            'salary_max': raw_job.get('salary_max'),
            'salary_currency': raw_job.get('salary_currency', 'USD'),
            'ats_platform': self.get_platform_name(),
            'ats_job_id': str(raw_job.get('id', '')),
            'raw_data': raw_job,
            'scraped_at': raw_job.get('posted_at'),
        }
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return ATS platform name (e.g., 'greenhouse')"""
        pass
```

### 4.2 Greenhouse Scraper

**File:** `backend/apps/scraper/ats/greenhouse.py`

```python
"""Greenhouse API scraper"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class GreenhouseScraper(BaseATSScraper):
    """
    Scrapes jobs from Greenhouse public API.
    API: https://api.greenhouse.io/v1/boards/{company}/jobs?content=true
    """
    
    API_URL = "https://api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    
    def get_platform_name(self) -> str:
        return 'greenhouse'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Greenhouse"""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job in data.get('jobs', []):
                # Greenhouse absolute_url IS the direct apply link
                apply_url = job.get('absolute_url', '')
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('content', ''),
                    'location': job.get('location', {}).get('name', ''),
                    'id': job.get('id'),
                    'posted_at': job.get('updated_at'),
                    'departments': [d['name'] for d in job.get('departments', [])],
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Greenhouse scrape failed for {self.company_slug}: {e}")
            return []


def fetch_greenhouse_jobs(company_slug: str) -> List[Dict]:
    """Convenience function"""
    scraper = GreenhouseScraper(company_slug)
    return scraper.fetch_jobs()
```

### 4.3 Lever Scraper

**File:** `backend/apps/scraper/ats/lever.py`

```python
"""Lever API scraper"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class LeverScraper(BaseATSScraper):
    """
    Scrapes jobs from Lever public API.
    API: https://api.lever.co/v0/postings/{company}?mode=json
    """
    
    API_URL = "https://api.lever.co/v0/postings/{company}?mode=json"
    
    def get_platform_name(self) -> str:
        return 'lever'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Lever"""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            jobs_data = response.json()
            jobs = []
            
            for job in jobs_data:
                # Lever hostedUrl IS the direct apply link
                apply_url = job.get('hostedUrl', '')
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('text', ''),
                    'apply_url': apply_url,
                    'description': job.get('description', '') or job.get('descriptionPlain', ''),
                    'location': job.get('categories', {}).get('location', ''),
                    'id': job.get('id'),
                    'posted_at': job.get('createdAt'),
                    'employment_type': self._parse_employment_type(job),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Lever scrape failed for {self.company_slug}: {e}")
            return []
    
    def _parse_employment_type(self, job: Dict) -> str:
        """Parse employment type from Lever categories"""
        commitment = job.get('categories', {}).get('commitment', '').lower()
        
        if 'full' in commitment:
            return 'full_time'
        elif 'part' in commitment:
            return 'part_time'
        elif 'contract' in commitment:
            return 'contract'
        elif 'intern' in commitment:
            return 'internship'
        
        return None


def fetch_lever_jobs(company_slug: str) -> List[Dict]:
    """Convenience function"""
    scraper = LeverScraper(company_slug)
    return scraper.fetch_jobs()
```

### 4.4 Ashby Scraper

**File:** `backend/apps/scraper/ats/ashby.py`

```python
"""Ashby API scraper"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class AshbyScraper(BaseATSScraper):
    """
    Scrapes jobs from Ashby public API.
    API: https://api.ashbyhq.com/posting-api/job-board/{company}
    """
    
    API_URL = "https://api.ashbyhq.com/posting-api/job-board/{company}"
    
    def get_platform_name(self) -> str:
        return 'ashby'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Ashby"""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job in data.get('jobs', []):
                # Ashby jobUrl IS the direct apply link
                apply_url = job.get('jobUrl', '')
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('description', ''),
                    'location': job.get('location', ''),
                    'id': job.get('id'),
                    'posted_at': job.get('publishedDate'),
                    'employment_type': job.get('employmentType'),
                    'remote_type': self._parse_remote(job.get('isRemote')),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Ashby scrape failed for {self.company_slug}: {e}")
            return []
    
    def _parse_remote(self, is_remote: bool) -> str:
        """Parse remote type"""
        if is_remote:
            return 'remote'
        return 'onsite'


def fetch_ashby_jobs(company_slug: str) -> List[Dict]:
    """Convenience function"""
    scraper = AshbyScraper(company_slug)
    return scraper.fetch_jobs()
```

### 4.5 BambooHR Scraper

**File:** `backend/apps/scraper/ats/bamboohr.py`

```python
"""BambooHR scraper"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class BambooHRScraper(BaseATSScraper):
    """
    Scrapes jobs from BambooHR public board.
    URL: https://{company}.bamboohr.com/jobs/embed2.php
    """
    
    API_URL = "https://{company}.bamboohr.com/jobs/list/"
    
    def get_platform_name(self) -> str:
        return 'bamboohr'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from BambooHR"""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # BambooHR returns JSON with job list
            data = response.json()
            jobs = []
            
            for job in data.get('result', []):
                job_id = job.get('id')
                apply_url = f"https://{self.company_slug}.bamboohr.com/jobs/view.php?id={job_id}"
                
                normalized = {
                    'title': job.get('jobOpening', {}).get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('jobOpening', {}).get('description', ''),
                    'location': job.get('location', {}).get('city', ''),
                    'id': job_id,
                    'posted_at': job.get('postingDate'),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"BambooHR scrape failed for {self.company_slug}: {e}")
            return []


def fetch_bamboohr_jobs(company_slug: str) -> List[Dict]:
    """Convenience function"""
    scraper = BambooHRScraper(company_slug)
    return scraper.fetch_jobs()
```

### 4.6 Workday Scraper (Playwright Required)

**File:** `backend/apps/scraper/ats/workday.py`

```python
"""
Workday scraper - requires Playwright for JS rendering.
Workday is heavily JavaScript-based.
"""
from typing import List, Dict
from .base import BaseATSScraper


class WorkdayScraper(BaseATSScraper):
    """
    Workday requires headless browser.
    Implementation deferred to Phase 1B advanced section.
    For MVP, we skip Workday or use JobSpy wrapper.
    """
    
    def get_platform_name(self) -> str:
        return 'workday'
    
    def fetch_jobs(self) -> List[Dict]:
        """Workday scraping - placeholder"""
        # TODO: Implement with Playwright in advanced section
        return []


def fetch_workday_jobs(company_slug: str) -> List[Dict]:
    """Convenience function"""
    scraper = WorkdayScraper(company_slug)
    return scraper.fetch_jobs()
```

---

## 🌍 Step 5: Regional Job Boards (JobSpy)

**File:** `backend/apps/scraper/regional/jobspy_wrapper.py`

```python
"""
JobSpy wrapper for regional job boards.
Supports: Bayt, Wuzzuf (via LinkedIn/Indeed fallback)
"""
from typing import List, Dict
from jobspy import scrape_jobs


def scrape_bayt(location: str = "Egypt", search_term: str = "") -> List[Dict]:
    """
    Scrape jobs from Bayt using JobSpy.
    Note: We only use Bayt as a DISCOVERY source.
    Apply URLs from Bayt are BLOCKED - we extract company name
    and try to find their direct careers page.
    """
    try:
        jobs = scrape_jobs(
            site_name=["bayt"],
            search_term=search_term,
            location=location,
            results_wanted=100,
            hours_old=72,
        )
        
        normalized_jobs = []
        
        for _, job in jobs.iterrows():
            # Extract company domain from job
            company_name = job.get('company', '')
            
            # We'll try to resolve company's real careers page
            # For now, we skip Bayt jobs without direct URLs
            
            normalized = {
                'title': job.get('title', ''),
                'company_name': company_name,
                'description': job.get('description', ''),
                'location': job.get('location', ''),
                'source': 'bayt',
                'job_url': job.get('job_url', ''),  # This is Bayt URL, NOT for apply
            }
            
            normalized_jobs.append(normalized)
        
        return normalized_jobs
        
    except Exception as e:
        print(f"Bayt scrape failed: {e}")
        return []


def scrape_wuzzuf(location: str = "Egypt", search_term: str = "") -> List[Dict]:
    """
    Scrape jobs from Wuzzuf.
    JobSpy doesn't directly support Wuzzuf, so we'll build custom scraper.
    """
    # TODO: Custom Wuzzuf scraper in next step
    return []


def scrape_gulftalent(location: str = "UAE", search_term: str = "") -> List[Dict]:
    """
    Scrape jobs from GulfTalent.
    Custom scraper needed.
    """
    # TODO: Custom GulfTalent scraper
    return []
```

---

## 🛡️ Step 6: Legitimacy Checker (Block G Port)

**File:** `backend/apps/scraper/pipeline/legitimacy.py`

```python
"""
Legitimacy checker - detects scam jobs and ghost postings.
Ported from career-ops Block G (Node.js → Python).
"""
import re
from typing import Dict, List, Tuple


# Red flags - scam indicators
SCAM_PATTERNS = {
    'title': [
        r'work from home',
        r'earn \$\d+ per (day|week|hour)',
        r'easy money',
        r'no experience needed',
        r'get rich quick',
        r'investment opportunity',
        r'crypto',
        r'bitcoin',
    ],
    'description': [
        r'wire transfer',
        r'western union',
        r'moneygram',
        r'pay.*fee',
        r'processing fee',
        r'training fee',
        r'background check fee',
        r'send money',
        r'cash advance',
        r'nigerian prince',  # Classic scam
    ],
    'salary': [
        r'\$\d{4,}\/day',  # Unrealistic daily rates
        r'\$10,000+',  # Suspiciously high entry-level
    ]
}

# Ghost job indicators
GHOST_INDICATORS = [
    'actively reviewing applications',
    'position may have been filled',
    'not currently accepting',
    'closed for applications',
]


def calculate_legitimacy_score(job: Dict) -> Tuple[float, List[str]]:
    """
    Calculate legitimacy score (0.0 to 1.0).
    Returns (score, list_of_flags).
    
    Score interpretation:
    - 1.0: Definitely legitimate
    - 0.8-0.99: Probably legitimate
    - 0.6-0.79: Uncertain (manual review recommended)
    - 0.0-0.59: Likely scam
    """
    score = 1.0
    flags = []
    
    title = job.get('title', '').lower()
    description = job.get('description', '').lower()
    company = job.get('company', '').lower()
    
    # Check title for scam patterns
    for pattern in SCAM_PATTERNS['title']:
        if re.search(pattern, title, re.IGNORECASE):
            score -= 0.2
            flags.append(f"Scam title pattern: {pattern}")
    
    # Check description for scam patterns
    for pattern in SCAM_PATTERNS['description']:
        if re.search(pattern, description, re.IGNORECASE):
            score -= 0.3
            flags.append(f"Scam description pattern: {pattern}")
    
    # Check for ghost job indicators
    for indicator in GHOST_INDICATORS:
        if indicator in description:
            score -= 0.1
            flags.append(f"Ghost job indicator: {indicator}")
    
    # Check if company name is suspicious
    if not company or len(company) < 3:
        score -= 0.2
        flags.append("Missing or invalid company name")
    
    # Check if description is too short (< 100 chars = suspicious)
    if len(description) < 100:
        score -= 0.15
        flags.append("Description too short")
    
    # Check if description is too long (> 10000 chars = spam)
    if len(description) > 10000:
        score -= 0.1
        flags.append("Description suspiciously long")
    
    # Cap score between 0 and 1
    score = max(0.0, min(1.0, score))
    
    return score, flags


def is_legitimate(job: Dict, threshold: float = 0.6) -> bool:
    """
    Quick check if job passes legitimacy threshold.
    """
    score, _ = calculate_legitimacy_score(job)
    return score >= threshold
```

---

## 🔄 Step 7: Deduplication Logic

**File:** `backend/apps/scraper/pipeline/deduplicator.py`

```python
"""
Job deduplication logic.
Prevents same job from being stored multiple times.
"""
import hashlib
from typing import Dict, Optional
from django.utils.text import slugify


def generate_job_hash(job: Dict) -> str:
    """
    Generate unique hash for a job based on:
    - Company name
    - Job title (normalized)
    - Location
    
    This allows us to detect duplicates across sources.
    """
    company = job.get('company', '').lower().strip()
    title = job.get('title', '').lower().strip()
    location = job.get('location', '').lower().strip()
    
    # Normalize title (remove common variations)
    title = title.replace('senior', '').replace('junior', '').replace('mid-level', '')
    title = ''.join(c for c in title if c.isalnum() or c.isspace())
    title = ' '.join(title.split())  # Normalize whitespace
    
    # Create hash input
    hash_input = f"{company}:{title}:{location}"
    
    # Generate SHA256 hash
    return hashlib.sha256(hash_input.encode()).hexdigest()


def generate_job_slug(company: str, title: str, job_id: str = "") -> str:
    """
    Generate URL-friendly slug for a job.
    Format: {company}-{title}-{short-hash}
    """
    company_slug = slugify(company)[:30]
    title_slug = slugify(title)[:50]
    
    if job_id:
        hash_suffix = job_id[:8]
    else:
        hash_input = f"{company}{title}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    return f"{company_slug}-{title_slug}-{hash_suffix}"


def is_duplicate(job_hash: str) -> bool:
    """
    Check if job with this hash already exists in database.
    """
    from apps.jobs.models import Job
    
    return Job.objects.filter(
        # We'll add a job_hash field in next migration
        # For now, check by slug or ats_job_id
        ats_job_id=job_hash
    ).exists()
```

---

## 📊 Step 8: Job Normalizer

**File:** `backend/apps/scraper/pipeline/normalizer.py`

```python
"""
Normalizes job data from different sources to standard format.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta


def normalize_employment_type(raw_type: str) -> Optional[str]:
    """Normalize employment type to our choices"""
    if not raw_type:
        return None
    
    raw_type = raw_type.lower()
    
    if 'full' in raw_type or 'fulltime' in raw_type:
        return 'full_time'
    elif 'part' in raw_type or 'parttime' in raw_type:
        return 'part_time'
    elif 'contract' in raw_type:
        return 'contract'
    elif 'intern' in raw_type:
        return 'internship'
    elif 'freelance' in raw_type:
        return 'freelance'
    
    return None


def normalize_experience_level(raw_level: str) -> Optional[str]:
    """Normalize experience level to our choices"""
    if not raw_level:
        return None
    
    raw_level = raw_level.lower()
    
    if 'student' in raw_level or 'graduate' in raw_level:
        return 'student'
    elif 'entry' in raw_level or 'junior' in raw_level or '0-2' in raw_level:
        return 'entry'
    elif 'mid' in raw_level or '2-5' in raw_level or '3-5' in raw_level:
        return 'mid'
    elif 'senior' in raw_level or '5+' in raw_level or 'lead' in raw_level:
        return 'senior'
    elif 'director' in raw_level or 'head' in raw_level:
        return 'director'
    elif 'c-level' in raw_level or 'cto' in raw_level or 'ceo' in raw_level:
        return 'c_level'
    
    return None


def normalize_remote_type(raw_remote: str) -> Optional[str]:
    """Normalize remote type to our choices"""
    if not raw_remote:
        return None
    
    raw_remote = raw_remote.lower()
    
    if 'remote' in raw_remote:
        return 'remote'
    elif 'hybrid' in raw_remote:
        return 'hybrid'
    elif 'onsite' in raw_remote or 'office' in raw_remote:
        return 'onsite'
    
    return None


def normalize_location(raw_location: str) -> str:
    """Normalize location string"""
    if not raw_location:
        return ''
    
    # Remove country if it's Egypt (implied)
    location = raw_location.replace(', Egypt', '').replace(',Egypt', '')
    
    # Normalize common city names
    location = location.replace('Cairo, Cairo', 'Cairo')
    
    return location.strip()


def parse_salary(salary_str: str) -> tuple:
    """
    Parse salary string to (min, max, currency).
    Examples:
    - "$50,000 - $70,000" → (50000, 70000, "USD")
    - "EGP 10,000" → (10000, 10000, "EGP")
    """
    import re
    
    if not salary_str:
        return None, None, 'USD'
    
    # Detect currency
    currency = 'USD'
    if 'EGP' in salary_str or 'LE' in salary_str:
        currency = 'EGP'
    elif 'AED' in salary_str:
        currency = 'AED'
    elif 'SAR' in salary_str:
        currency = 'SAR'
    elif '£' in salary_str or 'GBP' in salary_str:
        currency = 'GBP'
    elif '€' in salary_str or 'EUR' in salary_str:
        currency = 'EUR'
    
    # Extract numbers
    numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', salary_str)
    numbers = [int(n.replace(',', '')) for n in numbers]
    
    if len(numbers) >= 2:
        return min(numbers), max(numbers), currency
    elif len(numbers) == 1:
        return numbers[0], numbers[0], currency
    
    return None, None, currency


def calculate_expiry_date(posted_date: Optional[datetime], default_days: int = 90) -> datetime:
    """Calculate when job should expire"""
    if posted_date:
        base_date = posted_date
    else:
        base_date = datetime.now()
    
    return base_date + timedelta(days=default_days)
```

---

## 🎯 Step 9: Main Scraping Orchestrator

**File:** `backend/apps/scraper/tasks.py`

```python
"""
Celery tasks for job scraping pipeline.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict

from apps.jobs.models import Job, Source, Company
from apps.core.models import PipelineHealth

from .ats import greenhouse, lever, ashby, bamboohr
from .pipeline.url_resolver import is_direct_company_url, verify_url_live
from .pipeline.legitimacy import calculate_legitimacy_score
from .pipeline.deduplicator import generate_job_hash, generate_job_slug
from .pipeline.normalizer import (
    normalize_employment_type,
    normalize_experience_level,
    normalize_remote_type,
    normalize_location,
    calculate_expiry_date,
)


@shared_task(bind=True, max_retries=3)
def scrape_all_sources(self):
    """
    Master scraping task - runs all active sources.
    Called by Celery Beat every 6 hours.
    """
    start_time = timezone.now()
    total_found = 0
    total_added = 0
    
    try:
        # Get all active sources
        sources = Source.objects.filter(is_active=True)
        
        for source in sources:
            try:
                # Update source status
                source.last_run_at = timezone.now()
                source.last_run_status = 'running'
                source.save(update_fields=['last_run_at', 'last_run_status'])
                
                # Scrape based on ATS platform
                jobs = scrape_source(source)
                
                # Process and store jobs
                added = process_and_store_jobs(jobs, source)
                
                # Update source stats
                source.jobs_found_last_run = len(jobs)
                source.jobs_added_last_run = added
                source.last_run_status = 'success'
                source.error_count = 0
                source.last_error = ''
                source.save()
                
                total_found += len(jobs)
                total_added += added
                
            except Exception as e:
                # Log error and continue with next source
                source.last_run_status = 'failed'
                source.error_count += 1
                source.last_error = str(e)
                source.save()
                continue
        
        # Update pipeline health
        duration = (timezone.now() - start_time).total_seconds()
        PipelineHealth.objects.update_or_create(
            task_name='scrape_all_sources',
            defaults={
                'last_run_at': start_time,
                'last_status': 'success',
                'last_duration': duration,
                'run_count': models.F('run_count') + 1,
            }
        )
        
        return {
            'status': 'success',
            'total_found': total_found,
            'total_added': total_added,
            'duration': duration,
        }
        
    except Exception as exc:
        # Update pipeline health with failure
        PipelineHealth.objects.update_or_create(
            task_name='scrape_all_sources',
            defaults={
                'last_run_at': start_time,
                'last_status': 'failed',
                'last_error': str(exc),
            }
        )
        raise self.retry(exc=exc, countdown=60 * 10)  # Retry in 10 minutes


def scrape_source(source: Source) -> List[Dict]:
    """
    Scrape jobs from a single source based on ATS platform.
    """
    platform = source.ats_platform.lower()
    company_slug = source.slug
    
    if platform == 'greenhouse':
        return greenhouse.fetch_greenhouse_jobs(company_slug)
    elif platform == 'lever':
        return lever.fetch_lever_jobs(company_slug)
    elif platform == 'ashby':
        return ashby.fetch_ashby_jobs(company_slug)
    elif platform == 'bamboohr':
        return bamboohr.fetch_bamboohr_jobs(company_slug)
    else:
        return []


def process_and_store_jobs(jobs: List[Dict], source: Source) -> int:
    """
    Process scraped jobs and store valid ones to database.
    Returns count of jobs added.
    """
    added_count = 0
    
    for job_data in jobs:
        try:
            # 1. Validate apply URL
            apply_url = job_data.get('direct_apply_url') or job_data.get('apply_url')
            
            if not apply_url or not is_direct_company_url(apply_url):
                # Skip jobs without direct apply URLs
                continue
            
            # 2. Calculate legitimacy score
            legitimacy_score, legitimacy_flags = calculate_legitimacy_score(job_data)
            
            # Skip obviously scam jobs
            if legitimacy_score < 0.4:
                continue
            
            # 3. Get or create company
            company_name = job_data.get('company_slug', source.name)
            company, _ = Company.objects.get_or_create(
                name=company_name,
                defaults={'slug': company_name.lower().replace(' ', '-')}
            )
            
            # 4. Generate job hash for deduplication
            job_hash = generate_job_hash({
                'company': company.name,
                'title': job_data.get('title', ''),
                'location': job_data.get('location', ''),
            })
            
            # 5. Check if job already exists
            existing = Job.objects.filter(
                ats_job_id=job_data.get('ats_job_id', ''),
                ats_platform=job_data.get('ats_platform', ''),
            ).first()
            
            if existing:
                # Update existing job
                existing.is_expired = False
                existing.save(update_fields=['is_expired'])
                continue
            
            # 6. Create new job
            slug = generate_job_slug(
                company.name,
                job_data.get('title', ''),
                job_data.get('ats_job_id', '')
            )
            
            Job.objects.create(
                company=company,
                source=source,
                title=job_data.get('title', ''),
                slug=slug,
                description=job_data.get('description', ''),
                location=normalize_location(job_data.get('location', '')),
                direct_apply_url=apply_url,
                source_type='scraped',
                employment_type=normalize_employment_type(job_data.get('employment_type')),
                experience_level=normalize_experience_level(job_data.get('experience_level')),
                remote_type=normalize_remote_type(job_data.get('remote_type')),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_currency=job_data.get('salary_currency', 'USD'),
                scraped_at=timezone.now(),
                expires_at=calculate_expiry_date(None),
                legitimacy_score=legitimacy_score,
                legitimacy_flags=legitimacy_flags,
                ats_platform=job_data.get('ats_platform', ''),
                ats_job_id=job_data.get('ats_job_id', ''),
                raw_data=job_data.get('raw_data', {}),
            )
            
            added_count += 1
            
        except Exception as e:
            # Log error and continue
            print(f"Failed to process job: {e}")
            continue
    
    return added_count


@shared_task
def verify_apply_urls():
    """
    Daily task - checks every active job's apply URL.
    Marks jobs as expired if URL is dead.
    """
    start_time = timezone.now()
    checked = 0
    expired = 0
    
    try:
        # Get all active jobs
        jobs = Job.objects.filter(is_expired=False)
        
        for job in jobs.iterator():
            is_live, status_code = verify_url_live(job.direct_apply_url)
            
            job.apply_url_verified = is_live
            job.apply_url_status_code = status_code
            job.apply_url_checked_at = timezone.now()
            
            if not is_live:
                job.is_expired = True
                expired += 1
            
            job.save(update_fields=[
                'apply_url_verified',
                'apply_url_status_code',
                'apply_url_checked_at',
                'is_expired'
            ])
            
            checked += 1
        
        # Update pipeline health
        duration = (timezone.now() - start_time).total_seconds()
        PipelineHealth.objects.update_or_create(
            task_name='verify_apply_urls',
            defaults={
                'last_run_at': start_time,
                'last_status': 'success',
                'last_duration': duration,
                'run_count': models.F('run_count') + 1,
            }
        )
        
        return {
            'checked': checked,
            'expired': expired,
        }
        
    except Exception as e:
        PipelineHealth.objects.update_or_create(
            task_name='verify_apply_urls',
            defaults={
                'last_run_at': start_time,
                'last_status': 'failed',
                'last_error': str(e),
            }
        )
        raise


@shared_task
def expire_old_jobs():
    """
    Daily task - marks jobs older than max_job_age_days as expired.
    """
    from apps.core.models import PlatformConfig
    
    config = PlatformConfig.objects.get(pk=1)
    cutoff_date = timezone.now() - timedelta(days=config.max_job_age_days)
    
    expired_count = Job.objects.filter(
        created_at__lt=cutoff_date,
        is_expired=False
    ).update(is_expired=True)
    
    return {'expired': expired_count}
```

---

## 📥 Step 10: Import Companies Command

**File:** `backend/apps/scraper/management/commands/import_companies.py`

```python
"""
Import companies from OpenJobs companies_v2.json.
Download from: https://github.com/outscal/OpenJobs/raw/main/data/companies_v2.json
"""
import json
from django.core.management.base import BaseCommand
from apps.jobs.models import Company, Source


class Command(BaseCommand):
    help = 'Import companies from OpenJobs companies_v2.json'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='companies_v2.json',
            help='Path to companies JSON file'
        )
    
    def handle(self, *args, **options):
        file_path = options['file']
        
        self.stdout.write(f"Loading companies from {file_path}...")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        companies_added = 0
        sources_added = 0
        
        for company_data in data:
            company_name = company_data.get('name', '')
            slug = company_data.get('slug', '')
            ats = company_data.get('ats', '')
            domain = company_data.get('domain', '')
            
            if not company_name or not slug or not ats:
                continue
            
            # Create or update company
            company, created = Company.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': company_name,
                    'domain': domain,
                    'careers_page_url': company_data.get('careers_url', ''),
                }
            )
            
            if created:
                companies_added += 1
            
            # Create source for scraping
            source, created = Source.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': company_name,
                    'url': company_data.get('careers_url', ''),
                    'ats_platform': ats.lower(),
                    'is_active': True,
                }
            )
            
            if created:
                sources_added += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Import complete!\n"
                f"Companies added: {companies_added}\n"
                f"Sources added: {sources_added}"
            )
        )
```

---

## ⚙️ Step 11: Configure Celery

**File:** `backend/config/celery.py`

```python
"""
Celery configuration for background tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ecareer')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Celery Beat schedule
app.conf.beat_schedule = {
    'scrape-all-sources': {
        'task': 'apps.scraper.tasks.scrape_all_sources',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'verify-apply-urls': {
        'task': 'apps.scraper.tasks.verify_apply_urls',
        'schedule': crontab(minute=0, hour=2),  # 2 AM daily
    },
    'expire-old-jobs': {
        'task': 'apps.scraper.tasks.expire_old_jobs',
        'schedule': crontab(minute=0, hour=3),  # 3 AM daily
    },
}
```

**File:** `backend/config/__init__.py`

```python
# Import Celery app
from .celery import app as celery_app

__all__ = ('celery_app',)
```

**File:** `backend/config/settings/base.py`

Add Celery configuration:

```python
# ── Celery Configuration ────────────────────────────────────────────────
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

Add to INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    
    # Celery
    'django_celery_beat',
    
    # Scraper
    'apps.scraper',
]
```

---

## 🚀 Step 12: Start Celery Workers

Create these scripts for easy Celery management:

**File:** `backend/start_celery_worker.sh`

```bash
#!/bin/bash
celery -A config worker --loglevel=info --concurrency=4
```

**File:** `backend/start_celery_beat.sh`

```bash
#!/bin/bash
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Make them executable:
```bash
chmod +x backend/start_celery_worker.sh
chmod +x backend/start_celery_beat.sh
```

---

## 🧪 Step 13: Test the Pipeline

### 13.1 Download Company List

```bash
cd backend
wget https://github.com/outscal/OpenJobs/raw/main/data/companies_v2.json
```

### 13.2 Import Companies

```bash
python manage.py import_companies --file companies_v2.json
```

### 13.3 Test Single Scraper

```bash
python manage.py shell

from apps.scraper.ats.greenhouse import fetch_greenhouse_jobs

# Test with Stripe (known Greenhouse user)
jobs = fetch_greenhouse_jobs('stripe')
print(f"Found {len(jobs)} jobs from Stripe")
print(jobs[0] if jobs else "No jobs found")
```

### 13.4 Run Manual Scrape

```bash
python manage.py shell

from apps.scraper.tasks import scrape_all_sources

# Run scraping task
result = scrape_all_sources.delay()
print(result.get())
```

### 13.5 Start Workers

```bash
# Terminal 1: Start worker
cd backend
./start_celery_worker.sh

# Terminal 2: Start beat scheduler
./start_celery_beat.sh

# Terminal 3: Monitor tasks
celery -A config flower  # Web UI at http://localhost:5555
```

---

## ✅ Verification Checklist

Test each component:

```bash
# 1. Test URL validator
python manage.py shell
from apps.scraper.pipeline.url_resolver import is_direct_company_url

assert is_direct_company_url('https://boards.greenhouse.io/stripe/jobs/123') == True
assert is_direct_company_url('https://www.linkedin.com/jobs/view/123') == False
assert is_direct_company_url('https://careers.google.com/jobs/results/123') == True
print("✅ URL validator working")

# 2. Test legitimacy checker
from apps.scraper.pipeline.legitimacy import calculate_legitimacy_score

test_job = {
    'title': 'Software Engineer',
    'description': 'Build amazing things with Python',
    'company': 'Google',
}
score, flags = calculate_legitimacy_score(test_job)
print(f"✅ Legitimacy score: {score} (flags: {flags})")

# 3. Test Greenhouse scraper
from apps.scraper.ats.greenhouse import fetch_greenhouse_jobs
jobs = fetch_greenhouse_jobs('stripe')
print(f"✅ Fetched {len(jobs)} jobs from Greenhouse")

# 4. Check database
from apps.jobs.models import Job, Source
print(f"✅ Total sources: {Source.objects.count()}")
print(f"✅ Total jobs: {Job.objects.count()}")
print(f"✅ Active jobs: {Job.objects.filter(is_expired=False).count()}")
```

---

## 🐛 Troubleshooting

### Issue: Celery not connecting to Redis
```bash
# Check Redis is running
redis-cli ping

# Check Redis URL in settings
echo $CELERY_BROKER_URL
```

### Issue: Scrapers returning empty results
```bash
# Test manually with verbose output
python manage.py shell

from apps.scraper.ats.greenhouse import GreenhouseScraper
scraper = GreenhouseScraper('stripe')
jobs = scraper.fetch_jobs()

# Check API response
import requests
response = requests.get('https://api.greenhouse.io/v1/boards/stripe/jobs?content=true')
print(response.status_code)
print(response.json()[:100])
```

### Issue: Jobs not being stored
```bash
# Check legitimacy scores
python manage.py shell

from apps.scraper.pipeline.legitimacy import calculate_legitimacy_score

test_job = {
    'title': 'Senior Software Engineer',
    'description': 'Long description here...',
    'company': 'TestCompany',
}

score, flags = calculate_legitimacy_score(test_job)
print(f"Score: {score}, Flags: {flags}")
```

---

## 📋 Phase 1B Checklist

- [ ] Scraper dependencies installed
- [ ] Scraper app created with proper structure
- [ ] URL validator implemented and tested
- [ ] ATS scrapers implemented (Greenhouse, Lever, Ashby, BambooHR)
- [ ] Legitimacy checker implemented
- [ ] Deduplication logic implemented
- [ ] Normalizer implemented
- [ ] Celery configured
- [ ] Celery tasks created
- [ ] Celery Beat schedule configured
- [ ] Import companies command working
- [ ] Company list imported (12,000+)
- [ ] Manual scrape test passed
- [ ] Celery workers running
- [ ] Jobs appearing in database
- [ ] Pipeline health tracking working

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

---

## 🎯 What's Next?

After Phase 1B is complete:
1. ✅ Jobs are being scraped from 12,000+ companies
2. ✅ All apply URLs are validated (no aggregators)
3. ✅ Scam jobs are filtered out
4. ✅ Celery pipeline is running

**Next Phase:** `PHASE_1C_JOB_PAGES.md` - Enhanced job listing and detail pages

---

*Phase 1B Complete! Ready for Phase 1C: Job Pages Enhancement*

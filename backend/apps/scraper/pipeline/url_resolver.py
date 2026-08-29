"""
URL validation and verification.
This is the gatekeeper - blocks all aggregator links.
"""
import requests
from urllib.parse import urlparse
from typing import Tuple

from apps.verification.models import is_blocked_domain


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
        if is_blocked_domain(domain):
            return False

        # Check if it's an allowed ATS
        from apps.verification.models import ApprovedATS
        ats_domains = ApprovedATS.objects.filter(
            is_active=True
        ).values_list('domain', flat=True)
        if any(ats in domain for ats in ats_domains):
            return True
        
        # If not blocked and not ATS, assume it's company's own domain
        # (We trust companies to use their own domains)
        return True
        
    except Exception:
        return False


def verify_url_live(url: str, timeout: int = 10) -> Tuple[bool, int]:
    """
    Checks if URL is accessible (SSRF-safe).
    Returns (is_live, status_code).
    """
    from apps.core.safe_fetch import verify_url_is_live
    return verify_url_is_live(url, timeout=timeout, allow_http=True)


def extract_domain(url: str) -> str:
    """Extract clean domain from URL"""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ''
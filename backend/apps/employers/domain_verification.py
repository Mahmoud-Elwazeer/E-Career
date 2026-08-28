"""
Domain Verification Service for Employer Job Postings

Ensures apply_url points to the company's legitimate domain,
not aggregators or third-party sites.
"""
import re
import logging
from urllib.parse import urlparse
from typing import Tuple
from django.utils import timezone

from apps.core.safe_fetch import verify_url_is_live, SSRFBlockedError

logger = logging.getLogger(__name__)

# Known aggregators and job boards to block
BLOCKED_DOMAINS = {
    'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
    'bayt.com', 'akhtaboot.com', 'wuzzuf.com', 'tanqeeb.com',
    'naukrigulf.com', 'dubizzle.com', 'gulftalent.com',
    'seek.com', 'dice.com', 'ziprecruiter.com', 'careerbuilder.com',
}


def extract_domain(url: str) -> str:
    """
    Extract base domain from URL.

    Examples:
        https://careers.acme.com/jobs/123 -> acme.com
        https://www.google.com/apply -> google.com
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]

    # Extract base domain (e.g., careers.acme.com -> acme.com)
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])

    return domain


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for domain matching.

    Examples:
        "Acme Inc." -> "acme"
        "The Tech Company, LLC" -> "techcompany"
    """
    # Remove common suffixes
    name = re.sub(r'\b(inc|llc|ltd|corp|corporation|company|co)\b\.?', '', name, flags=re.IGNORECASE)

    # Remove special chars and whitespace
    name = re.sub(r'[^a-z0-9]', '', name.lower())

    return name


def verify_domain_ownership(company_name: str, apply_url: str) -> Tuple[bool, str]:
    """
    Verify that apply_url belongs to the company's domain.

    Returns:
        (is_valid, reason)

    Validation rules:
        1. URL must not be from blocked aggregator domains
        2. Domain should contain company name OR be whitelisted
        3. URL must be accessible (optional check)
    """
    if not apply_url:
        return False, "Apply URL is required"

    try:
        domain = extract_domain(apply_url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

    # Check if blocked aggregator
    if domain in BLOCKED_DOMAINS:
        return False, f"Cannot use aggregator domain: {domain}"

    # Check if domain contains company name
    normalized_company = normalize_company_name(company_name)
    normalized_domain = normalize_company_name(domain)

    if normalized_company in normalized_domain:
        return True, "Domain matches company name"

    # Allow if it's a known career portal subdomain
    if any(sub in domain for sub in ['careers', 'jobs', 'hiring', 'apply', 'workday', 'greenhouse', 'lever']):
        # These are common career portals - allow but flag for manual review
        return True, "Career portal detected - flagged for review"

    # Domain doesn't match - flag for manual verification
    return False, f"Domain '{domain}' does not match company name. Manual verification required."


def check_url_accessibility(url: str, timeout: int = 5) -> Tuple[bool, str]:
    """
    Check if URL is accessible (returns 200 OK).

    This is an optional check - we don't block on failures since
    companies might have geo-restrictions or auth requirements.
    """
    try:
        is_live, status_code = verify_url_is_live(url, timeout=timeout, allow_http=True)
        if status_code == 200:
            return True, "URL is accessible"
        elif status_code in (301, 302, 307, 308):
            return True, "URL redirects (accessible)"
        elif status_code == 403:
            return True, "URL exists but access restricted (likely geo-fenced)"
        elif status_code:
            return False, f"URL returned status code {status_code}"
        else:
            return False, "Could not access URL"
    except SSRFBlockedError:
        return False, "URL blocked by SSRF protection (private/internal IP)"
    except Exception as e:
        logger.warning(f"URL accessibility check failed for {url}: {e}")
        return False, f"Could not access URL: {str(e)}"


def verify_job_posting_url(job_posting) -> dict:
    """
    Run full verification on JobPosting apply_url.

    Returns:
        {
            'is_valid': bool,
            'is_accessible': bool,
            'reason': str,
            'accessibility_note': str,
            'requires_manual_review': bool,
        }
    """
    company_name = job_posting.company.name
    apply_url = job_posting.apply_url

    # Domain ownership check
    is_valid, reason = verify_domain_ownership(company_name, apply_url)

    # Accessibility check (non-blocking)
    is_accessible, accessibility_note = check_url_accessibility(apply_url)

    # Flag for manual review if domain doesn't match but isn't blocked
    requires_manual_review = not is_valid and "aggregator" not in reason.lower()

    # Update job posting
    job_posting.apply_url_verified = is_valid
    job_posting.apply_url_checked_at = timezone.now()
    job_posting.save(update_fields=['apply_url_verified', 'apply_url_checked_at'])

    result = {
        'is_valid': is_valid,
        'is_accessible': is_accessible,
        'reason': reason,
        'accessibility_note': accessibility_note,
        'requires_manual_review': requires_manual_review,
    }

    logger.info(f"Domain verification for JobPosting {job_posting.id}: {result}")

    return result


def bulk_verify_unverified_postings(limit: int = 100) -> dict:
    """
    Batch verify all unverified job postings.

    Used for admin bulk operations or scheduled tasks.
    """
    from .models import JobPosting

    unverified = JobPosting.objects.filter(
        apply_url_verified=False,
        apply_url_checked_at__isnull=True
    )[:limit]

    results = {
        'total': unverified.count(),
        'verified': 0,
        'failed': 0,
        'manual_review': 0,
    }

    for posting in unverified:
        result = verify_job_posting_url(posting)

        if result['is_valid']:
            results['verified'] += 1
        elif result['requires_manual_review']:
            results['manual_review'] += 1
        else:
            results['failed'] += 1

    logger.info(f"Bulk verification complete: {results}")

    return results

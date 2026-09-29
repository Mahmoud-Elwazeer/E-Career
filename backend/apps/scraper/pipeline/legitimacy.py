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
        # Tightened: require the APPLICANT-pays-a-fee scam context within a short
        # window, not a greedy 'pay.*fee' that matched benign long descriptions
        # (e.g. "we pay ... fee-free"). Real scams say "pay a/an ... fee".
        r'pay\s+(?:a|an|the)?\s*\$?\d*\s*\w{0,20}?\s*fee\s+(?:to|for|before)\b',
        r'(?:upfront|registration|onboarding|application|training|processing)\s+fee\s+(?:required|of\s+\$)',
        r'background check fee',
        # Tightened: 'send money to us/the employer/via', not any 'send money'.
        r'send money (?:to|via|through)\b',
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
    # Connectors normalize the employer into company_slug (base.py). Accept the
    # authoritative company field OR the slug so ATS jobs are not wrongly
    # penalized for a "missing company" they actually have (§4/§10).
    company = (
        job.get('company_name')
        or job.get('company')
        or job.get('company_slug')
        or ''
    ).lower()
    
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
    
    # Check if description is too short (< 100 chars = suspicious).
    # Structured ATS listings (Greenhouse/Lever/etc.) legitimately expose a
    # short/empty description on the LIST endpoint (full text is on the detail
    # endpoint), so we do not penalize them for it — source trust ≠ content
    # completeness (§5/§6). Enrichment can fill the description later.
    is_structured_ats = bool(job.get('ats_platform') and job.get('ats_job_id'))
    if len(description) < 100 and not is_structured_ats:
        score -= 0.15
        flags.append("Description too short")
    
    # Check if description is too long (spam). Structured-ATS descriptions are
    # full HTML job posts that legitimately exceed 10k chars, so raise the cap
    # and exempt structured ATS from this penalty (§5/§6). Only flag truly
    # extreme lengths for non-ATS scraped content.
    length_cap = 50000 if is_structured_ats else 10000
    if len(description) > length_cap:
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
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
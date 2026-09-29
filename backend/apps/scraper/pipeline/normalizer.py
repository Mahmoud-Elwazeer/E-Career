"""
Normalizes job data from different sources to standard format.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import re


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


def build_provenance(
    job_data: Dict,
    *,
    source: str,
    method: str = "ats_api",
    confidence: float = 1.0,
) -> Dict[str, Dict]:
    """Build per-field provenance for extracted job data (Section 14).

    Returns a mapping of field name -> {value, source, method, confidence}
    for the fields we ingest. This records lineage WITHOUT destroying the raw
    payload (which stays in Job.raw_data). Structured ATS-API fields get
    confidence 1.0 by default; callers may override for AI/heuristic fields.

    Args:
        job_data: the raw/normalized job dict from a connector.
        source: the origin, e.g. the source slug or ATS platform.
        method: extraction method, e.g. "ats_api", "ai_extraction", "heuristic".
        confidence: 0.0-1.0 confidence for these fields.
    """
    tracked_fields = (
        "title",
        "location",
        "employment_type",
        "experience_level",
        "salary_min",
        "salary_max",
        "salary_currency",
        "direct_apply_url",
        "ats_platform",
        "ats_job_id",
    )
    provenance: Dict[str, Dict] = {}
    for field in tracked_fields:
        if field in job_data and job_data[field] not in (None, ""):
            provenance[field] = {
                "value": job_data[field],
                "source": source,
                "method": method,
                "confidence": round(float(confidence), 3),
            }
    return provenance

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



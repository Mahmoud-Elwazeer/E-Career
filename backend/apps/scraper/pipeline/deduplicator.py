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



# ── Phase A layered deduplication (Section 9) ─────────────────────────────────

_TITLE_NOISE = (
    "senior", "junior", "mid-level", "mid level", "sr.", "sr ", "jr.", "jr ",
    "lead", "principal", "staff", "intern", "trainee", "(remote)", "remote",
    "- remote", "contract", "full-time", "part-time",
)


def normalize_title_for_dedup(title: str) -> str:
    """Aggressively normalize a title for fuzzy-equality dedup (Level 2)."""
    t = (title or "").lower()
    for noise in _TITLE_NOISE:
        t = t.replace(noise, " ")
    t = "".join(c for c in t if c.isalnum() or c.isspace())
    return " ".join(t.split())


def content_fingerprint(job: Dict) -> str:
    """Level 3: SHA256 over normalized company|title|location."""
    company = (job.get("company", "") or "").lower().strip()
    title = normalize_title_for_dedup(job.get("title", ""))
    location = (job.get("location", "") or "").lower().strip()
    return hashlib.sha256(f"{company}:{title}:{location}".encode()).hexdigest()


def dedup_verdict(job: Dict) -> Dict:
    """Return a layered dedup descriptor for a job (no DB access here).

    Layers (cheapest/strongest identity first):
      L1 canonical identity: (ats_platform, ats_job_id) or canonical/apply URL
      L2 normalized identity: company + normalized title + location
      L3 content fingerprint: sha256 of the L2 tuple

    The caller queries the DB using these keys in order. Semantic (L4) is left
    to an optional embeddings-backed check where justified; not computed here to
    avoid loading models in the ingestion hot path.
    """
    ats_platform = (job.get("ats_platform", "") or "").lower()
    ats_job_id = str(job.get("ats_job_id", "") or "")
    canonical_url = (
        job.get("canonical_job_url")
        or job.get("direct_apply_url")
        or job.get("apply_url")
        or ""
    )

    l1_key = None
    if ats_platform and ats_job_id:
        l1_key = f"{ats_platform}:{ats_job_id}"
    elif canonical_url:
        l1_key = canonical_url.strip().lower()

    company = (job.get("company", "") or "").lower().strip()
    norm_title = normalize_title_for_dedup(job.get("title", ""))
    location = (job.get("location", "") or "").lower().strip()
    l2_key = f"{company}|{norm_title}|{location}" if (company and norm_title) else None

    return {
        "l1_canonical_key": l1_key,
        "l2_normalized_key": l2_key,
        "l3_content_hash": content_fingerprint(job),
        "normalized_title": norm_title,
    }

"""Pipeline processing package for job scraping."""
from .url_resolver import is_direct_company_url, verify_url_live, extract_domain
from .legitimacy import calculate_legitimacy_score, is_legitimate
from .deduplicator import generate_job_hash, generate_job_slug
from .normalizer import (
    normalize_employment_type,
    normalize_experience_level,
    normalize_remote_type,
    normalize_location,
    parse_salary,
    calculate_expiry_date,
)

# Import verification engine
from apps.verification.stages.ats_fingerprint import BLOCKED_DOMAINS

# Import skill extraction
from apps.skills.extraction import skill_extractor, SkillExtractor, extract_skills_for_job

# Import embedding service
from apps.search.embeddings import embedding_service, EmbeddingService

__all__ = [
    'is_direct_company_url',
    'verify_url_live',
    'extract_domain',
    'calculate_legitimacy_score',
    'is_legitimate',
    'generate_job_hash',
    'generate_job_slug',
    'normalize_employment_type',
    'normalize_experience_level',
    'normalize_remote_type',
    'normalize_location',
    'parse_salary',
    'calculate_expiry_date',
    'BLOCKED_DOMAINS',
    'skill_extractor',
    'SkillExtractor',
    'extract_skills_for_job',
    'embedding_service',
    'EmbeddingService',
]

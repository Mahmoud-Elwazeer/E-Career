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
# NOTE: BLOCKED_DOMAINS (a static constant) was replaced by the DB-backed
# BlockedDomain model + is_blocked_domain() function during Phase 1 item
# 1.7 (unify 3 blocklists into one DB model, commit d06d24c) — this
# re-export was missed at the time and broke every import of this
# package (apps.scraper.pipeline) until now. No code outside this module
# consumed the re-export (confirmed via repo-wide grep), so this is a
# straight removal, not a behavior change.
from apps.verification.models import is_blocked_domain

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
    'is_blocked_domain',
    'skill_extractor',
    'SkillExtractor',
    'extract_skills_for_job',
    'embedding_service',
    'EmbeddingService',
]

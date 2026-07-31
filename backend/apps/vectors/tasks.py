"""
Celery Tasks for Vector Operations

Real-time embedding generation and synchronization tasks.
"""

import structlog
from celery import shared_task

from apps.vectors.service import get_vector_service, JOBS_COLLECTION, SKILLS_COLLECTION
from apps.vectors.plugins.vector_plugin import VectorDocument

logger = structlog.get_logger(__name__)


@shared_task(name="vectors.embed_job")
def embed_job_task(job_id: str) -> bool:
    """
    Generate embedding for a single job and index it.

    Called when a job is created or updated.
    """
    try:
        from apps.jobs.models import Job

        job = Job.objects.select_related("company", "verification").get(id=job_id)

        # Only embed verified jobs
        if not hasattr(job, "verification") or job.verification.status != "verified":
            logger.info("job_embed_skipped_not_verified", job_id=job_id)
            return False

        if job.verification.trust_score < 0.4:
            logger.info("job_embed_skipped_low_trust", job_id=job_id, trust_score=job.verification.trust_score)
            return False

        vector_service = get_vector_service()

        # Build embedding text
        text = _job_to_text(job)

        # Generate embedding
        embeddings = vector_service.generate_embeddings(
            texts=[text],
            input_type="search_document",
        )

        if not embeddings:
            logger.error("job_embed_failed_no_embedding", job_id=job_id)
            return False

        # Build document
        payload = {
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company.name if job.company else "",
            "location": job.location or "",
            "salary_min": job.salary_min or 0,
            "salary_max": job.salary_max or 0,
            "employment_type": job.employment_type or "",
            "experience_level": job.experience_level or "",
            "trust_score": job.verification.trust_score,
        }

        document = VectorDocument(
            id=str(job.id),
            vector=embeddings[0],
            payload=payload,
        )

        # Upsert to vector DB
        count = vector_service.vector_plugin.upsert(JOBS_COLLECTION, [document])

        logger.info("job_embed_success", job_id=job_id)
        return count > 0

    except Exception as e:
        logger.error("job_embed_failed", job_id=job_id, error=str(e))
        return False


@shared_task(name="vectors.remove_job")
def remove_job_from_vectors_task(job_id: str) -> bool:
    """
    Remove job from vector database.

    Called when a job is deleted or becomes unverified.
    """
    try:
        vector_service = get_vector_service()

        count = vector_service.vector_plugin.delete(JOBS_COLLECTION, [str(job_id)])

        logger.info("job_removed_from_vectors", job_id=job_id)
        return count > 0

    except Exception as e:
        logger.error("job_remove_from_vectors_failed", job_id=job_id, error=str(e))
        return False


@shared_task(name="vectors.embed_skill")
def embed_skill_task(skill_id: str) -> bool:
    """
    Generate embedding for a single skill and index it.
    """
    try:
        from apps.skills.models import Skill

        skill = Skill.objects.get(id=skill_id)

        vector_service = get_vector_service()

        # Build embedding text
        text = _skill_to_text(skill)

        # Generate embedding
        embeddings = vector_service.generate_embeddings(
            texts=[text],
            input_type="search_document",
        )

        if not embeddings:
            logger.error("skill_embed_failed_no_embedding", skill_id=skill_id)
            return False

        # Build document
        payload = {
            "skill_id": str(skill.id),
            "name": skill.name,
            "name_ar": skill.name_ar or "",
            "type": skill.type,
            "category": skill.category,
            "esco_uri": skill.esco_uri,
            "description": skill.description[:500] if skill.description else "",
        }

        document = VectorDocument(
            id=str(skill.id),
            vector=embeddings[0],
            payload=payload,
        )

        # Upsert to vector DB
        count = vector_service.vector_plugin.upsert(SKILLS_COLLECTION, [document])

        logger.info("skill_embed_success", skill_id=skill_id)
        return count > 0

    except Exception as e:
        logger.error("skill_embed_failed", skill_id=skill_id, error=str(e))
        return False


def _job_to_text(job) -> str:
    """Convert job to embedding text."""
    parts = [
        f"Title: {job.title}",
        f"Company: {job.company.name if job.company else 'Unknown'}",
    ]

    if job.description:
        desc = job.description[:2000]
        parts.append(f"Description: {desc}")

    if job.location:
        parts.append(f"Location: {job.location}")

    if job.employment_type:
        parts.append(f"Type: {job.employment_type}")

    if job.experience_level:
        parts.append(f"Experience: {job.experience_level}")

    return "\n".join(parts)


def _skill_to_text(skill) -> str:
    """Convert skill to embedding text."""
    parts = [
        f"Skill: {skill.name}",
        f"Type: {skill.type}",
    ]

    if skill.description:
        desc = skill.description[:500]
        parts.append(f"Description: {desc}")

    if skill.name_ar:
        parts.append(f"Arabic: {skill.name_ar}")

    return "\n".join(parts)

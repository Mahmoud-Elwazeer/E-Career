"""
Intelligence Layer Celery Tasks.

Scheduled and on-demand tasks for:
- Trend detection (weekly)
- Research jobs (on-demand)
- Email verification (async)
- Document processing (async)
"""
from __future__ import annotations

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="intelligence.detect_skill_trends", bind=True, max_retries=2)
def detect_skill_trends(self):
    """Weekly task: detect emerging and declining skills from job data."""
    try:
        from .trend_detection import get_trend_service

        service = get_trend_service()
        emerging = service.get_emerging_skills(days=30)
        declining = service.get_declining_skills(days=30)

        logger.info(
            "skill_trends_detected",
            emerging_count=len(emerging),
            declining_count=len(declining),
        )

        _store_trend_results(emerging, declining)
        return {"emerging": len(emerging), "declining": len(declining)}

    except Exception as e:
        logger.error("trend_detection_failed", error=str(e))
        self.retry(countdown=300, exc=e)


@shared_task(name="intelligence.run_topic_modeling", bind=True, max_retries=1)
def run_topic_modeling(self, days: int = 90):
    """Weekly task: run BERTopic on job descriptions for deep trend analysis."""
    try:
        from .trend_detection import get_trend_service

        service = get_trend_service()
        trends = service.detect_skill_trends(days=days)

        logger.info("topic_modeling_complete", topics_found=len(trends))
        return {"topics": [t.to_dict() for t in trends]}

    except Exception as e:
        logger.error("topic_modeling_failed", error=str(e))
        self.retry(countdown=600, exc=e)


@shared_task(name="intelligence.research_topic")
def research_topic(query: str, research_type: str = "market", depth: str = "standard"):
    """On-demand task: conduct research on a topic."""
    try:
        from .research_engine import get_research_engine, ResearchType

        engine = get_research_engine()
        result = engine.research(
            query=query,
            research_type=ResearchType(research_type),
            depth=depth,
        )

        logger.info(
            "research_complete",
            query=query,
            sources=result.source_count,
            confidence=result.confidence_score,
        )
        return result.to_dict()

    except Exception as e:
        logger.error("research_failed", query=query, error=str(e))
        return {"error": str(e), "query": query}


@shared_task(name="intelligence.verify_email_batch")
def verify_email_batch(emails: list[str]):
    """Batch email verification task."""
    try:
        from .email_verification import get_email_verification_service

        service = get_email_verification_service()
        results = []
        for email in emails:
            result = service.verify(email)
            results.append({
                "email": email,
                "status": result.status.value,
                "is_valid": result.is_valid,
                "domain": result.domain,
            })

        valid_count = sum(1 for r in results if r["is_valid"])
        logger.info("email_batch_verified", total=len(emails), valid=valid_count)
        return results

    except Exception as e:
        logger.error("email_verification_failed", error=str(e))
        return {"error": str(e)}


@shared_task(name="intelligence.process_document")
def process_document(file_path: str, user_id: int | None = None):
    """Async document processing task."""
    try:
        from .document_processor import get_document_processor

        processor = get_document_processor()
        result = processor.extract_text(file_path)

        logger.info(
            "document_processed",
            file=file_path,
            method=result.method,
            pages=result.pages,
            words=result.word_count,
            user_id=user_id,
        )
        return result.to_dict()

    except Exception as e:
        logger.error("document_processing_failed", file=file_path, error=str(e))
        return {"error": str(e)}


@shared_task(name="intelligence.analyze_cv_document")
def analyze_cv_document(file_path: str, user_id: int):
    """Process and analyze a CV document with AI extraction."""
    try:
        from .document_processor import get_document_processor
        from apps.intelligence import get_ai_service
        from apps.intelligence.llm_plugin import LLMRequest
        from apps.intelligence.model_router import select_model, TaskType, QualityLevel

        processor = get_document_processor()
        doc_result = processor.extract_text(file_path)

        if doc_result.is_empty:
            return {"error": "Document appears to be empty or unreadable."}

        model_selection = select_model(TaskType.CV_PARSING, QualityLevel.BALANCED)
        service = get_ai_service()

        extraction_prompt = f"""Extract structured information from this CV/resume text.

CV TEXT:
{doc_result.text[:6000]}

Return a JSON object with these fields:
{{
    "name": "full name",
    "email": "email address",
    "phone": "phone number",
    "location": "city/country",
    "summary": "brief professional summary",
    "skills": ["skill1", "skill2", ...],
    "experience": [
        {{"title": "job title", "company": "company", "duration": "dates", "description": "brief"}}
    ],
    "education": [
        {{"degree": "degree", "institution": "school", "year": "year"}}
    ],
    "certifications": ["cert1", ...],
    "languages": ["lang1", ...]
}}

Return ONLY valid JSON, no other text."""

        response = service.generate(LLMRequest(
            prompt=extraction_prompt,
            system_prompt="You are a CV parsing expert. Extract structured data accurately. Return only valid JSON.",
            model=model_selection.model_alias,
            max_tokens=model_selection.max_tokens,
            temperature=model_selection.temperature,
            user_id=user_id,
            operation="cv_parsing",
        ))

        import json
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed_data = json.loads(content)
        except json.JSONDecodeError:
            parsed_data = {"raw_text": doc_result.text[:3000], "parse_error": True}

        _update_career_profile(user_id, parsed_data)

        logger.info("cv_analysis_complete", user_id=user_id, skills_count=len(parsed_data.get("skills", [])))
        return parsed_data

    except Exception as e:
        logger.error("cv_analysis_failed", user_id=user_id, error=str(e))
        return {"error": str(e)}


def _store_trend_results(emerging: list, declining: list):
    """Store trend detection results for the admin dashboard."""
    from django.core.cache import cache

    cache.set("intelligence:emerging_skills", emerging, timeout=86400 * 7)
    cache.set("intelligence:declining_skills", declining, timeout=86400 * 7)


def _update_career_profile(user_id: int, parsed_data: dict):
    """Update user's career profile with parsed CV data."""
    try:
        from apps.career.models import CareerProfile

        profile, created = CareerProfile.objects.get_or_create(user_id=user_id)
        profile.cv_parsed_data = parsed_data
        profile.cv_parse_status = "completed"
        profile.save(update_fields=["cv_parsed_data", "cv_parse_status"])

        if parsed_data.get("skills"):
            _map_skills_to_taxonomy(user_id, parsed_data["skills"])

    except Exception as e:
        logger.error("profile_update_failed", user_id=user_id, error=str(e))


def _map_skills_to_taxonomy(user_id: int, skills: list[str]):
    """Map extracted skills to ESCO taxonomy."""
    try:
        from apps.skills.models import Skill
        from apps.career.models import CareerUserSkill

        for skill_name in skills[:30]:
            skill = Skill.objects.filter(name__iexact=skill_name).first()
            if not skill:
                skill = Skill.objects.filter(name__icontains=skill_name).first()

            if skill:
                CareerUserSkill.objects.update_or_create(
                    user_id=user_id,
                    skill=skill,
                    defaults={"source": "cv_extraction"},
                )
    except Exception as e:
        logger.warning("skill_mapping_failed", user_id=user_id, error=str(e))

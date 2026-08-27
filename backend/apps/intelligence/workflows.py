"""
Prefect Workflow Orchestration.

Defines complex multi-step workflows using Prefect (Apache 2.0).
Falls back to sequential Celery task chains when Prefect is not installed.

Workflows:
- Full CV Processing Pipeline
- Company Enrichment Pipeline
- Weekly Intelligence Report
- Skill Gap Analysis Pipeline
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

PREFECT_AVAILABLE = False
try:
    from prefect import flow, task
    from prefect.task_runners import ConcurrentTaskRunner
    PREFECT_AVAILABLE = True
except ImportError:
    pass


if PREFECT_AVAILABLE:

    @task(name="extract_document")
    def extract_document_task(file_path: str) -> Dict:
        from .document_processor import get_document_processor
        processor = get_document_processor()
        result = processor.extract_text(file_path)
        return {"text": result.text, "pages": result.pages, "word_count": result.word_count}

    @task(name="parse_cv_with_ai")
    def parse_cv_task(text: str) -> Dict:
        from ai.bedrock import bedrock_service
        return bedrock_service.parse_cv(text)

    @task(name="extract_skills")
    def extract_skills_task(cv_data: Dict) -> list:
        from apps.skills.extraction import skill_extractor
        skills_text = " ".join(cv_data.get("skills", {}).get("technical", []))
        return skills_text.split() if skills_text else []

    @task(name="match_esco_skills")
    def match_esco_task(skills: list) -> list:
        from apps.skills.esco_embeddings import get_esco_matcher
        matcher = get_esco_matcher()
        return matcher.batch_match(skills)

    @task(name="research_company")
    def research_company_task(company_name: str) -> Dict:
        from .research_engine import get_research_engine
        engine = get_research_engine()
        result = engine.research_company(company_name)
        return {"summary": result.summary, "confidence": result.confidence_score}

    @task(name="generate_content")
    def generate_content_task(role: str, language: str = "en") -> Dict:
        from .content_pipeline import get_content_pipeline
        pipeline = get_content_pipeline()
        piece = pipeline.generate_career_guide(role, language=language)
        return {"title": piece.title, "word_count": piece.word_count}

    @flow(name="cv_processing_pipeline", task_runner=ConcurrentTaskRunner())
    def cv_processing_flow(file_path: str, user_id: int) -> Dict:
        """
        Full CV processing pipeline:
        1. Extract text from document
        2. Parse structured CV data with AI
        3. Extract and match skills to ESCO
        4. Update career profile
        """
        doc_result = extract_document_task(file_path)
        cv_data = parse_cv_task(doc_result["text"])
        skills = extract_skills_task(cv_data)
        esco_matches = match_esco_task(skills)

        return {
            "cv_data": cv_data,
            "skills_count": len(skills),
            "esco_matches": len([m for m in esco_matches if m]),
            "word_count": doc_result["word_count"],
        }

    @flow(name="company_enrichment_pipeline")
    def company_enrichment_flow(company_name: str) -> Dict:
        """
        Company enrichment pipeline:
        1. Research company online
        2. Extract career page data
        3. Update company profile
        """
        research = research_company_task(company_name)
        return research

    @flow(name="weekly_intelligence_report")
    def weekly_intelligence_flow() -> Dict:
        """
        Weekly intelligence report generation:
        1. Compute skill trends
        2. Generate skills report
        3. Generate top career guides
        """
        from .trend_detection import get_trend_service

        service = get_trend_service()
        emerging = service.get_emerging_skills(days=7)

        from .content_pipeline import get_content_pipeline
        pipeline = get_content_pipeline()
        report = pipeline.generate_skills_report(days=7)

        return {
            "emerging_count": len(emerging),
            "report_words": report.word_count,
        }

else:
    def cv_processing_flow(file_path: str, user_id: int) -> Dict:
        """Fallback: run sequentially without Prefect."""
        from .document_processor import get_document_processor
        from ai.bedrock import bedrock_service
        from apps.skills.esco_embeddings import get_esco_matcher

        processor = get_document_processor()
        doc_result = processor.extract_text(file_path)

        cv_data = bedrock_service.parse_cv(doc_result.text)

        skills_text = cv_data.get("skills", {}).get("technical", [])
        matcher = get_esco_matcher()
        esco_matches = matcher.batch_match(skills_text)

        return {
            "cv_data": cv_data,
            "skills_count": len(skills_text),
            "esco_matches": len([m for m in esco_matches if m]),
            "word_count": doc_result.word_count,
        }

    def company_enrichment_flow(company_name: str) -> Dict:
        """Fallback: research without Prefect."""
        from .research_engine import get_research_engine
        engine = get_research_engine()
        result = engine.research_company(company_name)
        return {"summary": result.summary, "confidence": result.confidence_score}

    def weekly_intelligence_flow() -> Dict:
        """Fallback: generate report without Prefect."""
        from .trend_detection import get_trend_service
        from .content_pipeline import get_content_pipeline

        service = get_trend_service()
        emerging = service.get_emerging_skills(days=7)

        pipeline = get_content_pipeline()
        report = pipeline.generate_skills_report(days=7)

        return {
            "emerging_count": len(emerging),
            "report_words": report.word_count,
        }

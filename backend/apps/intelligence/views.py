"""
Intelligence Layer API Views.

Exposes AI services, research, trends, and tools via REST API.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_rashid(request):
    """Send a message to Rashid and get a response using Pydantic AI agent."""
    message = request.data.get("message", "").strip()
    if not message:
        return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .agent import get_rashid_agent, PlatformDeps
        import asyncio

        agent = get_rashid_agent()
        deps = PlatformDeps(
            user_id=request.user.id,
            user_email=request.user.email,
            user_name=getattr(request.user, "full_name", request.user.email),
            language=request.data.get("language", "en"),
            session_id=request.data.get("session_id", ""),
        )

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(agent.run(message, deps=deps))
        finally:
            loop.close()

        try:
            from apps.events.emitter import emit
            from apps.events.types import AI_MODEL_CALLED

            usage = result.usage() if hasattr(result, 'usage') and callable(result.usage) else None
            tokens_in = getattr(usage, 'request_tokens', 0) if usage else 0
            tokens_out = getattr(usage, 'response_tokens', 0) if usage else 0
            from apps.intelligence.bedrock_plugin import MODEL_COSTS, MODEL_ALIASES
            model_id = MODEL_ALIASES.get(getattr(settings, "RASHID_MODEL", "sonnet"), "")
            rates = MODEL_COSTS.get(model_id, {"input_per_1k": 0.003, "output_per_1k": 0.015})
            cost = round((tokens_in / 1000) * rates["input_per_1k"] + (tokens_out / 1000) * rates["output_per_1k"], 6)

            emit(
                event_type=AI_MODEL_CALLED,
                category="ai",
                user=request.user,
                target_type="model",
                target_id=model_id,
                data={
                    "model": model_id,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "cost_usd": cost,
                    "user_id": request.user.id,
                    "operation": "chat",
                    "agent": "rashid_pydantic_ai",
                },
            )
        except Exception:
            pass

        return Response({
            "response": result.data,
            "model": str(result.usage()) if hasattr(result, 'usage') else "unknown",
        })

    except Exception as e:
        from .service import get_ai_service
        from .llm_plugin import LLMRequest

        service = get_ai_service()
        response = service.generate(LLMRequest(
            prompt=message,
            system_prompt="You are Rashid, a friendly career advisor.",
            model="haiku",
            user_id=request.user.id,
            operation="chat",
        ))
        return Response({"response": response.content, "model": response.model, "fallback": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_emerging_skills(request):
    """Get currently trending skills from job data."""
    from .trend_detection import get_trend_service

    service = get_trend_service()
    days = int(request.query_params.get("days", 30))
    emerging = service.get_emerging_skills(days=days)
    return Response({"emerging_skills": emerging, "period_days": days})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_declining_skills(request):
    """Get skills that are declining in demand."""
    from .trend_detection import get_trend_service

    service = get_trend_service()
    days = int(request.query_params.get("days", 30))
    declining = service.get_declining_skills(days=days)
    return Response({"declining_skills": declining, "period_days": days})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_research(request):
    """Start an async research job."""
    query = request.data.get("query", "").strip()
    research_type = request.data.get("type", "market")

    if not query:
        return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)

    from .tasks import research_topic
    task = research_topic.delay(query=query, research_type=research_type)

    return Response({
        "task_id": task.id,
        "status": "started",
        "message": "Research started. Check back for results.",
    }, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_email_address(request):
    """Verify an email address."""
    email = request.data.get("email", "").strip()
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    from .email_verification import verify_email
    result = verify_email(email)

    return Response({
        "email": result.email,
        "normalized": result.normalized_email,
        "status": result.status.value,
        "is_valid": result.is_valid,
        "is_disposable": result.is_disposable,
        "has_mx_record": result.has_mx_record,
        "domain": result.domain,
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def intelligence_health(request):
    """Admin: check health of all intelligence services."""
    from .service import get_ai_service
    from .circuit_breaker import ai_circuit_breaker

    health = {
        "ai_service": get_ai_service().health_check(),
        "circuit_breaker": {
            "state": ai_circuit_breaker.state.value,
            "available": ai_circuit_breaker.is_available(),
        },
    }

    try:
        from .document_processor import get_document_processor
        processor = get_document_processor()
        health["document_processor"] = {
            "available": processor.converter != "fallback",
            "backend": "docling" if processor.converter != "fallback" else "pdfplumber",
        }
    except Exception:
        health["document_processor"] = {"available": False}

    try:
        from .trend_detection import get_trend_service
        health["trend_detection"] = {"available": True}
    except Exception:
        health["trend_detection"] = {"available": False}

    from django.core.cache import cache
    cached_emerging = cache.get("intelligence:emerging_skills")
    health["cached_trends"] = {
        "has_data": cached_emerging is not None,
        "count": len(cached_emerging) if cached_emerging else 0,
    }

    return Response(health)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_trends_dashboard(request):
    """Admin: get full trends data for the dashboard."""
    from django.core.cache import cache

    emerging = cache.get("intelligence:emerging_skills", [])
    declining = cache.get("intelligence:declining_skills", [])

    return Response({
        "emerging_skills": emerging[:20],
        "declining_skills": declining[:20],
        "last_updated": "cached",
    })


# --- Phase 4: Knowledge Graph ---

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def skill_neighborhood(request, skill_name):
    """Get the knowledge graph neighborhood for a skill."""
    from .knowledge_graph import get_knowledge_graph_service

    service = get_knowledge_graph_service()
    depth = int(request.query_params.get("depth", 2))
    result = service.get_skill_neighborhood(skill_name, depth=depth)

    return Response({
        "skill": skill_name,
        "nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in result.nodes],
        "edges": [{"source": e.source, "target": e.target, "relationship": e.relationship, "weight": e.weight} for e in result.edges],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def role_skills_graph(request, role_title):
    """Get skills graph for a role title."""
    from .knowledge_graph import get_knowledge_graph_service

    service = get_knowledge_graph_service()
    result = service.get_role_skills_graph(role_title)

    return Response({
        "role": role_title,
        "nodes": [{"id": n.id, "label": n.label, "type": n.type, **n.properties} for n in result.nodes],
        "edges": [{"source": e.source, "target": e.target, "weight": e.weight} for e in result.edges],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_path_graph(request, role_title):
    """Get career progression paths from a role."""
    from .knowledge_graph import get_knowledge_graph_service

    service = get_knowledge_graph_service()
    result = service.get_career_path_graph(role_title)

    return Response({
        "current_role": role_title,
        "paths": result.paths,
        "nodes": [{"id": n.id, "label": n.label, "type": n.type} for n in result.nodes],
        "edges": [{"source": e.source, "target": e.target, "relationship": e.relationship} for e in result.edges],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_skill_gaps(request):
    """Get skill gaps between user and a target role."""
    from .knowledge_graph import get_knowledge_graph_service

    target_role = request.query_params.get("role", "")
    if not target_role:
        return Response({"error": "role parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    service = get_knowledge_graph_service()
    gaps = service.get_user_skill_gaps(request.user.id, target_role)
    return Response(gaps)


# --- Phase 4: Marketing Intelligence ---

@api_view(["GET"])
@permission_classes([IsAdminUser])
def platform_metrics(request):
    """Admin: Get platform health and growth metrics."""
    from .marketing_intelligence import get_marketing_intelligence

    service = get_marketing_intelligence()
    metrics = service.get_platform_metrics()
    return Response(metrics)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def market_gaps(request):
    """Admin: Identify market gaps (high demand, low supply)."""
    from .marketing_intelligence import get_marketing_intelligence

    service = get_marketing_intelligence()
    gaps = service.get_market_gaps()

    return Response({
        "gaps": [
            {"category": g.category, "title": g.title, "description": g.description, "data": g.data}
            for g in gaps
        ],
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def content_opportunities(request):
    """Admin: Get content generation opportunities."""
    from .marketing_intelligence import get_marketing_intelligence

    service = get_marketing_intelligence()
    opportunities = service.get_content_opportunities()

    return Response({
        "opportunities": [
            {"category": o.category, "title": o.title, "description": o.description, "data": o.data}
            for o in opportunities
        ],
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def industry_breakdown(request):
    """Admin: Get job distribution by industry."""
    from .marketing_intelligence import get_marketing_intelligence

    service = get_marketing_intelligence()
    return Response(service.get_industry_breakdown())


@api_view(["GET"])
@permission_classes([IsAdminUser])
def location_insights(request):
    """Admin: Get job distribution by location."""
    from .marketing_intelligence import get_marketing_intelligence

    service = get_marketing_intelligence()
    return Response(service.get_location_insights())


# --- Phase 3: Content Pipeline ---

@api_view(["POST"])
@permission_classes([IsAdminUser])
def generate_content(request):
    """Admin: Generate a content piece."""
    from .content_pipeline import get_content_pipeline, ContentType

    content_type = request.data.get("type", "career_guide")
    role = request.data.get("role", "")
    language = request.data.get("language", "en")

    if not role:
        return Response({"error": "role is required"}, status=status.HTTP_400_BAD_REQUEST)

    pipeline = get_content_pipeline()

    if content_type == "career_guide":
        piece = pipeline.generate_career_guide(role, language=language)
    elif content_type == "interview_guide":
        company = request.data.get("company", "")
        piece = pipeline.generate_interview_guide(role, company=company, language=language)
    elif content_type == "skills_report":
        days = int(request.data.get("days", 30))
        piece = pipeline.generate_skills_report(days=days, language=language)
    else:
        return Response({"error": f"Unknown content type: {content_type}"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "title": piece.title,
        "type": piece.content_type.value,
        "body": piece.body,
        "meta_description": piece.meta_description,
        "keywords": piece.keywords,
        "word_count": piece.word_count,
        "language": piece.language,
    })


# --- Phase 3: Crawl4AI ---

@api_view(["POST"])
@permission_classes([IsAdminUser])
def extract_from_url(request):
    """Admin: Extract structured data from a URL using Crawl4AI."""
    from .crawl4ai_extractor import get_crawl4ai_extractor

    url = request.data.get("url", "").strip()
    extraction_type = request.data.get("type", "company_profile")

    if not url:
        return Response({"error": "url is required"}, status=status.HTTP_400_BAD_REQUEST)

    extractor = get_crawl4ai_extractor()

    if extraction_type == "company_profile":
        result = extractor.extract_company_profile(url)
    elif extraction_type == "job_details":
        result = extractor.extract_job_details(url)
    elif extraction_type == "markdown":
        result = extractor.extract_to_markdown(url)
    else:
        return Response({"error": f"Unknown extraction type: {extraction_type}"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "url": result.url,
        "success": result.success,
        "data": result.data,
        "markdown": result.markdown[:2000] if result.markdown else "",
        "method": result.extraction_method,
        "error": result.error,
    })

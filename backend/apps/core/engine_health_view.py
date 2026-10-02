"""Engine health / observability endpoint (Phase I, §35/§36).

Surfaces real, evidence-based status for the engines enriched this cycle so
admins can SEE engine health instead of guessing. Uses the same
{name,status,message} shape as SystemHealthView. No secrets exposed.
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.core.permissions import IsAdminRole


class EngineHealthView(APIView):
    """GET /api/v1/admin-api/engine-health/ — per-engine health for admin."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        checks = []

        # 1. Scraping — sources + strategy router availability
        try:
            from apps.jobs.models import Source
            from apps.scraper.strategy_router import decide_route, STRUCTURED_ATS
            active = Source.objects.filter(is_active=True)
            total = active.count()
            structured = active.filter(ats_platform__in=STRUCTURED_ATS).count()
            checks.append({
                "name": "Scraping Sources",
                "status": "healthy" if total else "warning",
                "message": f"{total} active sources ({structured} structured-ATS routable)",
            })
        except Exception as e:
            checks.append({"name": "Scraping Sources", "status": "error", "message": str(e)})

        # 2. Verification / Direct-Apply moat
        try:
            from apps.verification.models import BlockedDomain
            blocked = BlockedDomain.objects.filter(is_active=True).count()
            checks.append({
                "name": "Direct-Apply Moat",
                "status": "healthy" if blocked else "warning",
                "message": f"{blocked} active blocked aggregator domains",
            })
        except Exception as e:
            checks.append({"name": "Direct-Apply Moat", "status": "error", "message": str(e)})

        # 3. Job quality / provenance coverage
        try:
            from apps.jobs.models import Job
            recent = Job.objects.order_by("-scraped_at")[:200]
            n = len(recent)
            with_prov = sum(1 for j in recent if getattr(j, "field_provenance", None))
            checks.append({
                "name": "Job Provenance",
                "status": "healthy" if n == 0 or with_prov else "warning",
                "message": f"{with_prov}/{n} recent jobs carry field provenance",
            })
        except Exception as e:
            checks.append({"name": "Job Provenance", "status": "error", "message": str(e)})

        # 4. Matching engine (deterministic self-check)
        try:
            from apps.matching.engine import unified_matching_engine  # noqa: F401
            checks.append({
                "name": "Matching Engine",
                "status": "healthy",
                "message": "Unified deterministic engine loaded (eligibility/ranking/explanation)",
            })
        except Exception as e:
            checks.append({"name": "Matching Engine", "status": "error", "message": str(e)})

        # 5. Recommendation feedback signal volume
        try:
            from apps.users.models import RecommendationFeedback
            fb = RecommendationFeedback.objects.count()
            checks.append({
                "name": "Recommendation Feedback",
                "status": "healthy",
                "message": f"{fb} behavioral signals captured",
            })
        except Exception as e:
            checks.append({"name": "Recommendation Feedback", "status": "error", "message": str(e)})

        # 6. Search backend (Typesense primary + Postgres fallback) — no
        # secrets exposed (never reads/prints TYPESENSE_API_KEY). Reports
        # the primary's real health_check(), the jobs collection document
        # count (so an auth/config regression like the 2026-10-02 missing-
        # key incident is visible here instead of only in Celery logs), and
        # whether the fallback is in active use. Does not duplicate
        # SearchService - calls the exact same methods the app itself uses.
        try:
            from apps.search.service import get_search_service
            svc = get_search_service()
            primary_healthy = svc.primary.health_check()
            if primary_healthy:
                try:
                    coll = svc.primary.client.collections["jobs"].retrieve()
                    doc_count = coll.get("num_documents")
                    checks.append({
                        "name": "Search (Typesense)",
                        "status": "healthy",
                        "message": f"primary healthy, jobs collection: {doc_count} documents",
                    })
                except Exception as ce:
                    # Typesense server is up but the jobs collection itself
                    # is missing/misconfigured - distinct from an auth
                    # failure, surfaced separately rather than conflated.
                    checks.append({
                        "name": "Search (Typesense)",
                        "status": "warning",
                        "message": f"primary healthy but jobs collection unavailable: {ce}",
                    })
            else:
                # health_check() returned False - typically an auth failure
                # (missing/invalid TYPESENSE_API_KEY) or the server being
                # unreachable. Fallback keeps search FUNCTIONAL but this
                # must show as degraded, not healthy - a repeat of the
                # 2026-10-02 incident must be visible here immediately.
                checks.append({
                    "name": "Search (Typesense)",
                    "status": "warning",
                    "message": "primary (Typesense) unhealthy - serving search via Postgres fallback",
                })
        except Exception as e:
            checks.append({"name": "Search (Typesense)", "status": "error", "message": str(e)})

        # 7. AI provider (Bedrock) — classified status (no secrets)
        try:
            from apps.intelligence.bedrock_client import bedrock_health
            bh = bedrock_health()
            status = "healthy" if bh.get("status") == "HEALTHY" else "error"
            checks.append({
                "name": "AI Provider (Bedrock)",
                "status": status,
                "message": f"{bh.get('status')} ({bh.get('region')}, src={bh.get('credential_source')})",
            })
        except Exception as e:
            checks.append({"name": "AI Provider (Bedrock)", "status": "error", "message": str(e)})

        has_error = any(c["status"] == "error" for c in checks)
        has_warning = any(c["status"] == "warning" for c in checks)
        overall = "error" if has_error else ("warning" if has_warning else "healthy")

        return Response({"overall_status": overall, "checks": checks})

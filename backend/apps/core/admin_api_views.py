"""
Admin API views for E-Career admin panel.
Phase 7a + 7b: DRF API endpoints for admin functionality.

All views require IsAdminRole permission.
"""

from rest_framework import generics, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Value, CharField
from datetime import timedelta

from apps.core.permissions import IsAdminRole
from apps.core.models import ActivityLog, PipelineHealth
from apps.core.pagination import StandardPagination


# ---------------------------------------------------------------------------
# 1. SystemHealthView
# ---------------------------------------------------------------------------


class SystemHealthView(APIView):
    """
    System health monitoring endpoint.
    Checks Database, Redis, Celery, and Email services.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        from django.db import connection
        from django.core.cache import cache

        checks = []

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks.append({
                "name": "Database",
                "status": "healthy",
                "message": "PostgreSQL is responding",
            })
        except Exception as e:
            checks.append({
                "name": "Database",
                "status": "error",
                "message": str(e),
            })

        # Redis check
        try:
            cache.set("health_check", "ok", 10)
            if cache.get("health_check") == "ok":
                checks.append({
                    "name": "Redis",
                    "status": "healthy",
                    "message": "Redis is responding",
                })
            else:
                raise Exception("Cache write/read failed")
        except Exception as e:
            checks.append({
                "name": "Redis",
                "status": "error",
                "message": str(e),
            })

        # Celery check
        try:
            from celery import current_app

            inspect = current_app.control.inspect()
            stats = inspect.stats()
            if stats:
                worker_count = len(stats)
                checks.append({
                    "name": "Celery",
                    "status": "healthy",
                    "message": f"{worker_count} workers active",
                })
            else:
                checks.append({
                    "name": "Celery",
                    "status": "warning",
                    "message": "No workers detected",
                })
        except Exception as e:
            checks.append({
                "name": "Celery",
                "status": "error",
                "message": str(e),
            })

        # Email accounts check
        try:
            from apps.emails.models import EmailAccount

            email_accounts = EmailAccount.objects.filter(is_active=True)
            available_accounts = [
                acc for acc in email_accounts if acc.today_sent < acc.daily_limit
            ]
            if len(available_accounts) > 0:
                checks.append({
                    "name": "Email Accounts",
                    "status": "healthy",
                    "message": (
                        f"{len(available_accounts)}/{len(email_accounts)} "
                        "accounts available"
                    ),
                })
            else:
                checks.append({
                    "name": "Email Accounts",
                    "status": "warning",
                    "message": "No email accounts available",
                })
        except Exception as e:
            checks.append({
                "name": "Email Accounts",
                "status": "warning",
                "message": "Email system not configured",
            })

        has_error = any(c["status"] == "error" for c in checks)
        has_warning = any(c["status"] == "warning" for c in checks)
        overall_status = "error" if has_error else ("warning" if has_warning else "healthy")

        return Response({
            "overall_status": overall_status,
            "checks": checks,
        })


# ---------------------------------------------------------------------------
# 2. ScraperDashboardView
# ---------------------------------------------------------------------------


class ScraperDashboardView(APIView):
    """
    Scraper management dashboard data.
    Returns sources, scrape stats, scraper health, and pipeline health.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.jobs.models import Job, Source

        # Sources with stats
        sources_qs = Source.objects.annotate(
            total_jobs=Count("jobs"),
            active_jobs=Count("jobs", filter=Q(jobs__status="active")),
            jobs_today=Count(
                "jobs", filter=Q(jobs__created_at__date=timezone.now().date())
            ),
        )

        sources_data = []
        for src in sources_qs:
            sources_data.append({
                "id": src.id,
                "uuid": str(src.uuid),
                "name": src.name,
                "slug": src.slug,
                "url": src.url,
                "type": src.type,
                "is_active": src.is_active,
                "last_run_at": src.last_run_at,
                "last_run_status": src.last_run_status,
                "total_jobs": src.total_jobs,
                "active_jobs": src.active_jobs,
                "jobs_today": src.jobs_today,
            })

        # Scrape stats
        today = timezone.now()
        week_ago = today - timedelta(days=7)

        scam_jobs_blocked = 0
        try:
            scam_jobs_blocked = Job.objects.filter(is_legitimate=False).count()
        except Exception:
            scam_jobs_blocked = Job.objects.filter(quality_state="rejected").count()

        scrape_stats = {
            "total_jobs": Job.objects.count(),
            "active_jobs": Job.objects.filter(status="active").count(),
            "jobs_this_week": Job.objects.filter(posted_at__gte=week_ago.date()).count(),
            "scam_jobs_blocked": scam_jobs_blocked,
        }

        # Scraper health
        scraper_health = []
        for src in sources_qs:
            last_job = src.jobs.order_by("-created_at").first()
            health_status = "healthy"
            if not last_job:
                health_status = "no_data"
            elif last_job.created_at < timezone.now() - timedelta(days=2):
                health_status = "stale"

            scraper_health.append({
                "source_uuid": str(src.uuid),
                "source_name": src.name,
                "status": health_status,
                "last_scrape": last_job.created_at if last_job else None,
            })

        # Pipeline health
        pipeline_data = list(
            PipelineHealth.objects.all()
            .order_by("task_name")
            .values(
                "task_name",
                "last_run_at",
                "last_status",
                "last_duration",
                "last_error",
                "run_count",
            )
        )

        return Response({
            "sources": sources_data,
            "scrape_stats": scrape_stats,
            "scraper_health": scraper_health,
            "pipeline_health": pipeline_data,
        })


# ---------------------------------------------------------------------------
# 3. AICostDashboardView
# ---------------------------------------------------------------------------


class AICostDashboardView(APIView):
    """
    AI usage and cost dashboard.
    Returns cost summaries, feature breakdown, model usage, and trends.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from apps.events.models import EventLog as Event
        except ImportError:
            return Response({
                "error": "AI cost tracking models not available in this environment."
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        ai_events = Event.objects.filter(event_type="ai_model_called")

        def extract_cost(events):
            total = 0
            for event in events:
                if event.data and "cost_usd" in event.data:
                    total += float(event.data.get("cost_usd", 0))
            return total

        today_events = ai_events.filter(created_at__gte=today_start)
        today_cost = extract_cost(today_events)
        today_calls = today_events.count()

        week_events = ai_events.filter(created_at__gte=week_start)
        week_cost = extract_cost(week_events)
        week_calls = week_events.count()

        month_events = ai_events.filter(created_at__gte=month_start)
        month_cost = extract_cost(month_events)
        month_calls = month_events.count()

        feature_costs = {}
        for event in month_events:
            if event.data:
                operation = event.data.get("operation", "unknown")
                cost = float(event.data.get("cost_usd", 0))
                feature_costs[operation] = feature_costs.get(operation, 0) + cost
        feature_costs_sorted = sorted(
            feature_costs.items(), key=lambda x: x[1], reverse=True
        )

        model_usage = {}
        for event in month_events:
            if event.data:
                model = event.data.get("model", "unknown")
                model_usage[model] = model_usage.get(model, 0) + 1
        model_usage_sorted = sorted(
            model_usage.items(), key=lambda x: x[1], reverse=True
        )

        user_costs = {}
        for event in month_events.select_related("user"):
            if event.data and event.user_id:
                email = event.user.email if event.user else "Anonymous"
                cost = float(event.data.get("cost_usd", 0))
                user_costs[email] = user_costs.get(email, 0) + cost
        top_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)[:10]

        company_costs = {}
        try:
            from apps.employers.models import EmployerProfile
            employer_user_ids = set(
                EmployerProfile.objects.values_list("user_id", flat=True)
            )
            employer_company_map = dict(
                EmployerProfile.objects.select_related("company")
                .values_list("user_id", "company__name")
            )
            for event in month_events:
                if event.data and event.user_id and event.user_id in employer_user_ids:
                    company_name = employer_company_map.get(event.user_id, "Unknown")
                    cost = float(event.data.get("cost_usd", 0))
                    company_costs[company_name] = company_costs.get(company_name, 0) + cost
        except ImportError:
            pass
        top_companies = sorted(company_costs.items(), key=lambda x: x[1], reverse=True)[:10]

        daily_costs = []
        for i in range(30, -1, -1):
            day_start = now - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_events = ai_events.filter(
                created_at__gte=day_start, created_at__lt=day_end
            )
            day_cost = extract_cost(day_events)

            daily_costs.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "cost": round(day_cost, 4),
                "calls": day_events.count(),
            })

        return Response({
            "today": {
                "cost": round(today_cost, 4),
                "calls": today_calls,
            },
            "week": {
                "cost": round(week_cost, 4),
                "calls": week_calls,
            },
            "month": {
                "cost": round(month_cost, 4),
                "calls": month_calls,
            },
            "feature_costs": [
                {"feature": k, "cost": round(v, 4)} for k, v in feature_costs_sorted
            ],
            "model_usage": [
                {"model": k, "count": v} for k, v in model_usage_sorted
            ],
            "top_users": [
                {"email": k, "cost": round(v, 4)} for k, v in top_users
            ],
            "company_costs": [
                {"company": k, "cost": round(v, 4)} for k, v in top_companies
            ],
            "daily_costs": daily_costs,
        })


# ---------------------------------------------------------------------------
# 4. VerificationResultView
# ---------------------------------------------------------------------------


class VerificationResultView(APIView):
    """
    Return the full VerificationResult for a given job UUID.
    """

    permission_classes = [IsAdminRole]

    def get(self, request, job_uuid):
        try:
            from apps.verification.models import VerificationResult
        except ImportError:
            return Response(
                {"detail": "Verification module not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        result = VerificationResult.objects.filter(job__uuid=job_uuid).first()
        if not result:
            return Response(
                {"detail": "Verification result not found for this job."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "uuid": str(result.uuid),
            "job_uuid": str(result.job.uuid),
            "status": result.status,
            "trust_score": result.trust_score,
            # Stage 1: ATS Fingerprinting
            "ats_platform_detected": result.ats_platform_detected,
            "ats_confidence": result.ats_confidence,
            # Stage 2: Redirect Resolution
            "redirect_chain": result.redirect_chain,
            # Stage 3: Domain Verification
            "domain_trust": result.domain_trust,
            "domain_matches_company": result.domain_matches_company,
            "ssl_valid": result.ssl_valid,
            # Stage 4: Legitimacy Scoring
            "legitimacy_score": result.legitimacy_score,
            "legitimacy_flags": result.legitimacy_flags,
            # Stage 5: Freshness & Liveness
            "url_accessible": result.url_accessible,
            "http_status_code": result.http_status_code,
            # Stage 6: Deduplication
            "is_duplicate": result.is_duplicate,
            "duplicate_of": str(result.duplicate_of.uuid) if result.duplicate_of else None,
            "content_hash": result.content_hash,
            # Computed
            "overall_status": result.status,
            # Admin Override
            "admin_override": result.admin_override,
            "override_by": (
                result.override_by.email if result.override_by else None
            ),
            "override_reason": result.override_reason,
            # Metadata
            "verified_at": result.verified_at,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
        })


# ---------------------------------------------------------------------------
# 5. VerificationOverrideView
# ---------------------------------------------------------------------------


class VerificationOverrideView(APIView):
    """
    Allow admin to override a verification result.
    PATCH: accepts admin_override (bool) and override_reason (str).
    """

    permission_classes = [IsAdminRole]

    def patch(self, request, job_uuid):
        try:
            from apps.verification.models import VerificationResult
        except ImportError:
            return Response(
                {"detail": "Verification module not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        result = VerificationResult.objects.filter(job__uuid=job_uuid).first()
        if not result:
            return Response(
                {"detail": "Verification result not found for this job."},
                status=status.HTTP_404_NOT_FOUND,
            )

        admin_override = request.data.get("admin_override")
        override_reason = request.data.get("override_reason", "")

        if admin_override is None:
            return Response(
                {"detail": "admin_override field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result.admin_override = bool(admin_override)
        result.override_by = request.user
        result.override_reason = override_reason
        result.override_at = timezone.now()
        result.save(
            update_fields=[
                "admin_override",
                "override_by",
                "override_reason",
                "override_at",
            ]
        )

        # Log to ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action="verification_override",
            target_type="VerificationResult",
            target_id=str(result.uuid),
            metadata={
                "job_uuid": str(job_uuid),
                "admin_override": result.admin_override,
                "override_reason": override_reason,
            },
        )

        return Response({
            "detail": "Verification override applied.",
            "admin_override": result.admin_override,
            "override_by": request.user.email,
            "override_reason": result.override_reason,
            "override_at": result.override_at,
        })


# ---------------------------------------------------------------------------
# 6. SourceControlView
# ---------------------------------------------------------------------------


class SourceControlView(APIView):
    """
    Control a scraper Source: start, stop, pause, run_now.
    POST with { "action": "start" | "stop" | "pause" | "run_now" }.
    """

    permission_classes = [IsAdminRole]
    VALID_ACTIONS = {"start", "stop", "pause", "run_now"}

    def post(self, request, source_uuid):
        from apps.jobs.models import Source

        action = request.data.get("action")
        if action not in self.VALID_ACTIONS:
            return Response(
                {"detail": f"Invalid action. Must be one of: {', '.join(sorted(self.VALID_ACTIONS))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            source = Source.objects.get(uuid=source_uuid)
        except Source.DoesNotExist:
            return Response(
                {"detail": "Source not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if action == "start":
            source.is_active = True
            source.save(update_fields=["is_active"])
        elif action in ("stop", "pause"):
            source.is_active = False
            source.save(update_fields=["is_active"])
        elif action == "run_now":
            try:
                from apps.scraper.tasks import scrape_single_source

                scrape_single_source.delay(str(source.id))
            except ImportError:
                return Response(
                    {"detail": "Scraper tasks module not available."},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )

        # Log the action
        ActivityLog.objects.create(
            user=request.user,
            action=f"source_{action}",
            target_type="Source",
            target_id=str(source.uuid),
            metadata={
                "source_name": source.name,
                "action": action,
            },
        )

        return Response({
            "detail": f"Action '{action}' applied to source '{source.name}'.",
            "source_uuid": str(source.uuid),
            "is_active": source.is_active,
        })


# ---------------------------------------------------------------------------
# 7. AdminCompanyListView
# ---------------------------------------------------------------------------


class AdminCompanySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    industry = serializers.CharField()
    website = serializers.URLField(allow_blank=True, required=False)
    is_active = serializers.BooleanField()
    job_count = serializers.IntegerField(read_only=True)


class AdminCompanyListView(generics.ListAPIView):
    """List all companies with basic fields and job counts."""

    permission_classes = [IsAdminRole]
    serializer_class = AdminCompanySerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        from apps.jobs.models import Company

        return Company.objects.annotate(
            job_count=Count("jobs")
        ).order_by("-job_count")


# ---------------------------------------------------------------------------
# 8. AdminCompanyDetailView
# ---------------------------------------------------------------------------


class AdminCompanyDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    logo_url = serializers.URLField(read_only=True)
    domain = serializers.CharField(read_only=True)
    size = serializers.CharField(read_only=True)
    headquarters = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def update(self, instance, validated_data):
        for field in ("name", "industry", "website", "is_active"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class AdminCompanyDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a Company by UUID."""

    permission_classes = [IsAdminRole]
    serializer_class = AdminCompanyDetailSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        from apps.jobs.models import Company

        return Company.objects.all()


# ---------------------------------------------------------------------------
# 9. TalentPoolAdminView
# ---------------------------------------------------------------------------


class TalentPoolAdminSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    company_name = serializers.SerializerMethodField()
    candidate_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_company_name(self, obj):
        try:
            return obj.employer.company.name if obj.employer and obj.employer.company else None
        except Exception:
            return None


class TalentPoolAdminView(generics.ListAPIView):
    """Read-only list of TalentPool objects."""

    permission_classes = [IsAdminRole]
    serializer_class = TalentPoolAdminSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        try:
            from apps.employers.models import TalentPool

            return (
                TalentPool.objects.select_related("employer", "employer__company")
                .annotate(candidate_count=Count("candidates"))
                .order_by("-created_at")
            )
        except ImportError:
            return TalentPool.objects.none()


# ---------------------------------------------------------------------------
# 10. UserTimelineView
# ---------------------------------------------------------------------------


class UserTimelineView(APIView):
    """
    Aggregate ActivityLog entries for a given user into a timeline.
    """

    permission_classes = [IsAdminRole]

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not User.objects.filter(pk=user_id).exists():
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Activity log entries
        logs = ActivityLog.objects.filter(user_id=user_id).order_by("-created_at")[:100]

        events = []
        for log in logs:
            events.append({
                "type": "activity",
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "metadata": log.metadata,
                "timestamp": log.created_at,
            })

        # Attempt to include analytics events if available
        try:
            from apps.events.models import EventLog

            analytics = (
                EventLog.objects.filter(user_id=user_id)
                .order_by("-created_at")[:100]
            )
            for evt in analytics:
                events.append({
                    "type": "analytics",
                    "action": evt.event_type,
                    "target_type": getattr(evt, "target_type", ""),
                    "target_id": getattr(evt, "target_id", ""),
                    "metadata": evt.data if hasattr(evt, "data") else {},
                    "timestamp": evt.created_at,
                })
        except (ImportError, Exception):
            pass

        # Sort combined events by timestamp descending
        events.sort(key=lambda e: e["timestamp"], reverse=True)

        return Response({
            "user_id": user_id,
            "event_count": len(events),
            "events": events,
        })


# ---------------------------------------------------------------------------
# 11. CompanyTimelineView
# ---------------------------------------------------------------------------


class CompanyTimelineView(APIView):
    """
    Aggregate employer-related ActivityLog entries for a company into a timeline.
    """

    permission_classes = [IsAdminRole]

    def get(self, request, company_uuid):
        from apps.jobs.models import Company

        try:
            company = Company.objects.get(uuid=company_uuid)
        except Company.DoesNotExist:
            return Response(
                {"detail": "Company not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Gather activity logs related to this company
        logs = ActivityLog.objects.filter(
            Q(target_type="Company", target_id=str(company_uuid))
            | Q(target_type="company", target_id=str(company_uuid))
            | Q(target_type="Company", target_id=str(company.pk))
        ).order_by("-created_at")[:100]

        events = []
        for log in logs:
            events.append({
                "type": "activity",
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "user": log.user.email if log.user else None,
                "metadata": log.metadata,
                "timestamp": log.created_at,
            })

        # Also include job-related activity for this company
        job_uuids = list(
            company.jobs.values_list("uuid", flat=True)[:200]
        )
        if job_uuids:
            job_uuid_strs = [str(u) for u in job_uuids]
            job_logs = (
                ActivityLog.objects.filter(
                    target_type__in=["Job", "job"],
                    target_id__in=job_uuid_strs,
                )
                .order_by("-created_at")[:100]
            )
            for log in job_logs:
                events.append({
                    "type": "job_activity",
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "user": log.user.email if log.user else None,
                    "metadata": log.metadata,
                    "timestamp": log.created_at,
                })

        events.sort(key=lambda e: e["timestamp"], reverse=True)

        return Response({
            "company_uuid": str(company_uuid),
            "company_name": company.name,
            "event_count": len(events),
            "events": events,
        })


# ---------------------------------------------------------------------------
# 12. RecommendationDiagnosticsView
# ---------------------------------------------------------------------------


class RecommendationDiagnosticsView(APIView):
    """
    Compute a match breakdown between a user and a job.
    Query params: user_id (int), job_uuid (str).
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        from django.contrib.auth import get_user_model

        user_id = request.query_params.get("user_id")
        job_uuid = request.query_params.get("job_uuid")

        if not user_id or not job_uuid:
            return Response(
                {"detail": "Both user_id and job_uuid query params are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            from apps.jobs.models import Job

            job = Job.objects.get(uuid=job_uuid)
        except Exception:
            return Response(
                {"detail": "Job not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get the user's career profile
        try:
            from apps.career.models import CareerProfile

            profile = CareerProfile.objects.get(user=user)
        except Exception:
            return Response(
                {"detail": "Career profile not found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Use MatchingService to compute breakdown
        try:
            from apps.profiles.services import matching_service

            breakdown = matching_service.get_match_breakdown(profile, job)
        except ImportError:
            # Fallback: try direct import
            try:
                from apps.profiles.services import MatchingService

                service = MatchingService()
                breakdown = service.get_match_breakdown(profile, job)
            except Exception as e:
                return Response(
                    {"detail": f"Matching service unavailable: {str(e)}"},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )

        return Response({
            "user_id": int(user_id),
            "job_uuid": str(job_uuid),
            "match_breakdown": breakdown,
        })


# ---------------------------------------------------------------------------
# 13. GDPRAdminDashboardView
# ---------------------------------------------------------------------------


class GDPRAdminDashboardView(APIView):
    """
    GDPR overview: counts of pending data export and account deletion requests.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from apps.accounts.models_gdpr import (
                DataExportRequest,
                AccountDeletionRequest,
            )
        except ImportError:
            return Response(
                {"detail": "GDPR models not available in this environment."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        pending_exports = DataExportRequest.objects.filter(status="pending").count()
        processing_exports = DataExportRequest.objects.filter(status="processing").count()
        total_exports = DataExportRequest.objects.count()

        pending_deletions = AccountDeletionRequest.objects.filter(status="pending").count()
        processing_deletions = AccountDeletionRequest.objects.filter(
            status="processing"
        ).count()
        total_deletions = AccountDeletionRequest.objects.count()

        # Upcoming scheduled deletions (within next 7 days)
        upcoming_window = timezone.now() + timedelta(days=7)
        upcoming_deletions = AccountDeletionRequest.objects.filter(
            status="pending",
            scheduled_for__lte=upcoming_window,
        ).count()

        return Response({
            "data_exports": {
                "pending": pending_exports,
                "processing": processing_exports,
                "total": total_exports,
            },
            "account_deletions": {
                "pending": pending_deletions,
                "processing": processing_deletions,
                "total": total_deletions,
                "upcoming_7_days": upcoming_deletions,
            },
        })


# ---------------------------------------------------------------------------
# 14. CeleryBeatListView (Phase 7b.5)
# ---------------------------------------------------------------------------


class CeleryBeatListView(APIView):
    """
    List all Celery Beat periodic tasks with schedule info.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from django_celery_beat.models import PeriodicTask
        except ImportError:
            return Response(
                {"detail": "django-celery-beat not installed."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        tasks = PeriodicTask.objects.select_related(
            "interval", "crontab", "solar", "clocked"
        ).order_by("name")

        result = []
        for task in tasks:
            schedule_str = ""
            if task.crontab:
                c = task.crontab
                schedule_str = f"{c.minute} {c.hour} {c.day_of_week} {c.day_of_month} {c.month_of_year}"
            elif task.interval:
                schedule_str = f"every {task.interval.every} {task.interval.period}"
            elif task.solar:
                schedule_str = f"solar: {task.solar.event}"
            elif task.clocked:
                schedule_str = f"clocked: {task.clocked.clocked_time}"

            result.append({
                "id": task.id,
                "name": task.name,
                "task": task.task,
                "schedule": schedule_str,
                "enabled": task.enabled,
                "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
                "total_run_count": task.total_run_count,
                "description": task.description or "",
            })

        return Response({"tasks": result, "count": len(result)})


class CeleryBeatToggleView(APIView):
    """
    Enable or disable a Celery Beat periodic task.
    """

    permission_classes = [IsAdminRole]

    def patch(self, request, task_id):
        try:
            from django_celery_beat.models import PeriodicTask
        except ImportError:
            return Response(
                {"detail": "django-celery-beat not installed."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        try:
            task = PeriodicTask.objects.get(pk=task_id)
        except PeriodicTask.DoesNotExist:
            return Response(
                {"detail": "Periodic task not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        enabled = request.data.get("enabled")
        if enabled is None:
            return Response(
                {"detail": "Field 'enabled' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.enabled = bool(enabled)
        task.save(update_fields=["enabled"])

        ActivityLog.objects.create(
            user=request.user,
            action=f"celery_task_{'enable' if task.enabled else 'disable'}",
            target_type="PeriodicTask",
            target_id=str(task.id),
            metadata={"task_name": task.name, "enabled": task.enabled},
        )

        return Response({
            "id": task.id,
            "name": task.name,
            "enabled": task.enabled,
        })


# ---------------------------------------------------------------------------
# 15. AdminSearchView (Phase 7b.4)
# ---------------------------------------------------------------------------


class AdminSearchView(APIView):
    """
    Global admin search across Users, Companies, and Jobs.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q or len(q) < 2:
            return Response(
                {"detail": "Query parameter 'q' must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = min(int(request.query_params.get("limit", 20)), 50)
        results = []

        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(
            Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )[:limit]
        for u in users:
            results.append({
                "type": "user",
                "id": u.pk,
                "label": u.full_name or u.email,
                "detail": u.email,
                "role": u.role,
            })

        from apps.jobs.models import Company
        companies = Company.objects.filter(
            Q(name__icontains=q) | Q(domain__icontains=q)
        )[:limit]
        for c in companies:
            results.append({
                "type": "company",
                "id": str(c.uuid),
                "label": c.name,
                "detail": c.domain or c.website or "",
                "industry": c.industry,
            })

        from apps.jobs.models import Job
        jobs = Job.objects.filter(
            Q(title__icontains=q) | Q(company__name__icontains=q)
        ).select_related("company")[:limit]
        for j in jobs:
            results.append({
                "type": "job",
                "id": str(j.uuid),
                "label": j.title,
                "detail": j.company.name if j.company else "",
                "status": j.status if hasattr(j, "status") else "",
            })

        results.sort(key=lambda r: (0 if q.lower() in r["label"].lower() else 1))

        return Response({
            "query": q,
            "results": results[:limit],
            "count": len(results[:limit]),
        })


# ---------------------------------------------------------------------------
# 16. SubscriptionPlanViews (Phase 7b.2)
# ---------------------------------------------------------------------------


class SubscriptionPlanSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    feature_flags = serializers.ListField(child=serializers.CharField(), required=False)
    job_posting_limit = serializers.IntegerField(required=False)
    candidate_search_limit = serializers.IntegerField(required=False)
    ai_features_enabled = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True)


class SubscriptionPlanListView(generics.ListCreateAPIView):
    """List and create subscription plans."""

    permission_classes = [IsAdminRole]
    serializer_class = SubscriptionPlanSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        from apps.core.models import SubscriptionPlan
        return SubscriptionPlan.objects.order_by("-created_at")

    def get_serializer_class(self):
        from apps.core.models import SubscriptionPlan
        if not SubscriptionPlan._meta.db_table:
            pass

        class DynamicPlanSerializer(serializers.ModelSerializer):
            class Meta:
                model = SubscriptionPlan
                fields = [
                    "uuid", "name", "description", "feature_flags",
                    "job_posting_limit", "candidate_search_limit",
                    "ai_features_enabled", "is_active", "created_at",
                ]

        return DynamicPlanSerializer


class SubscriptionPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a subscription plan."""

    permission_classes = [IsAdminRole]
    lookup_field = "uuid"

    def get_queryset(self):
        from apps.core.models import SubscriptionPlan
        return SubscriptionPlan.objects.all()

    def get_serializer_class(self):
        from apps.core.models import SubscriptionPlan

        class DynamicPlanSerializer(serializers.ModelSerializer):
            class Meta:
                model = SubscriptionPlan
                fields = [
                    "uuid", "name", "description", "feature_flags",
                    "job_posting_limit", "candidate_search_limit",
                    "ai_features_enabled", "is_active", "created_at",
                ]

        return DynamicPlanSerializer


class CompanySubscriptionSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    company_name = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField(read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def get_company_name(self, obj):
        return obj.company.name if obj.company else ""

    def get_plan_name(self, obj):
        return obj.plan.name if obj.plan else ""


class CompanySubscriptionListView(generics.ListCreateAPIView):
    """List and create company subscriptions."""

    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_queryset(self):
        from apps.core.models import CompanySubscription
        return CompanySubscription.objects.select_related(
            "company", "plan"
        ).order_by("-started_at")

    def get_serializer_class(self):
        from apps.core.models import CompanySubscription

        class DynamicSubSerializer(serializers.ModelSerializer):
            company_name = serializers.SerializerMethodField()
            plan_name = serializers.SerializerMethodField()

            class Meta:
                model = CompanySubscription
                fields = [
                    "uuid", "company", "plan", "company_name", "plan_name",
                    "status", "started_at", "notes", "created_at",
                ]

            def get_company_name(self, obj):
                return obj.company.name if obj.company else ""

            def get_plan_name(self, obj):
                return obj.plan.name if obj.plan else ""

        return DynamicSubSerializer


class CompanySubscriptionDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a company subscription."""

    permission_classes = [IsAdminRole]
    lookup_field = "uuid"

    def get_queryset(self):
        from apps.core.models import CompanySubscription
        return CompanySubscription.objects.select_related("company", "plan")

    def get_serializer_class(self):
        from apps.core.models import CompanySubscription

        class DynamicSubSerializer(serializers.ModelSerializer):
            company_name = serializers.SerializerMethodField()
            plan_name = serializers.SerializerMethodField()

            class Meta:
                model = CompanySubscription
                fields = [
                    "uuid", "company", "plan", "company_name", "plan_name",
                    "status", "started_at", "notes", "created_at",
                ]

            def get_company_name(self, obj):
                return obj.company.name if obj.company else ""

            def get_plan_name(self, obj):
                return obj.plan.name if obj.plan else ""

        return DynamicSubSerializer


# ---------------------------------------------------------------------------
# 17. AdminCopilotChatView (Phase 7b.1)
# ---------------------------------------------------------------------------


class AdminCopilotChatView(APIView):
    """
    Admin AI Copilot chat endpoint.
    Wraps a pydantic-ai admin-scoped agent.
    """

    permission_classes = [IsAdminRole]

    def post(self, request):
        message = request.data.get("message", "").strip()
        if not message:
            return Response(
                {"detail": "Field 'message' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.intelligence.admin_agent import get_admin_agent, AdminDeps
            import asyncio

            agent = get_admin_agent()
            deps = AdminDeps(
                admin_id=request.user.id,
                admin_email=request.user.email,
            )

            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(agent.run(message, deps=deps))
            finally:
                loop.close()

            try:
                from apps.events.emitter import emit
                from apps.events.types import AI_MODEL_CALLED
                from apps.intelligence.bedrock_plugin import MODEL_COSTS, MODEL_ALIASES
                from django.conf import settings

                usage = result.usage if hasattr(result, 'usage') else None
                tokens_in = getattr(usage, 'input_tokens', 0) if usage else 0
                tokens_out = getattr(usage, 'output_tokens', 0) if usage else 0
                model_id = MODEL_ALIASES.get("haiku", "")
                rates = MODEL_COSTS.get(model_id, {"input_per_1k": 0.00025, "output_per_1k": 0.00125})
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
                        "operation": "admin_chat",
                        "agent": "admin_copilot",
                    },
                )
            except Exception:
                pass

            return Response({
                "response": result.output,
                "agent": "admin_copilot",
            })

        except ImportError:
            return Response(
                {"detail": "Admin copilot agent not available (pydantic-ai not installed)."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
            return Response(
                {"detail": f"Copilot error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# 20. GDPRExportActionView (Phase 7c)
# ---------------------------------------------------------------------------


class GDPRExportActionView(APIView):
    """
    Admin-triggered GDPR data export for a user.
    POST with {"user_id": <int>, "confirm": true} to execute.
    Omit confirm (or set false) to preview what will be exported.
    """

    permission_classes = [IsAdminRole]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id = request.data.get("user_id")
        confirm = request.data.get("confirm", False)

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not confirm:
            return Response({
                "action": "gdpr_export",
                "user_id": target_user.id,
                "email": target_user.email,
                "requires_confirm": True,
                "message": f"This will generate a full data export for {target_user.email}. "
                           "Re-submit with confirm=true to proceed.",
            })

        try:
            from apps.accounts.models_gdpr import DataExportRequest
        except ImportError:
            return Response(
                {"detail": "GDPR models not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        export_req = DataExportRequest.objects.create(
            user=target_user,
            status="processing",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        try:
            from apps.core.gdpr_service import GDPRService
            service = GDPRService(target_user)
            export_data = service.export_user_data_json()

            export_req.status = "completed"
            export_req.completed_at = timezone.now()
            export_req.file_size_bytes = len(export_data.encode("utf-8"))
            export_req.expires_at = timezone.now() + timedelta(days=30)
            export_req.save()

            ActivityLog.objects.create(
                action="gdpr_export",
                metadata={
                    "target_user_id": target_user.id,
                    "target_email": target_user.email,
                    "export_request_id": str(export_req.uuid),
                    "file_size_bytes": export_req.file_size_bytes,
                    "triggered_by": request.user.email,
                },
                user=request.user,
            )

            return Response({
                "action": "gdpr_export",
                "status": "completed",
                "export_request_id": str(export_req.uuid),
                "user_id": target_user.id,
                "email": target_user.email,
                "file_size_bytes": export_req.file_size_bytes,
                "expires_at": export_req.expires_at.isoformat(),
            })

        except Exception as e:
            export_req.status = "failed"
            export_req.error_message = str(e)
            export_req.save()
            return Response(
                {"detail": f"Export failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# 21. GDPRDeleteActionView (Phase 7c)
# ---------------------------------------------------------------------------


class GDPRDeleteActionView(APIView):
    """
    Admin-triggered GDPR account deletion for a user.
    POST with {"user_id": <int>, "confirm": true} to execute.
    Omit confirm to preview what will be deleted.
    Uses anonymization (not hard delete) to preserve aggregate analytics.
    """

    permission_classes = [IsAdminRole]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id = request.data.get("user_id")
        confirm = request.data.get("confirm", False)

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not confirm:
            return Response({
                "action": "gdpr_delete",
                "user_id": target_user.id,
                "email": target_user.email,
                "is_active": target_user.is_active,
                "requires_confirm": True,
                "message": f"This will anonymize all personal data for {target_user.email} "
                           "and deactivate the account. This action cannot be undone. "
                           "Re-submit with confirm=true to proceed.",
            })

        try:
            from apps.accounts.models_gdpr import AccountDeletionRequest
        except ImportError:
            return Response(
                {"detail": "GDPR models not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        deletion_req, created = AccountDeletionRequest.objects.get_or_create(
            user=target_user,
            defaults={
                "status": "processing",
                "scheduled_for": timezone.now(),
                "ip_address": request.META.get("REMOTE_ADDR"),
            },
        )

        if not created:
            if deletion_req.status == "completed":
                return Response(
                    {"detail": "Account already deleted/anonymized."},
                    status=status.HTTP_409_CONFLICT,
                )
            deletion_req.status = "processing"
            deletion_req.save()

        try:
            from apps.core.gdpr_service import GDPRService
            service = GDPRService(target_user)
            result = service.delete_user_data_anonymized()

            deletion_req.status = "completed"
            deletion_req.completed_at = timezone.now()
            deletion_req.save()

            ActivityLog.objects.create(
                action="gdpr_delete",
                metadata={
                    "target_user_id": target_user.id,
                    "target_email_was": target_user.email,
                    "deletion_request_id": str(deletion_req.uuid),
                    "anonymized_categories": result.get("anonymized_categories", {}),
                    "triggered_by": request.user.email,
                },
                user=request.user,
            )

            return Response({
                "action": "gdpr_delete",
                "status": "completed",
                "deletion_request_id": str(deletion_req.uuid),
                "user_id": target_user.id,
                "anonymized_categories": result.get("anonymized_categories", {}),
                "errors": result.get("errors", []),
            })

        except Exception as e:
            deletion_req.status = "failed"
            deletion_req.error_message = str(e)
            deletion_req.save()
            return Response(
                {"detail": f"Deletion failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# 22. DecisionSupportAlertsView (Final pass)
# ---------------------------------------------------------------------------


class DecisionSupportAlertsView(APIView):
    """
    Aggregated decision-support alerts for the admin dashboard.
    Evaluates current system state against thresholds and returns active alerts.
    Covers: scraper health, AI cost spikes, queue backlog, model failures.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        alerts = []
        now = timezone.now()

        try:
            from apps.events.models import EventLog
            today_cost = 0
            today_events = EventLog.objects.filter(
                category="ai",
                created_at__date=now.date(),
            )
            for e in today_events:
                if e.data:
                    today_cost += float(e.data.get("cost_usd", 0))
            if today_cost > 10.0:
                alerts.append({
                    "severity": "warning",
                    "category": "ai_cost_spike",
                    "message": f"AI spend today: ${today_cost:.2f} (threshold: $10.00)",
                    "value": round(today_cost, 2),
                })
        except Exception:
            pass

        try:
            from apps.scraper.models import ScraperSource
            stale_threshold = now - timedelta(days=2)
            sources = ScraperSource.objects.filter(is_active=True)
            stale = [s for s in sources if not s.last_scraped_at or s.last_scraped_at < stale_threshold]
            if stale:
                alerts.append({
                    "severity": "critical" if len(stale) > 2 else "warning",
                    "category": "scraper_stale",
                    "message": f"{len(stale)} scraper source(s) have not run in 2+ days: "
                               + ", ".join(s.name for s in stale[:5]),
                    "value": len(stale),
                })
        except Exception:
            pass

        try:
            from django.core.cache import cache
            cache.set("alert_health_check", "ok", 10)
            if cache.get("alert_health_check") != "ok":
                alerts.append({
                    "severity": "critical",
                    "category": "cache_failure",
                    "message": "Redis/cache is not responding correctly",
                })
        except Exception:
            alerts.append({
                "severity": "critical",
                "category": "cache_failure",
                "message": "Cache service unreachable",
            })

        try:
            from celery import current_app
            inspect = current_app.control.inspect(timeout=2)
            stats = inspect.stats()
            if not stats:
                alerts.append({
                    "severity": "warning",
                    "category": "queue_backlog",
                    "message": "No Celery workers detected — task queue may be backing up",
                })
        except Exception:
            alerts.append({
                "severity": "warning",
                "category": "queue_backlog",
                "message": "Cannot reach Celery broker to check worker status",
            })

        try:
            from apps.accounts.models_gdpr import AccountDeletionRequest
            overdue = AccountDeletionRequest.objects.filter(
                status="pending",
                scheduled_for__lt=now,
            ).count()
            if overdue:
                alerts.append({
                    "severity": "warning",
                    "category": "gdpr_overdue",
                    "message": f"{overdue} account deletion(s) past scheduled date",
                    "value": overdue,
                })
        except Exception:
            pass

        return Response({
            "alerts": alerts,
            "checked_at": now.isoformat(),
            "total_active": len(alerts),
        })


# ---------------------------------------------------------------------------
# 23. AdminUserListView (Phase 7c)
# ---------------------------------------------------------------------------


class AdminUserListView(generics.ListAPIView):
    """List all users with pagination and optional search."""

    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    class UserSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        email = serializers.EmailField(read_only=True)
        first_name = serializers.CharField(read_only=True)
        last_name = serializers.CharField(read_only=True)
        role = serializers.CharField(read_only=True)
        is_active = serializers.BooleanField(read_only=True)
        date_joined = serializers.DateTimeField(read_only=True)
        last_login = serializers.DateTimeField(read_only=True)

    serializer_class = UserSerializer

    def get_queryset(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        qs = User.objects.all().order_by("-date_joined")

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        return qs


# ---------------------------------------------------------------------------
# 24. AdminInterviewStatsView (Phase 7c)
# ---------------------------------------------------------------------------


class AdminInterviewStatsView(APIView):
    """
    Aggregate interview statistics for the admin dashboard.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from apps.interviews.models import InterviewSession
        except ImportError:
            return Response(
                {"detail": "Interviews module not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        from django.db.models import Avg

        total_sessions = InterviewSession.objects.count()
        completed_sessions = InterviewSession.objects.filter(
            status="completed"
        ).count()

        avg_score_result = InterviewSession.objects.filter(
            overall_score__isnull=False
        ).aggregate(avg=Avg("overall_score"))
        avg_score = round(avg_score_result["avg"], 2) if avg_score_result["avg"] is not None else None

        by_type = dict(
            InterviewSession.objects.values_list("interview_type")
            .annotate(cnt=Count("id"))
            .values_list("interview_type", "cnt")
        )

        by_difficulty = dict(
            InterviewSession.objects.values_list("difficulty")
            .annotate(cnt=Count("id"))
            .values_list("difficulty", "cnt")
        )

        recent_qs = (
            InterviewSession.objects.select_related("user")
            .order_by("-started_at")[:10]
        )
        recent_sessions = [
            {
                "id": s.id,
                "user_email": s.user.email if s.user else None,
                "interview_type": s.interview_type,
                "status": s.status,
                "overall_score": s.overall_score,
                "started_at": s.started_at,
            }
            for s in recent_qs
        ]

        return Response({
            "success": True,
            "data": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "avg_score": avg_score,
                "by_type": by_type,
                "by_difficulty": by_difficulty,
                "recent_sessions": recent_sessions,
            },
        })


# ---------------------------------------------------------------------------
# 25. AdminRashidStatsView (Phase 7c)
# ---------------------------------------------------------------------------


class AdminRashidStatsView(APIView):
    """
    Rashid AI conversation statistics for the admin dashboard.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from apps.rashid.models import RashidConversation
        except ImportError:
            return Response(
                {"detail": "Rashid module not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        total_conversations = RashidConversation.objects.count()

        by_mode = dict(
            RashidConversation.objects.values_list("mode")
            .annotate(cnt=Count("id"))
            .values_list("mode", "cnt")
        )

        recent_qs = (
            RashidConversation.objects.select_related("user")
            .order_by("-started_at")[:10]
        )
        recent_conversations = [
            {
                "id": c.id,
                "user_email": c.user.email if c.user else None,
                "mode": c.mode,
                "title": c.title,
                "created_at": c.started_at,
            }
            for c in recent_qs
        ]

        # Today's AI costs from EventLog
        today_ai_cost = 0
        today_ai_calls = 0
        try:
            from apps.events.models import EventLog

            today_events = EventLog.objects.filter(
                category="ai",
                created_at__date=timezone.now().date(),
            )
            today_ai_calls = today_events.count()
            for e in today_events:
                if e.data:
                    today_ai_cost += float(e.data.get("cost_usd", 0))
        except Exception:
            pass

        return Response({
            "success": True,
            "data": {
                "total_conversations": total_conversations,
                "by_mode": by_mode,
                "recent_conversations": recent_conversations,
                "today_ai_costs": {
                    "cost": round(today_ai_cost, 4),
                    "calls": today_ai_calls,
                },
            },
        })


# ---------------------------------------------------------------------------
# 26. AdminNotificationStatsView (Phase 7c)
# ---------------------------------------------------------------------------


class AdminNotificationStatsView(APIView):
    """
    Notification statistics for the admin dashboard.
    """

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            from apps.users.models import Notification
        except ImportError:
            return Response(
                {"detail": "Notification model not available."},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        total_notifications = Notification.objects.count()
        unread_count = Notification.objects.filter(is_read=False).count()

        by_type = dict(
            Notification.objects.values_list("type")
            .annotate(cnt=Count("id"))
            .values_list("type", "cnt")
        )

        recent_qs = (
            Notification.objects.select_related("user")
            .order_by("-created_at")[:20]
        )
        recent_notifications = [
            {
                "id": str(n.uuid),
                "user_email": n.user.email if n.user else None,
                "title": n.title,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in recent_qs
        ]

        return Response({
            "success": True,
            "data": {
                "total_notifications": total_notifications,
                "unread_count": unread_count,
                "by_type": by_type,
                "recent_notifications": recent_notifications,
            },
        })


# ---------------------------------------------------------------------------
# 27. AdminCsvImportView
# ---------------------------------------------------------------------------


class AdminBroadcastNotificationView(APIView):
    """Send a broadcast notification to all active users."""

    permission_classes = [IsAdminRole]

    def post(self, request):
        title = (request.data.get("title") or "").strip()
        body = (request.data.get("body") or "").strip()
        if not title:
            return Response(
                {"detail": "Title is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model
        from apps.users.models import Notification

        User = get_user_model()
        active_users = User.objects.filter(is_active=True)
        notifications = [
            Notification(user=u, title=title, body=body, type="system")
            for u in active_users
        ]
        Notification.objects.bulk_create(notifications)

        return Response({
            "success": True,
            "data": {
                "sent_to": len(notifications),
                "title": title,
            },
        })


class AdminCsvImportView(APIView):
    """Import jobs from a CSV file uploaded by admin."""

    permission_classes = [IsAdminRole]

    def post(self, request):
        import csv
        import io

        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"detail": "No file uploaded."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not csv_file.name.endswith(".csv"):
            return Response(
                {"detail": "File must be a .csv"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from apps.jobs.models import Job, Company, Tag

            decoded = csv_file.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(decoded))

            imported = 0
            skipped = 0
            errors = []
            total = 0

            for row_num, row in enumerate(reader, start=2):
                total += 1
                title = (row.get("title") or "").strip()
                if not title:
                    errors.append(f"Row {row_num}: missing title")
                    skipped += 1
                    continue

                company_name = (row.get("company") or "").strip()
                company = None
                if company_name:
                    company, _ = Company.objects.get_or_create(
                        name=company_name,
                        defaults={"slug": company_name.lower().replace(" ", "-")[:80]},
                    )

                salary_min = None
                salary_max = None
                try:
                    if row.get("salary_min"):
                        salary_min = int(row["salary_min"])
                    if row.get("salary_max"):
                        salary_max = int(row["salary_max"])
                except ValueError:
                    pass

                job = Job.objects.create(
                    title=title,
                    company=company,
                    description=(row.get("description") or "").strip(),
                    location=(row.get("location") or "").strip(),
                    work_arrangement=(row.get("work_mode") or "").strip() or None,
                    experience_level=(row.get("seniority") or "").strip() or None,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=(row.get("currency") or "EGP").strip(),
                    apply_url=(row.get("apply_url") or "").strip(),
                    source_type="employer_posted",
                    status="review",
                )

                tags_str = (row.get("tags") or "").strip()
                if tags_str:
                    for tag_name in tags_str.split(";"):
                        tag_name = tag_name.strip()
                        if tag_name:
                            tag, _ = Tag.objects.get_or_create(
                                name=tag_name,
                                defaults={"slug": tag_name.lower().replace(" ", "-")[:50]},
                            )
                            job.tags.add(tag)

                imported += 1

            return Response({
                "success": True,
                "data": {
                    "imported": imported,
                    "skipped": skipped,
                    "total": total,
                    "errors": errors,
                },
            })
        except Exception as e:
            return Response(
                {"detail": f"CSV processing failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

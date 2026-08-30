"""
Admin API views for E-Career admin panel.
Phase 7a: DRF API endpoints for admin functionality.

All views require IsAdminRole permission.
"""

from rest_framework import generics, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
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

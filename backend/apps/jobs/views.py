import logging
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from apps.jobs.models import Company, Source, Tag, Job
from apps.jobs.serializers import (
    CompanySerializer, CompanyWriteSerializer,
    SourceSerializer, TagSerializer,
    JobListSerializer, JobDetailSerializer, JobWriteSerializer,
)
from apps.jobs.filters import JobFilter
from apps.core.permissions import IsAdminRole
from apps.core.pagination import StandardPagination
from apps.core.utils import get_client_ip
from apps.events.emitter import emit
from apps.events.types import (
    JOB_VIEWED, JOB_SAVED, JOB_UNSAVED, JOB_APPLIED, JOB_DISMISSED,
    SEARCH_PERFORMED, SEARCH_RESULT_CLICKED,
    USER_REGISTERED, USER_LOGGED_IN, USER_PROFILE_UPDATED,
    CV_UPLOADED, CV_PARSED,
    AI_CONVERSATION_STARTED, AI_MESSAGE_SENT
)

logger = logging.getLogger(__name__)


# ── Job Save/Unsave Views ───────────────────────────────────────────────────────

@extend_schema(tags=["Jobs"])
class JobSaveView(APIView):
    """POST /api/v1/jobs/<slug>/save/ — Save a job for the authenticated user."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        try:
            job = Job.objects.get(slug=slug, status="active")
        except Job.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "Job not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check if already saved
        if job.saves.filter(user=request.user).exists():
            return Response(
                {"success": True, "data": {"is_saved": True}, "message": "Job already saved.", "errors": None},
            )
        
        # Create save
        from apps.users.models import SavedJob
        SavedJob.objects.create(user=request.user, job=job)
        
        # Emit JOB_SAVED event
        try:
            emit(
                event_type=JOB_SAVED,
                category="job",
                user=request.user,
                target_type="job",
                target_id=str(job.id),
                data={"source": "job_save_view"},
                request=request,
            )
        except Exception:
            pass
        
        return Response(
            {"success": True, "data": {"is_saved": True}, "message": "Job saved successfully.", "errors": None},
        )


@extend_schema(tags=["Jobs"])
class JobUnsaveView(APIView):
    """POST /api/v1/jobs/<slug>/unsave/ — Unsave a job for the authenticated user."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        try:
            job = Job.objects.get(slug=slug)
        except Job.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "Job not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Remove save
        from apps.users.models import SavedJob
        deleted, _ = SavedJob.objects.filter(user=request.user, job=job).delete()
        
        # Emit JOB_UNSAVED event
        try:
            emit(
                event_type=JOB_UNSAVED,
                category="job",
                user=request.user,
                target_type="job",
                target_id=str(job.id),
                data={"source": "job_unsave_view"},
                request=request,
            )
        except Exception:
            pass
        
        return Response(
            {"success": True, "data": {"is_saved": False}, "message": "Job unsaved.", "errors": None},
        )


@extend_schema(tags=["Jobs"])
class JobAskRashidView(APIView):
    """GET /api/v1/jobs/<slug>/ask-rashid/ — Get Rashid's analysis of this job (Phase 2B integration)."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        try:
            job = Job.objects.select_related("company", "source").prefetch_related("tags").get(slug=slug, status="active")
        except Job.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "Job not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # This will be fully implemented in Phase 2B
        # For now, return a placeholder with basic job info
        return Response({
            "success": True,
            "data": {
                "message": "Rashid analysis will be available after Phase 2B",
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company.name if job.company else None,
                "location": job.location,
                "salary_range": f"{job.salary_min} - {job.salary_max} {job.salary_currency}" if job.salary_min and job.salary_max else None,
                "skills_required": [tag.name for tag in job.tags.all()],
            },
            "message": "",
            "errors": None,
        })


# ── Companies ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["Companies"])
class CompanyListView(generics.ListCreateAPIView):
    """GET /api/v1/jobs/companies/ — List companies. POST — Create (admin)."""

    queryset = Company.objects.filter(is_active=True).order_by("name")
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "industry"]
    ordering_fields = ["name", "industry", "created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CompanyWriteSerializer
        return CompanySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Companies"])
class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/jobs/companies/<slug>/ — Company detail."""

    queryset = Company.objects.all()
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return CompanyWriteSerializer
        return CompanySerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsAdminRole()]
        return [AllowAny()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return Response(
            {"success": True, "data": None, "message": "Company deactivated.", "errors": None}
        )


# ── Sources ────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Sources"])
class SourceListView(generics.ListCreateAPIView):
    """GET /api/v1/jobs/sources/ — List sources. POST — Create (admin)."""

    queryset = Source.objects.filter(is_active=True).order_by("name")
    serializer_class = SourceSerializer
    pagination_class = None  # small dataset, return all

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Sources"])
class SourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/jobs/sources/<slug>/ — Source detail."""

    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsAdminRole()]
        return [AllowAny()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return Response(
            {"success": True, "data": None, "message": "Source deactivated.", "errors": None}
        )


# ── Tags ───────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Tags"])
class TagListView(generics.ListCreateAPIView):
    """GET /api/v1/jobs/tags/ — List tags. POST — Create (admin)."""

    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "category"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]

    def perform_create(self, serializer):
        from apps.core.utils import make_unique_slug
        name = serializer.validated_data["name"]
        slug = make_unique_slug(Tag, name)
        serializer.save(slug=slug)


@extend_schema(tags=["Tags"])
class TagDetailView(generics.RetrieveDestroyAPIView):
    """GET/DELETE /api/v1/jobs/tags/<slug>/ — Tag detail."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAdminRole()]
        return [AllowAny()]


# ── Jobs ───────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Jobs"])
class JobListView(generics.ListCreateAPIView):
    """
    GET /api/v1/jobs/
    List active jobs with full filtering, search, ordering, pagination.

    Filters: q, work_mode, industry, seniority, location, company, tag, salary_min, salary_max
    Ordering: posted_at, salary_min, salary_max, title (prefix with - to reverse)
    """

    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = JobFilter
    ordering_fields = ["posted_at", "salary_min", "salary_max", "title", "created_at"]
    ordering = ["-posted_at"]

    def get_queryset(self):
        qs = (
            Job.objects.filter(status="active")
            .select_related("company", "source")
            .prefetch_related("tags", "saves")
        )
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return JobWriteSerializer
        return JobListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        # Emit SEARCH_PERFORMED event
        try:
            q = request.query_params.get("q", "")
            emit(
                event_type=SEARCH_PERFORMED,
                category="search",
                user=request.user if request.user.is_authenticated else None,
                target_type="search",
                target_id="job_search",
                data={"query": q, "filters": {k: v for k, v in request.query_params.items() if k != "q"}},
                request=request,
            )
        except Exception:
            pass
        
        # Log search analytics
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page is not None:
            response = self.get_paginated_response(serializer.data)
        else:
            response = Response({"success": True, "data": serializer.data, "message": "", "errors": None})

        # Async-safe analytics log (fire and forget)
        try:
            q = request.query_params.get("q", "")
            if q:
                from apps.analytics.models import SearchLog
                SearchLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    query=q,
                    filters={k: v for k, v in request.query_params.items() if k != "q"},
                    results_count=queryset.count(),
                    session_key=request.session.session_key or "",
                )
        except Exception:
            pass

        return response

    def create(self, request, *args, **kwargs):
        serializer = JobWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        out = JobDetailSerializer(job, context={"request": request})
        return Response(
            {"success": True, "data": out.data, "message": "Job created.", "errors": None},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Jobs"])
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/jobs/<slug>/ — Job detail with view tracking."""

    queryset = Job.objects.select_related("company", "source").prefetch_related(
        "tags", "also_on_sources", "saves"
    )
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return JobWriteSerializer
        return JobDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsAdminRole()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Emit JOB_VIEWED event
        try:
            emit(
                event_type=JOB_VIEWED,
                category="job",
                user=request.user if request.user.is_authenticated else None,
                target_type="job",
                target_id=str(instance.id),
                data={"source": "job_detail"},
                request=request,
            )
        except Exception:
            pass
        # Track view
        try:
            from apps.analytics.models import JobView
            JobView.objects.create(
                job=instance,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or "",
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )
            Job.objects.filter(pk=instance.pk).update(view_count=instance.view_count + 1)
        except Exception:
            pass
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(
            {"success": True, "data": serializer.data, "message": "", "errors": None}
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = "archived"
        instance.save(update_fields=["status"])
        return Response(
            {"success": True, "data": None, "message": "Job archived.", "errors": None}
        )


@extend_schema(tags=["Jobs"])
class JobApplyView(APIView):
    """POST /api/v1/jobs/<slug>/apply/ — Track apply click and return the source URL."""

    permission_classes = [AllowAny]

    def post(self, request, slug):
        try:
            job = Job.objects.select_related("source").get(slug=slug, status="active")
        except Job.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "Job not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Emit JOB_APPLIED event
        try:
            emit(
                event_type=JOB_APPLIED,
                category="job",
                user=request.user if request.user.is_authenticated else None,
                target_type="job",
                target_id=str(job.id),
                data={"source": "job_apply_view"},
                request=request,
            )
        except Exception:
            pass
        # Track click
        try:
            from apps.analytics.models import JobClick
            JobClick.objects.create(
                job=job,
                source=job.source,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or "",
                ip_address=get_client_ip(request),
            )
            Job.objects.filter(pk=job.pk).update(click_count=job.click_count + 1)
        except Exception:
            pass
        return Response(
            {
                "success": True,
                "data": {"source_url": job.source_url},
                "message": "Redirect URL ready.",
                "errors": None,
            }
        )


@extend_schema(tags=["Jobs"])
class SimilarJobsView(generics.ListAPIView):
    """GET /api/v1/jobs/<slug>/similar/ — Get similar jobs."""

    serializer_class = JobListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        # Emit SEARCH_RESULT_CLICKED event
        try:
            job_slug = self.kwargs.get("slug")
            emit(
                event_type=SEARCH_RESULT_CLICKED,
                category="search",
                user=request.user if request.user.is_authenticated else None,
                target_type="job",
                target_id=job_slug,
                data={"source": "similar_jobs"},
                request=request,
            )
        except Exception:
            pass
        
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        slug = self.kwargs["slug"]
        try:
            job = Job.objects.get(slug=slug)
        except Job.DoesNotExist:
            return Job.objects.none()
        return (
            Job.objects.filter(status="active")
            .exclude(pk=job.pk)
            .filter(industry=job.industry)
            .select_related("company", "source")
            .prefetch_related("tags", "saves")[:6]
        )

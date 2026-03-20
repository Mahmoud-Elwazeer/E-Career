from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.core.models import FeatureFlag, ActivityLog, Media
from apps.core.serializers import FeatureFlagSerializer, ActivityLogSerializer, MediaSerializer
from apps.core.permissions import IsAdminRole
from apps.core.pagination import StandardPagination


@extend_schema(tags=["Feature Flags"])
class FeatureFlagListView(generics.ListAPIView):
    """List all feature flags."""

    permission_classes = [IsAdminRole]
    serializer_class = FeatureFlagSerializer
    queryset = FeatureFlag.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering = ["key"]
    pagination_class = None  # Return all flags (small dataset)


@extend_schema(tags=["Feature Flags"])
class FeatureFlagDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a feature flag."""

    permission_classes = [IsAdminRole]
    serializer_class = FeatureFlagSerializer
    queryset = FeatureFlag.objects.all()
    lookup_field = "uuid"


@extend_schema(tags=["Analytics"])
class ActivityLogListView(generics.ListAPIView):
    """List admin activity logs."""

    permission_classes = [IsAdminRole]
    serializer_class = ActivityLogSerializer
    queryset = ActivityLog.objects.select_related("user").all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["action", "target_type"]
    ordering = ["-created_at"]


@extend_schema(tags=["Analytics"])
class MediaListView(generics.ListCreateAPIView):
    """List or upload media files."""

    permission_classes = [IsAdminRole]
    serializer_class = MediaSerializer
    queryset = Media.objects.select_related("uploaded_by").all()
    pagination_class = StandardPagination
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        file = self.request.FILES.get("file")
        serializer.save(
            uploaded_by=self.request.user,
            filename=file.name if file else "",
            size=file.size if file else 0,
            mime_type=file.content_type if file else "",
        )


@extend_schema(tags=["Analytics"])
class MediaDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or delete a media file."""

    permission_classes = [IsAdminRole]
    serializer_class = MediaSerializer
    queryset = Media.objects.all()
    lookup_field = "uuid"

import logging
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.users.models import SavedJob, Alert
from apps.notifications.models import UserNotification
from apps.users.serializers import SavedJobSerializer, AlertSerializer, NotificationSerializer
from apps.core.pagination import StandardPagination

logger = logging.getLogger(__name__)


# ── Saved Jobs ────────────────────────────────────────────────────────────────

@extend_schema(tags=["Saved Jobs"])
class SavedJobListView(generics.ListCreateAPIView):
    """GET /api/v1/users/me/saved-jobs/ — List or save jobs."""

    permission_classes = [IsAuthenticated]
    serializer_class = SavedJobSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            SavedJob.objects.filter(user=self.request.user)
            .select_related("job", "job__company", "job__source")
            .prefetch_related("job__tags")
            .order_by("-saved_at")
        )

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            saved_job = serializer.save()
            out = SavedJobSerializer(saved_job, context={"request": request})
            return Response(
                {"success": True, "data": out.data, "message": "Job saved.", "errors": None},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"success": False, "data": None, "message": str(e), "errors": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["Saved Jobs"])
class SavedJobDetailView(generics.DestroyAPIView):
    """DELETE /api/v1/users/me/saved-jobs/<pk>/ — Unsave a job."""

    permission_classes = [IsAuthenticated]
    serializer_class = SavedJobSerializer

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": True, "data": None, "message": "Job removed from saved.", "errors": None}
        )


# ── Alerts ────────────────────────────────────────────────────────────────────

@extend_schema(tags=["Alerts"])
class AlertListView(generics.ListCreateAPIView):
    """GET/POST /api/v1/users/me/alerts/ — List or create job alerts."""

    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = serializer.save(user=request.user)
        out = AlertSerializer(alert)
        return Response(
            {"success": True, "data": out.data, "message": "Alert created.", "errors": None},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Alerts"])
class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/users/me/alerts/<uuid>/ — Manage a specific alert."""

    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": True, "data": None, "message": "Alert deleted.", "errors": None}
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


# ── Notifications ─────────────────────────────────────────────────────────────

@extend_schema(tags=["Notifications"])
class NotificationListView(generics.ListAPIView):
    """GET /api/v1/users/me/notifications/ — List user notifications."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by("-created_at")


@extend_schema(tags=["Notifications"])
class NotificationDetailView(APIView):
    """PATCH /api/v1/users/me/notifications/<uuid>/ — Mark a notification as read."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, uuid):
        try:
            notif = UserNotification.objects.get(uuid=uuid, user=request.user)
        except UserNotification.DoesNotExist:
            return Response(
                {"success": False, "data": None, "message": "Notification not found.", "errors": None},
                status=status.HTTP_404_NOT_FOUND,
            )
        notif.status = "read"
        notif.read_at = timezone.now()
        notif.save(update_fields=["status", "read_at"])
        return Response(
            {"success": True, "data": NotificationSerializer(notif).data, "message": "Marked as read.", "errors": None}
        )


@extend_schema(tags=["Notifications"])
class MarkAllNotificationsReadView(APIView):
    """POST /api/v1/users/me/notifications/mark-all-read/ — Mark all as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = UserNotification.objects.filter(
            user=request.user, status="unread"
        ).update(status="read", read_at=timezone.now())
        return Response(
            {"success": True, "data": {"marked_read": count}, "message": f"{count} notifications marked as read.", "errors": None}
        )

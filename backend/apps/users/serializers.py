from rest_framework import serializers
from apps.users.models import SavedJob, Alert
from apps.notifications.models import UserNotification
from apps.employers.models import JobApplication
from apps.jobs.serializers import JobListSerializer


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    job_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "job_id", "saved_at"]
        read_only_fields = ["id", "saved_at"]

    def validate_job_id(self, value):
        from apps.jobs.models import Job
        try:
            job = Job.objects.get(pk=value, status="active")
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found.")
        return value

    def create(self, validated_data):
        from apps.jobs.models import Job
        job = Job.objects.get(pk=validated_data["job_id"])
        user = self.context["request"].user
        saved_job, created = SavedJob.objects.get_or_create(user=user, job=job)
        if not created:
            raise serializers.ValidationError("Job is already saved.")
        return saved_job


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id", "uuid", "keyword", "work_mode", "industry",
            "frequency", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    body = serializers.CharField(source="message", read_only=True)
    type = serializers.CharField(source="notification_type", read_only=True)
    is_read = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = UserNotification
        fields = [
            "id", "uuid", "title", "body", "type",
            "is_read", "metadata", "created_at",
        ]
        read_only_fields = fields

    def get_is_read(self, obj):
        return obj.status != "unread"

    def get_metadata(self, obj):
        meta = {}
        if obj.related_id:
            meta["related_id"] = obj.related_id
        if obj.related_type:
            meta["related_type"] = obj.related_type
        if obj.related_url:
            meta["related_url"] = obj.related_url
        return meta or None


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications from the candidate's perspective"""
    job = JobListSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cv_url = serializers.SerializerMethodField()

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'status', 'status_display',
            'cv_snapshot', 'cv_url', 'custom_form_responses', 'applied_at'
        ]
        read_only_fields = fields

    def get_cv_url(self, obj):
        """Get CV URL if available"""
        if obj.cv_snapshot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cv_snapshot.url)
        return None

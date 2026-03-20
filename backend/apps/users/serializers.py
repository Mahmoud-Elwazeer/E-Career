from rest_framework import serializers
from apps.users.models import SavedJob, Alert, Notification
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
    class Meta:
        model = Notification
        fields = [
            "id", "uuid", "title", "body", "type",
            "is_read", "metadata", "created_at",
        ]
        read_only_fields = fields

from rest_framework import serializers
from apps.core.models import FeatureFlag, ActivityLog, Media


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ["id", "uuid", "key", "label", "description", "is_enabled", "metadata", "updated_at"]
        read_only_fields = ["id", "uuid", "key", "updated_at"]


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)

    class Meta:
        model = ActivityLog
        fields = ["id", "user_email", "action", "target_type", "target_id", "metadata", "created_at"]
        read_only_fields = fields


class MediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True, allow_null=True)

    class Meta:
        model = Media
        fields = ["id", "uuid", "filename", "file", "url", "size", "mime_type", "uploaded_by_email", "created_at"]
        read_only_fields = ["id", "uuid", "url", "uploaded_by_email", "created_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

from rest_framework import serializers
from apps.jobs.models import Company, Source, Tag, Job, JobTag


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id", "uuid", "name", "slug", "logo_url", "snippet",
            "about", "industry", "website", "is_active", "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]


class CompanyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["name", "slug", "logo_url", "snippet", "about", "industry", "website", "is_active"]

    def validate_name(self, value):
        from apps.core.utils import make_unique_slug
        if not self.instance:
            self.initial_data["slug"] = make_unique_slug(Company, value)
        return value


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "uuid", "name", "slug", "url", "logo_url", "type", "is_active", "created_at"]
        read_only_fields = ["id", "uuid", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "uuid", "name", "slug", "category", "created_at"]
        read_only_fields = ["id", "uuid", "slug", "created_at"]


class JobListSerializer(serializers.ModelSerializer):
    """Compact serializer for job list views."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_logo = serializers.CharField(source="company.logo_url", read_only=True)
    company_slug = serializers.SlugField(source="company.slug", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True, allow_null=True)
    source_logo = serializers.CharField(source="source.logo_url", read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "uuid", "title", "slug",
            "company_name", "company_logo", "company_slug",
            "location", "location_type", "industry", "experience_level",
            "salary_min", "salary_max", "salary_currency",
            "tags", "source_name", "source_logo", "source_url",
            "posted_at", "deadline", "status", "is_saved",
        ]
        read_only_fields = fields

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.saves.filter(user=request.user).exists()


class JobDetailSerializer(serializers.ModelSerializer):
    """Full serializer for job detail view."""

    company = CompanySerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    also_on_sources = SourceSerializer(many=True, read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "uuid", "title", "slug",
            "company", "location", "location_type",
            "industry", "experience_level", "description",
            "tags", "salary_min", "salary_max", "salary_currency",
            "source", "also_on_sources", "source_url",
            "posted_at", "deadline", "status",
            "view_count", "click_count", "is_saved",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.saves.filter(user=request.user).exists()


class JobWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating jobs (admin)."""

    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    also_on_source_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Job
        fields = [
            "title", "slug", "company", "location", "location_type",
            "industry", "experience_level", "description",
            "salary_min", "salary_max", "salary_currency",
            "source", "source_url", "posted_at", "deadline", "status",
            "tag_ids", "also_on_source_ids",
        ]

    def validate_title(self, value):
        from apps.core.utils import make_unique_slug
        if not self.instance:
            self.initial_data["slug"] = make_unique_slug(Job, value)
        return value

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        also_on_ids = validated_data.pop("also_on_source_ids", [])
        job = Job.objects.create(**validated_data)
        if tag_ids:
            tags = Tag.objects.filter(pk__in=tag_ids)
            for tag in tags:
                JobTag.objects.get_or_create(job=job, tag=tag)
        if also_on_ids:
            from apps.jobs.models import JobAlsoOnSource
            sources = Source.objects.filter(pk__in=also_on_ids)
            for src in sources:
                JobAlsoOnSource.objects.get_or_create(job=job, source=src)
        return job

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        also_on_ids = validated_data.pop("also_on_source_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            JobTag.objects.filter(job=instance).delete()
            tags = Tag.objects.filter(pk__in=tag_ids)
            for tag in tags:
                JobTag.objects.get_or_create(job=instance, tag=tag)
        if also_on_ids is not None:
            from apps.jobs.models import JobAlsoOnSource
            JobAlsoOnSource.objects.filter(job=instance).delete()
            sources = Source.objects.filter(pk__in=also_on_ids)
            for src in sources:
                JobAlsoOnSource.objects.get_or_create(job=instance, source=src)
        return instance

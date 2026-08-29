from datetime import datetime, time, timezone

from rest_framework import serializers
from django.contrib.humanize.templatetags.humanize import naturaltime
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
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Company
        fields = ["name", "slug", "logo_url", "snippet", "about", "industry", "website", "is_active"]

    def validate(self, attrs):
        from apps.core.utils import make_unique_slug
        if not self.instance and not attrs.get("slug"):
            attrs["slug"] = make_unique_slug(Company, attrs["name"])
        return attrs


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
    match_score = serializers.SerializerMethodField()
    salary_display = serializers.SerializerMethodField()
    posted_ago = serializers.SerializerMethodField()
    employment_type = serializers.CharField(read_only=True, allow_null=True)
    legitimacy_score = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Job
        fields = [
            "id", "uuid", "title", "slug",
            "company_name", "company_logo", "company_slug",
            "location", "location_type", "industry", "experience_level",
            "salary_min", "salary_max", "salary_currency", "salary_display",
            "tags", "source_name", "source_logo", "source_url",
            "posted_at", "posted_ago", "deadline", "status", "is_saved",
            "match_score", "employment_type", "legitimacy_score",
            "work_arrangement",
        ]
        read_only_fields = fields

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.saves.filter(user=request.user).exists()

    def get_match_score(self, obj):
        """Calculate job match percentage for authenticated users with profiles"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            from apps.profiles.models import UserProfile
            profile = request.user.userprofile
            from apps.profiles.services import MatchingService
            matcher = MatchingService()
            score = matcher.calculate_match_score(profile, obj)
            return round(score, 1)
        except Exception:
            return None

    def get_salary_display(self, obj):
        """Format salary for display"""
        if not obj.salary_min and not obj.salary_max:
            return None
        
        currency = obj.salary_currency or 'EGP'
        
        if obj.salary_min and obj.salary_max:
            return f"{currency} {obj.salary_min:,.0f} - {obj.salary_max:,.0f}"
        elif obj.salary_min:
            return f"{currency} {obj.salary_min:,.0f}+"
        elif obj.salary_max:
            return f"Up to {currency} {obj.salary_max:,.0f}"
        return None

    def get_posted_ago(self, obj):
        """Human-readable time since posting"""
        if obj.posted_at:
            dt = datetime.combine(obj.posted_at, time.min, tzinfo=timezone.utc)
            return naturaltime(dt)
        return None


class JobDetailSerializer(serializers.ModelSerializer):
    """Full serializer for job detail view."""

    company = CompanySerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    also_on_sources = SourceSerializer(many=True, read_only=True)
    is_saved = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    match_breakdown = serializers.SerializerMethodField()
    salary_display = serializers.SerializerMethodField()
    posted_ago = serializers.SerializerMethodField()
    similar_jobs = serializers.SerializerMethodField()
    employment_type = serializers.CharField(read_only=True, allow_null=True)
    legitimacy_score = serializers.FloatField(read_only=True, allow_null=True)
    legitimacy_flags = serializers.JSONField(read_only=True)
    direct_apply_url = serializers.URLField(read_only=True, allow_blank=True)
    apply_url_verified = serializers.BooleanField(read_only=True)
    custom_form_fields = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "uuid", "title", "slug",
            "company", "location", "location_type",
            "industry", "experience_level", "description",
            "tags", "salary_min", "salary_max", "salary_currency", "salary_display",
            "source", "also_on_sources", "source_url", "direct_apply_url", "apply_url_verified",
            "posted_at", "posted_ago", "deadline", "status",
            "view_count", "click_count", "is_saved",
            "match_score", "match_breakdown", "similar_jobs",
            "employment_type", "legitimacy_score", "legitimacy_flags",
            "custom_form_fields", "work_arrangement",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.saves.filter(user=request.user).exists()

    def get_match_score(self, obj):
        """Calculate job match percentage for authenticated users with profiles"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            from apps.profiles.models import UserProfile
            profile = request.user.userprofile
            from apps.profiles.services import MatchingService
            matcher = MatchingService()
            score = matcher.calculate_match_score(profile, obj)
            return round(score, 1)
        except Exception:
            return None

    def get_match_breakdown(self, obj):
        """Detailed breakdown of match score"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            from apps.profiles.models import UserProfile
            profile = request.user.userprofile
            from apps.profiles.services import MatchingService
            matcher = MatchingService()
            breakdown = matcher.get_match_breakdown(profile, obj)
            return breakdown
        except Exception:
            return None

    def get_salary_display(self, obj):
        """Format salary for display"""
        if not obj.salary_min and not obj.salary_max:
            return None
        
        currency = obj.salary_currency or 'EGP'
        
        if obj.salary_min and obj.salary_max:
            return f"{currency} {obj.salary_min:,.0f} - {obj.salary_max:,.0f}"
        elif obj.salary_min:
            return f"{currency} {obj.salary_min:,.0f}+"
        elif obj.salary_max:
            return f"Up to {currency} {obj.salary_max:,.0f}"
        return None

    def get_posted_ago(self, obj):
        """Human-readable time since posting"""
        if obj.posted_at:
            dt = datetime.combine(obj.posted_at, time.min, tzinfo=timezone.utc)
            return naturaltime(dt)
        return None

    def get_similar_jobs(self, obj):
        """Get 5 similar jobs based on industry and tags"""
        similar = Job.objects.filter(
            status="active"
        ).filter(
            industry=obj.industry
        ).exclude(
            id=obj.id
        ).select_related(
            "company", "source"
        ).prefetch_related("tags")[:5]

        return JobListSerializer(
            similar,
            many=True,
            context=self.context
        ).data

    def get_custom_form_fields(self, obj):
        """Get custom application form fields from linked employer posting."""
        try:
            if hasattr(obj, 'employer_posting') and obj.employer_posting:
                return obj.employer_posting.custom_form_fields or []
        except Exception:
            pass
        return []


class JobWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating jobs (admin)."""

    slug = serializers.SlugField(required=False, allow_blank=True)
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
            "employment_type", "work_arrangement",
            "tag_ids", "also_on_source_ids",
        ]

    def validate(self, attrs):
        from apps.core.utils import make_unique_slug
        if not self.instance and not attrs.get("slug"):
            attrs["slug"] = make_unique_slug(Job, attrs["title"])
        return attrs

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

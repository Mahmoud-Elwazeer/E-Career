from __future__ import annotations

from rest_framework import serializers


class JobSearchQuerySerializer(serializers.Serializer):
    """Validates incoming search requests."""

    q = serializers.CharField(required=False, default="", allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    location_type = serializers.CharField(required=False, allow_blank=True)
    work_arrangement = serializers.CharField(required=False, allow_blank=True)
    experience_level = serializers.CharField(required=False, allow_blank=True)
    employment_type = serializers.CharField(required=False, allow_blank=True)
    salary_min = serializers.IntegerField(required=False, min_value=0)
    salary_max = serializers.IntegerField(required=False, min_value=0)
    company_name = serializers.CharField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.CharField(required=False, allow_blank=True)
    sort_by = serializers.ChoiceField(
        required=False,
        choices=[
            ("relevance", "Relevance"),
            ("posted_at_timestamp:desc", "Newest First"),
            ("posted_at_timestamp:asc", "Oldest First"),
            ("salary_max:desc", "Highest Salary"),
        ],
        default="relevance",
    )
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    per_page = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)


class SearchResultSerializer(serializers.Serializer):
    """Serializes a single search result."""

    id = serializers.CharField()
    score = serializers.FloatField()
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    company_slug = serializers.SerializerMethodField()
    company_logo_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    location_type = serializers.SerializerMethodField()
    work_arrangement = serializers.SerializerMethodField()
    experience_level = serializers.SerializerMethodField()
    employment_type = serializers.SerializerMethodField()
    salary_min = serializers.SerializerMethodField()
    salary_max = serializers.SerializerMethodField()
    salary_currency = serializers.SerializerMethodField()
    direct_apply_url = serializers.SerializerMethodField()
    posted_at = serializers.SerializerMethodField()
    highlights = serializers.DictField(child=serializers.CharField(), default={})

    def _get_data_field(self, obj, field, default=""):
        return obj.data.get(field, default)

    def get_title(self, obj):
        return self._get_data_field(obj, "title")

    def get_slug(self, obj):
        return self._get_data_field(obj, "slug")

    def get_company_name(self, obj):
        return self._get_data_field(obj, "company_name")

    def get_company_slug(self, obj):
        return self._get_data_field(obj, "company_slug")

    def get_company_logo_url(self, obj):
        return self._get_data_field(obj, "company_logo_url")

    def get_location(self, obj):
        return self._get_data_field(obj, "location")

    def get_location_type(self, obj):
        return self._get_data_field(obj, "location_type")

    def get_work_arrangement(self, obj):
        return self._get_data_field(obj, "work_arrangement")

    def get_experience_level(self, obj):
        return self._get_data_field(obj, "experience_level")

    def get_employment_type(self, obj):
        return self._get_data_field(obj, "employment_type")

    def get_salary_min(self, obj):
        return self._get_data_field(obj, "salary_min")

    def get_salary_max(self, obj):
        return self._get_data_field(obj, "salary_max")

    def get_salary_currency(self, obj):
        return self._get_data_field(obj, "salary_currency")

    def get_direct_apply_url(self, obj):
        return self._get_data_field(obj, "direct_apply_url")

    def get_posted_at(self, obj):
        return self._get_data_field(obj, "posted_at")


class FacetCountSerializer(serializers.Serializer):
    value = serializers.CharField()
    count = serializers.IntegerField()


class SearchResponseSerializer(serializers.Serializer):
    """Serializes the full search response."""

    hits = SearchResultSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    per_page = serializers.IntegerField()
    facets = serializers.DictField(child=FacetCountSerializer(many=True))
    query_time_ms = serializers.IntegerField()

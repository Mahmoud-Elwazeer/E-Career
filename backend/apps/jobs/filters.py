import django_filters
from apps.jobs.models import Job


class JobFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_search", label="Search query")
    work_mode = django_filters.CharFilter(field_name="location_type", lookup_expr="exact")
    industry = django_filters.CharFilter(field_name="industry", lookup_expr="exact")
    seniority = django_filters.CharFilter(field_name="experience_level", lookup_expr="exact")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    company = django_filters.CharFilter(field_name="company__slug", lookup_expr="exact")
    tag = django_filters.CharFilter(method="filter_tag", label="Tag slug")
    salary_min = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    salary_max = django_filters.NumberFilter(field_name="salary_max", lookup_expr="lte")
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")

    class Meta:
        model = Job
        fields = ["work_mode", "industry", "seniority", "status"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(location__icontains=value)
            | Q(company__name__icontains=value)
        )

    def filter_tag(self, queryset, name, value):
        return queryset.filter(tags__slug=value)

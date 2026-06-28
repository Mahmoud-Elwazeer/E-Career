import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import Job


class JobFilter(django_filters.FilterSet):
    """Advanced filtering for job listings"""
    
    # Text search
    q = django_filters.CharFilter(method="filter_search", label="Search query")
    
    # Location
    work_mode = django_filters.CharFilter(field_name="location_type", lookup_expr="exact")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    location_in = django_filters.CharFilter(method="filter_location_in", label="Multiple locations")
    
    # Category/Industry
    industry = django_filters.CharFilter(field_name="industry", lookup_expr="exact")
    
    # Experience
    seniority = django_filters.CharFilter(field_name="experience_level", lookup_expr="exact")
    
    # Employment type
    employment_type = django_filters.MultipleChoiceFilter(
        field_name="employment_type",
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('freelance', 'Freelance'),
        ]
    )
    
    # Company
    company = django_filters.CharFilter(field_name="company__slug", lookup_expr="exact")
    
    # Tags
    tag = django_filters.CharFilter(method="filter_tag", label="Tag slug")
    tags = django_filters.CharFilter(method="filter_tags", label="Multiple tags")
    
    # Salary
    salary_min = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    salary_max = django_filters.NumberFilter(field_name="salary_max", lookup_expr="lte")
    has_salary = django_filters.BooleanFilter(method="filter_has_salary", label="Has salary info")
    
    # Date posted
    posted_within = django_filters.NumberFilter(method="filter_posted_within", label="Days since posted")
    
    # Status
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")
    
    # Legitimacy
    min_legitimacy = django_filters.NumberFilter(field_name="legitimacy_score", lookup_expr="gte")

    class Meta:
        model = Job
        fields = ["work_mode", "industry", "seniority", "status", "employment_type"]

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields"""
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(location__icontains=value)
            | Q(company__name__icontains=value)
        )

    def filter_tag(self, queryset, name, value):
        """Filter by single tag slug"""
        return queryset.filter(tags__slug=value)

    def filter_tags(self, queryset, name, value):
        """Filter by multiple tags (comma-separated)"""
        tags = [tag.strip() for tag in value.split(',')]
        for tag in tags:
            queryset = queryset.filter(tags__slug__icontains=tag)
        return queryset

    def filter_location_in(self, queryset, name, value):
        """Filter by multiple locations (comma-separated)"""
        locations = [loc.strip() for loc in value.split(',')]
        query = Q()
        for loc in locations:
            query |= Q(location__icontains=loc)
        return queryset.filter(query)

    def filter_has_salary(self, queryset, name, value):
        """Filter jobs that have salary information"""
        if value:
            return queryset.filter(
                Q(salary_min__isnull=False) | Q(salary_max__isnull=False)
            )
        return queryset.filter(salary_min__isnull=True, salary_max__isnull=True)

    def filter_posted_within(self, queryset, name, value):
        """Filter jobs posted within N days"""
        cutoff_date = timezone.now() - timedelta(days=value)
        # Convert to date for comparison with posted_at (DateField)
        cutoff_date = cutoff_date.date()
        return queryset.filter(posted_at__gte=cutoff_date)

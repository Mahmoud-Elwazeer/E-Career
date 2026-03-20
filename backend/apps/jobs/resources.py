"""
Import/Export resources for Job model.
Supports CSV and XLSX with smart field handling:
- company_name → auto-creates Company if not found
- source_name → looks up Source by name
- tags → comma-separated tag names, auto-creates if not found
- slug → auto-generated from title if blank
"""
import logging
from import_export import resources, fields, widgets
from django.utils.text import slugify
from .models import Job, Company, Source, Tag, JobTag

logger = logging.getLogger(__name__)


class CompanyWidget(widgets.ForeignKeyWidget):
    """Look up Company by name; auto-create if not found."""

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        value = str(value).strip()
        company, created = Company.objects.get_or_create(
            name__iexact=value,
            defaults={
                "name": value,
                "slug": slugify(value) or f"company-{Company.objects.count() + 1}",
                "industry": row.get("industry", "other") if row else "other",
            },
        )
        if created:
            logger.info(f"Auto-created company: {company.name}")
        return company


class SourceWidget(widgets.ForeignKeyWidget):
    """Look up Source by name; skip if not found."""

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        value = str(value).strip()
        try:
            return Source.objects.get(name__iexact=value)
        except Source.DoesNotExist:
            return None


class JobResource(resources.ModelResource):
    """
    Smart import/export resource for Job listings.

    CSV/XLSX columns:
        title           (required) — Job title
        company_name    (required) — Company name (auto-created if new)
        location        (required) — e.g. "Cairo, Egypt" or "Remote"
        location_type   (required) — remote | onsite | hybrid
        industry        (required) — technology | finance | healthcare | education | marketing | engineering | design | sales | other
        experience_level(required) — entry | mid | senior | lead
        description     (required) — Job description (supports multiline)
        source_url      (required) — Link to original job posting
        posted_at       (required) — Date: YYYY-MM-DD
        status                     — active | pending | archived (default: active)
        salary_min                 — Minimum salary (number)
        salary_max                 — Maximum salary (number)
        salary_currency            — e.g. USD, EGP (default: USD)
        source_name                — Source site name (must already exist)
        tags                       — Comma-separated: "Python, Django, REST API"
        deadline                   — Deadline date: YYYY-MM-DD
        slug                       — Auto-generated from title if blank
    """

    company_name = fields.Field(
        column_name="company_name",
        attribute="company",
        widget=CompanyWidget(Company, field="name"),
    )
    source_name = fields.Field(
        column_name="source_name",
        attribute="source",
        widget=SourceWidget(Source, field="name"),
    )
    tags = fields.Field(column_name="tags", attribute=None)

    class Meta:
        model = Job
        import_id_fields = ["slug"]
        fields = (
            "title",
            "slug",
            "company_name",
            "location",
            "location_type",
            "industry",
            "experience_level",
            "description",
            "salary_min",
            "salary_max",
            "salary_currency",
            "source_url",
            "source_name",
            "posted_at",
            "deadline",
            "status",
            "tags",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Auto-generate slug from title if not provided."""
        title = row.get("title", "")
        slug = row.get("slug", "")
        if not slug and title:
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            row["slug"] = slug

        # Default status to active
        if not row.get("status"):
            row["status"] = "active"

        # Default currency
        if not row.get("salary_currency"):
            row["salary_currency"] = "USD"

    def after_save_instance(self, instance, row, **kwargs):
        """Handle tags after the job is saved."""
        tags_str = row.get("tags", "")
        if not tags_str:
            return

        tag_names = [t.strip() for t in str(tags_str).split(",") if t.strip()]
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name__iexact=tag_name,
                defaults={
                    "name": tag_name,
                    "slug": slugify(tag_name) or f"tag-{Tag.objects.count() + 1}",
                    "category": "general",
                },
            )
            JobTag.objects.get_or_create(job=instance, tag=tag)

    def dehydrate_tags(self, job):
        """Export tags as comma-separated string."""
        return ", ".join(job.tags.values_list("name", flat=True))

    def dehydrate_company_name(self, job):
        """Export company name."""
        return job.company.name if job.company else ""

    def dehydrate_source_name(self, job):
        """Export source name."""
        return job.source.name if job.source else ""

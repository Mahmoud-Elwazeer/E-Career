from django.db import models


class JobView(models.Model):
    """Tracks every time a job detail page is viewed."""

    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="views",
        db_index=True,
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_views",
        db_index=True,
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_jobview"
        ordering = ["-viewed_at"]
        verbose_name = "Job View"
        verbose_name_plural = "Job Views"

    def __str__(self):
        return f"View: {self.job.title} at {self.viewed_at}"


class JobClick(models.Model):
    """Tracks every time a user clicks 'Apply Now' on a job."""

    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="clicks",
        db_index=True,
    )
    source = models.ForeignKey(
        "jobs.Source",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clicks",
        db_index=True,
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_clicks",
        db_index=True,
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_jobclick"
        ordering = ["-clicked_at"]
        verbose_name = "Job Click"
        verbose_name_plural = "Job Clicks"

    def __str__(self):
        return f"Click: {self.job.title} at {self.clicked_at}"


class SearchLog(models.Model):
    """Logs every search query with filters and result count."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="search_logs",
        db_index=True,
    )
    query = models.CharField(max_length=500, blank=True, db_index=True)
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    session_key = models.CharField(max_length=64, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_searchlog"
        ordering = ["-searched_at"]
        verbose_name = "Search Log"
        verbose_name_plural = "Search Logs"

    def __str__(self):
        return f'Search: "{self.query}" ({self.results_count} results)'

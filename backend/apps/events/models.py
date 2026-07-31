from django.db import models
from django.conf import settings


class EventLog(models.Model):
    """
    Append-only event log. Partitioned by month for performance.
    Every significant user/system action produces an event.
    Events feed: analytics, recommendations, scoring, notifications.
    """

    EVENT_CATEGORIES = [
        ("user", "User Action"),
        ("job", "Job Action"),
        ("search", "Search Action"),
        ("ai", "AI Action"),
        ("employer", "Employer Action"),
        ("system", "System Event"),
    ]

    id = models.BigAutoField(primary_key=True)

    event_type = models.CharField(max_length=50, db_index=True)
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )

    # Target entity
    target_type = models.CharField(max_length=50, blank=True, db_index=True)
    target_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Event payload
    data = models.JSONField(default=dict)

    # Request context
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "events_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["user", "event_type", "created_at"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["category", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} by user={self.user_id} at {self.created_at}"

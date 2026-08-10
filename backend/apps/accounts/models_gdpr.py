"""
GDPR Compliance Models - Data export and account deletion
"""
from django.db import models
from django.conf import settings
from apps.core.models import UUIDModel


class DataExportRequest(UUIDModel):
    """
    User request for GDPR data export (Article 15 - Right to Access).

    When a user requests their data, a Celery task generates a JSON export
    containing all their personal data, which they can download for 30 days.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='data_export_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated export file (S3 or local media)"
    )
    file_size_bytes = models.BigIntegerField(
        default=0,
        help_text="Size of export file in bytes"
    )
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Export file deleted after 30 days"
    )
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of requester (for audit)"
    )

    class Meta:
        db_table = 'accounts_data_export_request'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.requested_at.strftime('%Y-%m-%d')}"


class AccountDeletionRequest(UUIDModel):
    """
    User request for account deletion (Article 17 - Right to Erasure).

    Implements soft delete with grace period. User has 30 days to cancel.
    After 30 days, PII is anonymized and account is marked as deleted.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending (30-day grace period)'),
        ('cancelled', 'Cancelled by user'),
        ('processing', 'Processing deletion'),
        ('completed', 'Completed (anonymized)'),
        ('failed', 'Failed'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='deletion_request'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    reason = models.TextField(
        blank=True,
        help_text="Optional reason for deletion (for analytics)"
    )
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    scheduled_for = models.DateTimeField(
        help_text="Date when deletion will be executed (30 days from request)"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'accounts_deletion_request'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.requested_at.strftime('%Y-%m-%d')}"

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


def avatar_upload_path(instance, filename):
    return f"avatars/{instance.uuid}/{filename}"


class User(AbstractUser):
    """
    Custom user model using email as the primary login identifier.
    Extends AbstractUser with UUID, role, status, and soft-delete fields.
    """

    class Role(models.TextChoices):
        JOBSEEKER = "jobseeker", "Job Seeker"
        EMPLOYER = "employer", "Employer"
        ADMIN = "admin", "Admin"
        # Legacy
        USER = "user", "User"  # Deprecated: default to jobseeker

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        BANNED = "banned", "Banned"

    # Remove username from AbstractUser — use email as identifier
    username = None

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.JOBSEEKER, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()
    all_objects = models.Manager() 

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["is_deleted", "deleted_at", "is_active"])

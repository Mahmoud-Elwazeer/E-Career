"""
Extension Token Auth (Item 5.4)

Scoped, revocable tokens for the browser extension.
These are separate from JWT session tokens — they have limited scope
and can be individually revoked.
"""
import secrets
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def _generate_token():
    return f"eck_{secrets.token_urlsafe(32)}"


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


class ExtensionToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extension_tokens',
    )
    name = models.CharField(max_length=100, help_text="User-chosen label, e.g. 'Chrome on laptop'")
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    token_prefix = models.CharField(max_length=12, help_text="First 8 chars for identification")
    scopes = models.JSONField(
        default=list,
        help_text="Allowed scopes: profile_read, jobs_read, autofill_log",
    )
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'
        db_table = 'accounts_extensiontoken'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.token_prefix}...)"

    @classmethod
    def create_token(cls, user, name: str, scopes: list[str] | None = None, days_valid: int = 90):
        raw_token = _generate_token()
        token = cls.objects.create(
            user=user,
            name=name,
            token_hash=_hash_token(raw_token),
            token_prefix=raw_token[:12],
            scopes=scopes or ['profile_read', 'jobs_read', 'autofill_log'],
            expires_at=timezone.now() + timedelta(days=days_valid),
        )
        return token, raw_token

    def is_valid(self) -> bool:
        return self.is_active and self.expires_at > timezone.now()

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    def record_use(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class ExtensionTokenAuthentication(BaseAuthentication):
    keyword = 'ExtToken'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith(f'{self.keyword} '):
            return None

        raw_token = auth_header[len(self.keyword) + 1:]
        token_hash = _hash_token(raw_token)

        try:
            token = ExtensionToken.objects.select_related('user').get(token_hash=token_hash)
        except ExtensionToken.DoesNotExist:
            raise AuthenticationFailed('Invalid extension token')

        if not token.is_valid():
            raise AuthenticationFailed('Extension token expired or revoked')

        token.record_use()
        return (token.user, token)

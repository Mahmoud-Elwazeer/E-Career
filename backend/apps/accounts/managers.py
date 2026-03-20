from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import DjangoUnicodeDecodeError
from django.core.exceptions import ObjectDoesNotExist


class UserManager(BaseUserManager):
    """
    Custom manager for User model that uses email as the username field.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

    def get_user_from_reset_link(self, uid, token):
        """
        Validate the password reset token and return the user if valid.
        """
        token_generator = PasswordResetTokenGenerator()
        try:
            uid_decoded = urlsafe_base64_decode(uid).decode()
            user = self.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, DjangoUnicodeDecodeError, ObjectDoesNotExist):
            return None
        if user is not None and token_generator.check_token(user, token):
            return user
        return None

"""
Unit tests — serializers: validation, field checks, edge cases.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    UserMeSerializer,
)
from apps.jobs.serializers import JobListSerializer, JobWriteSerializer

User = get_user_model()


@pytest.mark.django_db
class TestRegisterSerializer:
    def _valid_data(self, **overrides):
        data = {
            "email": "newuser@gmail.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
        }
        data.update(overrides)
        return data

    def test_valid_registration(self):
        s = RegisterSerializer(data=self._valid_data())
        assert s.is_valid(), s.errors

    def test_passwords_must_match(self):
        s = RegisterSerializer(data=self._valid_data(password_confirm="WrongPass1!"))
        assert not s.is_valid()
        assert "password_confirm" in s.errors

    def test_email_is_normalized_to_lowercase(self):
        s = RegisterSerializer(data=self._valid_data(email="UPPER@Gmail.COM"))
        assert s.is_valid(), s.errors
        assert s.validated_data["email"] == "upper@gmail.com"

    def test_duplicate_email_is_rejected(self, user):
        s = RegisterSerializer(data=self._valid_data(email=user.email))
        assert not s.is_valid()
        assert "email" in s.errors

    def test_short_password_rejected(self):
        s = RegisterSerializer(data=self._valid_data(password="abc", password_confirm="abc"))
        assert not s.is_valid()
        assert "password" in s.errors

    def test_missing_first_name(self):
        data = self._valid_data()
        data.pop("first_name")
        s = RegisterSerializer(data=data)
        assert not s.is_valid()
        assert "first_name" in s.errors

    def test_missing_email(self):
        data = self._valid_data()
        data.pop("email")
        s = RegisterSerializer(data=data)
        assert not s.is_valid()
        assert "email" in s.errors

    def test_create_saves_user(self, db):
        s = RegisterSerializer(data=self._valid_data())
        assert s.is_valid()
        user = s.save()
        assert User.objects.filter(email="newuser@gmail.com").exists()
        assert user.check_password("StrongPass1!")

    def test_password_confirm_not_stored(self, db):
        s = RegisterSerializer(data=self._valid_data())
        assert s.is_valid()
        assert "password_confirm" not in s.validated_data


@pytest.mark.django_db
class TestLoginSerializer:
    def test_valid_login(self, user):
        s = LoginSerializer(data={"email": user.email, "password": "TestPass123!"})
        assert s.is_valid(), s.errors
        assert s.validated_data["user"] == user

    def test_wrong_password(self, user):
        s = LoginSerializer(data={"email": user.email, "password": "WrongPassword!"})
        assert not s.is_valid()

    def test_nonexistent_email(self, db):
        s = LoginSerializer(data={"email": "ghost@gmail.com", "password": "SomePass1!"})
        assert not s.is_valid()

    def test_inactive_user_rejected(self, user):
        user.is_active = False
        user.save()
        s = LoginSerializer(data={"email": user.email, "password": "TestPass123!"})
        assert not s.is_valid()

    def test_deleted_user_rejected(self, user):
        user.soft_delete()
        s = LoginSerializer(data={"email": user.email, "password": "TestPass123!"})
        assert not s.is_valid()

    def test_banned_user_rejected(self, user):
        user.status = "banned"
        user.save()
        s = LoginSerializer(data={"email": user.email, "password": "TestPass123!"})
        assert not s.is_valid()


@pytest.mark.django_db
class TestChangePasswordSerializer:
    def _make_request(self, user):
        from rest_framework.test import APIRequestFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = user
        return request

    def test_valid_change(self, user):
        request = self._make_request(user)
        s = ChangePasswordSerializer(
            data={
                "current_password": "TestPass123!",
                "new_password": "NewSecure99!",
                "new_password_confirm": "NewSecure99!",
            },
            context={"request": request},
        )
        assert s.is_valid(), s.errors

    def test_wrong_current_password(self, user):
        request = self._make_request(user)
        s = ChangePasswordSerializer(
            data={
                "current_password": "WrongCurrent!",
                "new_password": "NewSecure99!",
                "new_password_confirm": "NewSecure99!",
            },
            context={"request": request},
        )
        assert not s.is_valid()
        assert "current_password" in s.errors

    def test_new_passwords_mismatch(self, user):
        request = self._make_request(user)
        s = ChangePasswordSerializer(
            data={
                "current_password": "TestPass123!",
                "new_password": "NewSecure99!",
                "new_password_confirm": "DifferentPass99!",
            },
            context={"request": request},
        )
        assert not s.is_valid()
        assert "new_password_confirm" in s.errors


@pytest.mark.django_db
class TestJobListSerializer:
    def test_serializes_active_job(self, job):
        s = JobListSerializer(job)
        data = s.data
        assert data["title"] == job.title
        assert data["slug"] == job.slug
        assert data["company_name"] == job.company.name
        assert data["location_type"] == job.location_type
        assert "is_saved" in data

    def test_is_saved_false_for_unauthenticated(self, job):
        s = JobListSerializer(job, context={"request": None})
        assert s.data["is_saved"] is False

    def test_tags_list(self, job, tag):
        from apps.jobs.models import JobTag
        JobTag.objects.create(job=job, tag=tag)
        s = JobListSerializer(job)
        assert any(t["name"] == "Python" for t in s.data["tags"])

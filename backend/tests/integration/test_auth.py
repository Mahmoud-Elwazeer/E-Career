"""
Integration tests — auth endpoints: register, login, logout, token refresh,
password reset, /me/ GET/PATCH/DELETE, JWT guards.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegisterEndpoint:
    url = "/api/v1/auth/register/"

    def test_register_creates_user(self, api_client):
        resp = api_client.post(self.url, {
            "email": "newuser@gmail.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["success"] is True
        assert "access" in data["data"]
        assert "refresh" in data["data"]
        assert data["data"]["user"]["email"] == "newuser@gmail.com"
        assert User.objects.filter(email="newuser@gmail.com").exists()

    def test_register_duplicate_email(self, api_client, user):
        resp = api_client.post(self.url, {
            "email": user.email,
            "first_name": "Dupe",
            "last_name": "User",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["success"] is False

    def test_register_password_mismatch(self, api_client):
        resp = api_client.post(self.url, {
            "email": "mismatch@gmail.com",
            "first_name": "A",
            "last_name": "B",
            "password": "StrongPass1!",
            "password_confirm": "WrongPass1!",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, api_client):
        resp = api_client.post(self.url, {"email": "incomplete@gmail.com"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_not_in_response(self, api_client):
        resp = api_client.post(self.url, {
            "email": "safe@gmail.com",
            "first_name": "Safe",
            "last_name": "User",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
        })
        response_text = resp.content.decode()
        assert "StrongPass1!" not in response_text


@pytest.mark.django_db
class TestLoginEndpoint:
    url = "/api/v1/auth/login/"

    def test_login_returns_tokens(self, api_client, user):
        resp = api_client.post(self.url, {"email": user.email, "password": "TestPass123!"})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["success"] is True
        assert "access" in data["data"]
        assert "refresh" in data["data"]

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post(self.url, {"email": user.email, "password": "WrongPass!"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["success"] is False

    def test_login_unknown_email(self, api_client):
        resp = api_client.post(self.url, {"email": "ghost@gmail.com", "password": "SomePass1!"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_not_in_login_response(self, api_client, user):
        resp = api_client.post(self.url, {"email": user.email, "password": "TestPass123!"})
        assert "TestPass123!" not in resp.content.decode()


@pytest.mark.django_db
class TestTokenRefreshEndpoint:
    url = "/api/v1/auth/token/refresh/"

    def test_refresh_returns_new_access_token(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        resp = api_client.post(self.url, {"refresh": str(refresh)})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access" in data["data"]

    def test_refresh_with_invalid_token(self, api_client):
        resp = api_client.post(self.url, {"refresh": "not-a-valid-token"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_missing_token(self, api_client):
        resp = api_client.post(self.url, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogoutEndpoint:
    url = "/api/v1/auth/logout/"

    def test_logout_blacklists_token(self, auth_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        resp = auth_client.post(self.url, {"refresh": str(refresh)})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["success"] is True

    def test_logout_requires_authentication(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        resp = api_client.post(self.url, {"refresh": str(refresh)})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeEndpoint:
    url = "/api/v1/users/me/"

    def test_get_me_authenticated(self, auth_client, user):
        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["data"]["email"] == user.email

    def test_get_me_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_me_updates_name(self, auth_client, user):
        resp = auth_client.patch(self.url, {"first_name": "Updated"})
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_delete_me_soft_deletes(self, auth_client, user):
        resp = auth_client.delete(self.url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.is_deleted is True
        assert user.is_active is False

    def test_patch_cannot_change_role(self, auth_client, user):
        resp = auth_client.patch(self.url, {"role": "admin"})
        user.refresh_from_db()
        assert user.role == "user"

    def test_patch_cannot_change_email(self, auth_client, user):
        original_email = user.email
        resp = auth_client.patch(self.url, {"email": "hacker@gmail.com"})
        user.refresh_from_db()
        assert user.email == original_email


@pytest.mark.django_db
class TestPasswordResetEndpoint:
    request_url = "/api/v1/auth/password/reset/"
    confirm_url = "/api/v1/auth/password/reset/confirm/"

    def test_reset_request_always_returns_200(self, api_client):
        # Should not reveal whether email exists
        resp = api_client.post(self.request_url, {"email": "nonexistent@gmail.com"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["success"] is True

    def test_reset_request_for_existing_user(self, api_client, user):
        resp = api_client.post(self.request_url, {"email": user.email})
        assert resp.status_code == status.HTTP_200_OK

    def test_confirm_with_invalid_token(self, api_client):
        resp = api_client.post(self.confirm_url, {
            "uid": "invalid-uid",
            "token": "invalid-token",
            "new_password": "NewSecure99!",
            "new_password_confirm": "NewSecure99!",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_password_mismatch(self, api_client, user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        resp = api_client.post(self.confirm_url, {
            "uid": uid,
            "token": token,
            "new_password": "NewSecure99!",
            "new_password_confirm": "DifferentPass99!",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_valid_token_changes_password(self, api_client, user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        resp = api_client.post(self.confirm_url, {
            "uid": uid,
            "token": token,
            "new_password": "NewSecure99!",
            "new_password_confirm": "NewSecure99!",
        })
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewSecure99!")


@pytest.mark.django_db
class TestJWTGuards:
    def test_expired_token_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not.a.real.token")
        resp = api_client.get("/api/v1/users/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_token_returns_401(self, api_client):
        resp = api_client.get("/api/v1/users/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_wrong_role_returns_403(self, auth_client):
        resp = auth_client.get("/api/v1/analytics/stats/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

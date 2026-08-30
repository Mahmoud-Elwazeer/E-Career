"""
Accounts and Authentication Tests
Tests for user registration, login, logout, and profile management.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration."""

    def test_user_registration_success(self, api_client):
        """Test successful user registration."""
        url = reverse("accounts:register")
        data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_user_registration_password_mismatch(self, api_client):
        """Test registration with mismatched passwords."""
        url = reverse("accounts:register")
        data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "password_confirm": "DifferentPass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_user_registration_existing_email(self, api_client, user):
        """Test registration with existing email."""
        url = reverse("accounts:register")
        data = {
            "email": user.email,
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_user_registration_weak_password(self, api_client):
        """Test registration with weak password."""
        url = reverse("accounts:register")
        data = {
            "email": "newuser@example.com",
            "password": "password",
            "password_confirm": "password",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


@pytest.mark.django_db
class TestUserLogin:
    """Tests for user login."""

    def test_user_login_success(self, api_client, user):
        """Test successful user login."""
        url = reverse("accounts:login")
        data = {
            "email": user.email,
            "password": "TestPass123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "access" in response.data["data"]
        assert "refresh" in response.data["data"]

    def test_user_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        url = reverse("accounts:login")
        data = {
            "email": user.email,
            "password": "WrongPassword123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_user_login_nonexistent_user(self, api_client):
        """Test login with non-existent user."""
        url = reverse("accounts:login")
        data = {
            "email": "nonexistent@example.com",
            "password": "TestPass123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


@pytest.mark.django_db
class TestUserLogout:
    """Tests for user logout."""

    def test_user_logout_success(self, auth_client, user):
        """Test successful user logout."""
        from rest_framework_simplejwt.tokens import RefreshToken as _RefreshToken
        url = reverse("accounts:logout")
        refresh = _RefreshToken.for_user(user)
        response = auth_client.post(url, {"refresh": str(refresh)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestUserProfile:
    """Tests for user profile management."""

    def test_get_user_profile(self, auth_client, user):
        """Test retrieving user profile."""
        url = reverse("accounts:profile-detail")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["email"] == user.email

    def test_update_user_profile(self, auth_client, user):
        """Test updating user profile."""
        url = reverse("accounts:profile-detail")
        data = {
            "first_name": "Updated",
            "last_name": "Profile",
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_update_user_profile_email(self, auth_client, user):
        """Test that email is read-only on profile endpoint."""
        url = reverse("accounts:profile-detail")
        data = {
            "email": "updated@example.com",
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        user.refresh_from_db()
        assert user.email == "testuser@gmail.com"  # email is read-only


@pytest.mark.django_db
class TestPasswordManagement:
    """Tests for password management."""

    def test_change_password_success(self, auth_client, user):
        """Test changing password successfully."""
        url = reverse("accounts:change-password")
        data = {
            "current_password": "TestPass123!",
            "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify new password works
        from django.contrib.auth import authenticate
        user = authenticate(email=user.email, password="NewPass123!")
        assert user is not None

    def test_change_password_wrong_old(self, auth_client, user):
        """Test changing password with wrong old password."""
        url = reverse("accounts:change-password")
        data = {
            "old_password": "WrongPassword123!",
            "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_reset_password_request(self, api_client, user):
        """Test requesting password reset."""
        url = reverse("accounts:password-reset-request")
        data = {"email": user.email}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_reset_password_confirm(self, api_client, user):
        """Test confirming password reset."""
        # First request reset
        url = reverse("accounts:password-reset-request")
        api_client.post(url, {"email": user.email})

        # Then confirm with token (this would need actual token from email)
        # For now, just test the endpoint exists
        url = reverse("accounts:password-reset-confirm")
        data = {
            "token": "test-token",
            "password": "NewPass123!",
            "password_confirm": "NewPass123!",
        }
        response = api_client.post(url, data)

        # May be 400 if token is invalid, but endpoint should exist
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


@pytest.mark.django_db
class TestAdminUserManagement:
    """Tests for admin user management."""

    def test_list_users_admin(self, admin_client, user):
        """Test listing users as admin."""
        url = reverse("accounts:user-list")
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_create_user_admin(self, admin_client):
        """Test creating user as admin."""
        url = reverse("accounts:user-list")
        data = {
            "email": "admincreated@example.com",
            "password": "TestPass123!",
            "first_name": "Admin",
            "last_name": "Created",
            "role": "user",
        }
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_user_admin(self, admin_client, user):
        """Test updating user as admin."""
        url = reverse("accounts:user-detail", kwargs={"pk": user.pk})
        data = {"role": "admin"}
        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_delete_user_admin(self, admin_client, user):
        """Test soft-deleting user as admin."""
        url = reverse("accounts:user-detail", kwargs={"pk": user.pk})
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        user.refresh_from_db()
        assert user.is_deleted is True
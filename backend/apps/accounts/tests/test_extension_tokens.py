"""Tests for Extension Token auth (Phase 5.4)."""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestExtensionTokenLifecycle:
    def test_create_token(self, auth_client):
        url = reverse("accounts:extension-token-list")
        response = auth_client.post(url, {"name": "My Extension"})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data["data"]
        assert data["token"].startswith("eck_")
        assert data["name"] == "My Extension"

    def test_list_tokens_hides_raw(self, auth_client):
        url = reverse("accounts:extension-token-list")
        auth_client.post(url, {"name": "Token A"})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        tokens = response.data["data"]
        assert len(tokens) >= 1
        for t in tokens:
            assert "token" not in t
            assert "token_hash" not in t

    def test_revoke_token(self, auth_client):
        url = reverse("accounts:extension-token-list")
        create_resp = auth_client.post(url, {"name": "To Revoke"})
        token_id = create_resp.data["data"]["id"]
        revoke_url = reverse("accounts:extension-token-revoke", kwargs={"token_id": token_id})
        response = auth_client.delete(revoke_url)
        assert response.status_code == status.HTTP_200_OK

    def test_extension_profile_with_token(self, auth_client, user):
        create_url = reverse("accounts:extension-token-list")
        create_resp = auth_client.post(create_url, {"name": "For Profile"})
        raw_token = create_resp.data["data"]["token"]

        from rest_framework.test import APIClient
        ext_client = APIClient()
        ext_client.credentials(HTTP_AUTHORIZATION=f"ExtToken {raw_token}")
        profile_url = reverse("accounts:extension-profile")
        response = ext_client.get(profile_url)
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_create(self, api_client):
        url = reverse("accounts:extension-token-list")
        response = api_client.post(url, {"name": "Nope"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

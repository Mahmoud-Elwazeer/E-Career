"""Regression tests for the intelligence tool-registry endpoint.

Guards the frontend contract in `frontend/src/services/intelligence.ts`
(`listTools()` -> GET /api/v1/intelligence/tools/) which previously had no
backend route and would 404.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

User = get_user_model()


class PlatformToolsEndpointTests(APITestCase):
    def setUp(self):
        self.url = reverse("intelligence:platform-tools")
        self.user = User.objects.create_user(
            email="tools-user@example.com",
            password="pw-strong-123",
        )

    def test_requires_authentication(self):
        resp = self.client.get(self.url)
        self.assertIn(resp.status_code, (401, 403))

    def test_returns_tool_registry(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("tools", resp.data)
        tools = resp.data["tools"]
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        # Each tool matches the frontend PlatformTool shape {name, description}.
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)

    def test_registry_matches_rashid_tools(self):
        from apps.rashid.tools import RASHID_TOOLS

        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        names = {t["name"] for t in resp.data["tools"]}
        expected = {t.name for t in RASHID_TOOLS.values()}
        self.assertEqual(names, expected)

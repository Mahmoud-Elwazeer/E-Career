"""
API tests for the payments endpoints that don't require a live provider:
package listing, free-order checkout (immediate fulfillment), order status
ownership, and webhook dedup on unknown provider.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.payments.models import Package, Order

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="api@test.com", password="pw12345x")


@pytest.fixture
def auth_client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def test_packages_list_public():
    Package.objects.create(name="Free", slug="free", price_amount=0, currency="EGP", audience="individual")
    Package.objects.create(name="Pro", slug="pro", price_amount=10000, currency="EGP", audience="employer")
    resp = APIClient().get("/api/v1/payments/packages/?audience=employer")
    assert resp.status_code == 200
    payload = resp.json()["data"]
    # List endpoint is paginated -> {results: [...]}; tolerate a bare list too.
    items = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
    assert any(p["slug"] == "pro" for p in items)
    assert all(p["audience"] == "employer" for p in items)


def test_free_checkout_fulfills_immediately(auth_client):
    Package.objects.create(name="Free", slug="free", price_amount=0, currency="EGP", audience="individual")
    resp = auth_client.post("/api/v1/payments/checkout/", {"package": "free"}, format="json")
    assert resp.status_code == 200
    ref = resp.json()["data"]["order"]
    order = Order.objects.get(reference=ref)
    assert order.status == "paid"          # free order fulfilled without a provider
    assert resp.json()["data"]["checkout_url"] == ""


def test_checkout_unknown_package_404(auth_client):
    resp = auth_client.post("/api/v1/payments/checkout/", {"package": "nope"}, format="json")
    assert resp.status_code == 404


def test_order_status_owner_only(auth_client, user):
    pkg = Package.objects.create(name="Free", slug="free", price_amount=0, currency="EGP")
    order = Order.objects.create(user=user, package=pkg, total=0, currency="EGP")
    # Owner can read
    ok = auth_client.get(f"/api/v1/payments/orders/{order.reference}/")
    assert ok.status_code == 200
    # A different user cannot
    other = User.objects.create_user(email="other@test.com", password="pw12345x")
    c2 = APIClient(); c2.force_authenticate(user=other)
    assert c2.get(f"/api/v1/payments/orders/{order.reference}/").status_code == 404


def test_webhook_unknown_provider_rejected():
    resp = APIClient().post("/api/v1/payments/webhooks/notaprovider/", {}, format="json")
    assert resp.status_code == 400


# ============================================================================
# Admin Finance multi-platform control center (registry + provider health)
# ============================================================================

@pytest.fixture
def admin_user():
    return User.objects.create_user(email="finadmin@test.com", password="pw12345x", role="admin")


@pytest.fixture
def admin_client(admin_user):
    c = APIClient()
    c.force_authenticate(user=admin_user)
    return c


def test_platform_registry_endpoint_returns_all_platforms(admin_client):
    resp = admin_client.get("/api/v1/payments/admin/platforms/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    codes = {p["code"] for p in data}
    assert {"C", "E", "F", "K"} <= codes
    career = next(p for p in data if p["code"] == "C")
    assert career["name"] == "Career"
    assert career["merchant_prefix"] == "USAM-CAREER"


def test_provider_health_endpoint_reports_alexbank(admin_client):
    resp = admin_client.get("/api/v1/payments/admin/provider-health/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "alexbank" in data
    assert data["alexbank"]["live_enabled"] is False  # blocked until bank contract


def test_admin_finance_endpoints_require_admin(user):
    # A non-admin must not reach the registry or provider-health endpoints.
    c = APIClient(); c.force_authenticate(user=user)
    assert c.get("/api/v1/payments/admin/platforms/").status_code == 403
    assert c.get("/api/v1/payments/admin/provider-health/").status_code == 403

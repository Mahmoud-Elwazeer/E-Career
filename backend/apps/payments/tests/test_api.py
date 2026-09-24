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

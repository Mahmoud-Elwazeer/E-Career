"""
AI financial workspace: answers come from REAL analytics, never invented.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.payments.models import Package, Payment
from apps.payments import services, ai_workspace

User = get_user_model()
pytestmark = pytest.mark.django_db


def _paid(email, amount):
    u = User.objects.create_user(email=email, password="x")
    pkg = Package.objects.create(name="P", slug=f"p-{email}", price_amount=amount, currency="EGP", audience="employer")
    order = services.create_order(user=u, package=pkg)
    pay = Payment.objects.create(order=order, amount=order.total, currency="EGP", provider="stripe", status="pending")
    services.mark_order_paid(order=order, payment=pay)


def test_revenue_answer_matches_real_data():
    _paid("ai1@t.com", 20000)
    _paid("ai2@t.com", 30000)
    res = ai_workspace.answer("what revenue did we make")
    # 50000 minor units gross = 500.00 in the headline; overview carries the raw figure
    assert res["overview"]["gross_revenue"] == 50000
    assert "500.00" in res["answer"]
    assert res["source"]["query"] == "financial_overview"


def test_ai_endpoint_admin_only():
    User.objects.create_user(email="plain@t.com", password="x")
    c = APIClient(); c.force_authenticate(User.objects.get(email="plain@t.com"))
    assert c.post("/api/v1/payments/admin/ai/", {"question": "revenue"}, format="json").status_code == 403
    admin = User.objects.create_user(email="fadmin@t.com", password="x", role="admin")
    c2 = APIClient(); c2.force_authenticate(admin)
    ok = c2.post("/api/v1/payments/admin/ai/", {"question": "revenue this month"}, format="json")
    assert ok.status_code == 200
    assert "source" in ok.json()["data"]

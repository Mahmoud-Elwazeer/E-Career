"""
Tests for financial analytics + reconciliation — all from real rows.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.payments.models import Package, Payment
from apps.payments import services, analytics

User = get_user_model()
pytestmark = pytest.mark.django_db


def _paid_order(email, price=20000):
    user = User.objects.create_user(email=email, password="x")
    pkg = Package.objects.create(name="P", slug=f"p-{email}", price_amount=price,
                                 currency="EGP", audience="employer")
    order = services.create_order(user=user, package=pkg)
    pay = Payment.objects.create(order=order, amount=order.total, currency="EGP",
                                 provider="stripe", status="pending")
    services.mark_order_paid(order=order, payment=pay)
    return order, pay


def test_overview_reflects_real_revenue():
    _paid_order("a@t.com", 20000)
    _paid_order("b@t.com", 30000)
    data = analytics.financial_overview()
    assert data["gross_revenue"] == 50000
    assert data["orders_paid"] == 2
    assert data["payments_succeeded"] == 2
    assert data["payment_success_rate"] == 100.0
    # revenue attributed to the Career platform
    assert any(r["platform_code"] == "C" and r["total"] == 50000 for r in data["revenue_by_platform"])


def test_reconciliation_matches_clean_orders():
    _paid_order("c@t.com", 10000)
    result = analytics.reconcile()
    assert result["exception_count"] == 0
    assert result["matched"] >= 1


def test_reconciliation_flags_missing_ledger():
    order, pay = _paid_order("d@t.com", 10000)
    # Simulate drift: succeeded payment loses its ledger link.
    pay.ledger_transaction = None
    pay.save(update_fields=["ledger_transaction"])
    result = analytics.reconcile()
    assert result["exception_count"] >= 1
    assert any(e["type"] == "missing_ledger" for e in result["exceptions"])


def test_admin_overview_requires_admin():
    User.objects.create_user(email="plain@t.com", password="x")
    c = APIClient(); c.force_authenticate(User.objects.get(email="plain@t.com"))
    assert c.get("/api/v1/payments/admin/overview/").status_code == 403
    admin = User.objects.create_user(email="admin@t.com", password="x", role="admin")
    c2 = APIClient(); c2.force_authenticate(admin)
    assert c2.get("/api/v1/payments/admin/overview/").status_code == 200


def test_seed_packages_creates_real_packages():
    call_command("seed_packages")
    assert Package.objects.filter(slug="employer-growth").exists()
    growth = Package.objects.get(slug="employer-growth")
    assert growth.entitlement_plan is not None
    assert growth.entitlement_plan.ai_features_enabled is True

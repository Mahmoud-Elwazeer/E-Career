"""
Manual financial adjustment dual-approval (Part XXX).
Requester != approver; ledger posts only on approval; audit on each step.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.payments import services
from apps.payments.ledger import get_or_create_account
from apps.payments.models import AdjustmentRequest, LedgerAccount

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def accounts():
    get_or_create_account("revenue:c:egp", name="Rev", kind="revenue")
    get_or_create_account("adjustments:c:egp", name="Adj", kind="fees")


def test_request_creates_pending_no_ledger(accounts):
    req = User.objects.create_user(email="req@t.com", password="x", role="admin")
    adj = services.request_adjustment(
        requester=req, account_code="revenue:c:egp", counter_account_code="adjustments:c:egp",
        amount=-5000, currency="EGP", reason="correction",
    )
    assert adj.status == "pending"
    assert LedgerAccount.objects.get(code="revenue:c:egp").balance() == 0  # nothing posted yet


def test_requester_cannot_self_approve(accounts):
    req = User.objects.create_user(email="req2@t.com", password="x", role="admin")
    adj = services.request_adjustment(
        requester=req, account_code="revenue:c:egp", counter_account_code="adjustments:c:egp",
        amount=-5000, currency="EGP", reason="x",
    )
    with pytest.raises(ValueError):
        services.approve_adjustment(adjustment=adj, approver=req)


def test_second_admin_approval_posts_balanced_ledger(accounts):
    req = User.objects.create_user(email="req3@t.com", password="x", role="admin")
    approver = User.objects.create_user(email="app3@t.com", password="x", role="admin")
    adj = services.request_adjustment(
        requester=req, account_code="revenue:c:egp", counter_account_code="adjustments:c:egp",
        amount=-5000, currency="EGP", reason="goodwill credit",
    )
    services.approve_adjustment(adjustment=adj, approver=approver)
    adj.refresh_from_db()
    assert adj.status == "approved"
    assert adj.ledger_transaction is not None
    assert adj.ledger_transaction.is_balanced()
    assert LedgerAccount.objects.get(code="revenue:c:egp").balance() == -5000
    assert LedgerAccount.objects.get(code="adjustments:c:egp").balance() == 5000


def test_admin_endpoint_flow(accounts):
    from rest_framework.test import APIClient
    req = User.objects.create_user(email="areq@t.com", password="x", role="admin")
    approver = User.objects.create_user(email="aapp@t.com", password="x", role="admin")
    c1 = APIClient(); c1.force_authenticate(req)
    resp = c1.post("/api/v1/payments/admin/adjustments/", {
        "account_code": "revenue:c:egp", "counter_account_code": "adjustments:c:egp",
        "amount": -3000, "currency": "EGP", "reason": "test", "platform_code": "C",
    }, format="json")
    assert resp.status_code == 200
    ref = resp.json()["data"]["reference"]
    # requester self-approve -> 400
    bad = c1.post(f"/api/v1/payments/admin/adjustments/{ref}/decide/", {"decision": "approve"}, format="json")
    assert bad.status_code == 400
    # different admin approves -> ok
    c2 = APIClient(); c2.force_authenticate(approver)
    ok = c2.post(f"/api/v1/payments/admin/adjustments/{ref}/decide/", {"decision": "approve"}, format="json")
    assert ok.status_code == 200
    assert AdjustmentRequest.objects.get(reference=ref).status == "approved"

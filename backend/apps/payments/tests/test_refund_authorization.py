"""
Refund maker-checker / dual-authorization (directive item 13).

Mirrors test_adjustments.py's pattern deliberately: a RefundRequest is
REQUESTED by one admin with a reason, APPROVED (which EXECUTES the real
refund_payment) or REJECTED by a DIFFERENT admin. Requester != approver.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.payments import services
from apps.payments.models import Package, Payment, Refund, RefundRequest

User = get_user_model()
pytestmark = pytest.mark.django_db


def _paid_payment(email, amount=20000):
    user = User.objects.create_user(email=email, password="x")
    pkg = Package.objects.create(
        name=f"Pkg {email}", slug=f"pkg-auth-{email}", price_amount=amount,
        currency="EGP", audience="employer",
    )
    order = services.create_order(user=user, package=pkg)
    pay = Payment.objects.create(order=order, amount=order.total, currency="EGP",
                                 provider="", status="pending")
    services.mark_order_paid(order=order, payment=pay)
    pay.refresh_from_db()
    return pay


def test_request_refund_creates_pending_no_money_movement():
    pay = _paid_payment("refauth-req@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-maker@test.com", password="x", role="admin")

    req = services.request_refund(requester=requester, payment=pay, reason="customer unhappy")

    assert req.status == RefundRequest.Status.PENDING
    assert req.requested_by_id == requester.id
    assert req.executed_refund is None
    pay.refresh_from_db()
    assert pay.status == Payment.Status.SUCCEEDED  # untouched until approved


def test_request_refund_requires_a_reason():
    pay = _paid_payment("refauth-noreason@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-maker2@test.com", password="x", role="admin")
    with pytest.raises(ValueError):
        services.request_refund(requester=requester, payment=pay, reason="")


def test_requester_cannot_self_approve_refund():
    pay = _paid_payment("refauth-selfapprove@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-maker3@test.com", password="x", role="admin")
    req = services.request_refund(requester=requester, payment=pay, reason="dual control test")
    with pytest.raises(ValueError):
        services.approve_refund_request(refund_request=req, approver=requester)


def test_second_admin_approval_executes_real_refund():
    pay = _paid_payment("refauth-approve@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-maker4@test.com", password="x", role="admin")
    approver = User.objects.create_user(email="refauth-checker4@test.com", password="x", role="admin")

    req = services.request_refund(requester=requester, payment=pay, reason="approved refund")
    services.approve_refund_request(refund_request=req, approver=approver)

    req.refresh_from_db()
    assert req.status == RefundRequest.Status.APPROVED
    assert req.approved_by_id == approver.id
    assert req.executed_refund is not None
    assert req.executed_refund.status == Refund.Status.SUCCEEDED

    pay.refresh_from_db()
    assert pay.status == Payment.Status.REFUNDED  # the real refund actually ran


def test_rejecting_a_refund_request_never_executes_anything():
    pay = _paid_payment("refauth-reject@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-maker5@test.com", password="x", role="admin")
    approver = User.objects.create_user(email="refauth-checker5@test.com", password="x", role="admin")

    req = services.request_refund(requester=requester, payment=pay, reason="will be rejected")
    services.reject_refund_request(refund_request=req, approver=approver, note="not justified")

    req.refresh_from_db()
    assert req.status == RefundRequest.Status.REJECTED
    assert req.executed_refund is None
    pay.refresh_from_db()
    assert pay.status == Payment.Status.SUCCEEDED  # unaffected


def test_cannot_approve_an_already_resolved_request():
    pay = _paid_payment("refauth-doubledecide@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-maker6@test.com", password="x", role="admin")
    approver = User.objects.create_user(email="refauth-checker6@test.com", password="x", role="admin")

    req = services.request_refund(requester=requester, payment=pay, reason="first decision")
    services.approve_refund_request(refund_request=req, approver=approver)

    with pytest.raises(ValueError):
        services.approve_refund_request(refund_request=req, approver=approver)


def test_admin_endpoint_refund_authorization_flow():
    from rest_framework.test import APIClient

    pay = _paid_payment("refauth-endpoint@test.com", amount=10000)
    requester = User.objects.create_user(email="refauth-ep-maker@test.com", password="x", role="admin")
    approver = User.objects.create_user(email="refauth-ep-checker@test.com", password="x", role="admin")

    c1 = APIClient(); c1.force_authenticate(requester)
    resp = c1.post("/api/v1/payments/admin/refund-requests/", {
        "payment_reference": pay.reference, "reason": "endpoint test",
    }, format="json")
    assert resp.status_code == 200
    ref = resp.json()["data"]["reference"]

    # requester self-approve -> 400
    bad = c1.post(f"/api/v1/payments/admin/refund-requests/{ref}/decide/",
                  {"decision": "approve"}, format="json")
    assert bad.status_code == 400

    # different admin approves -> 200, refund actually executed
    c2 = APIClient(); c2.force_authenticate(approver)
    ok = c2.post(f"/api/v1/payments/admin/refund-requests/{ref}/decide/",
                 {"decision": "approve"}, format="json")
    assert ok.status_code == 200
    assert RefundRequest.objects.get(reference=ref).status == "approved"
    pay.refresh_from_db()
    assert pay.status == Payment.Status.REFUNDED

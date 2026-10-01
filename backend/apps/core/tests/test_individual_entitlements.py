"""Tests for the unified entitlement engine (individual + organization subjects).

The whole point of task #5 is that an individual User and an organization
Company are gated by the SAME logic against the SAME SubscriptionPlan — no
forked individual-only code path. These tests pin that: identical plan +
identical gate behaviour whether the subject is a User or a Company.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from apps.core.permissions import (
    check_entitlement, check_entitlement_for, resolve_active_plan,
)
from apps.core.models import SubscriptionPlan, CompanySubscription, UserSubscription
from apps.jobs.models import Company

User = get_user_model()
pytestmark = pytest.mark.django_db


def _user(email):
    return User.objects.create_user(email=email, password="TestPass123!")


# ── Plan resolution is subject-aware ──────────────────────────────────────────
def test_resolve_plan_for_user():
    u = _user("ind1@test.com")
    plan = SubscriptionPlan.objects.create(name="Pro Individual")
    UserSubscription.objects.create(user=u, plan=plan, status="active")
    assert resolve_active_plan(u) == plan


def test_resolve_plan_for_company():
    c = Company.objects.create(name="Acme", slug="acme-ent")
    plan = SubscriptionPlan.objects.create(name="Pro Employer")
    CompanySubscription.objects.create(company=c, plan=plan, status="active")
    assert resolve_active_plan(c) == plan


def test_resolve_plan_none_when_no_subscription():
    assert resolve_active_plan(_user("none@test.com")) is None
    assert resolve_active_plan(Company.objects.create(name="NoSub", slug="nosub-ent")) is None


def test_resolve_plan_ignores_cancelled_subscription():
    u = _user("cancelled@test.com")
    plan = SubscriptionPlan.objects.create(name="Lapsed")
    UserSubscription.objects.create(user=u, plan=plan, status="cancelled")
    assert resolve_active_plan(u) is None


# ── Individual gating uses the exact same rules as company gating ─────────────
def test_individual_feature_gate_denies_when_flag_false():
    u = _user("feat@test.com")
    plan = SubscriptionPlan.objects.create(
        name="No Pool Individual", feature_flags={"talent_pool": False},
    )
    UserSubscription.objects.create(user=u, plan=plan, status="active")
    with pytest.raises(PermissionDenied):
        check_entitlement_for(u, "feature", feature="talent_pool")


def test_individual_feature_gate_allows_unset_feature():
    u = _user("feat2@test.com")
    plan = SubscriptionPlan.objects.create(
        name="Other Individual", feature_flags={"other": False},
    )
    UserSubscription.objects.create(user=u, plan=plan, status="active")
    assert check_entitlement_for(u, "feature", feature="talent_pool") is True


def test_individual_ai_feature_gate():
    u = _user("ai@test.com")
    plan = SubscriptionPlan.objects.create(name="No AI Individual", ai_features_enabled=False)
    UserSubscription.objects.create(user=u, plan=plan, status="active")
    with pytest.raises(PermissionDenied):
        check_entitlement_for(u, "ai_feature")


def test_individual_no_subscription_allows_everything():
    u = _user("free@test.com")
    assert check_entitlement_for(u, "ai_feature") is True
    assert check_entitlement_for(u, "feature", feature="talent_pool") is True
    assert check_entitlement_for(u, "job_posting", 999) is True


def test_individual_count_limit_enforced():
    u = _user("limit@test.com")
    plan = SubscriptionPlan.objects.create(name="Capped Individual", job_posting_limit=2)
    UserSubscription.objects.create(user=u, plan=plan, status="active")
    assert check_entitlement_for(u, "job_posting", 1) is True
    with pytest.raises(PermissionDenied):
        check_entitlement_for(u, "job_posting", 2)


# ── Same plan, same verdict for either subject type ──────────────────────────
def test_same_plan_gives_same_verdict_for_user_and_company():
    plan = SubscriptionPlan.objects.create(
        name="Shared Plan", feature_flags={"talent_pool": False}, ai_features_enabled=False,
    )
    u = _user("shared-u@test.com")
    c = Company.objects.create(name="Shared Co", slug="shared-co-ent")
    UserSubscription.objects.create(user=u, plan=plan, status="active")
    CompanySubscription.objects.create(company=c, plan=plan, status="active")

    for subject in (u, c):
        with pytest.raises(PermissionDenied):
            check_entitlement_for(subject, "feature", feature="talent_pool")
        with pytest.raises(PermissionDenied):
            check_entitlement_for(subject, "ai_feature")


# ── Legacy company wrapper still works ───────────────────────────────────────
def test_company_wrapper_delegates_to_unified_gate():
    c = Company.objects.create(name="Legacy Co", slug="legacy-co-ent")
    plan = SubscriptionPlan.objects.create(name="Legacy Plan", job_posting_limit=1)
    CompanySubscription.objects.create(company=c, plan=plan, status="active")
    assert check_entitlement(c, "job_posting", 0) is True
    with pytest.raises(PermissionDenied):
        check_entitlement(c, "job_posting", 1)

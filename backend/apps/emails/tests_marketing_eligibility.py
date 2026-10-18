"""
Marketing-send eligibility gating (directive item 11).

Confirms the two genuinely promotional/broad-blast tasks
(`send_re_engagement_emails`, `send_weekly_career_digest`) actually call the
canonical `apps.legal.services.can_send_marketing` gate and skip ineligible
users — these previously sent unconditionally to entire user segments with
no marketing-consent check at all.
"""
from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.legal.models import MarketingPreference
from apps.profiles.models import UserProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


def _inactive_user(email, opted_in=False):
    user = User.objects.create_user(email=email, password="pw12345x")
    user.last_login = timezone.now() - timedelta(days=60)
    user.save(update_fields=["last_login"])
    UserProfile.objects.get_or_create(user=user)
    if opted_in:
        MarketingPreference.objects.create(user=user, email_marketing_opt_in=True)
    return user


@mock.patch("apps.emails.service.email_service.send_template_email", return_value=(True, "x"))
def test_re_engagement_skips_users_without_marketing_opt_in(mock_send):
    _inactive_user("not-opted-in@test.com", opted_in=False)
    opted_user = _inactive_user("opted-in@test.com", opted_in=True)

    from apps.emails.tasks import send_re_engagement_emails
    send_re_engagement_emails()

    sent_to = [call.kwargs.get("user") for call in mock_send.call_args_list]
    assert opted_user in sent_to
    assert len(sent_to) == 1  # only the opted-in user was emailed


@mock.patch("apps.intelligence.career_ai.career_ai_service.invoke_model", return_value="Keep learning!")
@mock.patch("apps.emails.service.email_service.send_template_email", return_value=(True, "x"))
def test_weekly_career_digest_skips_users_without_marketing_opt_in(mock_send, mock_ai):
    from apps.career.models import CareerProfile

    not_opted = User.objects.create_user(email="digest-no-optin@test.com", password="pw12345x", role="jobseeker")
    CareerProfile.objects.create(user=not_opted)

    opted = User.objects.create_user(email="digest-optin@test.com", password="pw12345x", role="jobseeker")
    CareerProfile.objects.create(user=opted)
    MarketingPreference.objects.create(user=opted, email_marketing_opt_in=True)

    import sys
    import types
    fake_module = types.ModuleType("apps.vectors.matching_service")
    fake_module.matching_service = mock.Mock(find_matching_jobs=mock.Mock(return_value=[]))
    sys.modules.setdefault("apps.vectors", types.ModuleType("apps.vectors"))
    sys.modules["apps.vectors.matching_service"] = fake_module

    from apps.emails.tasks import send_weekly_career_digest
    send_weekly_career_digest()

    sent_to = [call.kwargs.get("user") for call in mock_send.call_args_list]
    assert opted in sent_to
    assert not_opted not in sent_to

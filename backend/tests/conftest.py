"""
pytest configuration — fixtures and factory setup for all tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="testuser@gmail.com",
        password="TestPass123!",
        first_name="Test",
        last_name="User",
        role="user",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="testadmin@gmail.com",
        password="AdminPass123!",
        first_name="Admin",
        last_name="User",
        role="admin",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def auth_client(api_client, user):
    """API client authenticated as a regular user."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """API client authenticated as an admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


# ── Job fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def company(db):
    from apps.jobs.models import Company
    return Company.objects.create(
        name="Test Corp",
        slug="test-corp",
        industry="technology",
        website="https://testcorp.example.com",
        snippet="A great tech company.",
    )


@pytest.fixture
def source(db):
    from apps.jobs.models import Source
    return Source.objects.create(
        name="Test Board",
        slug="test-board",
        url="https://testboard.example.com",
    )


@pytest.fixture
def tag(db):
    from apps.jobs.models import Tag
    return Tag.objects.create(name="Python", slug="python", category="language")


@pytest.fixture
def job(db, company, source):
    from apps.jobs.models import Job
    import datetime
    return Job.objects.create(
        title="Software Engineer",
        slug="software-engineer",
        company=company,
        source=source,
        location="Remote",
        location_type="remote",
        industry="technology",
        experience_level="mid",
        description="Build great software.",
        source_url="https://testboard.example.com/jobs/1",
        posted_at=datetime.date.today(),
        status="active",
    )


@pytest.fixture
def inactive_job(db, company, source):
    from apps.jobs.models import Job
    import datetime
    return Job.objects.create(
        title="Old Job",
        slug="old-job",
        company=company,
        source=source,
        location="Dubai",
        location_type="onsite",
        industry="finance",
        experience_level="entry",
        description="Old listing.",
        source_url="https://testboard.example.com/jobs/2",
        posted_at=datetime.date.today(),
        status="archived",
    )


# ── Feature flag fixture ──────────────────────────────────────────────────────

@pytest.fixture
def feature_flag(db):
    from apps.core.models import FeatureFlag
    return FeatureFlag.objects.create(
        key="test_flag",
        label="Test Flag",
        is_enabled=True,
    )

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


# ── Mock fixtures for external services ───────────────────────────────────────

@pytest.fixture
def mock_bedrock_client(mocker):
    """Mock AWS Bedrock client."""
    mock = mocker.patch("apps.ai.bedrock.BedrockClient")
    mock.return_value.generate_text.return_value = "Mocked AI response"
    mock.return_value.generate_embedding.return_value = [0.1] * 768
    return mock.return_value


@pytest.fixture
def mock_typesense_client(mocker):
    """Mock Typesense search client."""
    mock = mocker.patch("apps.search.typesense_plugin.TypesenseClient")
    mock.return_value.search.return_value = {"hits": []}
    return mock.return_value


@pytest.fixture
def mock_qdrant_client(mocker):
    """Mock Qdrant vector database client."""
    mock = mocker.patch("apps.search.qdrant_plugin.QdrantClient")
    mock.return_value.search.return_value = []
    return mock.return_value


@pytest.fixture
def mock_s3_client(mocker):
    """Mock AWS S3 client."""
    mock = mocker.patch("boto3.client")
    mock.return_value.upload_fileobj.return_value = None
    mock.return_value.generate_presigned_url.return_value = "https://s3.example.com/file"
    return mock.return_value


@pytest.fixture
def mock_email_backend(mocker):
    """Mock email sending."""
    mock = mocker.patch("django.core.mail.send_mail")
    mock.return_value = 1
    return mock


@pytest.fixture
def mock_redis_client(mocker):
    """Mock Redis client."""
    mock = mocker.patch("redis.Redis")
    mock.return_value.get.return_value = None
    mock.return_value.set.return_value = True
    return mock.return_value


@pytest.fixture
def mock_celery_task(mocker):
    """Mock Celery task."""
    mock = mocker.patch("apps.career.tasks.calculate_talent_score")
    mock.delay.return_value = None
    return mock


# ── Additional user fixtures ──────────────────────────────────────────────────

@pytest.fixture
def employer_user(db):
    """Create an employer user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email="employer@example.com",
        password="EmployerPass123!",
        first_name="Employer",
        last_name="User",
        role="user",
    )


@pytest.fixture
def verified_company(db):
    """Create a verified company."""
    from apps.jobs.models import Company
    return Company.objects.create(
        name="Verified Corp",
        slug="verified-corp",
        industry="technology",
        website="https://verifiedcorp.example.com",
        snippet="A verified tech company.",
        is_verified=True,
    )

"""
Unit tests — models: custom User, Job, Company, Source, Tag.
"""
import datetime
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email="alice@gmail.com",
            password="SecurePass1!",
            first_name="Alice",
            last_name="Smith",
        )
        assert user.email == "alice@gmail.com"
        assert user.check_password("SecurePass1!")
        assert user.role == "user"
        assert user.status == "active"
        assert user.is_active is True
        assert user.is_deleted is False

    def test_email_is_unique(self, db):
        User.objects.create_user(email="bob@gmail.com", password="Pass1234!", first_name="Bob", last_name="Jones")
        with pytest.raises(Exception):
            User.objects.create_user(email="bob@gmail.com", password="Pass5678!", first_name="Bob2", last_name="Jones2")

    def test_username_field_is_email(self):
        assert User.USERNAME_FIELD == "email"

    def test_full_name_property(self, db):
        user = User.objects.create_user(
            email="carol@gmail.com", password="P@ssword1",
            first_name="Carol", last_name="White"
        )
        assert user.full_name == "Carol White"

    def test_soft_delete(self, user):
        user.soft_delete()
        user.refresh_from_db()
        assert user.is_deleted is True
        assert user.is_active is False
        assert user.deleted_at is not None

    def test_soft_delete_sets_timestamp(self, user):
        before = timezone.now()
        user.soft_delete()
        user.refresh_from_db()
        assert user.deleted_at >= before

    def test_create_superuser(self, db):
        admin = User.objects.create_superuser(
            email="superadmin@gmail.com",
            password="AdminPass1!",
            first_name="Super",
            last_name="Admin",
        )
        assert admin.is_superuser is True
        assert admin.is_staff is True

    def test_str_representation(self, user):
        expected = f"{user.get_full_name()} <{user.email}>"
        assert str(user) == expected

    def test_password_not_stored_in_plain_text(self, db):
        user = User.objects.create_user(
            email="dave@gmail.com", password="MySecret99",
            first_name="Dave", last_name="Lee"
        )
        assert user.password != "MySecret99"
        assert user.check_password("MySecret99")


@pytest.mark.django_db
class TestJobModel:
    def test_create_job(self, job):
        assert job.title == "Software Engineer"
        assert job.status == "active"
        assert job.view_count == 0
        assert job.click_count == 0

    def test_job_str(self, job):
        assert "Software Engineer" in str(job)
        assert "Test Corp" in str(job)

    def test_job_slug_is_unique(self, db, company, source):
        from apps.jobs.models import Job
        Job.objects.create(
            title="Dev A", slug="unique-dev",
            company=company, source=source,
            location="Cairo", location_type="remote",
            industry="technology", experience_level="mid",
            description="Desc", source_url="https://ex.com/1",
            posted_at=datetime.date.today(), status="active",
        )
        with pytest.raises(Exception):
            Job.objects.create(
                title="Dev B", slug="unique-dev",
                company=company, source=source,
                location="Dubai", location_type="hybrid",
                industry="technology", experience_level="senior",
                description="Desc 2", source_url="https://ex.com/2",
                posted_at=datetime.date.today(), status="active",
            )

    def test_archived_job_not_active(self, inactive_job):
        assert inactive_job.status == "archived"

    def test_job_company_relationship(self, job, company):
        assert job.company == company
        assert job in company.jobs.all()


@pytest.mark.django_db
class TestCompanyModel:
    def test_create_company(self, company):
        assert company.name == "Test Corp"
        assert company.slug == "test-corp"
        assert company.is_active is True

    def test_company_str(self, company):
        assert str(company) == "Test Corp"


@pytest.mark.django_db
class TestSourceModel:
    def test_create_source(self, source):
        assert source.name == "Test Board"
        assert source.is_active is True

    def test_source_str(self, source):
        assert str(source) == "Test Board"


@pytest.mark.django_db
class TestTagModel:
    def test_create_tag(self, tag):
        assert tag.name == "Python"
        assert tag.slug == "python"
        assert tag.category == "language"

    def test_tag_str(self, tag):
        assert str(tag) == "Python"


@pytest.mark.django_db
class TestFeatureFlag:
    def test_create_flag(self, feature_flag):
        assert feature_flag.key == "test_flag"
        assert feature_flag.is_enabled is True

    def test_flag_str(self, feature_flag):
        assert "Test Flag" in str(feature_flag)
        assert "on" in str(feature_flag)

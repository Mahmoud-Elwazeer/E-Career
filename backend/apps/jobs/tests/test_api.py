"""
Jobs API Tests
Tests for jobs, companies, sources, and tags endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.jobs.models import Company, Source, Tag, Job


@pytest.mark.django_db
class TestJobAPI:
    """Tests for Job endpoints."""

    def test_list_jobs_anonymous(self, api_client, job):
        """Test listing jobs as anonymous user."""
        url = reverse("jobs:job-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_list_jobs_with_filters(self, api_client, job):
        """Test filtering jobs by query."""
        url = reverse("jobs:job-list")
        response = api_client.get(url, {"q": "Software"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_jobs_by_industry(self, api_client, job):
        """Test filtering jobs by industry."""
        url = reverse("jobs:job-list")
        response = api_client.get(url, {"industry": "technology"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_jobs_by_location(self, api_client, job):
        """Test filtering jobs by location."""
        url = reverse("jobs:job-list")
        response = api_client.get(url, {"location": "Remote"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_jobs_by_company(self, api_client, job, company):
        """Test filtering jobs by company."""
        url = reverse("jobs:job-list")
        response = api_client.get(url, {"company": company.slug})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_jobs_by_tag(self, api_client, job, tag):
        """Test filtering jobs by tag."""
        url = reverse("jobs:job-list")
        response = api_client.get(url, {"tag": tag.slug})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_jobs_ordering(self, api_client, job):
        """Test ordering jobs."""
        url = reverse("jobs:job-list")
        response = api_client.get(url, {"ordering": "-posted_at"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_retrieve_job_detail(self, api_client, job):
        """Test retrieving a single job."""
        url = reverse("jobs:job-detail", kwargs={"slug": job.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["title"] == job.title

    def test_retrieve_job_not_found(self, api_client):
        """Test retrieving a non-existent job."""
        url = reverse("jobs:job-detail", kwargs={"slug": "non-existent"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_save_job(self, auth_client, job):
        """Test saving a job."""
        url = reverse("jobs:job-save", kwargs={"slug": job.slug})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["is_saved"] is True

    def test_unsave_job(self, auth_client, job):
        """Test unsaving a job."""
        # First save
        url = reverse("jobs:job-save", kwargs={"slug": job.slug})
        auth_client.post(url)

        # Then unsave
        url = reverse("jobs:job-unsave", kwargs={"slug": job.slug})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["is_saved"] is False

    def test_apply_job(self, api_client, job):
        """Test applying to a job."""
        url = reverse("jobs:job-apply", kwargs={"slug": job.slug})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "source_url" in response.data["data"]

    def test_similar_jobs(self, api_client, job):
        """Test getting similar jobs."""
        url = reverse("jobs:job-similar", kwargs={"slug": job.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestCompanyAPI:
    """Tests for Company endpoints."""

    def test_list_companies(self, api_client, company):
        """Test listing companies."""
        url = reverse("jobs:company-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_retrieve_company(self, api_client, company):
        """Test retrieving a single company."""
        url = reverse("jobs:company-detail", kwargs={"slug": company.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["name"] == company.name

    def test_create_company_admin(self, admin_client):
        """Test creating a company as admin."""
        url = reverse("jobs:company-list")
        data = {
            "name": "New Company",
            "slug": "new-company",
            "industry": "technology",
        }
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_create_company_unauthorized(self, api_client):
        """Test creating a company without admin privileges."""
        url = reverse("jobs:company-list")
        data = {
            "name": "New Company",
            "slug": "new-company",
            "industry": "technology",
        }
        response = api_client.post(url, data)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_update_company_admin(self, admin_client, company):
        """Test updating a company as admin."""
        url = reverse("jobs:company-detail", kwargs={"slug": company.slug})
        data = {"name": "Updated Company Name"}
        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_delete_company_admin(self, admin_client, company):
        """Test soft-deleting a company as admin."""
        url = reverse("jobs:company-detail", kwargs={"slug": company.slug})
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        # Verify company is deactivated
        company.refresh_from_db()
        assert company.is_active is False


@pytest.mark.django_db
class TestSourceAPI:
    """Tests for Source endpoints."""

    def test_list_sources(self, api_client, source):
        """Test listing sources."""
        url = reverse("jobs:source-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_retrieve_source(self, api_client, source):
        """Test retrieving a single source."""
        url = reverse("jobs:source-detail", kwargs={"slug": source.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_source_admin(self, admin_client):
        """Test creating a source as admin."""
        url = reverse("jobs:source-list")
        data = {
            "name": "New Source",
            "slug": "new-source",
            "url": "https://example.com",
        }
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_source_admin(self, admin_client, source):
        """Test updating a source as admin."""
        url = reverse("jobs:source-detail", kwargs={"slug": source.slug})
        data = {"name": "Updated Source Name"}
        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestTagAPI:
    """Tests for Tag endpoints."""

    def test_list_tags(self, api_client, tag):
        """Test listing tags."""
        url = reverse("jobs:tag-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_retrieve_tag(self, api_client, tag):
        """Test retrieving a single tag."""
        url = reverse("jobs:tag-detail", kwargs={"slug": tag.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_tag_admin(self, admin_client):
        """Test creating a tag as admin."""
        url = reverse("jobs:tag-list")
        data = {"name": "New Tag", "category": "tool"}
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_delete_tag_admin(self, admin_client, tag):
        """Test deleting a tag as admin."""
        url = reverse("jobs:tag-detail", kwargs={"slug": tag.slug})
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
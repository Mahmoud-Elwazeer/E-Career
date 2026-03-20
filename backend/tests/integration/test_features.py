"""
Integration tests — feature APIs: jobs, companies, sources, tags,
saved jobs, alerts, notifications, health check.
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestHealthCheck:
    url = "/health/"

    def test_health_returns_200(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["database"] == "ok"


@pytest.mark.django_db
class TestJobListEndpoint:
    url = "/api/v1/jobs/"

    def test_list_jobs_unauthenticated(self, api_client, job):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["count"] >= 1

    def test_list_jobs_pagination(self, api_client, job):
        resp = api_client.get(self.url + "?page_size=1")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]["results"]) == 1

    def test_list_jobs_filter_by_industry(self, api_client, job):
        resp = api_client.get(self.url + "?industry=technology")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["data"]["results"]
        assert all(j["industry"] == "technology" for j in results)

    def test_list_jobs_filter_by_location_type(self, api_client, job):
        resp = api_client.get(self.url + "?work_mode=remote")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["data"]["results"]
        assert all(j["location_type"] == "remote" for j in results)

    def test_list_jobs_search(self, api_client, job):
        resp = api_client.get(self.url + "?q=Software")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["data"]["results"]
        assert any("Software" in j["title"] for j in results)

    def test_archived_jobs_excluded(self, api_client, inactive_job):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        slugs = [j["slug"] for j in resp.json()["data"]["results"]]
        assert inactive_job.slug not in slugs

    def test_create_job_requires_admin(self, auth_client, company, source):
        import datetime
        resp = auth_client.post(self.url, {
            "title": "New Job",
            "company": company.id,
            "location": "Dubai",
            "location_type": "hybrid",
            "industry": "technology",
            "experience_level": "mid",
            "description": "A new role.",
            "source_url": "https://ex.com/newjob",
            "posted_at": str(datetime.date.today()),
            "status": "active",
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_job_as_admin(self, admin_client, company, source):
        import datetime
        resp = admin_client.post(self.url, {
            "title": "Admin Created Job",
            "slug": "admin-created-job",
            "company": company.id,
            "source": source.id,
            "location": "Riyadh",
            "location_type": "onsite",
            "industry": "finance",
            "experience_level": "senior",
            "description": "Senior role at a great firm.",
            "source_url": "https://ex.com/admin-job",
            "posted_at": str(datetime.date.today()),
            "status": "active",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["data"]["title"] == "Admin Created Job"


@pytest.mark.django_db
class TestJobDetailEndpoint:
    def test_get_job_by_slug(self, api_client, job):
        resp = api_client.get(f"/api/v1/jobs/{job.slug}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["slug"] == job.slug
        assert data["title"] == job.title

    def test_get_nonexistent_job_returns_404(self, api_client):
        resp = api_client.get("/api/v1/jobs/does-not-exist/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_archive_job_requires_admin(self, auth_client, job):
        resp = auth_client.delete(f"/api/v1/jobs/{job.slug}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_archive_job_as_admin(self, admin_client, job):
        resp = admin_client.delete(f"/api/v1/jobs/{job.slug}/")
        assert resp.status_code == status.HTTP_200_OK
        job.refresh_from_db()
        assert job.status == "archived"

    def test_apply_click_tracking(self, api_client, job):
        resp = api_client.post(f"/api/v1/jobs/{job.slug}/apply/")
        assert resp.status_code == status.HTTP_200_OK
        assert "source_url" in resp.json()["data"]
        job.refresh_from_db()
        assert job.click_count == 1

    def test_similar_jobs(self, api_client, job):
        resp = api_client.get(f"/api/v1/jobs/{job.slug}/similar/")
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json()["data"], list)


@pytest.mark.django_db
class TestCompanyEndpoints:
    url = "/api/v1/jobs/companies/"

    def test_list_companies(self, api_client, company):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_get_company_by_slug(self, api_client, company):
        resp = api_client.get(f"{self.url}{company.slug}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["name"] == company.name

    def test_create_company_requires_admin(self, auth_client):
        resp = auth_client.post(self.url, {"name": "New Co", "industry": "technology"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSourceEndpoints:
    url = "/api/v1/jobs/sources/"

    def test_list_sources(self, api_client, source):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_create_source_requires_admin(self, auth_client):
        resp = auth_client.post(self.url, {"name": "New Board", "url": "https://newboard.com"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTagEndpoints:
    url = "/api/v1/jobs/tags/"

    def test_list_tags(self, api_client, tag):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        names = [t["name"] for t in resp.json()["data"]]
        assert "Python" in names

    def test_create_tag_requires_admin(self, auth_client):
        resp = auth_client.post(self.url, {"name": "NewTag", "category": "skill"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tag_as_admin(self, admin_client):
        resp = admin_client.post(self.url, {"name": "React", "category": "framework"})
        assert resp.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestSavedJobsEndpoints:
    url = "/api/v1/users/me/saved-jobs/"

    def test_save_job(self, auth_client, job):
        resp = auth_client.post(self.url, {"job_id": job.id})
        assert resp.status_code == status.HTTP_201_CREATED

    def test_list_saved_jobs(self, auth_client, job, user):
        from apps.users.models import SavedJob
        SavedJob.objects.create(user=user, job=job)
        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["count"] >= 1

    def test_save_job_requires_auth(self, api_client, job):
        resp = api_client.post(self.url, {"job_id": job.id})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_save_same_job_twice(self, auth_client, job, user):
        from apps.users.models import SavedJob
        SavedJob.objects.create(user=user, job=job)
        resp = auth_client.post(self.url, {"job_id": job.id})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_unsave_job(self, auth_client, job, user):
        from apps.users.models import SavedJob
        saved = SavedJob.objects.create(user=user, job=job)
        resp = auth_client.delete(f"{self.url}{saved.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert not SavedJob.objects.filter(id=saved.id).exists()


@pytest.mark.django_db
class TestAlertsEndpoints:
    url = "/api/v1/users/me/alerts/"

    def test_create_alert(self, auth_client):
        resp = auth_client.post(self.url, {"keyword": "Python", "frequency": "daily"})
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()["data"]
        assert data["keyword"] == "Python"
        assert data["frequency"] == "daily"

    def test_list_alerts(self, auth_client, user):
        from apps.users.models import Alert
        Alert.objects.create(user=user, keyword="React", frequency="weekly", is_active=True)
        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_alerts_require_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_alert(self, auth_client, user):
        from apps.users.models import Alert
        alert = Alert.objects.create(user=user, keyword="Go", frequency="daily", is_active=True)
        resp = auth_client.patch(f"{self.url}{alert.uuid}/", {"is_active": False})
        assert resp.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.is_active is False

    def test_delete_alert(self, auth_client, user):
        from apps.users.models import Alert
        alert = Alert.objects.create(user=user, keyword="Rust", frequency="weekly", is_active=True)
        resp = auth_client.delete(f"{self.url}{alert.uuid}/")
        assert resp.status_code == status.HTTP_200_OK
        assert not Alert.objects.filter(id=alert.id).exists()


@pytest.mark.django_db
class TestNotificationsEndpoints:
    url = "/api/v1/users/me/notifications/"

    def test_list_notifications(self, auth_client, user):
        from apps.users.models import Notification
        Notification.objects.create(user=user, title="Hello!", type="system")
        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["count"] >= 1

    def test_mark_notification_read(self, auth_client, user):
        from apps.users.models import Notification
        notif = Notification.objects.create(user=user, title="Ping", type="system", is_read=False)
        resp = auth_client.patch(f"{self.url}{notif.uuid}/")
        assert resp.status_code == status.HTTP_200_OK
        notif.refresh_from_db()
        assert notif.is_read is True

    def test_mark_all_notifications_read(self, auth_client, user):
        from apps.users.models import Notification
        Notification.objects.create(user=user, title="N1", type="system", is_read=False)
        Notification.objects.create(user=user, title="N2", type="system", is_read=False)
        resp = auth_client.post(f"{self.url}mark-all-read/")
        assert resp.status_code == status.HTTP_200_OK
        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_notifications_require_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAnalyticsEndpoints:
    def test_stats_requires_admin(self, auth_client):
        resp = auth_client.get("/api/v1/analytics/stats/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_stats_accessible_by_admin(self, admin_client):
        resp = admin_client.get("/api/v1/analytics/stats/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert "total_jobs" in data
        assert "total_users" in data

    def test_charts_accessible_by_admin(self, admin_client):
        resp = admin_client.get("/api/v1/analytics/charts/")
        assert resp.status_code == status.HTTP_200_OK

    def test_click_analytics_accessible_by_admin(self, admin_client):
        resp = admin_client.get("/api/v1/analytics/clicks/")
        assert resp.status_code == status.HTTP_200_OK

    def test_search_analytics_accessible_by_admin(self, admin_client):
        resp = admin_client.get("/api/v1/analytics/searches/")
        assert resp.status_code == status.HTTP_200_OK

    def test_conversion_analytics_accessible_by_admin(self, admin_client):
        resp = admin_client.get("/api/v1/analytics/conversion/")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestErrorHandling:
    def test_404_returns_json(self, api_client):
        resp = api_client.get("/api/v1/jobs/this-slug-does-not-exist/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        data = resp.json()
        assert "success" in data
        assert data["success"] is False

    def test_method_not_allowed_returns_json(self, api_client):
        resp = api_client.delete("/api/v1/jobs/")
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert resp.json()["success"] is False

    def test_unauthenticated_returns_json(self, api_client):
        resp = api_client.get("/api/v1/users/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert data["success"] is False
        assert "message" in data

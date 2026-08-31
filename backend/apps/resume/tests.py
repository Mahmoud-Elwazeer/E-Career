"""
Tests for the Resume Builder app — models, views, and export service.
"""
import json
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.resume.models import (
    ResumeTemplate, Resume, ResumeExport, ProfileSection, SkillVerification,
)
from apps.resume.export_service import resume_export_service

User = get_user_model()


# ── Model tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestResumeTemplateModel:
    def test_create_template(self):
        tpl = ResumeTemplate.objects.create(
            title="Modern Tech",
            description="A modern resume template for tech professionals.",
            category="modern",
        )
        assert tpl.title == "Modern Tech"
        assert tpl.category == "modern"
        assert tpl.is_active is True
        assert tpl.is_premium is False
        assert str(tpl) == "Modern Tech (modern)"

    def test_default_rating(self):
        tpl = ResumeTemplate.objects.create(
            title="Basic", description="Basic template", category="minimalist",
        )
        assert tpl.rating == Decimal("4.50")


@pytest.mark.django_db
class TestResumeModel:
    def test_create_resume(self, user):
        resume = Resume.objects.create(
            user=user,
            title="My CV",
            personal_info={"full_name": "Test User", "email": "test@example.com"},
            summary="Experienced engineer.",
            skills=["Python", "Django"],
        )
        assert resume.title == "My CV"
        assert resume.personal_info["full_name"] == "Test User"
        assert resume.is_public is False
        assert str(resume) == f"My CV ({user.email})"

    def test_resume_defaults(self, user):
        resume = Resume.objects.create(user=user)
        assert resume.title == "My Resume"
        assert resume.experience == []
        assert resume.education == []
        assert resume.privacy_settings == {}


@pytest.mark.django_db
class TestResumeExportModel:
    def test_create_export(self, user):
        resume = Resume.objects.create(user=user, title="Export Test")
        export = ResumeExport.objects.create(
            resume=resume, format="pdf", status="completed",
        )
        assert export.format == "pdf"
        assert export.status == "completed"
        assert str(export) == "Export Test - pdf"


@pytest.mark.django_db
class TestProfileSectionModel:
    def test_create_section(self, user):
        section = ProfileSection.objects.create(
            user=user, section_type="experience", title="Work History",
            content={"items": [{"company": "Acme"}]}, order=1,
        )
        assert section.section_type == "experience"
        assert section.is_visible is True
        assert str(section) == f"{user.email} - experience"


@pytest.mark.django_db
class TestSkillVerificationModel:
    def test_create_verification(self, user):
        sv = SkillVerification.objects.create(
            user=user, skill_name="Python", skill_category="programming",
            verification_method="assessment", score=85, level="advanced",
        )
        assert sv.skill_name == "Python"
        assert sv.score == 85
        assert str(sv) == f"{user.email} - Python (advanced)"

    def test_unique_constraint(self, user):
        SkillVerification.objects.create(
            user=user, skill_name="Django", verification_method="cv",
        )
        with pytest.raises(Exception):
            SkillVerification.objects.create(
                user=user, skill_name="Django", verification_method="github",
            )


# ── View tests ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetResumeTemplatesView:
    url = "/api/v1/resume/templates/"

    def test_get_templates_unauthenticated(self, api_client):
        ResumeTemplate.objects.create(
            title="T1", description="d", category="modern",
        )
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["success"] is True
        assert len(resp.json()["data"]) >= 1

    def test_inactive_templates_hidden(self, auth_client):
        ResumeTemplate.objects.create(
            title="Active", description="d", category="modern", is_active=True,
        )
        ResumeTemplate.objects.create(
            title="Inactive", description="d", category="modern", is_active=False,
        )
        resp = auth_client.get(self.url)
        titles = [t["title"] for t in resp.json()["data"]]
        assert "Active" in titles
        assert "Inactive" not in titles


@pytest.mark.django_db
class TestResumesCRUDViews:
    list_url = "/api/v1/resume/resumes/"

    def test_list_requires_auth(self, api_client):
        resp = api_client.get(self.list_url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_resume(self, auth_client, user):
        resp = auth_client.post(self.list_url, {
            "title": "New Resume",
            "summary": "A test resume.",
            "skills": ["Python"],
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["success"] is True
        assert Resume.objects.filter(user=user, title="New Resume").exists()

    def test_list_own_resumes(self, auth_client, user):
        Resume.objects.create(user=user, title="R1")
        Resume.objects.create(user=user, title="R2")
        resp = auth_client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) == 2

    def test_get_single_resume(self, auth_client, user):
        resume = Resume.objects.create(user=user, title="Detail")
        resp = auth_client.get(f"/api/v1/resume/resumes/{resume.uuid}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["title"] == "Detail"

    def test_get_resume_not_found(self, auth_client):
        import uuid
        resp = auth_client.get(f"/api/v1/resume/resumes/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_resume(self, auth_client, user):
        resume = Resume.objects.create(user=user, title="Old Title")
        resp = auth_client.put(
            f"/api/v1/resume/resumes/{resume.uuid}/update/",
            {"title": "New Title"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        resume.refresh_from_db()
        assert resume.title == "New Title"

    def test_delete_resume(self, auth_client, user):
        resume = Resume.objects.create(user=user, title="Delete Me")
        resp = auth_client.delete(f"/api/v1/resume/resumes/{resume.uuid}/delete/")
        assert resp.status_code == status.HTTP_200_OK
        assert not Resume.objects.filter(id=resume.id).exists()

    def test_delete_resume_not_found(self, auth_client):
        import uuid
        resp = auth_client.delete(f"/api/v1/resume/resumes/{uuid.uuid4()}/delete/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProfileSectionViews:
    url = "/api/v1/resume/profile-sections/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_and_list(self, auth_client, user):
        resp = auth_client.post(self.url, {
            "section_type": "skills",
            "title": "Technical Skills",
            "content": json.dumps({"items": ["Python", "Django"]}),
            "order": 1,
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) == 1


@pytest.mark.django_db
class TestSkillVerificationViews:
    url = "/api/v1/resume/skill-verifications/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_and_list(self, auth_client, user):
        resp = auth_client.post(self.url, {
            "skill_name": "React",
            "skill_category": "frontend",
            "verification_method": "project",
            "score": 70,
            "level": "intermediate",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["skill_name"] == "React"


# ── Export service tests ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestResumeExportService:
    def _make_resume(self, user):
        return Resume.objects.create(
            user=user,
            title="Export Resume",
            personal_info={"full_name": "Test User", "email": "t@e.com"},
            summary="Senior engineer with 5 years of experience.",
            experience=[{
                "title": "Engineer", "company": "Acme",
                "start_date": "2020-01", "end_date": "2024-01",
                "description": "Built things.",
            }],
            education=[{"degree": "BSc", "field": "CS", "school": "MIT"}],
            skills=["Python", "Django", "React"],
            certifications=["AWS SAA"],
            languages=["English", "Arabic"],
        )

    def test_export_json(self, user):
        resume = self._make_resume(user)
        result = resume_export_service.export_json(resume)
        data = json.loads(result)
        assert data["personal_info"]["full_name"] == "Test User"
        assert "Python" in data["skills"]
        assert len(data["experience"]) == 1

    def test_export_html(self, user):
        resume = self._make_resume(user)
        html = resume_export_service.export_html(resume)
        assert isinstance(html, str)
        assert len(html) > 100

    def test_export_view_json(self, auth_client, user):
        resume = self._make_resume(user)
        resp = auth_client.post("/api/v1/resume/export/", {
            "resume_id": str(resume.uuid),
            "format": "json",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/json"
        assert ResumeExport.objects.filter(resume=resume, format="json").exists()

    def test_export_view_html(self, auth_client, user):
        resume = self._make_resume(user)
        resp = auth_client.post("/api/v1/resume/export/", {
            "resume_id": str(resume.uuid),
            "format": "html",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "text/html"

    def test_export_view_bad_format(self, auth_client, user):
        resume = self._make_resume(user)
        resp = auth_client.post("/api/v1/resume/export/", {
            "resume_id": str(resume.uuid),
            "format": "xlsx",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

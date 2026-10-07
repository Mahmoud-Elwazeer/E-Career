"""Tests for Rashid tool citation/evidence trailers.

Evaluated hydra-db/open-glean (Apache-2.0, 1583 stars) during the Master
Implementation Directive engagement: its Deep Research feature dedupes
retrieval results into a numbered citation list. Open Glean itself is
REFERENCE_ONLY here (it's a UI shell over a proprietary paid Hydra DB
backend we don't have access to), but the underlying idea — tell the user
exactly which record a tool's answer came from — is adapted into
`format_career_profile` / `format_salary_insights` / `format_match_score`
in `apps.intelligence.agent`, extracted out of the `@agent.tool` functions
so they're plain, DB-only functions testable without a live Bedrock call.

`AgentResponse.sources` in this module was previously dead code (declared,
never populated); these tests don't resurrect that field directly, but they
pin the actual mechanism now used instead (a "_Source: ..._" trailer on the
tool's returned text) so it doesn't silently regress.
"""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.career.models import CareerProfile, TalentScore
from apps.intelligence.agent import (
    format_career_profile,
    format_evidence_trailer,
    format_match_score,
    format_salary_insights,
)
from apps.jobs.models import Company, Job, Source
from apps.salary.models import SalaryData

User = get_user_model()


class FormatEvidenceTrailerTests(TestCase):
    def test_empty_sources_returns_empty_string(self):
        self.assertEqual(format_evidence_trailer([]), "")

    def test_single_source_is_wrapped(self):
        trailer = format_evidence_trailer(["CareerProfile#1"])
        self.assertEqual(trailer, "\n\n_Source: CareerProfile#1_")

    def test_multiple_sources_are_joined(self):
        trailer = format_evidence_trailer(["CareerProfile#1", "TalentScore#2"])
        self.assertEqual(trailer, "\n\n_Source: CareerProfile#1; TalentScore#2_")


class FormatCareerProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profile-user@example.com", password="pw-strong-123"
        )

    def test_no_profile_returns_plain_message_without_trailer(self):
        result = format_career_profile(self.user.id, "Nour")
        self.assertEqual(
            result, "No career profile found. Please complete your profile first."
        )
        self.assertNotIn("_Source:", result)

    def test_profile_without_talent_score_cites_only_profile(self):
        profile = CareerProfile.objects.create(
            user=self.user,
            cv_parsed_data={"skills": ["Python", "Django"]},
        )
        result = format_career_profile(self.user.id, "Nour")
        self.assertIn("Skills: Python, Django", result)
        self.assertIn(f"_Source: CareerProfile#{profile.pk}_", result)
        self.assertNotIn("TalentScore", result.split("_Source:")[1])

    def test_profile_with_talent_score_cites_both(self):
        profile = CareerProfile.objects.create(user=self.user)
        score = TalentScore.objects.create(user=self.user, overall_score=0.82)
        result = format_career_profile(self.user.id, "Nour")
        self.assertIn("Talent Score: 82/100", result)
        self.assertIn(
            f"_Source: CareerProfile#{profile.pk}; TalentScore#{score.pk}_", result
        )


class FormatSalaryInsightsTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Acme Corp", slug="acme-corp-salary-test")
        self.source = Source.objects.create(
            name="Test Source", slug="test-source-salary", url="https://example.com"
        )
        self._counter = 0

    def _make_job(self, title="Backend Engineer"):
        self._counter += 1
        return Job.objects.create(
            company=self.company,
            source=self.source,
            title=title,
            slug=f"{title.replace(' ', '-').lower()}-{self._counter}",
            location="Cairo",
            location_type="hybrid",
            industry="technology",
            experience_level="mid",
            description="desc",
            source_url=f"https://example.com/jobs/{title.replace(' ', '-').lower()}-{self._counter}",
            posted_at=datetime.date.today(),
        )

    def test_no_data_returns_plain_message_without_trailer(self):
        result = format_salary_insights("Nonexistent Role")
        self.assertIn("No salary data available", result)
        self.assertNotIn("_Source:", result)

    def test_cites_the_contributing_salary_rows(self):
        job = self._make_job()
        salary = SalaryData.objects.create(
            job=job, salary_min=50000, salary_max=70000, salary_currency="USD"
        )
        result = format_salary_insights("Backend Engineer")
        self.assertIn("Average: USD 60,000", result)
        self.assertIn(f"_Source: SalaryData#{salary.pk}_", result)

    def test_truncates_citation_list_beyond_five(self):
        for i in range(7):
            job = self._make_job(title=f"Backend Engineer {i}")
            SalaryData.objects.create(
                job=job, salary_min=50000, salary_max=70000, salary_currency="USD"
            )
        result = format_salary_insights("Backend Engineer")
        self.assertIn("+2 more", result)


class FormatMatchScoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="match-user@example.com", password="pw-strong-123"
        )
        self.company = Company.objects.create(name="Acme", slug="acme-corp-match-test")
        self.source = Source.objects.create(
            name="Test Source 2", slug="test-source-match", url="https://example2.com"
        )

    def test_no_profile_returns_plain_message_without_trailer(self):
        job = Job.objects.create(
            company=self.company,
            source=self.source,
            title="Data Scientist",
            slug="data-scientist-match-test",
            location="Cairo",
            location_type="hybrid",
            industry="technology",
            experience_level="mid",
            description="desc",
            source_url="https://example2.com/jobs/data-scientist",
            posted_at=datetime.date.today(),
        )
        result = format_match_score(self.user.id, str(job.uuid))
        self.assertIn("No career profile found", result)
        self.assertNotIn("_Source:", result)

    def test_unknown_job_returns_plain_message_without_trailer(self):
        CareerProfile.objects.create(user=self.user)
        result = format_match_score(self.user.id, "00000000-0000-0000-0000-000000000000")
        self.assertIn("not found", result)
        self.assertNotIn("_Source:", result)

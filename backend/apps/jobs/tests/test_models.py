"""
Tests for the jobs app models.
"""
import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.jobs.models import Job, Company, Tag, JobTag, Source
from apps.employers.models import JobApplication

User = get_user_model()


class JobModelTest(TestCase):
    """Tests for the Job model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-model',
            description='A test company',
            website='https://testcompany.com',
            logo_url='https://testcompany.com/logo.png',
            size='1-10',
            industry='technology',
            is_verified=True,
        )

        self.source = Source.objects.create(
            name='Test Source',
            slug='test-source-model',
            url='https://testsource.com',
        )

        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            slug='software-engineer-model-test',
            description='We are looking for a software engineer',
            location='Cairo, Egypt',
            location_type='hybrid',
            industry='technology',
            employment_type='full_time',
            experience_level='mid',
            work_arrangement='hybrid',
            salary_min=50000,
            salary_max=80000,
            salary_currency='USD',
            source_url='https://testsource.com/jobs/1',
            source=self.source,
            status='active',
            posted_at=datetime.date.today(),
        )

    def test_job_creation(self):
        """Test that a job can be created."""
        self.assertEqual(self.job.title, 'Software Engineer')
        self.assertEqual(self.job.company, self.company)
        self.assertEqual(self.job.status, 'active')
        self.assertIsNotNone(self.job.uuid)

    def test_job_str(self):
        """Test the string representation of a job."""
        self.assertEqual(str(self.job), f"{self.job.title} @ {self.job.company.name}")

    def test_job_fields(self):
        """Test that job fields are set correctly."""
        self.assertEqual(self.job.employment_type, 'full_time')
        self.assertEqual(self.job.experience_level, 'mid')
        self.assertEqual(self.job.work_arrangement, 'hybrid')
        self.assertEqual(self.job.salary_min, 50000)
        self.assertEqual(self.job.salary_max, 80000)

    def test_job_company_relationship(self):
        """Test the company-job relationship."""
        self.assertIn(self.job, self.company.jobs.all())


class CompanyModelTest(TestCase):
    """Tests for the Company model."""

    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-comp',
            description='A test company',
            website='https://testcompany.com',
            logo_url='https://testcompany.com/logo.png',
            size='1-10',
            industry='technology',
            is_verified=True,
        )

    def test_company_creation(self):
        """Test that a company can be created."""
        self.assertEqual(self.company.name, 'Test Company')
        self.assertEqual(self.company.slug, 'test-company-comp')
        self.assertTrue(self.company.is_verified)

    def test_company_str(self):
        """Test the string representation of a company."""
        self.assertEqual(str(self.company), self.company.name)

    def test_company_fields(self):
        """Test company fields are set correctly."""
        self.assertEqual(self.company.industry, 'technology')
        self.assertEqual(self.company.website, 'https://testcompany.com')
        self.assertTrue(self.company.is_verified)


class TagModelTest(TestCase):
    """Tests for the Tag model."""

    def setUp(self):
        """Set up test data."""
        self.tag = Tag.objects.create(
            name='Python',
            slug='python-model-test',
            category='language',
        )

    def test_tag_creation(self):
        """Test that a tag can be created."""
        self.assertEqual(self.tag.name, 'Python')
        self.assertEqual(self.tag.slug, 'python-model-test')

    def test_tag_str(self):
        """Test the string representation of a tag."""
        self.assertEqual(str(self.tag), self.tag.name)

    def test_job_tags(self):
        """Test the many-to-many relationship between jobs and tags."""
        company = Company.objects.create(
            name='Tag Test Co',
            slug='tag-test-co',
            industry='technology',
        )
        source = Source.objects.create(
            name='Tag Source',
            slug='tag-source',
            url='https://tagsource.com',
        )
        job = Job.objects.create(
            company=company,
            title='Tag Test Job',
            slug='tag-test-job',
            description='A job to test tags',
            location='Cairo',
            location_type='remote',
            industry='technology',
            experience_level='mid',
            source_url='https://tagsource.com/jobs/1',
            source=source,
            posted_at=datetime.date.today(),
        )
        JobTag.objects.create(job=job, tag=self.tag)
        self.assertIn(self.tag, job.tags.all())
        self.assertEqual(job.tags.count(), 1)


class JobApplicationModelTest(TestCase):
    """Tests for the JobApplication model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-app',
            description='A test company',
            website='https://testcompany.com',
            industry='technology',
            is_verified=True,
        )

        self.source = Source.objects.create(
            name='App Source',
            slug='app-source',
            url='https://appsource.com',
        )

        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            slug='software-engineer-app-test',
            description='We are looking for a software engineer',
            location='Cairo, Egypt',
            location_type='hybrid',
            industry='technology',
            employment_type='full_time',
            experience_level='mid',
            source_url='https://appsource.com/jobs/1',
            source=self.source,
            posted_at=datetime.date.today(),
        )

        self.application = JobApplication.objects.create(
            user=self.user,
            job=self.job,
            status='applied',
        )

    def test_application_creation(self):
        """Test that an application can be created."""
        self.assertEqual(self.application.user, self.user)
        self.assertEqual(self.application.job, self.job)
        self.assertEqual(self.application.status, 'applied')

    def test_application_str(self):
        """Test the string representation of an application."""
        expected = f"{self.user.email} → {self.job.title}"
        self.assertEqual(str(self.application), expected)

    def test_application_status_choices(self):
        """Test the status choices."""
        valid_statuses = ['applied', 'viewed', 'shortlisted', 'rejected']
        for status_val in valid_statuses:
            self.application.status = status_val
            self.application.save()
            self.assertEqual(self.application.status, status_val)

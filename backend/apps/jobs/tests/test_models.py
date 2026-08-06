"""
Tests for the jobs app models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import Job, Company, JobTag, JobApplication

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
            slug='test-company',
            description='A test company',
            website='https://testcompany.com',
            logo='https://testcompany.com/logo.png',
            size='1-10',
            industry='Technology',
            is_verified=True,
            created_by=self.user
        )
        
        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='We are looking for a software engineer',
            location='Cairo, Egypt',
            employment_type='full_time',
            experience_level='mid',
            remote_type='hybrid',
            salary_min=50000,
            salary_max=80000,
            salary_currency='USD',
            is_active=True,
            posted_at=timezone.now() - timedelta(days=1)
        )

    def test_job_creation(self):
        """Test that a job can be created."""
        self.assertEqual(self.job.title, 'Software Engineer')
        self.assertEqual(self.job.company, self.company)
        self.assertTrue(self.job.is_active)
        self.assertIsNotNone(self.job.uuid)

    def test_job_str(self):
        """Test the string representation of a job."""
        self.assertEqual(str(self.job), f"{self.job.title} at {self.job.company.name}")

    def test_job_get_absolute_url(self):
        """Test the get_absolute_url method."""
        url = self.job.get_absolute_url()
        self.assertIn('/jobs/', url)
        self.assertIn(str(self.job.uuid), url)

    def test_job_is_expired(self):
        """Test the is_expired method."""
        # Job posted 1 day ago, not expired (90 day threshold)
        self.assertFalse(self.job.is_expired())
        
        # Create a job that is 91 days old
        old_job = Job.objects.create(
            company=self.company,
            title='Old Job',
            description='An old job',
            location='Cairo, Egypt',
            employment_type='full_time',
            experience_level='mid',
            remote_type='onsite',
            salary_min=50000,
            salary_max=80000,
            salary_currency='USD',
            is_active=True,
            posted_at=timezone.now() - timedelta(days=91)
        )
        self.assertTrue(old_job.is_expired())

    def test_job_manager_active(self):
        """Test the active manager."""
        active_jobs = Job.objects.active()
        self.assertIn(self.job, active_jobs)
        
        # Deactivate the job
        self.job.is_active = False
        self.job.save()
        
        active_jobs = Job.objects.active()
        self.assertNotIn(self.job, active_jobs)


class CompanyModelTest(TestCase):
    """Tests for the Company model."""

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
            slug='test-company',
            description='A test company',
            website='https://testcompany.com',
            logo='https://testcompany.com/logo.png',
            size='1-10',
            industry='Technology',
            is_verified=True,
            created_by=self.user
        )

    def test_company_creation(self):
        """Test that a company can be created."""
        self.assertEqual(self.company.name, 'Test Company')
        self.assertEqual(self.company.slug, 'test-company')
        self.assertTrue(self.company.is_verified)

    def test_company_str(self):
        """Test the string representation of a company."""
        self.assertEqual(str(self.company), self.company.name)

    def test_company_get_absolute_url(self):
        """Test the get_absolute_url method."""
        url = self.company.get_absolute_url()
        self.assertIn('/companies/', url)
        self.assertIn(self.company.slug, url)


class JobTagModelTest(TestCase):
    """Tests for the JobTag model."""

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
            slug='test-company',
            description='A test company',
            website='https://testcompany.com',
            logo='https://testcompany.com/logo.png',
            size='1-10',
            industry='Technology',
            is_verified=True,
            created_by=self.user
        )
        
        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='We are looking for a software engineer',
            location='Cairo, Egypt',
            employment_type='full_time',
            experience_level='mid',
            remote_type='hybrid',
            salary_min=50000,
            salary_max=80000,
            salary_currency='USD',
            is_active=True,
            posted_at=timezone.now() - timedelta(days=1)
        )
        
        self.tag = JobTag.objects.create(
            name='Python',
            slug='python',
            description='Python programming language'
        )
        
        self.job.tags.add(self.tag)

    def test_tag_creation(self):
        """Test that a tag can be created."""
        self.assertEqual(self.tag.name, 'Python')
        self.assertEqual(self.tag.slug, 'python')

    def test_tag_str(self):
        """Test the string representation of a tag."""
        self.assertEqual(str(self.tag), self.tag.name)

    def test_job_tags(self):
        """Test the many-to-many relationship between jobs and tags."""
        self.assertIn(self.tag, self.job.tags.all())
        self.assertEqual(self.job.tags.count(), 1)


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
            slug='test-company',
            description='A test company',
            website='https://testcompany.com',
            logo='https://testcompany.com/logo.png',
            size='1-10',
            industry='Technology',
            is_verified=True,
            created_by=self.user
        )
        
        self.job = Job.objects.create(
            company=self.company,
            title='Software Engineer',
            description='We are looking for a software engineer',
            location='Cairo, Egypt',
            employment_type='full_time',
            experience_level='mid',
            remote_type='hybrid',
            salary_min=50000,
            salary_max=80000,
            salary_currency='USD',
            is_active=True,
            posted_at=timezone.now() - timedelta(days=1)
        )
        
        self.application = JobApplication.objects.create(
            user=self.user,
            job=self.job,
            status='submitted',
            cover_letter='I am interested in this position.',
            resume='path/to/resume.pdf'
        )

    def test_application_creation(self):
        """Test that an application can be created."""
        self.assertEqual(self.application.user, self.user)
        self.assertEqual(self.application.job, self.job)
        self.assertEqual(self.application.status, 'submitted')

    def test_application_str(self):
        """Test the string representation of an application."""
        self.assertEqual(
            str(self.application),
            f"{self.user.email} - {self.job.title}"
        )

    def test_application_status_choices(self):
        """Test the status choices."""
        valid_statuses = ['submitted', 'reviewed', 'interviewed', 'offered', 'accepted', 'rejected']
        for status in valid_statuses:
            self.application.status = status
            self.application.save()
            self.assertEqual(self.application.status, status)
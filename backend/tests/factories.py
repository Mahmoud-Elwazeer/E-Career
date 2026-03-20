"""
factory_boy model factories for generating test data.
"""
import datetime
import factory
import factory.django
from django.contrib.auth import get_user_model
from apps.jobs.models import Company, Source, Tag, Job
from apps.users.models import SavedJob, Alert, Notification
from apps.core.models import FeatureFlag

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@gmail.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")
    role = "user"
    status = "active"
    is_active = True


class AdminUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"admin{n}@gmail.com")
    role = "admin"
    is_staff = True
    is_superuser = True


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Company {n}")
    slug = factory.Sequence(lambda n: f"company-{n}")
    industry = "technology"
    website = factory.LazyAttribute(lambda o: f"https://{o.slug}.example.com")
    snippet = factory.Faker("sentence", nb_words=10)
    is_active = True


class SourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Source

    name = factory.Sequence(lambda n: f"Source {n}")
    slug = factory.Sequence(lambda n: f"source-{n}")
    url = factory.LazyAttribute(lambda o: f"https://{o.slug}.example.com")
    type = "manual"
    is_active = True


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag{n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")
    category = "skill"


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    title = factory.Faker("job")
    slug = factory.Sequence(lambda n: f"job-{n}")
    company = factory.SubFactory(CompanyFactory)
    source = factory.SubFactory(SourceFactory)
    location = "Remote"
    location_type = "remote"
    industry = "technology"
    experience_level = "mid"
    description = factory.Faker("paragraph", nb_sentences=5)
    source_url = factory.Sequence(lambda n: f"https://example.com/jobs/{n}")
    posted_at = factory.LazyFunction(datetime.date.today)
    status = "active"
    salary_min = 5000
    salary_max = 10000
    salary_currency = "USD"


class SavedJobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavedJob

    user = factory.SubFactory(UserFactory)
    job = factory.SubFactory(JobFactory)


class AlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Alert

    user = factory.SubFactory(UserFactory)
    keyword = "Python"
    frequency = "daily"
    is_active = True


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence", nb_words=6)
    body = factory.Faker("paragraph", nb_sentences=2)
    type = "system"
    is_read = False


class FeatureFlagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeatureFlag

    key = factory.Sequence(lambda n: f"flag_{n}")
    label = factory.Sequence(lambda n: f"Flag {n}")
    is_enabled = True

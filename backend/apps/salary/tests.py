"""
Tests for the Salary Intelligence app — models, views, and benchmark logic.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.salary.models import (
    SalaryData, MarketRate, SalaryBenchmark, SalaryInsight, SalaryAlert,
)

User = get_user_model()


# ── Model tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSalaryDataModel:
    def test_annualize_yearly(self, job):
        sd = SalaryData.objects.create(
            job=job,
            salary_min=Decimal("80000"),
            salary_max=Decimal("120000"),
            frequency="yearly",
        )
        sd.annualize_salary()
        assert sd.annualized_salary_min == Decimal("80000")
        assert sd.annualized_salary_max == Decimal("120000")

    def test_annualize_monthly(self, job):
        sd = SalaryData.objects.create(
            job=job,
            salary_min=Decimal("6000"),
            salary_max=Decimal("10000"),
            frequency="monthly",
        )
        sd.annualize_salary()
        assert sd.annualized_salary_min == Decimal("72000")
        assert sd.annualized_salary_max == Decimal("120000")

    def test_annualize_weekly(self, job):
        sd = SalaryData.objects.create(
            job=job,
            salary_min=Decimal("1500"),
            salary_max=Decimal("2000"),
            frequency="weekly",
        )
        sd.annualize_salary()
        assert sd.annualized_salary_min == Decimal("78000")
        assert sd.annualized_salary_max == Decimal("104000")

    def test_annualize_hourly(self, job):
        sd = SalaryData.objects.create(
            job=job,
            salary_min=Decimal("40"),
            salary_max=Decimal("60"),
            frequency="hourly",
        )
        sd.annualize_salary()
        assert sd.annualized_salary_min == Decimal("83200")
        assert sd.annualized_salary_max == Decimal("124800")

    def test_str_representation(self, job):
        sd = SalaryData.objects.create(
            job=job,
            salary_min=Decimal("80000"),
            salary_max=Decimal("120000"),
        )
        assert "80000" in str(sd)
        assert "120000" in str(sd)


@pytest.mark.django_db
class TestMarketRateModel:
    def test_create_market_rate(self):
        mr = MarketRate.objects.create(
            role="Backend Engineer",
            location="Dubai, UAE",
            experience_level="mid",
            currency="USD",
            percentile_25=Decimal("70000"),
            percentile_50=Decimal("90000"),
            percentile_75=Decimal("115000"),
            percentile_90=Decimal("140000"),
            sample_size=50,
        )
        assert mr.role == "Backend Engineer"
        assert mr.percentile_50 == Decimal("90000")
        assert "Backend Engineer" in str(mr)

    def test_unique_constraint(self):
        MarketRate.objects.create(
            role="Frontend Dev", location="Remote", experience_level="senior",
            percentile_25=Decimal("80000"), percentile_50=Decimal("100000"),
            percentile_75=Decimal("120000"), percentile_90=Decimal("150000"),
        )
        with pytest.raises(Exception):
            MarketRate.objects.create(
                role="Frontend Dev", location="Remote", experience_level="senior",
                percentile_25=Decimal("85000"), percentile_50=Decimal("105000"),
                percentile_75=Decimal("125000"), percentile_90=Decimal("155000"),
            )


@pytest.mark.django_db
class TestSalaryBenchmarkModel:
    def test_create_benchmark(self, user):
        bm = SalaryBenchmark.objects.create(
            user=user,
            role="Backend Engineer",
            location="Dubai",
            experience_level="mid",
            user_salary_min=Decimal("75000"),
            user_salary_max=Decimal("85000"),
            market_median=Decimal("90000"),
            market_25th=Decimal("70000"),
            market_75th=Decimal("115000"),
            percentile_rank=40,
            is_underpaid="maybe",
        )
        assert bm.percentile_rank == 40
        assert bm.is_underpaid == "maybe"


@pytest.mark.django_db
class TestSalaryInsightModel:
    def test_create_insight(self, user):
        ins = SalaryInsight.objects.create(
            user=user,
            insight_type="user_underpaid",
            title="Below market rate",
            description="Your salary is 15% below the market median.",
            priority="high",
        )
        assert ins.is_actionable is True
        assert "underpaid" in str(ins)


@pytest.mark.django_db
class TestSalaryAlertModel:
    def test_create_alert(self, user):
        alert = SalaryAlert.objects.create(
            user=user,
            alert_type="market_increase",
            title="Market rates increased",
            description="Backend Engineer salaries in Dubai increased by 8%.",
            impact="moderate",
        )
        assert alert.is_read is False
        assert alert.is_resolved is False

    def test_mark_as_read(self, user):
        alert = SalaryAlert.objects.create(
            user=user,
            alert_type="new_high_paying_job",
            title="New match",
            description="A new job matches your profile.",
        )
        alert.is_read = True
        alert.save()
        alert.refresh_from_db()
        assert alert.is_read is True


# ── View tests ───────────────────────────────────────────────────────────────


@pytest.fixture
def market_rate(db):
    return MarketRate.objects.create(
        role="Backend Engineer",
        location="Dubai",
        experience_level="mid",
        currency="USD",
        percentile_25=Decimal("70000"),
        percentile_50=Decimal("90000"),
        percentile_75=Decimal("115000"),
        percentile_90=Decimal("140000"),
        sample_size=42,
    )


@pytest.mark.django_db
class TestSalaryBenchmarkView:
    url = "/api/v1/salary/benchmark/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_benchmark_with_market_data(self, auth_client, market_rate):
        resp = auth_client.get(self.url, {
            "role": "Backend Engineer",
            "location": "Dubai",
            "experience_level": "mid",
            "salary_min": "75000",
            "salary_max": "85000",
        })
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()["data"]
        assert data["market_median"] == "90000.00"
        assert data["is_underpaid"] in ("yes", "maybe", "fair", "above")

    def test_benchmark_no_market_data(self, auth_client):
        resp = auth_client.get(self.url, {
            "role": "Nonexistent Role",
            "location": "Nowhere",
            "experience_level": "entry",
        })
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMarketRatesView:
    url = "/api/v1/salary/market-rates/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_filter_by_role(self, auth_client, market_rate):
        resp = auth_client.get(self.url, {"role": "Backend"})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) >= 1

    def test_returns_empty_for_no_match(self, auth_client):
        resp = auth_client.get(self.url, {"role": "zzzNonExistent"})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) == 0


@pytest.mark.django_db
class TestSalaryInsightsView:
    url = "/api/v1/salary/insights/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_insights(self, auth_client, user):
        SalaryInsight.objects.create(
            user=user, insight_type="user_underpaid",
            title="Underpaid", description="You are underpaid.",
        )
        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) == 1


@pytest.mark.django_db
class TestSalaryAlertsView:
    url = "/api/v1/salary/alerts/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_alerts(self, auth_client, user):
        SalaryAlert.objects.create(
            user=user, alert_type="market_increase",
            title="Market up", description="Salaries rose.",
        )
        resp = auth_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["data"]) == 1

    def test_mark_alert_as_read(self, auth_client, user):
        alert = SalaryAlert.objects.create(
            user=user, alert_type="new_high_paying_job",
            title="New match", description="A new job.",
        )
        resp = auth_client.post(f"/api/v1/salary/alerts/{alert.id}/read/")
        assert resp.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.is_read is True

    def test_mark_nonexistent_alert(self, auth_client):
        resp = auth_client.post("/api/v1/salary/alerts/99999/read/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

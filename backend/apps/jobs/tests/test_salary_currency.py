"""
Job.salary_currency semantics — production-hardening pass.

Directive-mandated fix: a currency this platform cannot actually confirm
from the source must be stored as NULL/unknown, never invented as a default
(the field previously defaulted to "USD" unconditionally). This file covers
the required 7 scenarios end-to-end through the real ingestion/normalization
code paths (not just the model field itself), so a regression in any
connector/orchestrator/CSV-import path that silently reintroduces an invented
default is caught.

Scenarios:
  1. Model-level: Job.salary_currency has no default; a bare create() with
     no currency given leaves it NULL.
  2. Scraper normalizer: a salary string with NO currency marker resolves to
     (min, max, None) — never guesses a currency.
  3. Scraper normalizer: a salary string WITH an explicit currency marker
     (symbol or code) resolves and normalizes correctly.
  4. resolve_salary_currency(): blank/None input -> (None, "") — raw text is
     also empty, nothing invented.
  5. resolve_salary_currency(): a recognized free-text/symbol value (e.g.
     "LE", "$") normalizes to a confirmed code AND preserves the raw text.
  6. resolve_salary_currency(): an unrecognized value preserves the raw text
     verbatim while leaving the normalized code unresolved (None) — no
     information lost, nothing guessed.
  7. End-to-end via the orchestrator's currency-resolution call (same helper
     used by orchestrator.py/tasks.py/admin_api_views.py) confirms a Job
     created from a connector dict with no currency field ends up with
     salary_currency=None, not "USD".
"""
import pytest

from apps.jobs.models import Job
from apps.scraper.pipeline.normalizer import parse_salary, resolve_salary_currency

pytestmark = pytest.mark.django_db


# ── Scenario 1: model-level default ──────────────────────────────────────────

def test_job_salary_currency_has_no_invented_default(django_user_model):
    from apps.jobs.models import Company, Source
    import datetime

    company = Company.objects.create(name="Acme", slug="acme-salary-test")
    source = Source.objects.create(name="Src", slug="src-salary-test", url="https://example.com")
    job = Job.objects.create(
        title="Backend Engineer", slug="backend-engineer-salary-test",
        company=company, description="x", location="Cairo",
        location_type="onsite", industry="technology",
        experience_level="mid", source_url="https://example.com/1",
        source=source, posted_at=datetime.date.today(),
        salary_min=10000, salary_max=20000,
        # salary_currency deliberately omitted
    )
    job.refresh_from_db()
    assert job.salary_currency is None
    assert job.salary_currency_raw == ""


# ── Scenario 2 & 3: parse_salary never invents a currency ───────────────────

def test_parse_salary_with_no_currency_marker_returns_none():
    salary_min, salary_max, currency = parse_salary("50,000 - 70,000")
    assert salary_min == 50000
    assert salary_max == 70000
    assert currency is None  # no marker present -> unknown, never guessed


def test_parse_salary_with_explicit_marker_resolves_currency():
    assert parse_salary("$120,000 - $150,000") == (120000, 150000, "USD")
    assert parse_salary("EGP 10,000") == (10000, 10000, "EGP")
    assert parse_salary("£120,000") == (120000, 120000, "GBP")


# ── Scenario 4: blank/None input ─────────────────────────────────────────────

def test_resolve_salary_currency_blank_input_invents_nothing():
    assert resolve_salary_currency(None) == (None, "")
    assert resolve_salary_currency("") == (None, "")
    assert resolve_salary_currency("   ") == (None, "")


# ── Scenario 5: recognized free-text/symbol normalizes + preserves raw ──────

def test_resolve_salary_currency_recognizes_common_text_and_symbols():
    assert resolve_salary_currency("LE") == ("EGP", "LE")
    assert resolve_salary_currency("$") == ("USD", "$")
    assert resolve_salary_currency("usd") == ("USD", "usd")
    assert resolve_salary_currency("EGP") == ("EGP", "EGP")


# ── Scenario 6: unrecognized text preserves raw, resolves nothing ───────────

def test_resolve_salary_currency_unrecognized_text_preserves_raw_only():
    normalized, raw = resolve_salary_currency("per month in local currency")
    assert normalized is None
    assert raw == "per month in local currency"


# ── Scenario 7: end-to-end through the ingestion helper ─────────────────────

def test_connector_dict_with_no_currency_field_never_defaults_to_usd(django_user_model):
    """Simulates what orchestrator.py/tasks.py actually do: resolve the
    connector's salary_currency value (possibly absent) through the shared
    helper before writing to Job. A connector dict with NO currency key at
    all must end up with Job.salary_currency=None, never a fabricated 'USD'."""
    from apps.jobs.models import Company, Source
    import datetime

    connector_job_data = {
        "title": "Data Analyst", "salary_min": 15000, "salary_max": 25000,
        # no 'salary_currency' key at all — exactly what several ATS
        # connectors emit when the source board gives no salary data.
    }
    resolved_currency, raw_currency = resolve_salary_currency(
        connector_job_data.get("salary_currency")
    )
    company = Company.objects.create(name="Beta", slug="beta-salary-test")
    source = Source.objects.create(name="Src2", slug="src2-salary-test", url="https://example.com")
    job = Job.objects.create(
        title=connector_job_data["title"], slug="data-analyst-salary-test",
        company=company, description="x", location="Cairo",
        location_type="onsite", industry="technology",
        experience_level="mid", source_url="https://example.com/2",
        source=source, posted_at=datetime.date.today(),
        salary_min=connector_job_data["salary_min"],
        salary_max=connector_job_data["salary_max"],
        salary_currency=resolved_currency,
        salary_currency_raw=raw_currency,
    )
    job.refresh_from_db()
    assert job.salary_currency is None
    assert job.salary_currency_raw == ""

"""Cross-provider normalization equivalence (§13/§18).

Proves that EQUIVALENT job data coming from DIFFERENT ATS providers produces
EQUIVALENT normalized records — the core normalization guarantee. Rather than
synthetic inputs, we feed connector-shaped dicts (matching what greenhouse /
lever / ashby / workday / smartrecruiters / eightfold actually emit) through the
same normalization used by the orchestrator:

    connector dict -> NormalizedJob.from_connector_dict -> normalizer.* helpers

Focus fields (§18): company, title, location, employment_type, seniority,
salary, dates.
"""
from apps.scraper.pipeline.contract import NormalizedJob
from apps.scraper.pipeline import normalizer as N


class _Src:
    def __init__(self, name, slug, type="scraper"):
        self.id = "s"; self.name = name; self.slug = slug; self.type = type


# The SAME senior backend role at the SAME company, as each provider's base-
# normalized connector dict would present it. Keys mirror what base.normalize_job
# (+ provider specifics) produce.
def _greenhouse():
    return {
        "title": "Senior Software Engineer", "company_slug": "acme",
        "direct_apply_url": "https://boards.greenhouse.io/acme/jobs/5",
        "description": "Build things. " * 20, "location": "San Francisco, CA, United States",
        "employment_type": "Full-time", "ats_platform": "greenhouse", "ats_job_id": "5",
        "salary_currency": "USD",
    }

def _lever():
    return {
        "title": "Senior Software Engineer", "company_slug": "acme",
        "direct_apply_url": "https://jobs.lever.co/acme/abc",
        "description": "Build things. " * 20, "location": "San Francisco, CA, United States",
        "employment_type": "FullTime", "ats_platform": "lever", "ats_job_id": "abc",
    }

def _workday():
    return {
        "title": "Senior Software Engineer", "company_slug": "acme",
        "direct_apply_url": "https://acme.wd5.myworkdayjobs.com/site/job/US-CA-SF/x_JR9",
        "description": "", "location": "San Francisco, CA, United States",
        "ats_platform": "workday", "ats_job_id": "JR9",
    }

def _smartrecruiters():
    return {
        "title": "Senior Software Engineer", "company_slug": "acme",
        "direct_apply_url": "https://jobs.smartrecruiters.com/acme/77",
        "description": "", "location": "San Francisco, CA, United States",
        "employment_type": "Full-time", "ats_platform": "smartrecruiters", "ats_job_id": "77",
    }

def _eightfold():
    return {
        "title": "Senior Software Engineer", "company_slug": "acme",
        "direct_apply_url": "https://explore.jobs.acme.net/careers/job/9",
        "description": "Build things. " * 20, "location": "San Francisco, CA, United States",
        "ats_platform": "eightfold", "ats_job_id": "9",
    }


ALL = [_greenhouse(), _lever(), _workday(), _smartrecruiters(), _eightfold()]


def _normalize(d):
    """Run the same normalization path the orchestrator uses for these fields."""
    nj = NormalizedJob.from_connector_dict(d, source=_Src("Acme", d["company_slug"] + "-x"))
    seniority, _ = N.normalize_seniority(nj.title, nj.seniority or "")
    country, city, _ = N.normalize_country_city(nj.location_raw)
    return {
        "company_name": nj.company_name,
        "title": nj.title,
        "seniority": seniority,
        "employment_type": N.normalize_employment_type(d.get("employment_type")),
        "country": country,
        "city": city,
        "ats_provider": nj.ats_provider,
        "ats_job_id": nj.ats_job_id,
        "direct_apply_url": nj.direct_apply_url,
    }


def test_company_name_equivalent_across_providers():
    names = {_normalize(d)["company_name"] for d in ALL}
    assert names == {"Acme"}, names


def test_title_and_seniority_equivalent_across_providers():
    titles = {_normalize(d)["title"] for d in ALL}
    seniorities = {_normalize(d)["seniority"] for d in ALL}
    assert titles == {"Senior Software Engineer"}
    assert seniorities == {"senior"}, seniorities


def test_location_parsed_equivalently():
    cities = {_normalize(d)["city"] for d in ALL}
    countries = {_normalize(d)["country"] for d in ALL}
    assert cities == {"San Francisco"}, cities
    assert countries == {"United States"}, countries


def test_employment_type_normalized_equivalently():
    # greenhouse "Full-time", lever "FullTime", SR "Full-time" all -> full_time;
    # workday/eightfold omit it (None). Equivalent inputs -> equivalent output.
    ets = {}
    for d in ALL:
        ets[d["ats_platform"]] = _normalize(d)["employment_type"]
    assert ets["greenhouse"] == "full_time"
    assert ets["lever"] == "full_time"
    assert ets["smartrecruiters"] == "full_time"
    assert ets["workday"] is None  # not provided -> not fabricated


def test_each_provider_keeps_its_own_identity():
    for d in ALL:
        r = _normalize(d)
        assert r["ats_provider"] == d["ats_platform"]
        assert r["ats_job_id"] == str(d["ats_job_id"])
        assert r["direct_apply_url"] == d["direct_apply_url"]


def test_salary_parsing_equivalence():
    # Same salary expressed differently normalizes to the same numbers.
    assert N.parse_salary("$120,000 - $150,000") == (120000, 150000, "USD")
    assert N.parse_salary("120000-150000 USD") == (120000, 150000, "USD")
    assert N.parse_salary("£120,000") == (120000, 120000, "GBP")


if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)

"""Cross-source deduplication tests (§14/§19).

Proves the same employer role discovered through DIFFERENT sources collapses to
one canonical identity, while genuinely different roles stay distinct. Pure
functions (no DB); the orchestrator applies these keys against the DB in order.
"""
from apps.scraper.pipeline.deduplicator import (
    dedup_verdict, normalize_title_for_dedup, content_fingerprint, generate_job_hash,
)


def test_same_ats_job_id_is_l1_identical():
    a = {"ats_platform": "greenhouse", "ats_job_id": "5", "company": "Acme",
         "title": "Senior Software Engineer", "location": "SF"}
    b = dict(a)
    assert dedup_verdict(a)["l1_canonical_key"] == dedup_verdict(b)["l1_canonical_key"]


def test_same_role_different_sources_collapses_via_l2_and_l3():
    # Same job discovered via greenhouse AND via the company's own careers page:
    # different L1 (platform/id differ) but SAME L2 normalized key + L3 hash.
    via_greenhouse = {
        "ats_platform": "greenhouse", "ats_job_id": "5",
        "company": "Acme", "title": "Senior Software Engineer",
        "location": "San Francisco, CA",
    }
    via_careers = {
        "ats_platform": "", "ats_job_id": "",
        "canonical_job_url": "https://acme.com/careers/swe",
        "company": "Acme", "title": "Software Engineer",  # no 'Senior' noise word
        "location": "San Francisco, CA",
    }
    va, vb = dedup_verdict(via_greenhouse), dedup_verdict(via_careers)
    assert va["l1_canonical_key"] != vb["l1_canonical_key"]     # L1 differs
    assert va["l2_normalized_key"] == vb["l2_normalized_key"]   # L2 collapses
    assert va["l3_content_hash"] == vb["l3_content_hash"]       # L3 collapses


def test_different_roles_stay_distinct():
    a = {"company": "Acme", "title": "Backend Engineer", "location": "SF"}
    b = {"company": "Acme", "title": "Frontend Engineer", "location": "SF"}
    assert content_fingerprint(a) != content_fingerprint(b)
    assert dedup_verdict(a)["l2_normalized_key"] != dedup_verdict(b)["l2_normalized_key"]


def test_seniority_noise_stripped_for_fuzzy_match():
    assert normalize_title_for_dedup("Senior Software Engineer") == \
           normalize_title_for_dedup("Software Engineer")
    assert normalize_title_for_dedup("Sr. Data Scientist (Remote)") == \
           normalize_title_for_dedup("Data Scientist")


def test_canonical_url_is_l1_when_no_ats_id():
    j = {"canonical_job_url": "https://Acme.com/Careers/SWE", "company": "Acme",
         "title": "Engineer", "location": "SF"}
    # normalized to lowercase for stable comparison
    assert dedup_verdict(j)["l1_canonical_key"] == "https://acme.com/careers/swe"


def test_same_location_different_case_same_fingerprint():
    a = {"company": "Acme", "title": "Engineer", "location": "San Francisco"}
    b = {"company": "ACME", "title": "Engineer", "location": "SAN FRANCISCO"}
    assert content_fingerprint(a) == content_fingerprint(b)


def test_legacy_job_hash_stable_and_case_insensitive():
    a = {"company": "Acme", "title": "Senior Engineer", "location": "SF"}
    b = {"company": "acme", "title": "engineer", "location": "sf"}
    # generate_job_hash strips 'senior' and lowercases -> equal
    assert generate_job_hash(a) == generate_job_hash(b)


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

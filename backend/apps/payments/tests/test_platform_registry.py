"""Tests for the centralized Platform/Product registry (directive Part XII).

These assert the registry is the single source of truth and that the legacy
`references.Platform` facade stays byte-for-byte compatible with every existing
consumer (model-field choices/defaults, `dict(CHOICES)`, `in ALL`).

Pure-Python — no DB, no Django models — so the registry contract is pinned
independently of migrations.
"""
import pytest

from apps.payments import platforms
from apps.payments.references import Platform, generate_reference


# ── Registry invariants ───────────────────────────────────────────────────────
def test_registry_has_the_four_known_platforms():
    assert platforms.codes() == frozenset({"C", "E", "F", "K"})


def test_default_code_is_career():
    assert platforms.DEFAULT_CODE == "C"
    assert platforms.get(platforms.DEFAULT_CODE).slug == "career"


def test_choices_shape_matches_field_choices():
    assert platforms.choices() == [
        ("C", "Career"), ("E", "Education"),
        ("F", "Freelancing"), ("K", "Kids"),
    ]


def test_get_resolves_rich_metadata():
    career = platforms.get("C")
    assert career.name == "Career"
    assert career.slug == "career"
    assert career.merchant_prefix == "USAM-CAREER"
    assert career.default_currency == "EGP"
    assert career.is_chargeable is True


def test_get_by_slug_round_trips():
    assert platforms.get_by_slug("education").code == "E"


def test_unknown_code_raises_rather_than_returning_none():
    with pytest.raises(ValueError):
        platforms.get("Z")
    with pytest.raises(ValueError):
        platforms.get_by_slug("nope")


def test_is_valid_and_helpers():
    assert platforms.is_valid("C") is True
    assert platforms.is_valid("Z") is False
    assert platforms.merchant_prefix_for("E") == "USAM-EDU"
    assert platforms.default_currency_for("F") == "EGP"


def test_registry_has_no_duplicate_codes_or_slugs():
    defs = platforms.all_platforms()
    assert len({d.code for d in defs}) == len(defs)
    assert len({d.slug for d in defs}) == len(defs)


# ── Facade backward-compatibility ─────────────────────────────────────────────
def test_facade_constants_derive_from_registry():
    assert Platform.CAREER == "C"
    assert Platform.EDUCATION == "E"
    assert Platform.FREELANCING == "F"
    assert Platform.KIDS == "K"


def test_facade_choices_and_all_match_registry():
    assert Platform.CHOICES == platforms.choices()
    assert Platform.ALL == set(platforms.codes())
    # The pattern used by services.py: dict(Platform.CHOICES).get(code)
    assert dict(Platform.CHOICES).get("C") == "Career"


# ── Reference generation is validated against the registry ────────────────────
def test_generate_reference_rejects_code_not_in_registry():
    with pytest.raises(ValueError):
        generate_reference("Z")


def test_generate_reference_accepts_every_registered_code():
    for code in platforms.codes():
        ref = generate_reference(code)
        assert ref.startswith(f"{code}-")

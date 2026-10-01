"""
Centralized Platform/Product registry (directive Part XII).

Every USAM product that can generate a financial transaction is defined here
ONCE, with all of its billing-relevant metadata:

    code             single-char namespace stamped onto every reference/txn
    name             human label for admin surfaces
    slug             stable machine key (urls, config, exports)
    merchant_prefix  prefix a bank/PSP (e.g. Bank of Alexandria) uses to route
                     settlement to the correct USAM merchant account
    default_currency ISO-4217 currency a platform bills in unless overridden
    status           "active" | "beta" | "retired" — gates whether new charges
                     may be created against the platform
    audience         "individual" | "employer" | "mixed" (informational)

Why a Python registry and not a DB table: the platform CODE is structural
identity. It is referenced at class-definition time by every model field
(`platform_code = CharField(choices=Platform.CHOICES, default=Platform.CAREER)`)
and inside migrations. A DB row cannot supply `choices`/defaults at import time
without circular app-loading problems. Keeping ONE authoritative in-code
registry removes the scattering (merchant prefixes, currencies, codes were
previously implicit or hardcoded as "C"/"EGP" literals) while staying
import-safe. `references.Platform` derives its CHOICES/ALL from this registry,
so every existing consumer keeps working unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass


class PlatformStatus:
    ACTIVE = "active"
    BETA = "beta"
    RETIRED = "retired"

    # A charge may only be created against a platform in one of these states.
    CHARGEABLE = {ACTIVE, BETA}


@dataclass(frozen=True)
class PlatformDef:
    code: str
    name: str
    slug: str
    merchant_prefix: str
    default_currency: str
    status: str = PlatformStatus.ACTIVE
    audience: str = "mixed"

    @property
    def is_chargeable(self) -> bool:
        return self.status in PlatformStatus.CHARGEABLE


# ── The registry ────────────────────────────────────────────────────────────
# Ordered; the first entry is the platform-wide default (Career / jobs).
_DEFS: tuple[PlatformDef, ...] = (
    PlatformDef(
        code="C", name="Career", slug="career",
        merchant_prefix="USAM-CAREER",
        default_currency="EGP", status=PlatformStatus.ACTIVE, audience="mixed",
    ),
    PlatformDef(
        code="E", name="Education", slug="education",
        merchant_prefix="USAM-EDU",
        default_currency="EGP", status=PlatformStatus.BETA, audience="individual",
    ),
    PlatformDef(
        code="F", name="Freelancing", slug="freelancing",
        merchant_prefix="USAM-FREE",
        default_currency="EGP", status=PlatformStatus.BETA, audience="mixed",
    ),
    PlatformDef(
        code="K", name="Kids", slug="kids",
        merchant_prefix="USAM-KIDS",
        default_currency="EGP", status=PlatformStatus.BETA, audience="individual",
    ),
)

# Index by code for O(1) lookup; codes are unique by construction.
_BY_CODE: dict[str, PlatformDef] = {d.code: d for d in _DEFS}
_BY_SLUG: dict[str, PlatformDef] = {d.slug: d for d in _DEFS}

# Fail loudly at import if the registry is ever edited into an inconsistent
# state (duplicate code or slug), rather than silently losing a platform.
assert len(_BY_CODE) == len(_DEFS), "Duplicate platform code in registry"
assert len(_BY_SLUG) == len(_DEFS), "Duplicate platform slug in registry"

DEFAULT_CODE = _DEFS[0].code  # "C" (Career)


# ── Public accessors ─────────────────────────────────────────────────────────
def all_platforms() -> tuple[PlatformDef, ...]:
    """Every registered platform, in canonical order."""
    return _DEFS


def codes() -> frozenset[str]:
    """The set of valid platform codes (used for validation)."""
    return frozenset(_BY_CODE)


def choices() -> list[tuple[str, str]]:
    """Django model-field `choices` form: [(code, name), ...]."""
    return [(d.code, d.name) for d in _DEFS]


def get(code: str) -> PlatformDef:
    """Resolve a platform by code. Raises ValueError on an unknown code so a
    typo can never mint an unattributable financial reference."""
    try:
        return _BY_CODE[code]
    except KeyError:
        raise ValueError(f"Unknown platform code: {code!r}") from None


def get_by_slug(slug: str) -> PlatformDef:
    try:
        return _BY_SLUG[slug]
    except KeyError:
        raise ValueError(f"Unknown platform slug: {slug!r}") from None


def is_valid(code: str) -> bool:
    return code in _BY_CODE


def default_currency_for(code: str) -> str:
    return get(code).default_currency


def merchant_prefix_for(code: str) -> str:
    return get(code).merchant_prefix

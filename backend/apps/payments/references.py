"""
Globally-unique, human-legible financial references with a USAM platform
namespace and transaction category (directive Part XII).

Format:  {PLATFORM}-{CATEGORY}-{YYYYMMDD}-{RANDOM}
Example: C-PAY-20260924-7QK3M9XA

    PLATFORM  which USAM product minted this (see the platforms registry)
    CATEGORY  what kind of financial object it is (see Category below): a
              finance admin reads the KIND off the reference without resolving
              any user identity — the reference carries NO PII.
    YYYYMMDD  UTC date, for at-a-glance chronology and ops bucketing
    RANDOM    Crockford base32 (no ambiguous chars) from a CSPRNG — unguessable
              and collision-resistant; DB uniqueness is still enforced by the
              unique constraint on each reference column.

Backward compatibility: ``category`` is optional. When omitted the legacy
three-segment form ``{PLATFORM}-{YYYYMMDD}-{RANDOM}`` is produced, so references
already stored in that shape remain valid and parseable.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from . import platforms


class Category:
    """Transaction category segment. Short, uppercase, no PII.

    One per financial object kind so a reference is self-describing:
        ORD  order (customer purchase intent)
        PAY  payment (money captured)
        REF  refund
        INV  invoice
        SUB  subscription charge
        ADJ  manual ledger adjustment
        TXN  generic ledger transaction (fallback when none of the above fits)
    """

    ORDER = "ORD"
    PAYMENT = "PAY"
    REFUND = "REF"
    INVOICE = "INV"
    SUBSCRIPTION = "SUB"
    ADJUSTMENT = "ADJ"
    TRANSACTION = "TXN"

    ALL = {ORDER, PAYMENT, REFUND, INVOICE, SUBSCRIPTION, ADJUSTMENT, TRANSACTION}


class Platform:
    """Backward-compatible facade over the centralized ``platforms`` registry.

    Historically this held the hardcoded code list. The codes now live in ONE
    place (``platforms._DEFS``); this class just re-exports them so every
    existing consumer — model-field ``choices``/defaults, ``dict(CHOICES)``,
    ``in ALL`` membership checks — keeps working unchanged.
    """

    CAREER = platforms.get_by_slug("career").code
    EDUCATION = platforms.get_by_slug("education").code
    FREELANCING = platforms.get_by_slug("freelancing").code
    KIDS = platforms.get_by_slug("kids").code

    CHOICES = platforms.choices()

    ALL = set(platforms.codes())


# Crockford base32 alphabet (excludes I, L, O, U to avoid confusion).
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _random_suffix(length: int = 8) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def generate_reference(
    platform_code: str,
    category: str | None = None,
    *,
    suffix_length: int = 8,
) -> str:
    """Build a reference like ``C-PAY-20260924-7QK3M9XA``.

    With ``category`` omitted, produces the legacy three-segment form
    ``C-20260924-7QK3M9XA`` for backward compatibility.

    Raises ValueError for an unknown platform code or category so a typo can
    never mint an unattributable financial reference. The result is well within
    the 40-char ``reference`` column limit: 1 + 1 + 3 + 1 + 8 + 1 + 8 = 23.
    """
    if not platforms.is_valid(platform_code):
        raise ValueError(f"Unknown platform code: {platform_code!r}")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = _random_suffix(suffix_length)
    if category is None:
        return f"{platform_code}-{day}-{suffix}"
    if category not in Category.ALL:
        raise ValueError(f"Unknown transaction category: {category!r}")
    return f"{platform_code}-{category}-{day}-{suffix}"

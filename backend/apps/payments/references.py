"""
Globally-unique, human-legible financial references with a USAM platform
namespace (directive Part XII).

Format:  {PLATFORM}-{YYYYMMDD}-{RANDOM}
Example: C-20260924-7QK3M9XA

The leading platform code lets a financial admin instantly tell WHICH USAM
product generated a transaction without resolving user identity. RANDOM is
Crockford base32 (no ambiguous chars) from a CSPRNG, so references are
unguessable and collision-resistant; uniqueness is still enforced by a DB
unique constraint on the reference column.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone


class Platform:
    CAREER = "C"
    EDUCATION = "E"
    FREELANCING = "F"
    KIDS = "K"

    CHOICES = [
        (CAREER, "Career"),
        (EDUCATION, "Education"),
        (FREELANCING, "Freelancing"),
        (KIDS, "Kids"),
    ]

    ALL = {CAREER, EDUCATION, FREELANCING, KIDS}


# Crockford base32 alphabet (excludes I, L, O, U to avoid confusion).
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _random_suffix(length: int = 8) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def generate_reference(platform_code: str, *, suffix_length: int = 8) -> str:
    """Build a reference like ``C-20260924-7QK3M9XA``.

    Raises ValueError for an unknown platform code so a typo can never mint an
    unattributable financial reference.
    """
    if platform_code not in Platform.ALL:
        raise ValueError(f"Unknown platform code: {platform_code!r}")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{platform_code}-{day}-{_random_suffix(suffix_length)}"

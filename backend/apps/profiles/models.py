"""
Profiles app models — re-exports from the canonical location.

The canonical profile model is CareerProfile in apps.career.models.
UserProfile in apps.users.models is DEPRECATED — all new code should use
CareerProfile (aliased here as UserProfile for backwards compatibility).

JobMatchScore remains in apps.users.models.
"""
from apps.career.models import CareerProfile  # noqa: F401

# Backwards-compat alias: code that does `from apps.profiles.models import UserProfile`
# now gets CareerProfile transparently.
UserProfile = CareerProfile  # noqa: F811

try:
    from apps.users.models import JobMatchScore  # noqa: F401
except ImportError:
    pass

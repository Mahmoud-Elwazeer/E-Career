from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


def resolve_active_plan(subject):
    """Return the active/trial SubscriptionPlan for a subject, or None.

    A *subject* is whatever a purchase can be billed to — today an individual
    ``User`` or an organization ``Company``. Both hang a subscription off the
    SAME ``SubscriptionPlan``; the only difference is which model/column the
    subscription lives on. Resolving the plan here (not the gating) is the one
    place that is subject-aware, so the gate itself stays identical for everyone.

    None means "no active subscription" — the caller treats that as unrestricted
    so the platform stays usable while admins configure plans.
    """
    try:
        from apps.core.models import CompanySubscription, UserSubscription
        from apps.jobs.models import Company
    except ImportError:
        return None

    if subject is None:
        return None

    # Organization subject.
    if isinstance(subject, Company):
        sub = (CompanySubscription.objects
               .filter(company=subject, status__in=("active", "trial"))
               .select_related("plan").first())
        return sub.plan if sub else None

    # Individual subject (duck-typed: anything that isn't a Company is treated
    # as a user). Guard with hasattr so a stray type can't crash the gate.
    if hasattr(subject, "pk"):
        sub = (UserSubscription.objects
               .filter(user=subject, status__in=("active", "trial"))
               .select_related("plan").first())
        return sub.plan if sub else None

    return None


def _gate_plan(plan, check_type, current_count=0, feature=None):
    """Subject-agnostic gate. Given a resolved plan (or None), allow or deny.

    This is the ONE place the entitlement rules live, shared by individuals and
    organizations. Returns True if allowed, raises PermissionDenied otherwise.
    """
    if plan is None:
        return True

    if check_type == "job_posting":
        limit = plan.job_posting_limit
        if limit and current_count >= limit:
            raise PermissionDenied(
                f"Your plan ({plan.name}) allows up to {limit} active job postings. "
                "Contact admin to upgrade."
            )
    elif check_type == "candidate_search":
        limit = plan.candidate_search_limit
        if limit and current_count >= limit:
            raise PermissionDenied(
                f"Your plan ({plan.name}) allows up to {limit} candidate discoveries per month. "
                "Contact admin to upgrade."
            )
    elif check_type == "ai_feature":
        if not getattr(plan, "ai_features_enabled", True):
            raise PermissionDenied(
                f"Your plan ({plan.name}) does not include AI features. Contact admin to upgrade."
            )
    elif check_type == "feature":
        # Canonical shape is a dict {feature_key: bool} where an explicit False
        # disables the feature. We tolerate a legacy LIST (older data where the
        # list held the ENABLED keys) so stale rows never 500 the gate:
        #   - dict: deny only if flags.get(feature) is False
        #   - list: deny only if the list is non-empty AND feature not in it
        #           (an allow-list); an empty list disables nothing.
        if feature is not None:
            disabled = feature_is_disabled(getattr(plan, "feature_flags", None), feature)
            if disabled:
                raise PermissionDenied(
                    f"Your plan ({plan.name}) does not include '{feature}'. Contact admin to upgrade."
                )
    return True


def check_entitlement_for(subject, check_type, current_count=0, feature=None):
    """Unified entitlement gate for ANY subject (individual User or Company).

    check_type:
        "job_posting"      — gated by plan.job_posting_limit
        "candidate_search" — gated by plan.candidate_search_limit
        "ai_feature"       — gated by plan.ai_features_enabled
        "feature"          — gated by plan.feature_flags[feature] (admin-configurable)
    current_count: how many the subject has already used (count-limited types)
    feature: feature-flag key (required when check_type == "feature")

    Returns True if allowed, raises PermissionDenied if not. No active
    subscription => allowed (platform stays usable while admins configure plans).
    """
    return _gate_plan(resolve_active_plan(subject), check_type, current_count, feature)


def check_entitlement(company, check_type, current_count=0, feature=None):
    """Backward-compatible company-scoped gate.

    Thin wrapper over the unified ``check_entitlement_for`` so existing callers
    that pass a Company keep working unchanged. New code can call
    ``check_entitlement_for`` with either a User or a Company.
    """
    return check_entitlement_for(company, check_type, current_count, feature)


def feature_is_disabled(flags, feature) -> bool:
    """Return True iff `feature` is explicitly disabled by a plan's flags.

    Canonical: flags is a dict {key: bool}; disabled == flags.get(key) is False.
    Backward-compatible with a legacy list of ENABLED keys: disabled == the list
    is non-empty and does not contain the key. None/empty => not disabled (so a
    newly-added feature is never silently locked out before admins configure it).
    """
    if not flags:
        return False
    if isinstance(flags, dict):
        return flags.get(feature) is False
    if isinstance(flags, (list, tuple, set)):
        return len(flags) > 0 and feature not in flags
    return False


class IsAdminRole(BasePermission):
    """
    Allows access only to users with role='admin'.
    """

    message = "Admin access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Allows access to the object owner or an admin user.
    Requires the object to have a 'user' attribute.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.role == "admin":
            return True
        owner = getattr(obj, "user", None)
        if owner is None:
            owner = obj  # The object IS the user
        return owner == request.user

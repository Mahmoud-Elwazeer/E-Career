from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


def check_entitlement(company, check_type, current_count=0, feature=None):
    """
    Check whether a company's active subscription allows an action.

    check_type:
        "job_posting"      — gated by plan.job_posting_limit
        "candidate_search" — gated by plan.candidate_search_limit
        "ai_feature"       — gated by plan.ai_features_enabled
        "feature"          — gated by plan.feature_flags[feature] (admin-configurable)
    current_count: how many the company has already used (for count-limited types)
    feature: feature-flag key (required when check_type == "feature")

    Returns True if allowed, raises PermissionDenied if not.
    If no active subscription exists, the action is allowed (no gating), so the
    platform stays usable for un-subscribed companies while admins configure plans.
    """
    try:
        from apps.core.models import CompanySubscription
    except ImportError:
        return True

    sub = CompanySubscription.objects.filter(
        company=company,
        status__in=("active", "trial"),
    ).select_related("plan").first()

    if not sub:
        return True

    plan = sub.plan
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

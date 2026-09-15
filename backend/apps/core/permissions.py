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
        flags = getattr(plan, "feature_flags", None) or {}
        # A feature is allowed unless explicitly disabled in the plan's flags,
        # so adding a new admin-configurable feature never silently locks users out.
        if feature is not None and flags.get(feature) is False:
            raise PermissionDenied(
                f"Your plan ({plan.name}) does not include '{feature}'. Contact admin to upgrade."
            )
    return True


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

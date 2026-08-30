from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


def check_entitlement(company, check_type, current_count=0):
    """
    Check whether a company's active subscription allows an action.

    check_type: "job_posting" or "candidate_search"
    current_count: how many the company has already used

    Returns True if allowed, raises PermissionDenied if not.
    If no active subscription exists, the action is allowed (no gating).
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

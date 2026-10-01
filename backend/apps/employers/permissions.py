"""
Employer Portal Permissions
Phase 3A: Employer self-service portal
Updated for multi-seat employer (Phase 2 item 2.8).
"""
from rest_framework import permissions


def _get_team_membership(user):
    """Return the user's active, accepted EmployerTeamMember or None."""
    from .models import EmployerTeamMember
    return (
        EmployerTeamMember.objects
        .filter(user=user, is_active=True, accepted_at__isnull=False)
        .select_related('company')
        .first()
    )


class IsEmployer(permissions.BasePermission):
    """
    Check if user has employer role/profile OR is an active team member.
    """
    message = "You must have an employer profile to access this resource."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in ['employer', 'admin'] and hasattr(request.user, 'employer_profile'):
            return True
        return _get_team_membership(request.user) is not None


class IsVerifiedEmployer(permissions.BasePermission):
    """
    Check if employer is verified, or team member's company has a verified profile.
    """
    message = "Your employer account must be verified to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if (
            request.user.role in ['employer', 'admin']
            and hasattr(request.user, 'employer_profile')
            and request.user.employer_profile.is_verified
        ):
            return True
        membership = _get_team_membership(request.user)
        if membership:
            from .models import EmployerProfile
            return EmployerProfile.objects.filter(
                company=membership.company, is_verified=True
            ).exists()
        return False


class IsOwnerEmployer(permissions.BasePermission):
    """
    Check if user owns the employer profile OR is an admin team member on the same company.
    """
    message = "You can only access your own employer profile."

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'employer'):
            if obj.employer.user == request.user:
                return True
            membership = _get_team_membership(request.user)
            return membership is not None and membership.company_id == obj.employer.company_id and membership.role in ('owner', 'admin')
        if hasattr(obj, 'user'):
            if obj.user == request.user:
                return True
            membership = _get_team_membership(request.user)
            if membership and hasattr(obj, 'company_id'):
                return membership.company_id == obj.company_id and membership.role in ('owner', 'admin')
        return False


class CanPostJobs(permissions.BasePermission):
    """
    Check if employer can post jobs. Allows admin/recruiter team members.
    """
    message = "You do not have permission to post jobs."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in ['employer', 'admin'] and hasattr(request.user, 'employer_profile'):
            return request.user.employer_profile.is_verified
        membership = _get_team_membership(request.user)
        if membership and membership.role in ('owner', 'admin', 'recruiter'):
            from .models import EmployerProfile
            return EmployerProfile.objects.filter(
                company=membership.company, is_verified=True
            ).exists()
        return False


def _resolve_posting(obj):
    """Resolve the owning EmployerProfile + company_id from either a JobPosting
    or a JobApplication (whose employer link is job.employer_posting).

    Returns (employer_profile_or_None, company_id_or_None). This keeps the
    permission usable on both the postings and the applications viewsets without
    assuming one object shape.
    """
    # JobPosting-like: has a direct .employer / .company_id.
    emp = getattr(obj, 'employer', None)
    company_id = getattr(obj, 'company_id', None)
    if emp is not None and company_id is not None:
        return emp, company_id
    # JobApplication-like: reach the employer posting through the mirrored job.
    job = getattr(obj, 'job', None)
    posting = getattr(job, 'employer_posting', None) if job is not None else None
    if posting is not None:
        return getattr(posting, 'employer', None), getattr(posting, 'company_id', None)
    return None, None


class CanViewApplicants(permissions.BasePermission):
    """
    Check if employer can view/act on applicants. Allows admin/recruiter/
    hiring_manager team members (and the company owner). Works for both a
    JobPosting object and a JobApplication object.
    """
    message = "You do not have permission to view these applicants."

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        employer, company_id = _resolve_posting(obj)
        if company_id is None:
            return False
        if request.user.role in ['employer', 'admin'] and hasattr(request.user, 'employer_profile'):
            if employer is not None and getattr(employer, 'user_id', None) == request.user.id:
                return True
            # Owner by profile on the same company.
            if request.user.employer_profile.company_id == company_id:
                return True
        membership = _get_team_membership(request.user)
        if membership and membership.role in ('owner', 'admin', 'recruiter', 'hiring_manager'):
            return membership.company_id == company_id
        return False

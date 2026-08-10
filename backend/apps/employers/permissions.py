"""
Employer Portal Permissions
Phase 3A: Employer self-service portal
"""
from rest_framework import permissions


class IsEmployer(permissions.BasePermission):
    """
    Check if user has employer role and profile.
    Used for basic employer access.
    """
    message = "You must have an employer profile to access this resource."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['employer', 'admin'] and  # Role check
            hasattr(request.user, 'employer_profile')
        )


class IsVerifiedEmployer(permissions.BasePermission):
    """
    Check if employer is verified.
    Used for job posting and applicant management.
    """
    message = "Your employer account must be verified to perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['employer', 'admin'] and  # Role check
            hasattr(request.user, 'employer_profile') and
            request.user.employer_profile.is_verified
        )


class IsOwnerEmployer(permissions.BasePermission):
    """
    Check if user owns the employer profile.
    Used for profile management.
    """
    message = "You can only access your own employer profile."
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has an employer attribute
        if hasattr(obj, 'employer'):
            return obj.employer.user == request.user
        # Check if the object is an EmployerProfile
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class CanPostJobs(permissions.BasePermission):
    """
    Check if employer can post jobs.
    Additional check beyond verification if needed.
    """
    message = "You do not have permission to post jobs."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Role check
        if request.user.role not in ['employer', 'admin']:
            return False

        if not hasattr(request.user, 'employer_profile'):
            return False

        employer = request.user.employer_profile

        # Must be verified
        if not employer.is_verified:
            return False

        # Additional checks can be added here (e.g., subscription status)
        return True


class CanViewApplicants(permissions.BasePermission):
    """
    Check if employer can view applicants for a job.
    """
    message = "You do not have permission to view these applicants."

    def has_object_permission(self, request, view, obj):
        # obj is a JobPosting
        if not request.user.is_authenticated:
            return False

        # Role check
        if request.user.role not in ['employer', 'admin']:
            return False

        if not hasattr(request.user, 'employer_profile'):
            return False

        return obj.employer.user == request.user
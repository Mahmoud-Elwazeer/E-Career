"""
DRF Permission Classes for Role-Based Access Control
"""
from rest_framework import permissions


class IsJobSeeker(permissions.BasePermission):
    """
    Permission class that only allows job seekers to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["jobseeker", "user"]  # 'user' for legacy
        )


class IsEmployer(permissions.BasePermission):
    """
    Permission class that only allows employers to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "employer"
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission class that only allows admins to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == "admin" or request.user.is_staff)
        )


class IsJobSeekerOrEmployer(permissions.BasePermission):
    """
    Permission class for endpoints accessible to both job seekers and employers.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["jobseeker", "employer", "user", "admin"]
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.user == request.user or request.user.is_staff

from rest_framework import permissions

class IsSystemAdministrator(permissions.BasePermission):
    """
    Custom permission to only allow System Administrators to access.
    Enforces FR-04 and FR-05 role restrictions.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'System Administrator'
        )

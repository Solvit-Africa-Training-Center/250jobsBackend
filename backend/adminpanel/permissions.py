from rest_framework.permissions import BasePermission


class IsAdminRoleOrStaff(BasePermission):
    """Allow access to users who are staff/superuser or have role='admin'."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False) or getattr(user, "role", None) == "admin")


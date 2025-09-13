from rest_framework.permissions import BasePermission


class IsEmployer(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        role = (getattr(user, "role", "") or "").lower() if user else ""
        return bool(user and user.is_authenticated and role == "employer")


class IsTechnician(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        role = (getattr(user, "role", "") or "").lower() if user else ""
        return bool(user and user.is_authenticated and role == "technician")

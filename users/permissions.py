from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Allow access to the object owner or an admin/staff user."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class IsAdminUser(BasePermission):
    """Restrict access to admin (staff) users only."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

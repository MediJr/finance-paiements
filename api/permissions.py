"""Permissions API — administration."""

from rest_framework.permissions import BasePermission


class IsAdministrateur(BasePermission):
    """Accès réservé aux utilisateurs staff."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )

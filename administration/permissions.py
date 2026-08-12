"""Contrôles d'autorisation pour l'administration fonctionnelle."""

from django.core.exceptions import PermissionDenied


def require_administrateur(user):
    """
    Vérifie que l'utilisateur est un administrateur (staff Django).

    Lève PermissionDenied sinon.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        raise PermissionDenied('Authentification requise.')
    if not user.is_staff:
        raise PermissionDenied('Accès réservé aux administrateurs.')
    return user

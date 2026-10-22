"""Décorateurs d'accès administration."""

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from administration.permissions import require_administrateur


def administrateur_required(view_func):
    """Restreint une vue web aux administrateurs (staff)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            require_administrateur(request.user)
        except PermissionDenied:
            if not request.user.is_authenticated:
                return redirect('accounts:connexion')
            messages.error(request, 'Accès réservé aux administrateurs.')
            return redirect('accounts:utilisateur-list')
        return view_func(request, *args, **kwargs)

    return _wrapped

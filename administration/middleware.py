"""
Middleware Security by Design — Sprint 7.

- Applique la durée de session depuis ParametresApplication.
- Bloque les écritures financières HTTP en mode maintenance (filet complémentaire
  aux contrôles des services métier).
"""

from __future__ import annotations

from django.http import HttpResponseForbidden, JsonResponse
from django.utils.deprecation import MiddlewareMixin


# Préfixes d'écriture métier bloqués en maintenance (hors administration).
_FINANCIAL_WRITE_PREFIXES = (
    '/virements/',
    '/paiements/',
    '/remboursements/',
    '/api/virements/',
    '/api/paiements/',
    '/api/remboursements/',
)

_WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


class SecurityParametresMiddleware(MiddlewareMixin):
    """Applique session timeout et filet maintenance HTTP."""

    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            self._appliquer_delai_session(request)

        if request.method not in _WRITE_METHODS:
            return None
        if user is not None and getattr(user, 'is_staff', False):
            return None
        if not self._est_ecriture_financiere(request.path):
            return None
        if not self._mode_maintenance_actif():
            return None

        message = (
            'Application en maintenance : '
            'les opérations financières sont temporairement indisponibles.'
        )
        if request.path.startswith('/api/'):
            return JsonResponse({'detail': [message]}, status=503)
        return HttpResponseForbidden(message)

    @staticmethod
    def _est_ecriture_financiere(path: str) -> bool:
        return any(path.startswith(prefix) for prefix in _FINANCIAL_WRITE_PREFIXES)

    @staticmethod
    def _mode_maintenance_actif() -> bool:
        try:
            from administration.services.securite_service import get_parametres_courants

            return bool(get_parametres_courants().mode_maintenance)
        except Exception:
            return False

    @staticmethod
    def _appliquer_delai_session(request) -> None:
        try:
            from administration.services.securite_service import get_parametres_courants

            minutes = int(get_parametres_courants().delai_session_minutes)
            if minutes >= 1 and hasattr(request, 'session'):
                request.session.set_expiry(minutes * 60)
        except Exception:
            return

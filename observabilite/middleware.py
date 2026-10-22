"""Middleware — journalisation des erreurs HTTP 500."""

from __future__ import annotations

import logging

from django.utils.deprecation import MiddlewareMixin

from commun.http import adresse_ip_client as _client_ip
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_ERREUR_APPLICATION,
    TYPE_HTTP_500,
    enregistrer_evenement_durable,
)

logger = logging.getLogger(__name__)


class ObservabiliteExceptionMiddleware(MiddlewareMixin):
    """Journalise les exceptions non gérées (erreurs applicatives / 500)."""

    def process_exception(self, request, exception):
        user = getattr(request, 'user', None)
        utilisateur = user if getattr(user, 'is_authenticated', False) else None
        enregistrer_evenement_durable(
            type_evenement=TYPE_HTTP_500,
            module='http',
            description=f'Erreur HTTP 500 : {exception.__class__.__name__}: {exception}',
            niveau=Evenement.Niveau.ERROR,
            utilisateur=utilisateur,
            contexte={
                'path': getattr(request, 'path', ''),
                'method': getattr(request, 'method', ''),
                'exception_type': exception.__class__.__name__,
            },
            adresse_ip=_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:512],
        )
        # Aussi typé erreur applicative importante
        enregistrer_evenement_durable(
            type_evenement=TYPE_ERREUR_APPLICATION,
            module='application',
            description=str(exception)[:2000],
            niveau=Evenement.Niveau.ERROR,
            utilisateur=utilisateur,
            contexte={'exception_type': exception.__class__.__name__},
            adresse_ip=_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:512],
        )
        return None

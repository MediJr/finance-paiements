"""
journal_service — unique point d'écriture des événements d'observabilité.

Aucun autre composant ne doit créer d'Evenement directement.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models import Q
from django.shortcuts import get_object_or_404

from administration.permissions import require_administrateur
from administration.services.period_filters import apply_period_filter, parse_identifiant
from observabilite.models import Evenement

logger = logging.getLogger(__name__)

TYPE_UTILISATEUR_CREATION = 'utilisateur_creation'
TYPE_UTILISATEUR_ACTIVATION = 'utilisateur_activation'
TYPE_UTILISATEUR_DESACTIVATION = 'utilisateur_desactivation'
TYPE_WALLET_CREATION = 'wallet_creation'
TYPE_BENEFICIAIRE_CREATION = 'beneficiaire_creation'
TYPE_BENEFICIAIRE_MODIFICATION = 'beneficiaire_modification'
TYPE_BENEFICIAIRE_DESACTIVATION = 'beneficiaire_desactivation'
TYPE_VIREMENT_CREATION = 'virement_creation'
TYPE_VIREMENT_REUSSITE = 'virement_reussite'
TYPE_VIREMENT_ECHEC = 'virement_echec'
TYPE_PAIEMENT_CREATION = 'paiement_creation'
TYPE_PAIEMENT_REUSSITE = 'paiement_reussite'
TYPE_PAIEMENT_ECHEC = 'paiement_echec'
TYPE_REMBOURSEMENT_CREATION = 'remboursement_creation'
TYPE_REMBOURSEMENT_REUSSITE = 'remboursement_reussite'
TYPE_REMBOURSEMENT_ECHEC = 'remboursement_echec'
TYPE_ALIMENTATION_REUSSITE = 'alimentation_reussite'
TYPE_ALIMENTATION_REFUS = 'alimentation_refus'
TYPE_ALIMENTATION_ECHEC = 'alimentation_echec'
TYPE_AUTH_INSCRIPTION = 'auth_inscription'
TYPE_AUTH_CONNEXION = 'auth_connexion'
TYPE_AUTH_ECHEC = 'auth_echec_connexion'
TYPE_AUTH_BLOCAGE = 'auth_blocage'
TYPE_AUTH_DECONNEXION = 'auth_deconnexion'
TYPE_ADMIN_PARAMETRES = 'admin_modification_parametres'
TYPE_ADMIN_ACCES = 'admin_acces'
TYPE_ERREUR_APPLICATION = 'erreur_application'
TYPE_HTTP_500 = 'http_500'


def enregistrer_evenement(
    *,
    type_evenement: str,
    module: str,
    description: str,
    niveau: str = Evenement.Niveau.INFO,
    utilisateur=None,
    contexte: dict[str, Any] | None = None,
    adresse_ip: str | None = None,
    user_agent: str | None = None,
) -> Evenement | None:
    """
    Unique point d'écriture du journal d'observabilité.

    Best-effort : n'interrompt jamais le flux métier appelant.
    """
    try:
        if niveau not in Evenement.Niveau.values:
            niveau = Evenement.Niveau.INFO
        ctx = contexte if isinstance(contexte, dict) else {'valeur': str(contexte)}
        if ctx is None:
            ctx = {}
        return Evenement.objects.create(
            type_evenement=(type_evenement or 'inconnu')[:100],
            niveau=niveau,
            module=(module or 'inconnu')[:64],
            utilisateur=utilisateur if getattr(utilisateur, 'pk', None) else None,
            description=(description or '')[:4000],
            contexte=ctx,
            adresse_ip=adresse_ip or None,
            user_agent=(user_agent or '')[:512],
        )
    except Exception:
        logger.exception('Échec de journalisation observabilité (%s)', type_evenement)
        return None


def enregistrer_evenement_durable(**kwargs) -> Evenement | None:
    """
    Alias sémantique : à appeler hors bloc atomic métier (après rollback).

    Même implémentation que enregistrer_evenement.
    """
    return enregistrer_evenement(**kwargs)


def list_evenements(
    *,
    administrateur,
    niveau: str | None = None,
    module: str | None = None,
    type_evenement: str | None = None,
    utilisateur_id=None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    q: str | None = None,
    limit: int = 200,
):
    """Liste filtrable des événements (admin uniquement, lecture seule)."""
    require_administrateur(administrateur)
    queryset = Evenement.objects.select_related('utilisateur').all()
    if niveau:
        queryset = queryset.filter(niveau=niveau)
    if module:
        queryset = queryset.filter(module__iexact=module)
    if type_evenement:
        queryset = queryset.filter(type_evenement=type_evenement)
    if utilisateur_id not in (None, ''):
        uid = parse_identifiant(utilisateur_id, champ='utilisateur')
        queryset = queryset.filter(utilisateur_id=uid)
    queryset = apply_period_filter(
        queryset,
        date_debut=date_debut,
        date_fin=date_fin,
    )
    if q:
        queryset = queryset.filter(
            Q(description__icontains=q)
            | Q(type_evenement__icontains=q)
            | Q(module__icontains=q)
        )
    return queryset[: max(1, min(int(limit or 200), 1000))]


def get_evenement(*, administrateur, evenement_id: int) -> Evenement:
    """Détail d'un événement (admin uniquement)."""
    require_administrateur(administrateur)
    return get_object_or_404(
        Evenement.objects.select_related('utilisateur'),
        pk=evenement_id,
    )

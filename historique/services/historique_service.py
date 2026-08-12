"""
Services métier — historique des opérations.

Consultation, recherche, filtrage avec scoping propriétaire (Sprint 7).
La création d'événements est centralisée ici ; elle n'exécute aucune
opération financière et ne modifie jamais le solde.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone, make_aware

from accounts.models import Utilisateur
from administration.services.securite_service import parse_identifiant, parse_reference
from historique.models import HistoriqueOperation
from wallets.models import Wallet


def _is_date_only(value: str) -> bool:
    """True si la valeur est une date calendaire sans composante horaire."""
    parsed_date = parse_date(value)
    return parsed_date is not None and value == parsed_date.isoformat()


def _parse_period_bound(value: str | None, *, is_end: bool = False):
    """
    Convertit une borne de période en datetime timezone-aware.

    - date seule (YYYY-MM-DD) : début de journée locale
      (ou début du jour suivant si borne de fin exclusive)
    - datetime ISO : utilisée telle quelle
    """
    if not value:
        return None

    tz = get_current_timezone()

    # Django 6 peut parser une date seule via parse_datetime → minuit.
    # On traite explicitement les dates calendaires.
    if _is_date_only(value):
        parsed_date = parse_date(value)
        if is_end:
            return make_aware(
                datetime.combine(parsed_date + timedelta(days=1), time.min),
                tz,
            )
        return make_aware(datetime.combine(parsed_date, time.min), tz)

    parsed = parse_datetime(value)
    if parsed is not None:
        if parsed.tzinfo is None:
            return make_aware(parsed, tz)
        return parsed

    raise ValidationError(f'Date invalide : {value}')


@transaction.atomic
def create_historique_operation(
    *,
    wallet: Wallet,
    type_operation: str,
    description: str = '',
    montant: Decimal | None = None,
    devise: str | None = None,
    statut: str = HistoriqueOperation.Statut.ENREGISTREE,
    reference: str | None = None,
) -> HistoriqueOperation:
    """
    Enregistre un événement d'historique.

    N'effectue aucun débit/crédit et ne modifie pas le solde du Wallet.
    """
    if wallet is None or wallet.pk is None:
        raise ValidationError('Une opération doit appartenir à un Wallet.')

    if type_operation not in HistoriqueOperation.TypeOperation.values:
        raise ValidationError(f'Type d\'opération invalide : {type_operation}')

    if statut not in HistoriqueOperation.Statut.values:
        raise ValidationError(f'Statut invalide : {statut}')

    ref = reference or f'OP-{uuid.uuid4().hex[:16].upper()}'
    return HistoriqueOperation.objects.create(
        wallet=wallet,
        type_operation=type_operation,
        statut=statut,
        description=description or '',
        montant=montant,
        devise=devise or wallet.devise,
        reference=ref,
    )


def get_historique_operation(
    operation_id: int,
    *,
    proprietaire: Utilisateur | None = None,
    vue_admin: bool = False,
) -> HistoriqueOperation:
    """Retourne une opération d'historique (scoping propriétaire)."""
    queryset = HistoriqueOperation.objects.select_related(
        'wallet',
        'wallet__utilisateur',
    )
    if vue_admin:
        return get_object_or_404(queryset, pk=operation_id)
    if proprietaire is not None:
        return get_object_or_404(
            queryset,
            pk=operation_id,
            wallet__utilisateur=proprietaire,
        )
    return get_object_or_404(queryset, pk=operation_id)


def list_historique_operations(
    *,
    wallet_id: int | None = None,
    type_operation: str | None = None,
    statut: str | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    reference: str | None = None,
    proprietaire: Utilisateur | None = None,
    vue_admin: bool = False,
):
    """
    Liste les opérations d'historique avec filtres optionnels.

    Un non-admin (proprietaire fourni) ne voit que ses propres opérations.
    """
    queryset = HistoriqueOperation.objects.select_related(
        'wallet',
        'wallet__utilisateur',
    ).all()

    if not vue_admin and proprietaire is not None:
        queryset = queryset.filter(wallet__utilisateur=proprietaire)

    if wallet_id is not None:
        wallet_id = parse_identifiant(wallet_id, champ='wallet')
        if not vue_admin and proprietaire is not None:
            # Refuse silencieusement le filtre vers un wallet tiers (résultat vide).
            if not Wallet.objects.filter(
                pk=wallet_id,
                utilisateur=proprietaire,
            ).exists():
                return queryset.none()
        queryset = queryset.filter(wallet_id=wallet_id)

    if type_operation:
        queryset = queryset.filter(type_operation=type_operation)

    if statut:
        queryset = queryset.filter(statut=statut)

    if reference:
        queryset = queryset.filter(
            reference__iexact=parse_reference(reference) or reference
        )

    debut = _parse_period_bound(date_debut, is_end=False)
    fin = _parse_period_bound(date_fin, is_end=True)
    if debut is not None:
        queryset = queryset.filter(date_creation__gte=debut)
    if fin is not None:
        if date_fin and _is_date_only(date_fin):
            queryset = queryset.filter(date_creation__lt=fin)
        else:
            queryset = queryset.filter(date_creation__lte=fin)

    return queryset

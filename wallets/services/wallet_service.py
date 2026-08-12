"""
Services métier — Wallet (portefeuille).

Création et consultation. Toute modification de solde passe par mouvement_service.
"""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from wallets.models import Wallet


def _devise_par_defaut() -> str:
    try:
        from administration.services.securite_service import get_parametres_courants

        return get_parametres_courants().devise_par_defaut or 'EUR'
    except Exception:
        return 'EUR'


@transaction.atomic
def create_wallet_for_utilisateur(utilisateur: Utilisateur) -> Wallet:
    """
    Crée le Wallet d'un utilisateur métier.

    Idempotent : si un Wallet existe déjà, il est renvoyé tel quel.
    Le solde initial est toujours 0. Aucun découvert.
    """
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Un Wallet ne peut pas être créé sans utilisateur.')

    wallet, created = Wallet.objects.get_or_create(
        utilisateur=utilisateur,
        defaults={
            'solde': Decimal('0.00'),
            'devise': _devise_par_defaut(),
            'statut': Wallet.Statut.ACTIF,
        },
    )
    if created:
        from observabilite.services.journal_service import (
            TYPE_WALLET_CREATION,
            enregistrer_evenement,
        )

        enregistrer_evenement(
            type_evenement=TYPE_WALLET_CREATION,
            module='wallets',
            description=f'Création wallet #{wallet.pk}',
            utilisateur=getattr(utilisateur, 'user', None),
            contexte={
                'wallet_id': wallet.pk,
                'utilisateur_id': utilisateur.pk,
            },
        )
    return wallet


def get_wallet(
    wallet_id: int,
    *,
    proprietaire: Utilisateur | None = None,
    vue_admin: bool = False,
) -> Wallet:
    """
    Retourne un Wallet par identifiant.

    Un non-admin ne peut consulter que son propre Wallet.
    """
    queryset = Wallet.objects.select_related('utilisateur', 'utilisateur__user')
    if vue_admin:
        return get_object_or_404(queryset, pk=wallet_id)
    if proprietaire is not None:
        return get_object_or_404(queryset, pk=wallet_id, utilisateur=proprietaire)
    return get_object_or_404(queryset, pk=wallet_id)


def get_wallet_for_utilisateur(
    utilisateur_id: int,
    *,
    demandeur: Utilisateur | None = None,
    vue_admin: bool = False,
) -> Wallet:
    """Retourne le Wallet d'un utilisateur métier (scoping propriétaire)."""
    if not vue_admin and demandeur is not None and demandeur.pk != utilisateur_id:
        raise PermissionDenied('Accès refusé à ce Wallet.')
    return get_object_or_404(
        Wallet.objects.select_related('utilisateur', 'utilisateur__user'),
        utilisateur_id=utilisateur_id,
    )

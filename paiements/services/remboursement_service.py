"""
Services métier — remboursements.

Réutilise `wallets.services.mouvement_service`.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from administration.services.securite_service import assert_not_maintenance
from historique.models import HistoriqueOperation
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_REMBOURSEMENT_CREATION,
    TYPE_REMBOURSEMENT_ECHEC,
    TYPE_REMBOURSEMENT_REUSSITE,
    enregistrer_evenement,
    enregistrer_evenement_durable,
)
from paiements.models import Paiement, Remboursement
from wallets.models import Wallet
from wallets.services.mouvement_service import (
    journaliser_transfert,
    parse_montant,
    transferer_fonds,
)


def executer_remboursement(
    *,
    acteur: Utilisateur,
    paiement_id: int,
    montant=None,
) -> Remboursement:
    """
    Rembourse un paiement existant (total ou partiel).

    Seul le bénéficiaire d'origine (Wallet ayant reçu le paiement) peut rembourser.
    Le montant par défaut est le reste remboursable.
    """
    try:
        remboursement = _executer_remboursement_atomic(
            acteur=acteur,
            paiement_id=paiement_id,
            montant=montant,
        )
    except ValidationError as exc:
        enregistrer_evenement_durable(
            type_evenement=TYPE_REMBOURSEMENT_ECHEC,
            module='paiements',
            description=f'Échec remboursement : {exc}',
            niveau=Evenement.Niveau.WARNING,
            utilisateur=getattr(acteur, 'user', None),
            contexte={'paiement_id': paiement_id, 'erreur': str(exc)},
        )
        raise

    user = getattr(acteur, 'user', None)
    ctx = {
        'remboursement_id': remboursement.pk,
        'reference': remboursement.reference,
        'montant': str(remboursement.montant),
        'paiement_id': paiement_id,
    }
    enregistrer_evenement(
        type_evenement=TYPE_REMBOURSEMENT_CREATION,
        module='paiements',
        description=f'Création remboursement {remboursement.reference}',
        utilisateur=user,
        contexte=ctx,
    )
    enregistrer_evenement(
        type_evenement=TYPE_REMBOURSEMENT_REUSSITE,
        module='paiements',
        description=f'Remboursement réussi {remboursement.reference}',
        utilisateur=user,
        contexte=ctx,
    )
    return remboursement


@transaction.atomic
def _executer_remboursement_atomic(
    *,
    acteur: Utilisateur,
    paiement_id: int,
    montant=None,
) -> Remboursement:
    if acteur is None or acteur.pk is None:
        raise ValidationError('Acteur invalide.')
    if not acteur.est_actif:
        raise ValidationError('L\'acteur doit être actif.')

    assert_not_maintenance(operation='les remboursements')

    try:
        paiement = (
            Paiement.objects.select_related(
                'wallet_payeur',
                'wallet_beneficiaire',
                'wallet_payeur__utilisateur',
                'wallet_beneficiaire__utilisateur',
            )
            .select_for_update()
            .get(pk=paiement_id)
        )
    except Paiement.DoesNotExist as exc:
        raise ValidationError('Paiement inexistant.') from exc

    try:
        wallet_acteur = acteur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    if wallet_acteur.pk != paiement.wallet_beneficiaire_id:
        raise ValidationError(
            'Seul le bénéficiaire du paiement peut émettre un remboursement.'
        )

    restant = paiement.montant_restant
    if restant <= Decimal('0.00'):
        raise ValidationError('Ce paiement est déjà totalement remboursé.')

    if montant is None:
        montant_decimal = restant
    else:
        montant_decimal = parse_montant(montant)
        if montant_decimal > restant:
            raise ValidationError(
                f'Le montant dépasse le reste remboursable ({restant}).'
            )

    wallet_remboursant, wallet_rembourse = transferer_fonds(
        wallet_source=paiement.wallet_beneficiaire,
        wallet_destination=paiement.wallet_payeur,
        montant=montant_decimal,
        label_source='remboursant',
        label_destination='remboursé',
    )

    reference = f'RMB-{uuid.uuid4().hex[:16].upper()}'
    remboursement = Remboursement.objects.create(
        reference=reference,
        paiement=paiement,
        wallet_remboursant=wallet_remboursant,
        wallet_rembourse=wallet_rembourse,
        montant=montant_decimal,
        devise=paiement.devise,
        statut=Remboursement.Statut.REUSSI,
    )

    paiement.montant_rembourse = (
        paiement.montant_rembourse + montant_decimal
    ).quantize(Decimal('0.01'))
    if paiement.montant_rembourse >= paiement.montant:
        paiement.statut = Paiement.Statut.REMBOURSE
        paiement.montant_rembourse = paiement.montant
    else:
        paiement.statut = Paiement.Statut.REMBOURSE_PARTIELLEMENT
    paiement.save(update_fields=['montant_rembourse', 'statut', 'date_mise_a_jour'])

    journaliser_transfert(
        wallet_source=wallet_remboursant,
        wallet_destination=wallet_rembourse,
        montant=montant_decimal,
        type_operation=HistoriqueOperation.TypeOperation.REMBOURSEMENT,
        reference_base=reference,
        description=f'Remboursement {reference} du paiement {paiement.reference}',
    )
    return remboursement


def list_remboursements(*, utilisateur: Utilisateur):
    """Liste les remboursements liés aux Wallets de l'utilisateur."""
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    try:
        wallet = utilisateur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    return (
        Remboursement.objects.select_related(
            'paiement',
            'wallet_remboursant',
            'wallet_remboursant__utilisateur',
            'wallet_rembourse',
            'wallet_rembourse__utilisateur',
        )
        .filter(Q(wallet_remboursant=wallet) | Q(wallet_rembourse=wallet))
        .distinct()
    )


def get_remboursement_pour_utilisateur(
    *,
    utilisateur: Utilisateur,
    remboursement_id: int,
) -> Remboursement:
    """Retourne un remboursement auquel l'utilisateur a participé."""
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    try:
        wallet = utilisateur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    return get_object_or_404(
        Remboursement.objects.select_related(
            'paiement',
            'wallet_remboursant',
            'wallet_remboursant__utilisateur',
            'wallet_rembourse',
            'wallet_rembourse__utilisateur',
        ),
        Q(wallet_remboursant=wallet) | Q(wallet_rembourse=wallet),
        pk=remboursement_id,
    )

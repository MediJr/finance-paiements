"""
Services métier — paiements.

Réutilise `wallets.services.mouvement_service` (pas de duplication avec virements).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from administration.services.securite_service import (
    assert_montant_paiement_max,
    assert_not_maintenance,
)
from beneficiaires.models import Beneficiaire
from historique.models import HistoriqueOperation
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_PAIEMENT_CREATION,
    TYPE_PAIEMENT_ECHEC,
    TYPE_PAIEMENT_REUSSITE,
    enregistrer_evenement,
    enregistrer_evenement_durable,
)
from paiements.models import Paiement
from wallets.models import Wallet
from wallets.services.mouvement_service import (
    journaliser_transfert,
    parse_montant,
    transferer_fonds,
)


def executer_paiement(
    *,
    payeur: Utilisateur,
    beneficiaire_id: int,
    montant,
    motif: str = '',
) -> Paiement:
    """Exécute un paiement atomique vers un bénéficiaire actif."""
    try:
        paiement = _executer_paiement_atomic(
            payeur=payeur,
            beneficiaire_id=beneficiaire_id,
            montant=montant,
            motif=motif,
        )
    except ValidationError as exc:
        enregistrer_evenement_durable(
            type_evenement=TYPE_PAIEMENT_ECHEC,
            module='paiements',
            description=f'Échec paiement : {exc}',
            niveau=Evenement.Niveau.WARNING,
            utilisateur=getattr(payeur, 'user', None),
            contexte={
                'beneficiaire_id': beneficiaire_id,
                'montant': str(montant),
                'erreur': str(exc),
            },
        )
        raise

    user = getattr(payeur, 'user', None)
    ctx = {
        'paiement_id': paiement.pk,
        'reference': paiement.reference,
        'montant': str(paiement.montant),
    }
    enregistrer_evenement(
        type_evenement=TYPE_PAIEMENT_CREATION,
        module='paiements',
        description=f'Création paiement {paiement.reference}',
        utilisateur=user,
        contexte=ctx,
    )
    enregistrer_evenement(
        type_evenement=TYPE_PAIEMENT_REUSSITE,
        module='paiements',
        description=f'Paiement réussi {paiement.reference}',
        utilisateur=user,
        contexte=ctx,
    )
    return paiement


@transaction.atomic
def _executer_paiement_atomic(
    *,
    payeur: Utilisateur,
    beneficiaire_id: int,
    montant,
    motif: str = '',
) -> Paiement:
    if payeur is None or payeur.pk is None:
        raise ValidationError('Payeur invalide.')
    if not payeur.est_actif:
        raise ValidationError('Le payeur doit être actif.')

    montant_decimal = parse_montant(montant)
    assert_not_maintenance(operation='les paiements')
    assert_montant_paiement_max(montant_decimal)

    try:
        lien = Beneficiaire.objects.select_related(
            'utilisateur_beneficiaire',
            'utilisateur_beneficiaire__wallet',
            'proprietaire__wallet',
        ).get(pk=beneficiaire_id, proprietaire=payeur)
    except Beneficiaire.DoesNotExist as exc:
        raise ValidationError('Bénéficiaire inexistant ou non autorisé.') from exc

    if lien.statut != Beneficiaire.Statut.ACTIF:
        raise ValidationError('Le bénéficiaire est inactif.')

    destinataire = lien.utilisateur_beneficiaire
    if not destinataire.est_actif:
        raise ValidationError('Le destinataire est inactif.')
    if destinataire.pk == payeur.pk:
        raise ValidationError('Impossible d\'effectuer un paiement vers soi-même.')

    try:
        wallet_payeur = payeur.wallet
        wallet_beneficiaire = destinataire.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError(
            'Wallet introuvable pour le payeur ou le destinataire.'
        ) from exc

    wallet_payeur, wallet_beneficiaire = transferer_fonds(
        wallet_source=wallet_payeur,
        wallet_destination=wallet_beneficiaire,
        montant=montant_decimal,
        label_source='payeur',
        label_destination='bénéficiaire',
    )

    reference = f'PAY-{uuid.uuid4().hex[:16].upper()}'
    motif_clean = (motif or '').strip()

    paiement = Paiement.objects.create(
        reference=reference,
        wallet_payeur=wallet_payeur,
        wallet_beneficiaire=wallet_beneficiaire,
        montant=montant_decimal,
        montant_rembourse=Decimal('0.00'),
        devise=wallet_payeur.devise,
        statut=Paiement.Statut.REUSSI,
        motif=motif_clean,
    )

    description = f'Paiement {reference}' + (f' — {motif_clean}' if motif_clean else '')
    journaliser_transfert(
        wallet_source=wallet_payeur,
        wallet_destination=wallet_beneficiaire,
        montant=montant_decimal,
        type_operation=HistoriqueOperation.TypeOperation.PAIEMENT,
        reference_base=reference,
        description=description,
    )
    return paiement


def list_paiements(*, utilisateur: Utilisateur):
    """Liste les paiements où l'utilisateur est payeur ou bénéficiaire."""
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    try:
        wallet = utilisateur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    return (
        Paiement.objects.select_related(
            'wallet_payeur',
            'wallet_payeur__utilisateur',
            'wallet_beneficiaire',
            'wallet_beneficiaire__utilisateur',
        )
        .filter(Q(wallet_payeur=wallet) | Q(wallet_beneficiaire=wallet))
        .distinct()
    )


def get_paiement_pour_utilisateur(
    *,
    utilisateur: Utilisateur,
    paiement_id: int,
) -> Paiement:
    """Retourne un paiement auquel l'utilisateur a participé."""
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    try:
        wallet = utilisateur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    return get_object_or_404(
        Paiement.objects.select_related(
            'wallet_payeur',
            'wallet_payeur__utilisateur',
            'wallet_beneficiaire',
            'wallet_beneficiaire__utilisateur',
        ),
        Q(wallet_payeur=wallet) | Q(wallet_beneficiaire=wallet),
        pk=paiement_id,
    )

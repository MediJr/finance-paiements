"""
Services métier — virements sécurisés.

Réutilise `wallets.services.mouvement_service` pour les mouvements de fonds.
"""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from administration.services.securite_service import (
    assert_montant_virement_max,
    assert_not_maintenance,
    assert_plafond_journalier,
    parse_cle_idempotence,
)
from beneficiaires.models import Beneficiaire
from historique.models import HistoriqueOperation
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_VIREMENT_CREATION,
    TYPE_VIREMENT_ECHEC,
    TYPE_VIREMENT_REUSSITE,
    enregistrer_evenement,
    enregistrer_evenement_durable,
)
from virements.models import Virement
from wallets.models import Wallet
from wallets.services.mouvement_service import (
    journaliser_transfert,
    parse_montant,
    transferer_fonds,
)


def executer_virement(
    *,
    emetteur: Utilisateur,
    beneficiaire_id: int,
    montant,
    motif: str = '',
    cle_idempotence: str | None = None,
) -> Virement:
    """
    Exécute un virement atomique vers un bénéficiaire actif du propriétaire.

    Avec une clé d'idempotence déjà utilisée par l'émetteur, le virement
    existant est renvoyé (`est_rejeu=True`) sans nouveau débit : un double clic
    ou une requête renvoyée après une coupure réseau ne débite jamais deux fois.
    """
    try:
        virement, cree = _executer_virement_atomic(
            emetteur=emetteur,
            beneficiaire_id=beneficiaire_id,
            montant=montant,
            motif=motif,
            cle_idempotence=cle_idempotence,
        )
    except ValidationError as exc:
        enregistrer_evenement_durable(
            type_evenement=TYPE_VIREMENT_ECHEC,
            module='virements',
            description=f'Échec virement : {exc}',
            niveau=Evenement.Niveau.WARNING,
            utilisateur=getattr(emetteur, 'user', None),
            contexte={
                'beneficiaire_id': beneficiaire_id,
                'montant': str(montant),
                'erreur': str(exc),
            },
        )
        raise

    virement.est_rejeu = not cree
    if not cree:
        return virement

    user = getattr(emetteur, 'user', None)
    ctx = {
        'virement_id': virement.pk,
        'reference': virement.reference,
        'montant': str(virement.montant),
    }
    enregistrer_evenement(
        type_evenement=TYPE_VIREMENT_CREATION,
        module='virements',
        description=f'Création virement {virement.reference}',
        utilisateur=user,
        contexte=ctx,
    )
    enregistrer_evenement(
        type_evenement=TYPE_VIREMENT_REUSSITE,
        module='virements',
        description=f'Virement réussi {virement.reference}',
        utilisateur=user,
        contexte=ctx,
    )
    return virement


@transaction.atomic
def _executer_virement_atomic(
    *,
    emetteur: Utilisateur,
    beneficiaire_id: int,
    montant,
    motif: str = '',
    cle_idempotence: str | None = None,
) -> tuple[Virement, bool]:
    if emetteur is None or emetteur.pk is None:
        raise ValidationError('Émetteur invalide.')
    if not emetteur.est_actif:
        raise ValidationError('L\'émetteur doit être actif.')

    cle = parse_cle_idempotence(cle_idempotence)
    if cle is not None:
        # Verrou sur le Wallet émetteur : deux requêtes simultanées portant la
        # même clé sont sérialisées, la seconde retrouve le virement de la première.
        wallet_verrouille = Wallet.objects.select_for_update().filter(
            utilisateur=emetteur
        ).first()
        existant = Virement.objects.filter(
            wallet_emetteur=wallet_verrouille,
            cle_idempotence=cle,
        ).first()
        if existant is not None:
            return existant, False

    montant_decimal = parse_montant(montant)
    assert_not_maintenance(operation='les virements')
    assert_montant_virement_max(montant_decimal)

    try:
        lien = Beneficiaire.objects.select_related(
            'utilisateur_beneficiaire',
            'utilisateur_beneficiaire__wallet',
            'proprietaire',
            'proprietaire__wallet',
        ).get(pk=beneficiaire_id, proprietaire=emetteur)
    except Beneficiaire.DoesNotExist as exc:
        raise ValidationError('Bénéficiaire inexistant ou non autorisé.') from exc

    if lien.statut != Beneficiaire.Statut.ACTIF:
        raise ValidationError('Le bénéficiaire est inactif.')

    destinataire = lien.utilisateur_beneficiaire
    if not destinataire.est_actif:
        raise ValidationError('Le destinataire est inactif.')

    if destinataire.pk == emetteur.pk:
        raise ValidationError('Impossible d\'effectuer un virement vers soi-même.')

    try:
        wallet_emetteur = emetteur.wallet
        wallet_beneficiaire = destinataire.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError(
            'Wallet introuvable pour l\'émetteur ou le destinataire.'
        ) from exc

    wallet_emetteur, wallet_beneficiaire = transferer_fonds(
        wallet_source=wallet_emetteur,
        wallet_destination=wallet_beneficiaire,
        montant=montant_decimal,
        label_source='émetteur',
        label_destination='bénéficiaire',
    )
    # Wallet verrouillé par transferer_fonds ; un refus annule toute la transaction.
    assert_plafond_journalier(wallet_emetteur, montant_decimal)

    reference = f'VIR-{uuid.uuid4().hex[:16].upper()}'
    motif_clean = (motif or '').strip()

    virement = Virement.objects.create(
        reference=reference,
        wallet_emetteur=wallet_emetteur,
        wallet_beneficiaire=wallet_beneficiaire,
        montant=montant_decimal,
        devise=wallet_emetteur.devise,
        statut=Virement.Statut.REUSSI,
        motif=motif_clean,
        cle_idempotence=cle,
    )

    description = f'Virement {reference}' + (f' — {motif_clean}' if motif_clean else '')
    journaliser_transfert(
        wallet_source=wallet_emetteur,
        wallet_destination=wallet_beneficiaire,
        montant=montant_decimal,
        type_operation=HistoriqueOperation.TypeOperation.VIREMENT,
        reference_base=reference,
        description=description,
    )

    return virement, True


def list_virements(*, utilisateur: Utilisateur):
    """Liste les virements où l'utilisateur est émetteur ou destinataire."""
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    try:
        wallet = utilisateur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    return (
        Virement.objects.select_related(
            'wallet_emetteur',
            'wallet_emetteur__utilisateur',
            'wallet_beneficiaire',
            'wallet_beneficiaire__utilisateur',
        )
        .filter(Q(wallet_emetteur=wallet) | Q(wallet_beneficiaire=wallet))
        .distinct()
    )


def get_virement_pour_utilisateur(
    *,
    utilisateur: Utilisateur,
    virement_id: int,
) -> Virement:
    """Retourne un virement auquel l'utilisateur a participé."""
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    try:
        wallet = utilisateur.wallet
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    return get_object_or_404(
        Virement.objects.select_related(
            'wallet_emetteur',
            'wallet_emetteur__utilisateur',
            'wallet_beneficiaire',
            'wallet_beneficiaire__utilisateur',
        ),
        Q(wallet_emetteur=wallet) | Q(wallet_beneficiaire=wallet),
        pk=virement_id,
    )

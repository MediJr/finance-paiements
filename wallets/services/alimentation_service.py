"""
Services métier — alimentation d'un Wallet par carte bancaire.

Seul point d'entrée de fonds sur la plateforme : sans lui, les Wallets
(créés à 0) ne pourraient jamais être utilisés.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import Utilisateur
from administration.services.securite_service import (
    assert_montant_alimentation_max,
    assert_not_maintenance,
    parse_cle_idempotence,
)
from historique.models import HistoriqueOperation
from historique.services import create_historique_operation
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_ALIMENTATION_ECHEC,
    TYPE_ALIMENTATION_REFUS,
    TYPE_ALIMENTATION_REUSSITE,
    enregistrer_evenement,
    enregistrer_evenement_durable,
)
from wallets.models import Alimentation, Wallet
from wallets.services.mouvement_service import parse_montant
from wallets.services.passerelle_carte import autoriser_carte


def alimenter_wallet(
    *,
    utilisateur: Utilisateur,
    montant,
    numero_carte,
    cle_idempotence: str | None = None,
) -> Alimentation:
    """
    Crédite le Wallet de l'utilisateur après autorisation de la carte.

    Retourne l'alimentation (acceptée ou refusée). Un format de carte ou de
    montant invalide lève ValidationError sans rien enregistrer. Avec une clé
    d'idempotence déjà utilisée, l'alimentation existante est renvoyée
    (`est_rejeu=True`) sans nouveau crédit.
    """
    try:
        alimentation, creee = _alimenter_atomic(
            utilisateur=utilisateur,
            montant=montant,
            numero_carte=numero_carte,
            cle_idempotence=cle_idempotence,
        )
    except ValidationError as exc:
        enregistrer_evenement_durable(
            type_evenement=TYPE_ALIMENTATION_ECHEC,
            module='wallets',
            description=f'Échec alimentation : {exc}',
            niveau=Evenement.Niveau.WARNING,
            utilisateur=getattr(utilisateur, 'user', None),
            contexte={'montant': str(montant), 'erreur': str(exc)},
        )
        raise

    alimentation.est_rejeu = not creee
    if creee:
        acceptee = alimentation.statut == Alimentation.Statut.ACCEPTEE
        enregistrer_evenement(
            type_evenement=TYPE_ALIMENTATION_REUSSITE if acceptee else TYPE_ALIMENTATION_REFUS,
            module='wallets',
            description=(
                f'Alimentation {alimentation.reference} '
                f'{"acceptée" if acceptee else "refusée"}'
            ),
            niveau=Evenement.Niveau.INFO if acceptee else Evenement.Niveau.WARNING,
            utilisateur=getattr(utilisateur, 'user', None),
            contexte={
                'reference': alimentation.reference,
                'montant': str(alimentation.montant),
                'carte': alimentation.carte_masquee,
            },
        )
    return alimentation


@transaction.atomic
def _alimenter_atomic(
    *,
    utilisateur: Utilisateur,
    montant,
    numero_carte,
    cle_idempotence: str | None,
) -> tuple[Alimentation, bool]:
    if utilisateur is None or utilisateur.pk is None:
        raise ValidationError('Utilisateur invalide.')
    if not utilisateur.est_actif:
        raise ValidationError("L'utilisateur doit être actif.")

    try:
        wallet = Wallet.objects.select_for_update().get(utilisateur=utilisateur)
    except Wallet.DoesNotExist as exc:
        raise ValidationError('Wallet introuvable.') from exc

    cle = parse_cle_idempotence(cle_idempotence)
    if cle is not None:
        existante = Alimentation.objects.filter(wallet=wallet, cle_idempotence=cle).first()
        if existante is not None:
            return existante, False

    montant_decimal = parse_montant(montant)
    assert_not_maintenance(operation='les alimentations')
    assert_montant_alimentation_max(montant_decimal)
    if wallet.statut != Wallet.Statut.ACTIF:
        raise ValidationError('Le Wallet est inactif.')

    # Décision serveur (format invalide → ValidationError, rien n'est enregistré)
    autorisation = autoriser_carte(numero_carte)
    reference = f'DEP-{uuid.uuid4().hex[:16].upper()}'

    if autorisation.accepte:
        wallet.solde = (wallet.solde + montant_decimal).quantize(Decimal('0.01'))
        wallet.save(update_fields=['solde', 'date_mise_a_jour'])

    alimentation = Alimentation.objects.create(
        reference=reference,
        wallet=wallet,
        montant=montant_decimal,
        devise=wallet.devise,
        statut=(
            Alimentation.Statut.ACCEPTEE if autorisation.accepte else Alimentation.Statut.REFUSEE
        ),
        carte_masquee=autorisation.carte_masquee,
        motif_refus=autorisation.motif_refus,
        cle_idempotence=cle,
    )
    create_historique_operation(
        wallet=wallet,
        type_operation=HistoriqueOperation.TypeOperation.CREDIT,
        description=(
            f'Alimentation par carte {autorisation.carte_masquee}'
            + ('' if autorisation.accepte else f' — refusée : {autorisation.motif_refus}')
        ),
        montant=montant_decimal,
        devise=wallet.devise,
        statut=(
            HistoriqueOperation.Statut.REUSSIE
            if autorisation.accepte
            else HistoriqueOperation.Statut.ECHOUEE
        ),
        reference=reference,
    )
    return alimentation, True


def list_alimentations(*, utilisateur: Utilisateur):
    """Alimentations du Wallet de l'utilisateur (plus récentes d'abord)."""
    return Alimentation.objects.filter(wallet__utilisateur=utilisateur)

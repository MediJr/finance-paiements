"""
Services techniques — mouvements de fonds entre Wallets.

Utilisé exclusivement par les services métier (virements, paiements,
remboursements). Toute modification de solde passe par ce module.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from historique.models import HistoriqueOperation
from historique.services import create_historique_operation
from wallets.models import Wallet


def parse_montant(montant) -> Decimal:
    """Parse et valide un montant strictement positif."""
    try:
        value = Decimal(str(montant))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError('Montant invalide.') from exc
    if value <= Decimal('0'):
        raise ValidationError('Le montant doit être strictement positif.')
    return value.quantize(Decimal('0.01'))


def lock_wallets(wallet_a: Wallet, wallet_b: Wallet) -> tuple[Wallet, Wallet]:
    """Verrouille deux Wallets dans un ordre stable (anti-deadlock)."""
    ids = sorted([wallet_a.pk, wallet_b.pk])
    locked = {
        w.pk: w
        for w in Wallet.objects.select_for_update().filter(pk__in=ids)
    }
    return locked[wallet_a.pk], locked[wallet_b.pk]


def transferer_fonds(
    *,
    wallet_source: Wallet,
    wallet_destination: Wallet,
    montant: Decimal,
    label_source: str = 'source',
    label_destination: str = 'destination',
) -> tuple[Wallet, Wallet]:
    """
    Débite wallet_source et crédite wallet_destination.

    Doit être appelé dans une transaction atomique.
    """
    if wallet_source.pk == wallet_destination.pk:
        raise ValidationError('Les Wallets source et destination doivent être distincts.')

    wallet_source, wallet_destination = lock_wallets(wallet_source, wallet_destination)

    if wallet_source.statut != Wallet.Statut.ACTIF:
        raise ValidationError(f'Le Wallet {label_source} est inactif.')
    if wallet_destination.statut != Wallet.Statut.ACTIF:
        raise ValidationError(f'Le Wallet {label_destination} est inactif.')

    if wallet_source.devise != wallet_destination.devise:
        raise ValidationError('Les devises des Wallets sont incompatibles.')

    if wallet_source.solde < montant:
        raise ValidationError('Solde insuffisant.')

    wallet_source.solde = (wallet_source.solde - montant).quantize(Decimal('0.01'))
    wallet_destination.solde = (wallet_destination.solde + montant).quantize(
        Decimal('0.01')
    )
    if wallet_source.solde < Decimal('0.00'):
        raise ValidationError('Solde insuffisant.')

    wallet_source.save(update_fields=['solde', 'date_mise_a_jour'])
    wallet_destination.save(update_fields=['solde', 'date_mise_a_jour'])
    return wallet_source, wallet_destination


def journaliser_transfert(
    *,
    wallet_source: Wallet,
    wallet_destination: Wallet,
    montant: Decimal,
    type_operation: str,
    reference_base: str,
    description: str,
) -> None:
    """Crée les deux écritures d'historique d'un transfert de fonds."""
    create_historique_operation(
        wallet=wallet_source,
        type_operation=type_operation,
        description=f'{description} (sortie)',
        montant=montant,
        devise=wallet_source.devise,
        statut=HistoriqueOperation.Statut.REUSSIE,
        reference=f'{reference_base}-OUT',
    )
    create_historique_operation(
        wallet=wallet_destination,
        type_operation=type_operation,
        description=f'{description} (entrée)',
        montant=montant,
        devise=wallet_destination.devise,
        statut=HistoriqueOperation.Statut.REUSSIE,
        reference=f'{reference_base}-IN',
    )

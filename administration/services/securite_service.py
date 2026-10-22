"""
Services de sécurité transverses — Sprint 7 Security by Design.

Validations centralisées : maintenance, plafonds, identifiants.
Utilisé exclusivement par les services métier (jamais depuis les vues seules).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from administration.models import ParametresApplication


def get_parametres_courants() -> ParametresApplication:
    """Lecture des paramètres sans contrôle admin (usage interne services)."""
    parametres, _ = ParametresApplication.objects.get_or_create(pk=1)
    return parametres


def assert_not_maintenance(*, operation: str = 'cette opération') -> None:
    """Refuse les opérations financières si le mode maintenance est actif."""
    parametres = get_parametres_courants()
    if parametres.mode_maintenance:
        raise ValidationError(
            f'Application en maintenance : {operation} est temporairement indisponible.'
        )


def assert_montant_virement_max(montant: Decimal) -> None:
    """Contrôle le plafond de virement défini dans les paramètres."""
    parametres = get_parametres_courants()
    plafond = parametres.montant_virement_max
    if montant > plafond:
        raise ValidationError(
            f'Le montant dépasse le plafond de virement autorisé ({plafond}).'
        )


def assert_montant_paiement_max(montant: Decimal) -> None:
    """Contrôle le plafond de paiement défini dans les paramètres."""
    parametres = get_parametres_courants()
    plafond = parametres.montant_paiement_max
    if montant > plafond:
        raise ValidationError(
            f'Le montant dépasse le plafond de paiement autorisé ({plafond}).'
        )


def assert_montant_alimentation_max(montant: Decimal) -> None:
    """Contrôle le plafond d'une alimentation de Wallet par carte."""
    plafond = get_parametres_courants().montant_alimentation_max
    if montant > plafond:
        raise ValidationError(
            f"Le montant dépasse le plafond d'alimentation autorisé ({plafond})."
        )


def total_sorties_du_jour(wallet) -> Decimal:
    """Somme des virements et paiements émis par le Wallet depuis minuit (heure locale)."""
    from paiements.models import Paiement
    from virements.models import Virement

    debut = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    virements = Virement.objects.filter(
        wallet_emetteur=wallet,
        statut=Virement.Statut.REUSSI,
        date_creation__gte=debut,
    ).aggregate(total=Sum('montant'))['total']
    paiements = Paiement.objects.filter(
        wallet_payeur=wallet,
        date_creation__gte=debut,
    ).aggregate(total=Sum('montant'))['total']
    return (virements or Decimal('0.00')) + (paiements or Decimal('0.00'))


def assert_plafond_journalier(wallet, montant: Decimal) -> None:
    """
    Contrôle le cumul quotidien des sorties.

    Sans ce contrôle, le plafond par opération se contourne en multipliant
    les petites opérations. À appeler Wallet verrouillé (select_for_update).
    """
    plafond = get_parametres_courants().plafond_journalier
    deja = total_sorties_du_jour(wallet)
    if deja + montant > plafond:
        disponible = max(plafond - deja, Decimal('0.00'))
        raise ValidationError(
            f"Plafond journalier atteint : {disponible} disponible aujourd'hui "
            f'(plafond {plafond}).'
        )


def parse_cle_idempotence(valeur) -> str | None:
    """Normalise une clé d'idempotence optionnelle (1 à 64 caractères imprimables)."""
    if valeur is None:
        return None
    cle = str(valeur).strip()
    if not cle:
        return None
    if len(cle) > 64 or not cle.isprintable():
        raise ValidationError("Clé d'idempotence invalide (64 caractères maximum).")
    return cle


def parse_identifiant(valeur, *, champ: str = 'identifiant') -> int:
    """Valide et convertit un identifiant numérique provenant du client."""
    try:
        parsed = int(valeur)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f'{champ} invalide.') from exc
    if parsed < 1:
        raise ValidationError(f'{champ} invalide.')
    return parsed


def parse_reference(valeur: str | None, *, max_length: int = 64) -> str | None:
    """Normalise une référence optionnelle (rejette les chaînes vides trop longues)."""
    if valeur is None:
        return None
    cleaned = str(valeur).strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValidationError(f'Référence trop longue (max {max_length}).')
    return cleaned

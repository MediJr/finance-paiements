"""
Services de sécurité transverses — Sprint 7 Security by Design.

Validations centralisées : maintenance, plafonds, identifiants.
Utilisé exclusivement par les services métier (jamais depuis les vues seules).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError

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

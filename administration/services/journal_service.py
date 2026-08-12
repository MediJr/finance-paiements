"""
Journal simple des actions d'administration — Sprint 7.

Pas d'observabilité avancée ni de SIEM : enregistrement métier local uniquement.
"""

from __future__ import annotations

from administration.models import JournalAdministration
from administration.permissions import require_administrateur


def journaliser_action(
    *,
    administrateur,
    action: str,
    details: str = '',
    cible_type: str = '',
    cible_id: int | None = None,
    adresse_ip: str | None = None,
) -> JournalAdministration:
    """Enregistre une action d'administration (appelé depuis les services admin)."""
    require_administrateur(administrateur)
    if action not in JournalAdministration.Action.values:
        action = JournalAdministration.Action.AUTRE
    return JournalAdministration.objects.create(
        administrateur=administrateur,
        action=action,
        details=(details or '')[:2000],
        cible_type=(cible_type or '')[:100],
        cible_id=cible_id,
        adresse_ip=adresse_ip or None,
    )


def list_journal_admin(*, administrateur, action: str | None = None, limit: int = 200):
    """Liste les entrées du journal (admin uniquement)."""
    require_administrateur(administrateur)
    queryset = JournalAdministration.objects.select_related('administrateur').all()
    if action:
        queryset = queryset.filter(action=action)
    return queryset[: max(1, min(limit, 500))]

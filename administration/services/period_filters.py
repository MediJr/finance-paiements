"""
Filtres de période partagés — pilotage admin (Sprint 8).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone, make_aware

from administration.services.securite_service import parse_identifiant


def _is_date_only(value: str) -> bool:
    parsed_date = parse_date(value)
    return parsed_date is not None and value == parsed_date.isoformat()


def parse_period_bound(value: str | None, *, is_end: bool = False):
    """Convertit une borne de période en datetime timezone-aware."""
    if not value:
        return None
    tz = get_current_timezone()
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


def apply_period_filter(
    queryset: QuerySet,
    *,
    date_debut: str | None = None,
    date_fin: str | None = None,
    field: str = 'date_creation',
) -> QuerySet:
    """Applique un filtre de période sur un champ datetime."""
    debut = parse_period_bound(date_debut, is_end=False)
    fin = parse_period_bound(date_fin, is_end=True)
    if debut is not None:
        queryset = queryset.filter(**{f'{field}__gte': debut})
    if fin is not None:
        if date_fin and _is_date_only(date_fin):
            queryset = queryset.filter(**{f'{field}__lt': fin})
        else:
            queryset = queryset.filter(**{f'{field}__lte': fin})
    return queryset


def parse_utilisateur_filtre(utilisateur_id) -> int | None:
    """Valide un filtre utilisateur optionnel (admin)."""
    if utilisateur_id in (None, ''):
        return None
    return parse_identifiant(utilisateur_id, champ='utilisateur')

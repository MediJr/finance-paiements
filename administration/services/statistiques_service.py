"""
Service métier — statistiques administrateur (Sprint 8).

Indicateurs métier simples : volumes, cumuls, répartition, activité par jour.
Aucune prédiction / ML / Data Analytics avancée.
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from administration.permissions import require_administrateur
from administration.services.period_filters import (
    apply_period_filter,
    parse_utilisateur_filtre,
)
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet


def _decimal(value) -> str:
    if value is None:
        return '0.00'
    return str(Decimal(value).quantize(Decimal('0.01')))


def _repartition_statut(queryset, *, field='statut') -> dict[str, int]:
    rows = queryset.values(field).annotate(total=Count('id')).order_by(field)
    return {row[field]: row['total'] for row in rows}


def _filtre_wallet_utilisateur(queryset, *, utilisateur_id: int | None, wallet_lookups: list[str]):
    if utilisateur_id is None:
        return queryset
    from django.db.models import Q

    condition = Q()
    for lookup in wallet_lookups:
        condition |= Q(**{f'{lookup}__utilisateur_id': utilisateur_id})
    return queryset.filter(condition)


def get_statistiques(
    *,
    administrateur,
    date_debut: str | None = None,
    date_fin: str | None = None,
    statut: str | None = None,
    utilisateur_id=None,
) -> dict:
    """Calcule les statistiques métier filtrables."""
    require_administrateur(administrateur)
    uid = parse_utilisateur_filtre(utilisateur_id)

    virements_qs = apply_period_filter(Virement.objects.all(), date_debut=date_debut, date_fin=date_fin)
    paiements_qs = apply_period_filter(Paiement.objects.all(), date_debut=date_debut, date_fin=date_fin)
    remboursements_qs = apply_period_filter(
        Remboursement.objects.all(),
        date_debut=date_debut,
        date_fin=date_fin,
    )

    virements_qs = _filtre_wallet_utilisateur(
        virements_qs,
        utilisateur_id=uid,
        wallet_lookups=['wallet_emetteur', 'wallet_beneficiaire'],
    )
    paiements_qs = _filtre_wallet_utilisateur(
        paiements_qs,
        utilisateur_id=uid,
        wallet_lookups=['wallet_payeur', 'wallet_beneficiaire'],
    )
    remboursements_qs = _filtre_wallet_utilisateur(
        remboursements_qs,
        utilisateur_id=uid,
        wallet_lookups=['wallet_remboursant', 'wallet_rembourse'],
    )

    if statut:
        virements_qs = virements_qs.filter(statut=statut)
        paiements_qs = paiements_qs.filter(statut=statut)
        remboursements_qs = remboursements_qs.filter(statut=statut)

    virements_agg = virements_qs.aggregate(nombre=Count('id'), montant=Sum('montant'))
    paiements_agg = paiements_qs.aggregate(nombre=Count('id'), montant=Sum('montant'))
    remboursements_agg = remboursements_qs.aggregate(
        nombre=Count('id'),
        montant=Sum('montant'),
    )

    activite = (
        apply_period_filter(Virement.objects.all(), date_debut=date_debut, date_fin=date_fin)
        .annotate(jour=TruncDate('date_creation'))
        .values('jour')
        .annotate(virements=Count('id'))
        .order_by('jour')
    )
    # Enrichir activité avec paiements / remboursements du même jour
    paiements_par_jour = {
        row['jour']: row['total']
        for row in (
            apply_period_filter(Paiement.objects.all(), date_debut=date_debut, date_fin=date_fin)
            .annotate(jour=TruncDate('date_creation'))
            .values('jour')
            .annotate(total=Count('id'))
        )
    }
    remboursements_par_jour = {
        row['jour']: row['total']
        for row in (
            apply_period_filter(
                Remboursement.objects.all(),
                date_debut=date_debut,
                date_fin=date_fin,
            )
            .annotate(jour=TruncDate('date_creation'))
            .values('jour')
            .annotate(total=Count('id'))
        )
    }
    jours = {row['jour'] for row in activite} | set(paiements_par_jour) | set(
        remboursements_par_jour
    )
    virements_par_jour = {row['jour']: row['virements'] for row in activite}
    activite_par_periode = [
        {
            'jour': jour.isoformat() if jour else None,
            'virements': virements_par_jour.get(jour, 0),
            'paiements': paiements_par_jour.get(jour, 0),
            'remboursements': remboursements_par_jour.get(jour, 0),
        }
        for jour in sorted(j for j in jours if j is not None)
    ]

    wallets_qs = Wallet.objects.all()
    if uid is not None:
        wallets_qs = wallets_qs.filter(utilisateur_id=uid)

    return {
        'filtres': {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'statut': statut,
            'utilisateur_id': uid,
        },
        'virements': {
            'nombre': virements_agg['nombre'] or 0,
            'montant_cumule': _decimal(virements_agg['montant']),
            'par_statut': _repartition_statut(
                apply_period_filter(
                    _filtre_wallet_utilisateur(
                        Virement.objects.all(),
                        utilisateur_id=uid,
                        wallet_lookups=['wallet_emetteur', 'wallet_beneficiaire'],
                    ),
                    date_debut=date_debut,
                    date_fin=date_fin,
                )
            ),
        },
        'paiements': {
            'nombre': paiements_agg['nombre'] or 0,
            'montant_cumule': _decimal(paiements_agg['montant']),
            'par_statut': _repartition_statut(
                apply_period_filter(
                    _filtre_wallet_utilisateur(
                        Paiement.objects.all(),
                        utilisateur_id=uid,
                        wallet_lookups=['wallet_payeur', 'wallet_beneficiaire'],
                    ),
                    date_debut=date_debut,
                    date_fin=date_fin,
                )
            ),
        },
        'remboursements': {
            'nombre': remboursements_agg['nombre'] or 0,
            'montant_cumule': _decimal(remboursements_agg['montant']),
            'par_statut': _repartition_statut(
                apply_period_filter(
                    _filtre_wallet_utilisateur(
                        Remboursement.objects.all(),
                        utilisateur_id=uid,
                        wallet_lookups=['wallet_remboursant', 'wallet_rembourse'],
                    ),
                    date_debut=date_debut,
                    date_fin=date_fin,
                )
            ),
        },
        'wallets': {
            'nombre': wallets_qs.count(),
            'actifs': wallets_qs.filter(statut=Wallet.Statut.ACTIF).count(),
            'solde_cumule': _decimal(wallets_qs.aggregate(total=Sum('solde'))['total']),
        },
        'activite_par_periode': activite_par_periode,
    }

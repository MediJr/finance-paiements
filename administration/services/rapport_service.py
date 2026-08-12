"""
Service métier — rapports administrateur (Sprint 8).

Rapports en lecture seule. Pas d'export avancé / pas d'analytique.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum

from accounts.models import Utilisateur
from administration.permissions import require_administrateur
from administration.services.period_filters import (
    apply_period_filter,
    parse_utilisateur_filtre,
)
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet

TYPES_RAPPORT = (
    'virements',
    'paiements',
    'remboursements',
    'wallets',
    'utilisateurs',
)


def _decimal(value) -> str:
    if value is None:
        return '0.00'
    return str(Decimal(value).quantize(Decimal('0.01')))


def generer_rapport(
    *,
    administrateur,
    type_rapport: str,
    date_debut: str | None = None,
    date_fin: str | None = None,
    statut: str | None = None,
    utilisateur_id=None,
    limit: int = 500,
) -> dict:
    """
    Génère un rapport consultable (lecture seule).

    Types : virements, paiements, remboursements, wallets, utilisateurs.
    """
    require_administrateur(administrateur)
    type_rapport = (type_rapport or '').strip().lower()
    if type_rapport not in TYPES_RAPPORT:
        raise ValidationError(
            f'Type de rapport invalide. Attendus : {", ".join(TYPES_RAPPORT)}.'
        )
    uid = parse_utilisateur_filtre(utilisateur_id)
    limit = max(1, min(int(limit or 500), 1000))

    filtres = {
        'type': type_rapport,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'statut': statut,
        'utilisateur_id': uid,
    }

    if type_rapport == 'virements':
        return _rapport_virements(filtres, limit=limit)
    if type_rapport == 'paiements':
        return _rapport_paiements(filtres, limit=limit)
    if type_rapport == 'remboursements':
        return _rapport_remboursements(filtres, limit=limit)
    if type_rapport == 'wallets':
        return _rapport_wallets(filtres, limit=limit)
    return _rapport_utilisateurs(filtres, limit=limit)


def _rapport_virements(filtres: dict, *, limit: int) -> dict:
    qs = apply_period_filter(
        Virement.objects.select_related(
            'wallet_emetteur__utilisateur',
            'wallet_beneficiaire__utilisateur',
        ),
        date_debut=filtres['date_debut'],
        date_fin=filtres['date_fin'],
    )
    if filtres['utilisateur_id'] is not None:
        from django.db.models import Q

        uid = filtres['utilisateur_id']
        qs = qs.filter(
            Q(wallet_emetteur__utilisateur_id=uid)
            | Q(wallet_beneficiaire__utilisateur_id=uid)
        )
    if filtres['statut']:
        qs = qs.filter(statut=filtres['statut'])

    nombre = qs.count()
    montant = qs.aggregate(total=Sum('montant'))['total']
    lignes = [
        {
            'id': v.pk,
            'reference': v.reference,
            'montant': _decimal(v.montant),
            'devise': v.devise,
            'statut': v.statut,
            'emetteur_id': v.wallet_emetteur.utilisateur_id,
            'beneficiaire_id': v.wallet_beneficiaire.utilisateur_id,
            'date_creation': v.date_creation.isoformat(),
        }
        for v in qs[:limit]
    ]
    return {
        'type': 'virements',
        'filtres': filtres,
        'totaux': {'nombre': nombre, 'montant_cumule': _decimal(montant)},
        'lignes': lignes,
    }


def _rapport_paiements(filtres: dict, *, limit: int) -> dict:
    qs = apply_period_filter(
        Paiement.objects.select_related(
            'wallet_payeur__utilisateur',
            'wallet_beneficiaire__utilisateur',
        ),
        date_debut=filtres['date_debut'],
        date_fin=filtres['date_fin'],
    )
    if filtres['utilisateur_id'] is not None:
        from django.db.models import Q

        uid = filtres['utilisateur_id']
        qs = qs.filter(
            Q(wallet_payeur__utilisateur_id=uid)
            | Q(wallet_beneficiaire__utilisateur_id=uid)
        )
    if filtres['statut']:
        qs = qs.filter(statut=filtres['statut'])

    nombre = qs.count()
    montant = qs.aggregate(total=Sum('montant'))['total']
    lignes = [
        {
            'id': p.pk,
            'reference': p.reference,
            'montant': _decimal(p.montant),
            'montant_rembourse': _decimal(p.montant_rembourse),
            'devise': p.devise,
            'statut': p.statut,
            'payeur_id': p.wallet_payeur.utilisateur_id,
            'beneficiaire_id': p.wallet_beneficiaire.utilisateur_id,
            'date_creation': p.date_creation.isoformat(),
        }
        for p in qs[:limit]
    ]
    return {
        'type': 'paiements',
        'filtres': filtres,
        'totaux': {'nombre': nombre, 'montant_cumule': _decimal(montant)},
        'lignes': lignes,
    }


def _rapport_remboursements(filtres: dict, *, limit: int) -> dict:
    qs = apply_period_filter(
        Remboursement.objects.select_related(
            'paiement',
            'wallet_remboursant__utilisateur',
            'wallet_rembourse__utilisateur',
        ),
        date_debut=filtres['date_debut'],
        date_fin=filtres['date_fin'],
    )
    if filtres['utilisateur_id'] is not None:
        from django.db.models import Q

        uid = filtres['utilisateur_id']
        qs = qs.filter(
            Q(wallet_remboursant__utilisateur_id=uid)
            | Q(wallet_rembourse__utilisateur_id=uid)
        )
    if filtres['statut']:
        qs = qs.filter(statut=filtres['statut'])

    nombre = qs.count()
    montant = qs.aggregate(total=Sum('montant'))['total']
    lignes = [
        {
            'id': r.pk,
            'reference': r.reference,
            'paiement_reference': r.paiement.reference,
            'montant': _decimal(r.montant),
            'devise': r.devise,
            'statut': r.statut,
            'remboursant_id': r.wallet_remboursant.utilisateur_id,
            'rembourse_id': r.wallet_rembourse.utilisateur_id,
            'date_creation': r.date_creation.isoformat(),
        }
        for r in qs[:limit]
    ]
    return {
        'type': 'remboursements',
        'filtres': filtres,
        'totaux': {'nombre': nombre, 'montant_cumule': _decimal(montant)},
        'lignes': lignes,
    }


def _rapport_wallets(filtres: dict, *, limit: int) -> dict:
    qs = Wallet.objects.select_related('utilisateur', 'utilisateur__user').all()
    if filtres['utilisateur_id'] is not None:
        qs = qs.filter(utilisateur_id=filtres['utilisateur_id'])
    if filtres['statut']:
        qs = qs.filter(statut=filtres['statut'])
    if filtres['date_debut'] or filtres['date_fin']:
        qs = apply_period_filter(
            qs,
            date_debut=filtres['date_debut'],
            date_fin=filtres['date_fin'],
        )

    nombre = qs.count()
    solde = qs.aggregate(total=Sum('solde'))['total']
    lignes = [
        {
            'id': w.pk,
            'utilisateur_id': w.utilisateur_id,
            'email': w.utilisateur.email,
            'solde': _decimal(w.solde),
            'devise': w.devise,
            'statut': w.statut,
            'date_creation': w.date_creation.isoformat(),
        }
        for w in qs[:limit]
    ]
    return {
        'type': 'wallets',
        'filtres': filtres,
        'totaux': {'nombre': nombre, 'solde_cumule': _decimal(solde)},
        'lignes': lignes,
    }


def _rapport_utilisateurs(filtres: dict, *, limit: int) -> dict:
    qs = Utilisateur.objects.select_related('user', 'wallet').all()
    if filtres['utilisateur_id'] is not None:
        qs = qs.filter(pk=filtres['utilisateur_id'])
    if filtres['statut'] in ('1', 'true', 'True', 'actif'):
        qs = qs.filter(est_actif=True)
    elif filtres['statut'] in ('0', 'false', 'False', 'inactif'):
        qs = qs.filter(est_actif=False)
    if filtres['date_debut'] or filtres['date_fin']:
        qs = apply_period_filter(
            qs,
            date_debut=filtres['date_debut'],
            date_fin=filtres['date_fin'],
        )

    nombre = qs.count()
    actifs = qs.filter(est_actif=True).count()
    lignes = [
        {
            'id': u.pk,
            'username': u.user.username,
            'email': u.email,
            'prenom': u.prenom,
            'nom': u.nom,
            'est_actif': u.est_actif,
            'wallet_id': getattr(u, 'wallet', None).pk if hasattr(u, 'wallet') else None,
            'date_creation': u.date_creation.isoformat(),
        }
        for u in qs[:limit]
    ]
    return {
        'type': 'utilisateurs',
        'filtres': filtres,
        'totaux': {'nombre': nombre, 'actifs': actifs},
        'lignes': lignes,
    }

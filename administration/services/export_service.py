"""
Service d'export — Prototype 4 Sprint 10.

Centralise tous les exports CSV / JSON (lecture seule, admin uniquement).
Aucun export direct dans les vues.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable

from django.core.exceptions import ValidationError
from django.utils.timezone import localtime, now

from accounts.models import Utilisateur
from administration.permissions import require_administrateur
from administration.services.period_filters import apply_period_filter
from beneficiaires.models import Beneficiaire
from historique.models import HistoriqueOperation
from observabilite.models import Evenement
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet

TYPES_EXPORT = (
    'utilisateurs',
    'wallets',
    'beneficiaires',
    'virements',
    'paiements',
    'remboursements',
    'historique',
    'evenements',
)

FORMATS_EXPORT = ('csv', 'json')

EXPORT_VERSION = 'finance-export-v1'


def _json_default(value: Any):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f'Type non sérialisable : {type(value)!r}')


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return localtime(value).isoformat()
    return str(value)


def exporter(
    *,
    administrateur,
    type_export: str,
    format_export: str = 'json',
    date_debut: str | None = None,
    date_fin: str | None = None,
    statut: str | None = None,
) -> dict:
    """
    Génère un export CSV ou JSON.

    Retourne :
    - filename
    - content_type
    - content (str)
    - meta (dict)
    """
    require_administrateur(administrateur)
    type_export = (type_export or '').strip().lower()
    format_export = (format_export or 'json').strip().lower()

    if type_export not in TYPES_EXPORT:
        raise ValidationError(
            f'Type d\'export invalide. Attendus : {", ".join(TYPES_EXPORT)}.'
        )
    if format_export not in FORMATS_EXPORT:
        raise ValidationError('Format d\'export invalide. Attendus : csv, json.')

    rows = _collect_rows(
        type_export=type_export,
        date_debut=date_debut,
        date_fin=date_fin,
        statut=statut,
    )
    generated_at = now()
    meta = {
        'application': '11-finance',
        'version': EXPORT_VERSION,
        'type': type_export,
        'format': format_export,
        'generated_at': generated_at.isoformat(),
        'filtres': {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'statut': statut,
        },
        'count': len(rows),
    }

    stamp = localtime(generated_at).strftime('%Y%m%d-%H%M%S')
    if format_export == 'json':
        content = _to_json(meta=meta, rows=rows)
        content_type = 'application/json; charset=utf-8'
        filename = f'finance-{type_export}-{stamp}.json'
    else:
        content = _to_csv(rows=rows)
        content_type = 'text/csv; charset=utf-8'
        filename = f'finance-{type_export}-{stamp}.csv'

    _journaliser_export(
        administrateur=administrateur,
        type_export=type_export,
        format_export=format_export,
        count=len(rows),
    )

    return {
        'filename': filename,
        'content_type': content_type,
        'content': content,
        'meta': meta,
    }


def _journaliser_export(*, administrateur, type_export, format_export, count):
    try:
        from observabilite.models import Evenement as Ev
        from observabilite.services.journal_service import enregistrer_evenement

        enregistrer_evenement(
            type_evenement='admin_export',
            module='administration',
            description=f'Export {format_export} — {type_export} ({count} lignes)',
            niveau=Ev.Niveau.SECURITY,
            utilisateur=administrateur,
            contexte={
                'type': type_export,
                'format': format_export,
                'count': count,
            },
        )
    except Exception:
        return


def _collect_rows(
    *,
    type_export: str,
    date_debut: str | None,
    date_fin: str | None,
    statut: str | None,
) -> list[dict]:
    collectors = {
        'utilisateurs': _rows_utilisateurs,
        'wallets': _rows_wallets,
        'beneficiaires': _rows_beneficiaires,
        'virements': _rows_virements,
        'paiements': _rows_paiements,
        'remboursements': _rows_remboursements,
        'historique': _rows_historique,
        'evenements': _rows_evenements,
    }
    return collectors[type_export](
        date_debut=date_debut,
        date_fin=date_fin,
        statut=statut,
    )


def _rows_utilisateurs(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Utilisateur.objects.select_related('user', 'wallet').all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut in ('1', 'true', 'True', 'actif'):
        qs = qs.filter(est_actif=True)
    elif statut in ('0', 'false', 'False', 'inactif'):
        qs = qs.filter(est_actif=False)
    return [
        {
            'id': u.pk,
            'username': u.user.username,
            'prenom': u.prenom,
            'nom': u.nom,
            'email': u.email,
            'telephone': u.telephone,
            'est_actif': u.est_actif,
            'wallet_id': getattr(getattr(u, 'wallet', None), 'pk', None),
            'date_creation': _iso(u.date_creation),
        }
        for u in qs
    ]


def _rows_wallets(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Wallet.objects.select_related('utilisateur').all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut:
        qs = qs.filter(statut=statut)
    return [
        {
            'id': w.pk,
            'utilisateur_id': w.utilisateur_id,
            'solde': str(w.solde),
            'devise': w.devise,
            'statut': w.statut,
            'date_creation': _iso(w.date_creation),
        }
        for w in qs
    ]


def _rows_beneficiaires(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Beneficiaire.objects.select_related(
        'proprietaire',
        'utilisateur_beneficiaire',
    ).all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut:
        qs = qs.filter(statut=statut)
    return [
        {
            'id': b.pk,
            'proprietaire_id': b.proprietaire_id,
            'utilisateur_beneficiaire_id': b.utilisateur_beneficiaire_id,
            'alias': b.alias,
            'statut': b.statut,
            'date_creation': _iso(b.date_creation),
        }
        for b in qs
    ]


def _rows_virements(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Virement.objects.select_related(
        'wallet_emetteur',
        'wallet_beneficiaire',
    ).all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut:
        qs = qs.filter(statut=statut)
    return [
        {
            'id': v.pk,
            'reference': v.reference,
            'wallet_emetteur_id': v.wallet_emetteur_id,
            'wallet_beneficiaire_id': v.wallet_beneficiaire_id,
            'montant': str(v.montant),
            'devise': v.devise,
            'statut': v.statut,
            'motif': v.motif,
            'date_creation': _iso(v.date_creation),
        }
        for v in qs
    ]


def _rows_paiements(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Paiement.objects.select_related(
        'wallet_payeur',
        'wallet_beneficiaire',
    ).all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut:
        qs = qs.filter(statut=statut)
    return [
        {
            'id': p.pk,
            'reference': p.reference,
            'wallet_payeur_id': p.wallet_payeur_id,
            'wallet_beneficiaire_id': p.wallet_beneficiaire_id,
            'montant': str(p.montant),
            'montant_rembourse': str(p.montant_rembourse),
            'devise': p.devise,
            'statut': p.statut,
            'motif': p.motif,
            'date_creation': _iso(p.date_creation),
        }
        for p in qs
    ]


def _rows_remboursements(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Remboursement.objects.select_related('paiement').all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut:
        qs = qs.filter(statut=statut)
    return [
        {
            'id': r.pk,
            'reference': r.reference,
            'paiement_id': r.paiement_id,
            'wallet_remboursant_id': r.wallet_remboursant_id,
            'wallet_rembourse_id': r.wallet_rembourse_id,
            'montant': str(r.montant),
            'devise': r.devise,
            'statut': r.statut,
            'date_creation': _iso(r.date_creation),
        }
        for r in qs
    ]


def _rows_historique(*, date_debut, date_fin, statut) -> list[dict]:
    qs = HistoriqueOperation.objects.select_related('wallet').all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    if statut:
        qs = qs.filter(statut=statut)
    return [
        {
            'id': h.pk,
            'wallet_id': h.wallet_id,
            'type_operation': h.type_operation,
            'statut': h.statut,
            'description': h.description,
            'montant': str(h.montant) if h.montant is not None else None,
            'devise': h.devise,
            'reference': h.reference,
            'date_creation': _iso(h.date_creation),
        }
        for h in qs
    ]


def _rows_evenements(*, date_debut, date_fin, statut) -> list[dict]:
    qs = Evenement.objects.select_related('utilisateur').all()
    qs = apply_period_filter(qs, date_debut=date_debut, date_fin=date_fin)
    # Pour les événements, "statut" mappe le niveau.
    if statut:
        qs = qs.filter(niveau=statut)
    return [
        {
            'id': e.pk,
            'date_creation': _iso(e.date_creation),
            'type_evenement': e.type_evenement,
            'niveau': e.niveau,
            'module': e.module,
            'utilisateur_id': e.utilisateur_id,
            'description': e.description,
            'contexte': e.contexte,
            'adresse_ip': e.adresse_ip,
            'user_agent': e.user_agent,
        }
        for e in qs
    ]


def _to_json(*, meta: dict, rows: list[dict]) -> str:
    payload = {
        'export': meta,
        'data': rows,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)


def _to_csv(*, rows: list[dict]) -> str:
    buffer = io.StringIO()
    # BOM UTF-8 pour compatibilité tableurs.
    buffer.write('\ufeff')
    if not rows:
        buffer.write('id\n')
        return buffer.getvalue()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        flat = {}
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                flat[key] = json.dumps(value, ensure_ascii=False, default=_json_default)
            elif value is None:
                flat[key] = ''
            else:
                flat[key] = value
        writer.writerow(flat)
    return buffer.getvalue()

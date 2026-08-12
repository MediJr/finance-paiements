"""
Services métier — administration fonctionnelle.

Lecture, recherche, filtrage et paramètres.
Aucune logique financière (pas de modification de solde).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from administration.models import JournalAdministration, ParametresApplication
from administration.permissions import require_administrateur
from administration.services.journal_service import journaliser_action
from historique.models import HistoriqueOperation
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet


def get_parametres(*, administrateur=None) -> ParametresApplication:
    """Retourne les paramètres globaux (crée le singleton si besoin)."""
    if administrateur is not None:
        require_administrateur(administrateur)
    parametres, _ = ParametresApplication.objects.get_or_create(pk=1)
    return parametres


@transaction.atomic
def update_parametres(
    *,
    administrateur,
    adresse_ip: str | None = None,
    **kwargs,
) -> ParametresApplication:
    """Met à jour les paramètres globaux (admin uniquement)."""
    require_administrateur(administrateur)
    ParametresApplication.objects.get_or_create(pk=1)
    parametres = ParametresApplication.objects.select_for_update().get(pk=1)

    allowed = {
        'nom_application',
        'devise_par_defaut',
        'mode_maintenance',
        'montant_virement_max',
        'montant_paiement_max',
        'delai_session_minutes',
    }
    changes = []
    for key, value in kwargs.items():
        if key not in allowed or value is None:
            continue
        if key in ('montant_virement_max', 'montant_paiement_max'):
            try:
                value = Decimal(str(value)).quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValidationError(f'Montant invalide pour {key}.') from exc
            if value <= Decimal('0'):
                raise ValidationError(f'{key} doit être strictement positif.')
        if key == 'devise_par_defaut':
            value = str(value).strip().upper()
            if len(value) != 3:
                raise ValidationError('La devise doit être un code ISO à 3 lettres.')
        if key == 'delai_session_minutes':
            value = int(value)
            if value < 1:
                raise ValidationError('La durée de session doit être >= 1.')
        if key == 'mode_maintenance':
            value = bool(value)
        if key == 'nom_application':
            value = str(value).strip()
            if not value:
                raise ValidationError('Le nom de l\'application est obligatoire.')
        ancien = getattr(parametres, key)
        if ancien != value:
            changes.append(f'{key}: {ancien!r} → {value!r}')
        setattr(parametres, key, value)

    parametres.save()
    if changes:
        journaliser_action(
            administrateur=administrateur,
            action=JournalAdministration.Action.MODIFICATION_PARAMETRES,
            details='; '.join(changes),
            cible_type='ParametresApplication',
            cible_id=1,
            adresse_ip=adresse_ip,
        )
        from observabilite.models import Evenement
        from observabilite.services.journal_service import (
            TYPE_ADMIN_PARAMETRES,
            enregistrer_evenement,
        )

        enregistrer_evenement(
            type_evenement=TYPE_ADMIN_PARAMETRES,
            module='administration',
            description='Modification des paramètres application',
            niveau=Evenement.Niveau.SECURITY,
            utilisateur=administrateur,
            contexte={'changes': changes},
            adresse_ip=adresse_ip,
        )
    return parametres


def list_utilisateurs_admin(
    *,
    administrateur,
    q: str | None = None,
    est_actif: bool | None = None,
):
    """Liste filtrable des utilisateurs métier."""
    require_administrateur(administrateur)
    queryset = Utilisateur.objects.select_related('user', 'wallet').all()
    if est_actif is not None:
        queryset = queryset.filter(est_actif=est_actif)
    if q:
        queryset = queryset.filter(
            Q(prenom__icontains=q)
            | Q(nom__icontains=q)
            | Q(email__icontains=q)
            | Q(user__username__icontains=q)
        )
    return queryset


@transaction.atomic
def activer_utilisateur(
    *,
    administrateur,
    utilisateur_id: int,
    adresse_ip: str | None = None,
) -> Utilisateur:
    """Active un utilisateur métier (et son compte auth)."""
    require_administrateur(administrateur)
    utilisateur = get_object_or_404(
        Utilisateur.objects.select_related('user'),
        pk=utilisateur_id,
    )
    utilisateur.est_actif = True
    utilisateur.save(update_fields=['est_actif', 'date_mise_a_jour'])
    utilisateur.user.is_active = True
    utilisateur.user.save(update_fields=['is_active'])
    journaliser_action(
        administrateur=administrateur,
        action=JournalAdministration.Action.ACTIVATION_UTILISATEUR,
        details=f'Activation de {utilisateur.email}',
        cible_type='Utilisateur',
        cible_id=utilisateur.pk,
        adresse_ip=adresse_ip,
    )
    from observabilite.models import Evenement
    from observabilite.services.journal_service import (
        TYPE_UTILISATEUR_ACTIVATION,
        enregistrer_evenement,
    )

    enregistrer_evenement(
        type_evenement=TYPE_UTILISATEUR_ACTIVATION,
        module='administration',
        description=f'Activation utilisateur {utilisateur.email}',
        niveau=Evenement.Niveau.SECURITY,
        utilisateur=administrateur,
        contexte={'utilisateur_id': utilisateur.pk},
        adresse_ip=adresse_ip,
    )
    return utilisateur


@transaction.atomic
def desactiver_utilisateur(
    *,
    administrateur,
    utilisateur_id: int,
    adresse_ip: str | None = None,
) -> Utilisateur:
    """Désactive un utilisateur métier (et son compte auth)."""
    require_administrateur(administrateur)
    utilisateur = get_object_or_404(
        Utilisateur.objects.select_related('user'),
        pk=utilisateur_id,
    )
    if utilisateur.user_id == administrateur.pk:
        raise ValidationError('Un administrateur ne peut pas se désactiver lui-même.')
    utilisateur.est_actif = False
    utilisateur.save(update_fields=['est_actif', 'date_mise_a_jour'])
    utilisateur.user.is_active = False
    utilisateur.user.save(update_fields=['is_active'])
    journaliser_action(
        administrateur=administrateur,
        action=JournalAdministration.Action.DESACTIVATION_UTILISATEUR,
        details=f'Désactivation de {utilisateur.email}',
        cible_type='Utilisateur',
        cible_id=utilisateur.pk,
        adresse_ip=adresse_ip,
    )
    from observabilite.models import Evenement
    from observabilite.services.journal_service import (
        TYPE_UTILISATEUR_DESACTIVATION,
        enregistrer_evenement,
    )

    enregistrer_evenement(
        type_evenement=TYPE_UTILISATEUR_DESACTIVATION,
        module='administration',
        description=f'Désactivation utilisateur {utilisateur.email}',
        niveau=Evenement.Niveau.SECURITY,
        utilisateur=administrateur,
        contexte={'utilisateur_id': utilisateur.pk},
        adresse_ip=adresse_ip,
    )
    return utilisateur


def enregistrer_acces_admin(*, administrateur, adresse_ip: str | None = None) -> None:
    """Journalise un accès important à l'espace d'administration."""
    journaliser_action(
        administrateur=administrateur,
        action=JournalAdministration.Action.ACCES_ADMIN,
        details='Accès à l\'accueil administration',
        cible_type='Administration',
        adresse_ip=adresse_ip,
    )
    from observabilite.models import Evenement
    from observabilite.services.journal_service import (
        TYPE_ADMIN_ACCES,
        enregistrer_evenement,
    )

    enregistrer_evenement(
        type_evenement=TYPE_ADMIN_ACCES,
        module='administration',
        description='Accès à l\'accueil administration',
        niveau=Evenement.Niveau.SECURITY,
        utilisateur=administrateur,
        adresse_ip=adresse_ip,
    )


def list_wallets_admin(
    *,
    administrateur,
    q: str | None = None,
    statut: str | None = None,
    devise: str | None = None,
):
    """Liste filtrable des Wallets (lecture seule)."""
    require_administrateur(administrateur)
    queryset = Wallet.objects.select_related('utilisateur', 'utilisateur__user').all()
    if statut:
        queryset = queryset.filter(statut=statut)
    if devise:
        queryset = queryset.filter(devise__iexact=devise)
    if q:
        queryset = queryset.filter(
            Q(utilisateur__prenom__icontains=q)
            | Q(utilisateur__nom__icontains=q)
            | Q(utilisateur__email__icontains=q)
        )
    return queryset


def list_virements_admin(
    *,
    administrateur,
    q: str | None = None,
    statut: str | None = None,
):
    require_administrateur(administrateur)
    queryset = Virement.objects.select_related(
        'wallet_emetteur__utilisateur',
        'wallet_beneficiaire__utilisateur',
    ).all()
    if statut:
        queryset = queryset.filter(statut=statut)
    if q:
        queryset = queryset.filter(
            Q(reference__icontains=q) | Q(motif__icontains=q)
        )
    return queryset


def list_paiements_admin(
    *,
    administrateur,
    q: str | None = None,
    statut: str | None = None,
):
    require_administrateur(administrateur)
    queryset = Paiement.objects.select_related(
        'wallet_payeur__utilisateur',
        'wallet_beneficiaire__utilisateur',
    ).all()
    if statut:
        queryset = queryset.filter(statut=statut)
    if q:
        queryset = queryset.filter(
            Q(reference__icontains=q) | Q(motif__icontains=q)
        )
    return queryset


def list_remboursements_admin(
    *,
    administrateur,
    q: str | None = None,
    statut: str | None = None,
):
    require_administrateur(administrateur)
    queryset = Remboursement.objects.select_related(
        'paiement',
        'wallet_remboursant__utilisateur',
        'wallet_rembourse__utilisateur',
    ).all()
    if statut:
        queryset = queryset.filter(statut=statut)
    if q:
        queryset = queryset.filter(
            Q(reference__icontains=q) | Q(paiement__reference__icontains=q)
        )
    return queryset


def list_historique_admin(
    *,
    administrateur,
    q: str | None = None,
    type_operation: str | None = None,
    statut: str | None = None,
):
    require_administrateur(administrateur)
    queryset = HistoriqueOperation.objects.select_related(
        'wallet',
        'wallet__utilisateur',
    ).all()
    if type_operation:
        queryset = queryset.filter(type_operation=type_operation)
    if statut:
        queryset = queryset.filter(statut=statut)
    if q:
        queryset = queryset.filter(
            Q(reference__icontains=q) | Q(description__icontains=q)
        )
    return queryset

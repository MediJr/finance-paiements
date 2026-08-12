"""
Services métier — bénéficiaires.

Toutes les règles de gestion et de sécurité d'accès sont centralisées ici.
Aucune opération financière n'est réalisée.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from beneficiaires.models import Beneficiaire


def _require_proprietaire(proprietaire: Utilisateur) -> Utilisateur:
    if proprietaire is None or proprietaire.pk is None:
        raise ValidationError('Propriétaire invalide.')
    if not proprietaire.est_actif:
        raise ValidationError('Le propriétaire doit être actif.')
    return proprietaire


def get_utilisateur_connecte(user) -> Utilisateur:
    """Résout l'utilisateur métier lié au User Django authentifié."""
    if user is None or not getattr(user, 'is_authenticated', False):
        raise PermissionDenied('Authentification requise.')
    try:
        return Utilisateur.objects.select_related('user').get(user=user)
    except Utilisateur.DoesNotExist as exc:
        raise PermissionDenied(
            'Aucun profil métier associé à ce compte.'
        ) from exc


@transaction.atomic
def create_beneficiaire(
    *,
    proprietaire: Utilisateur,
    beneficiaire_id: int,
    alias: str = '',
) -> Beneficiaire:
    """Ajoute un bénéficiaire à la liste du propriétaire."""
    proprietaire = _require_proprietaire(proprietaire)

    try:
        destinataire = Utilisateur.objects.get(pk=beneficiaire_id)
    except Utilisateur.DoesNotExist as exc:
        raise ValidationError('Bénéficiaire introuvable.') from exc

    if destinataire.pk == proprietaire.pk:
        raise ValidationError(
            'Un utilisateur ne peut pas s\'ajouter lui-même comme bénéficiaire.'
        )

    if not destinataire.est_actif:
        raise ValidationError('Le bénéficiaire sélectionné est inactif.')

    try:
        beneficiaire = Beneficiaire.objects.create(
            proprietaire=proprietaire,
            utilisateur_beneficiaire=destinataire,
            alias=(alias or '').strip(),
            statut=Beneficiaire.Statut.ACTIF,
        )
    except IntegrityError as exc:
        raise ValidationError(
            'Ce bénéficiaire est déjà présent dans votre liste.'
        ) from exc

    from observabilite.services.journal_service import (
        TYPE_BENEFICIAIRE_CREATION,
        enregistrer_evenement,
    )

    enregistrer_evenement(
        type_evenement=TYPE_BENEFICIAIRE_CREATION,
        module='beneficiaires',
        description=f'Création bénéficiaire #{beneficiaire.pk}',
        utilisateur=getattr(proprietaire, 'user', None),
        contexte={
            'beneficiaire_id': beneficiaire.pk,
            'destinataire_id': destinataire.pk,
        },
    )
    return beneficiaire


def list_beneficiaires(
    *,
    proprietaire: Utilisateur,
    statut: str | None = None,
):
    """Liste les bénéficiaires du propriétaire (éventuellement filtrés)."""
    proprietaire = _require_proprietaire(proprietaire)
    queryset = Beneficiaire.objects.select_related(
        'proprietaire',
        'utilisateur_beneficiaire',
        'utilisateur_beneficiaire__user',
    ).filter(proprietaire=proprietaire)
    if statut:
        queryset = queryset.filter(statut=statut)
    return queryset


def list_beneficiaires_selectionnables(*, proprietaire: Utilisateur):
    """
    Bénéficiaires actifs sélectionnables pour de futurs virements.

    Un bénéficiaire inactif est exclu.
    """
    return list_beneficiaires(
        proprietaire=proprietaire,
        statut=Beneficiaire.Statut.ACTIF,
    )


def get_beneficiaire_pour_proprietaire(
    *,
    proprietaire: Utilisateur,
    beneficiaire_id: int,
) -> Beneficiaire:
    """Retourne un bénéficiaire appartenant exclusivement au propriétaire."""
    proprietaire = _require_proprietaire(proprietaire)
    return get_object_or_404(
        Beneficiaire.objects.select_related(
            'proprietaire',
            'utilisateur_beneficiaire',
            'utilisateur_beneficiaire__user',
        ),
        pk=beneficiaire_id,
        proprietaire=proprietaire,
    )


@transaction.atomic
def update_beneficiaire(
    *,
    proprietaire: Utilisateur,
    beneficiaire_id: int,
    alias: str | None = None,
    statut: str | None = None,
) -> Beneficiaire:
    """Modifie l'alias et/ou le statut d'un bénéficiaire du propriétaire."""
    beneficiaire = get_beneficiaire_pour_proprietaire(
        proprietaire=proprietaire,
        beneficiaire_id=beneficiaire_id,
    )
    if alias is not None:
        beneficiaire.alias = alias.strip()
    if statut is not None:
        if statut not in Beneficiaire.Statut.values:
            raise ValidationError(f'Statut invalide : {statut}')
        beneficiaire.statut = statut
    beneficiaire.save()

    from observabilite.models import Evenement
    from observabilite.services.journal_service import (
        TYPE_BENEFICIAIRE_DESACTIVATION,
        TYPE_BENEFICIAIRE_MODIFICATION,
        enregistrer_evenement,
    )

    if statut == Beneficiaire.Statut.INACTIF:
        enregistrer_evenement(
            type_evenement=TYPE_BENEFICIAIRE_DESACTIVATION,
            module='beneficiaires',
            description=f'Désactivation bénéficiaire #{beneficiaire.pk}',
            niveau=Evenement.Niveau.SECURITY,
            utilisateur=getattr(proprietaire, 'user', None),
            contexte={'beneficiaire_id': beneficiaire.pk},
        )
    else:
        enregistrer_evenement(
            type_evenement=TYPE_BENEFICIAIRE_MODIFICATION,
            module='beneficiaires',
            description=f'Modification bénéficiaire #{beneficiaire.pk}',
            utilisateur=getattr(proprietaire, 'user', None),
            contexte={'beneficiaire_id': beneficiaire.pk},
        )
    return beneficiaire


@transaction.atomic
def desactiver_beneficiaire(
    *,
    proprietaire: Utilisateur,
    beneficiaire_id: int,
) -> Beneficiaire:
    """Désactivation logique d'un bénéficiaire (suppression métier)."""
    return update_beneficiaire(
        proprietaire=proprietaire,
        beneficiaire_id=beneficiaire_id,
        statut=Beneficiaire.Statut.INACTIF,
    )


@transaction.atomic
def reactiver_beneficiaire(
    *,
    proprietaire: Utilisateur,
    beneficiaire_id: int,
) -> Beneficiaire:
    """Réactive un bénéficiaire précédemment désactivé."""
    return update_beneficiaire(
        proprietaire=proprietaire,
        beneficiaire_id=beneficiaire_id,
        statut=Beneficiaire.Statut.ACTIF,
    )

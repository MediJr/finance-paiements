"""
Services métier — utilisateurs de la plateforme.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404

from accounts.models import Utilisateur
from wallets.services.wallet_service import create_wallet_for_utilisateur

User = get_user_model()


@transaction.atomic
def create_utilisateur(
    *,
    username: str,
    password: str,
    prenom: str,
    nom: str,
    email: str,
    telephone: str = '',
    est_actif: bool = True,
) -> Utilisateur:
    """
    Crée un utilisateur métier et son compte d'authentification.

    Le Wallet associé est créé automatiquement via le service Wallet
    (signal post_save + service centralisé).
    """
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=prenom,
        last_name=nom,
        is_active=est_actif,
    )
    utilisateur = Utilisateur.objects.create(
        user=user,
        prenom=prenom,
        nom=nom,
        email=email,
        telephone=telephone or '',
        est_actif=est_actif,
    )
    # Garantit la création même si le signal n'est pas encore branché.
    create_wallet_for_utilisateur(utilisateur)
    from observabilite.services.journal_service import (
        TYPE_UTILISATEUR_CREATION,
        enregistrer_evenement,
    )

    enregistrer_evenement(
        type_evenement=TYPE_UTILISATEUR_CREATION,
        module='accounts',
        description=f'Création utilisateur {utilisateur.email}',
        utilisateur=user,
        contexte={'utilisateur_id': utilisateur.pk, 'email': utilisateur.email},
    )
    return utilisateur


def list_utilisateurs(
    *,
    actifs_uniquement: bool = False,
    demandeur: Utilisateur | None = None,
    vue_admin: bool = False,
):
    """
    Retourne la liste des utilisateurs métier.

    - vue_admin=True : vision globale (staff)
    - demandeur fourni : uniquement le profil du demandeur
    - sinon (usage interne / rétrocompat tests) : tous
    """
    queryset = Utilisateur.objects.select_related('user', 'wallet').all()
    if actifs_uniquement:
        queryset = queryset.filter(est_actif=True)
    if vue_admin:
        return queryset
    if demandeur is not None:
        return queryset.filter(pk=demandeur.pk)
    return queryset


def get_utilisateur(
    utilisateur_id: int,
    *,
    demandeur: Utilisateur | None = None,
    vue_admin: bool = False,
) -> Utilisateur:
    """
    Retourne un utilisateur métier par identifiant.

    Un non-admin ne peut consulter que son propre profil.
    """
    queryset = Utilisateur.objects.select_related('user', 'wallet')
    if vue_admin:
        return get_object_or_404(queryset, pk=utilisateur_id)
    if demandeur is not None:
        if demandeur.pk != utilisateur_id:
            raise PermissionDenied('Accès refusé à ce profil utilisateur.')
        return get_object_or_404(queryset, pk=demandeur.pk)
    return get_object_or_404(queryset, pk=utilisateur_id)

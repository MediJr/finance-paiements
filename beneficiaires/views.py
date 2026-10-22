"""Vues web — gestion des bénéficiaires (délégation aux services)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from beneficiaires.forms import BeneficiaireCreateForm, BeneficiaireUpdateForm
from beneficiaires.services.beneficiaire_service import (
    ajouter_beneficiaire_par_email,
    get_beneficiaire_pour_proprietaire,
    get_utilisateur_connecte,
    list_beneficiaires,
    update_beneficiaire,
)


def _messages_from_validation(exc: ValidationError):
    """Normalise les messages ValidationError Django."""
    if hasattr(exc, 'message_dict'):
        return exc.messages
    if hasattr(exc, 'messages'):
        return exc.messages
    return [str(exc)]


@login_required
def beneficiaire_list(request):
    """Liste des bénéficiaires du propriétaire connecté."""
    try:
        proprietaire = get_utilisateur_connecte(request.user)
    except PermissionDenied:
        messages.error(request, 'Profil métier introuvable.')
        return redirect('accounts:connexion')

    statut = request.GET.get('statut') or None
    beneficiaires = list_beneficiaires(proprietaire=proprietaire, statut=statut)
    return render(
        request,
        'beneficiaires/beneficiaire_list.html',
        {
            'beneficiaires': beneficiaires,
            'filtre_statut': statut or '',
        },
    )


@login_required
def beneficiaire_detail(request, pk):
    """Détail d'un bénéficiaire du propriétaire connecté."""
    proprietaire = get_utilisateur_connecte(request.user)
    beneficiaire = get_beneficiaire_pour_proprietaire(
        proprietaire=proprietaire,
        beneficiaire_id=pk,
    )
    return render(
        request,
        'beneficiaires/beneficiaire_detail.html',
        {'beneficiaire': beneficiaire},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def beneficiaire_create(request):
    """Création d'un bénéficiaire."""
    proprietaire = get_utilisateur_connecte(request.user)
    form = BeneficiaireCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            beneficiaire = ajouter_beneficiaire_par_email(
                proprietaire=proprietaire,
                email=form.cleaned_data['email'],
                alias=form.cleaned_data.get('alias', ''),
            )
        except ValidationError as exc:
            for message in _messages_from_validation(exc):
                form.add_error(None, message)
        else:
            messages.success(request, 'Bénéficiaire ajouté.')
            return redirect('beneficiaires:beneficiaire-detail', pk=beneficiaire.pk)

    return render(
        request,
        'beneficiaires/beneficiaire_form.html',
        {
            'form': form,
            'titre': 'Ajouter un bénéficiaire',
            'mode': 'create',
        },
    )


@login_required
@require_http_methods(['GET', 'POST'])
def beneficiaire_update(request, pk):
    """Modification d'un bénéficiaire (alias / statut)."""
    proprietaire = get_utilisateur_connecte(request.user)
    beneficiaire = get_beneficiaire_pour_proprietaire(
        proprietaire=proprietaire,
        beneficiaire_id=pk,
    )
    form = BeneficiaireUpdateForm(
        request.POST or None,
        initial={
            'alias': beneficiaire.alias,
            'statut': beneficiaire.statut,
        },
    )
    if request.method == 'POST' and form.is_valid():
        try:
            beneficiaire = update_beneficiaire(
                proprietaire=proprietaire,
                beneficiaire_id=pk,
                alias=form.cleaned_data['alias'],
                statut=form.cleaned_data['statut'],
            )
        except ValidationError as exc:
            for message in _messages_from_validation(exc):
                form.add_error(None, message)
        else:
            messages.success(request, 'Bénéficiaire mis à jour.')
            return redirect('beneficiaires:beneficiaire-detail', pk=beneficiaire.pk)

    return render(
        request,
        'beneficiaires/beneficiaire_form.html',
        {
            'form': form,
            'titre': 'Modifier le bénéficiaire',
            'mode': 'update',
            'beneficiaire': beneficiaire,
        },
    )

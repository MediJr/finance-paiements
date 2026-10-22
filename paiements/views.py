"""Vues web — paiements et remboursements."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from beneficiaires.services.beneficiaire_service import get_utilisateur_connecte
from paiements.forms import PaiementCreateForm, RemboursementCreateForm
from paiements.services import (
    executer_paiement,
    executer_remboursement,
    get_paiement_pour_utilisateur,
    get_remboursement_pour_utilisateur,
    list_paiements,
    list_remboursements,
)


def _messages_from_validation(exc: ValidationError):
    if hasattr(exc, 'messages'):
        return exc.messages
    return [str(exc)]


@login_required
def paiement_list(request):
    utilisateur = get_utilisateur_connecte(request.user)
    return render(
        request,
        'paiements/paiement_list.html',
        {'paiements': list_paiements(utilisateur=utilisateur)},
    )


@login_required
def paiement_detail(request, pk):
    utilisateur = get_utilisateur_connecte(request.user)
    paiement = get_paiement_pour_utilisateur(utilisateur=utilisateur, paiement_id=pk)
    return render(
        request,
        'paiements/paiement_detail.html',
        {'paiement': paiement},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def paiement_create(request):
    utilisateur = get_utilisateur_connecte(request.user)
    form = PaiementCreateForm(request.POST or None, payeur=utilisateur)
    if request.method == 'POST' and form.is_valid():
        try:
            paiement = executer_paiement(
                payeur=utilisateur,
                beneficiaire_id=form.cleaned_data['beneficiaire'].pk,
                montant=form.cleaned_data['montant'],
                motif=form.cleaned_data.get('motif', ''),
                cle_idempotence=form.cleaned_data.get('cle_idempotence'),
            )
        except ValidationError as exc:
            for message in _messages_from_validation(exc):
                form.add_error(None, message)
        else:
            messages.success(request, f'Paiement {paiement.reference} exécuté.')
            return redirect('paiements:paiement-detail', pk=paiement.pk)

    return render(
        request,
        'paiements/paiement_form.html',
        {'form': form, 'wallet': getattr(utilisateur, 'wallet', None)},
    )


@login_required
def remboursement_list(request):
    utilisateur = get_utilisateur_connecte(request.user)
    return render(
        request,
        'paiements/remboursement_list.html',
        {'remboursements': list_remboursements(utilisateur=utilisateur)},
    )


@login_required
def remboursement_detail(request, pk):
    utilisateur = get_utilisateur_connecte(request.user)
    remboursement = get_remboursement_pour_utilisateur(
        utilisateur=utilisateur,
        remboursement_id=pk,
    )
    return render(
        request,
        'paiements/remboursement_detail.html',
        {'remboursement': remboursement},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def remboursement_create(request):
    try:
        utilisateur = get_utilisateur_connecte(request.user)
    except PermissionDenied:
        messages.error(request, 'Profil métier introuvable.')
        return redirect('accounts:connexion')

    form = RemboursementCreateForm(request.POST or None, acteur=utilisateur)
    if request.method == 'POST' and form.is_valid():
        try:
            remboursement = executer_remboursement(
                acteur=utilisateur,
                paiement_id=form.cleaned_data['paiement'].pk,
                montant=form.cleaned_data.get('montant'),
            )
        except ValidationError as exc:
            for message in _messages_from_validation(exc):
                form.add_error(None, message)
        else:
            messages.success(
                request,
                f'Remboursement {remboursement.reference} exécuté.',
            )
            return redirect('paiements:remboursement-detail', pk=remboursement.pk)

    return render(
        request,
        'paiements/remboursement_form.html',
        {'form': form},
    )

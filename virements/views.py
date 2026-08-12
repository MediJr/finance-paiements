"""Vues web — virements (délégation aux services)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from beneficiaires.services.beneficiaire_service import get_utilisateur_connecte
from virements.forms import VirementCreateForm
from virements.services import (
    executer_virement,
    get_virement_pour_utilisateur,
    list_virements,
)


def _messages_from_validation(exc: ValidationError):
    if hasattr(exc, 'messages'):
        return exc.messages
    return [str(exc)]


@login_required
def virement_list(request):
    """Liste des virements de l'utilisateur connecté."""
    try:
        utilisateur = get_utilisateur_connecte(request.user)
    except PermissionDenied:
        messages.error(request, 'Profil métier introuvable.')
        return redirect('admin:login')

    virements = list_virements(utilisateur=utilisateur)
    return render(
        request,
        'virements/virement_list.html',
        {'virements': virements},
    )


@login_required
def virement_detail(request, pk):
    """Détail d'un virement auquel l'utilisateur a participé."""
    utilisateur = get_utilisateur_connecte(request.user)
    virement = get_virement_pour_utilisateur(
        utilisateur=utilisateur,
        virement_id=pk,
    )
    return render(
        request,
        'virements/virement_detail.html',
        {'virement': virement},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def virement_create(request):
    """Formulaire d'exécution d'un virement."""
    utilisateur = get_utilisateur_connecte(request.user)
    form = VirementCreateForm(request.POST or None, emetteur=utilisateur)
    if request.method == 'POST' and form.is_valid():
        try:
            virement = executer_virement(
                emetteur=utilisateur,
                beneficiaire_id=form.cleaned_data['beneficiaire'].pk,
                montant=form.cleaned_data['montant'],
                motif=form.cleaned_data.get('motif', ''),
            )
        except ValidationError as exc:
            for message in _messages_from_validation(exc):
                form.add_error(None, message)
        else:
            messages.success(request, f'Virement {virement.reference} exécuté.')
            return redirect('virements:virement-detail', pk=virement.pk)

    return render(
        request,
        'virements/virement_form.html',
        {
            'form': form,
            'wallet': getattr(utilisateur, 'wallet', None),
        },
    )

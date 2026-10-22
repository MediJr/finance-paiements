"""Vues web — alimentation du Wallet par carte (délégation aux services)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from beneficiaires.services import get_utilisateur_connecte
from wallets.forms import AlimentationForm
from wallets.models import Alimentation
from wallets.services import alimenter_wallet, list_alimentations
from wallets.services.passerelle_carte import CARTE_TEST_ACCEPTEE, CARTE_TEST_REFUSEE


@login_required
@require_http_methods(['GET', 'POST'])
def alimentation(request):
    try:
        utilisateur = get_utilisateur_connecte(request.user)
    except PermissionDenied:
        return redirect('accueil')

    form = AlimentationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            resultat = alimenter_wallet(
                utilisateur=utilisateur,
                montant=form.cleaned_data['montant'],
                numero_carte=form.cleaned_data['numero_carte'],
                cle_idempotence=form.cleaned_data.get('cle_idempotence'),
            )
        except ValidationError as exc:
            for message in exc.messages:
                form.add_error(None, message)
        else:
            if resultat.statut == Alimentation.Statut.ACCEPTEE:
                messages.success(
                    request,
                    f'{resultat.montant} {resultat.devise} crédités '
                    f'(carte {resultat.carte_masquee}).',
                )
            else:
                messages.warning(request, f'Alimentation refusée : {resultat.motif_refus}')
            return redirect('accounts:espace')

    return render(
        request,
        'wallets/alimentation.html',
        {
            'form': form,
            'wallet': getattr(utilisateur, 'wallet', None),
            'alimentations': list_alimentations(utilisateur=utilisateur)[:5],
            'carte_acceptee': CARTE_TEST_ACCEPTEE,
            'carte_refusee': CARTE_TEST_REFUSEE,
        },
    )

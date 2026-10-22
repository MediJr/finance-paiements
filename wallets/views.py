"""Vues web — consultation Wallet (délégation aux services)."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render

from beneficiaires.services import get_utilisateur_connecte
from wallets.services import get_wallet


@login_required
def wallet_detail(request, pk):
    """Consultation d'un Wallet (propre ou admin)."""
    try:
        if request.user.is_staff:
            wallet = get_wallet(pk, vue_admin=True)
        else:
            acteur = get_utilisateur_connecte(request.user)
            wallet = get_wallet(pk, proprietaire=acteur, vue_admin=False)
    except PermissionDenied:
        return HttpResponseForbidden('Accès refusé à ce Wallet.')
    except Http404:
        raise
    return render(
        request,
        'wallets/wallet_detail.html',
        {'wallet': wallet},
    )

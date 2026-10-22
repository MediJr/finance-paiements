"""Vues web — inscription, connexion, déconnexion et espace client."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.forms import ConnexionForm, InscriptionForm
from accounts.services import authentifier_client, deconnecter, inscrire_client
from beneficiaires.services import get_utilisateur_connecte
from commun.http import redirection_sure
from historique.services import list_historique_operations


def accueil(request):
    """Racine : espace client, administration (personnel) ou connexion."""
    if not request.user.is_authenticated:
        return redirect('accounts:connexion')
    if request.user.is_staff:
        return redirect('administration:index')
    return redirect('accounts:espace')


@require_http_methods(['GET', 'POST'])
def inscription(request):
    if request.user.is_authenticated:
        return redirect('accounts:espace')
    form = InscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            inscrire_client(**form.cleaned_data, request=request)
        except ValidationError as exc:
            for champ, erreurs in exc.message_dict.items():
                for erreur in erreurs:
                    form.add_error(champ if champ in form.fields else None, erreur)
        else:
            authentifier_client(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            messages.success(request, 'Compte créé. Alimentez votre portefeuille pour commencer.')
            return redirect('accounts:espace')
    return render(request, 'accounts/inscription.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def connexion(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    form = ConnexionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user, erreur = authentifier_client(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is not None:
            return redirection_sure(request, request.GET.get('next'), 'accueil')
        form.add_error(None, erreur)
    return render(request, 'accounts/connexion.html', {'form': form})


@require_POST
def deconnexion(request):
    """Déconnexion en POST uniquement (protégée par CSRF)."""
    deconnecter(request)
    messages.info(request, 'Vous êtes déconnecté.')
    return redirect('accounts:connexion')


@login_required
def espace_client(request):
    """Tableau de bord du client : solde, actions rapides, dernières opérations."""
    try:
        utilisateur = get_utilisateur_connecte(request.user)
    except PermissionDenied:
        return redirect('accueil')
    operations = list_historique_operations(proprietaire=utilisateur)[:8]
    return render(
        request,
        'accounts/espace.html',
        {
            'utilisateur': utilisateur,
            'wallet': getattr(utilisateur, 'wallet', None),
            'operations': operations,
        },
    )

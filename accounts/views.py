"""Vues web — utilisateurs métier (délégation aux services)."""



from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied

from django.http import HttpResponseForbidden

from django.shortcuts import render



from accounts.services import get_utilisateur, list_utilisateurs

from beneficiaires.services import get_utilisateur_connecte





def _scope_web(request):

    if request.user.is_staff:

        return None, True

    return get_utilisateur_connecte(request.user), False





@login_required

def utilisateur_list(request):

    """Liste des utilisateurs : soi-même, ou tous si admin."""

    try:

        acteur, vue_admin = _scope_web(request)

    except PermissionDenied:

        return HttpResponseForbidden('Profil métier requis.')

    utilisateurs = list_utilisateurs(demandeur=acteur, vue_admin=vue_admin)

    return render(

        request,

        'accounts/utilisateur_list.html',

        {'utilisateurs': utilisateurs, 'vue_admin': vue_admin},

    )





@login_required

def utilisateur_detail(request, pk):

    """Détail d'un utilisateur métier et de son Wallet (scoping)."""

    try:

        acteur, vue_admin = _scope_web(request)

        utilisateur = get_utilisateur(pk, demandeur=acteur, vue_admin=vue_admin)

    except PermissionDenied:

        return HttpResponseForbidden('Accès refusé à ce profil.')

    return render(

        request,

        'accounts/utilisateur_detail.html',

        {

            'utilisateur': utilisateur,

            'wallet': getattr(utilisateur, 'wallet', None),

        },

    )



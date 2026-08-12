"""Vues web — consultation de l'historique (délégation aux services)."""



from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied, ValidationError

from django.http import HttpResponseForbidden

from django.shortcuts import render



from beneficiaires.services import get_utilisateur_connecte

from historique.models import HistoriqueOperation

from historique.services import get_historique_operation, list_historique_operations





@login_required

def historique_list(request):

    """Liste filtrable de l'historique (scoping propriétaire)."""

    try:

        if request.user.is_staff:

            acteur, vue_admin = None, True

        else:

            acteur, vue_admin = get_utilisateur_connecte(request.user), False

    except PermissionDenied:

        return HttpResponseForbidden('Profil métier requis.')



    filters = {

        'wallet_id': request.GET.get('wallet') or None,

        'type_operation': request.GET.get('type') or None,

        'statut': request.GET.get('statut') or None,

        'date_debut': request.GET.get('date_debut') or None,

        'date_fin': request.GET.get('date_fin') or None,

        'reference': request.GET.get('reference') or None,

    }

    if filters['wallet_id'] is not None:

        try:

            filters['wallet_id'] = int(filters['wallet_id'])

        except (TypeError, ValueError):

            filters['wallet_id'] = None



    try:

        operations = list_historique_operations(

            **filters,

            proprietaire=acteur,

            vue_admin=vue_admin,

        )

    except ValidationError:

        operations = HistoriqueOperation.objects.none()



    return render(

        request,

        'historique/historique_list.html',

        {

            'operations': operations,

            'filters': {

                'wallet': request.GET.get('wallet', ''),

                'type': request.GET.get('type', ''),

                'statut': request.GET.get('statut', ''),

                'date_debut': request.GET.get('date_debut', ''),

                'date_fin': request.GET.get('date_fin', ''),

                'reference': request.GET.get('reference', ''),

            },

            'type_choices': HistoriqueOperation.TypeOperation.choices,

            'statut_choices': HistoriqueOperation.Statut.choices,

        },

    )





@login_required

def historique_detail(request, pk):

    """Détail d'une opération d'historique (scoping)."""

    try:

        if request.user.is_staff:

            operation = get_historique_operation(pk, vue_admin=True)

        else:

            acteur = get_utilisateur_connecte(request.user)

            operation = get_historique_operation(pk, proprietaire=acteur)

    except PermissionDenied:

        return HttpResponseForbidden('Accès refusé à cette opération.')

    return render(

        request,

        'historique/historique_detail.html',

        {'operation': operation},

    )



"""Vues web — consultation des événements d'observabilité."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render

from administration.decorators import administrateur_required
from observabilite.models import Evenement
from observabilite.services.journal_service import get_evenement, list_evenements


@login_required
@administrateur_required
def evenement_list(request):
    """Liste filtrable des événements (lecture seule)."""
    filtres = {
        'niveau': request.GET.get('niveau') or None,
        'module': request.GET.get('module') or None,
        'type_evenement': request.GET.get('type') or None,
        'utilisateur_id': request.GET.get('utilisateur') or None,
        'date_debut': request.GET.get('date_debut') or None,
        'date_fin': request.GET.get('date_fin') or None,
        'q': request.GET.get('q') or None,
    }
    try:
        evenements = list_evenements(administrateur=request.user, **filtres)
    except ValidationError:
        evenements = []
    return render(
        request,
        'observabilite/evenement_list.html',
        {
            'evenements': evenements,
            'niveau_choices': Evenement.Niveau.choices,
            'filtre_niveau': request.GET.get('niveau', ''),
            'filtre_module': request.GET.get('module', ''),
            'filtre_type': request.GET.get('type', ''),
            'filtre_utilisateur': request.GET.get('utilisateur', ''),
            'filtre_date_debut': request.GET.get('date_debut', ''),
            'filtre_date_fin': request.GET.get('date_fin', ''),
            'filtre_q': request.GET.get('q', ''),
        },
    )


@login_required
@administrateur_required
def evenement_detail(request, pk):
    """Détail d'un événement (lecture seule)."""
    evenement = get_evenement(administrateur=request.user, evenement_id=pk)
    return render(
        request,
        'observabilite/evenement_detail.html',
        {'evenement': evenement},
    )

"""Vues web — administration fonctionnelle."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from administration.decorators import administrateur_required
from administration.forms import ParametresForm
from administration.http import client_ip
from administration.models import JournalAdministration
from administration.services import (
    FORMATS_EXPORT,
    TYPES_EXPORT,
    TYPES_RAPPORT,
    activer_utilisateur,
    desactiver_utilisateur,
    enregistrer_acces_admin,
    exporter,
    generer_rapport,
    get_dashboard,
    get_parametres,
    get_statistiques,
    list_historique_admin,
    list_journal_admin,
    list_paiements_admin,
    list_remboursements_admin,
    list_utilisateurs_admin,
    list_virements_admin,
    list_wallets_admin,
    update_parametres,
)
from historique.models import HistoriqueOperation
from paiements.models import Paiement, Remboursement
from virements.models import Virement
from wallets.models import Wallet


def _filtres_pilotage(request):
    return {
        'date_debut': request.GET.get('date_debut') or None,
        'date_fin': request.GET.get('date_fin') or None,
        'statut': request.GET.get('statut') or None,
        'utilisateur_id': request.GET.get('utilisateur') or None,
    }


@login_required
@administrateur_required
def admin_index(request):
    """Tableau d'administration (navigation)."""
    parametres = get_parametres(administrateur=request.user)
    enregistrer_acces_admin(
        administrateur=request.user,
        adresse_ip=client_ip(request),
    )
    dashboard = get_dashboard(administrateur=request.user)
    return render(
        request,
        'administration/index.html',
        {
            'parametres': parametres,
            'dashboard': dashboard,
            'nb_utilisateurs': dashboard['utilisateurs'],
            'nb_wallets': dashboard['wallets'],
        },
    )


@login_required
@administrateur_required
def admin_dashboard(request):
    """Tableau de bord — indicateurs globaux."""
    dashboard = get_dashboard(administrateur=request.user)
    return render(
        request,
        'administration/dashboard.html',
        {'dashboard': dashboard},
    )


@login_required
@administrateur_required
def admin_statistiques(request):
    """Statistiques métier filtrables."""
    filtres = _filtres_pilotage(request)
    try:
        stats = get_statistiques(administrateur=request.user, **filtres)
    except ValidationError as exc:
        messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
        stats = None
    return render(
        request,
        'administration/statistiques.html',
        {
            'stats': stats,
            'filtre_date_debut': request.GET.get('date_debut', ''),
            'filtre_date_fin': request.GET.get('date_fin', ''),
            'filtre_statut': request.GET.get('statut', ''),
            'filtre_utilisateur': request.GET.get('utilisateur', ''),
        },
    )


@login_required
@administrateur_required
def admin_rapports(request):
    """Rapports consultables (lecture seule)."""
    type_rapport = request.GET.get('type') or 'virements'
    filtres = _filtres_pilotage(request)
    rapport = None
    try:
        rapport = generer_rapport(
            administrateur=request.user,
            type_rapport=type_rapport,
            **filtres,
        )
    except ValidationError as exc:
        messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
    return render(
        request,
        'administration/rapports.html',
        {
            'rapport': rapport,
            'types_rapport': TYPES_RAPPORT,
            'type_rapport': type_rapport,
            'filtre_date_debut': request.GET.get('date_debut', ''),
            'filtre_date_fin': request.GET.get('date_fin', ''),
            'filtre_statut': request.GET.get('statut', ''),
            'filtre_utilisateur': request.GET.get('utilisateur', ''),
        },
    )


@login_required
@administrateur_required
def admin_exports(request):
    """Page de sélection d'export (admin)."""
    return render(
        request,
        'administration/exports.html',
        {
            'types_export': TYPES_EXPORT,
            'formats_export': FORMATS_EXPORT,
            'filtre_type': request.GET.get('type', 'utilisateurs'),
            'filtre_format': request.GET.get('format', 'json'),
            'filtre_date_debut': request.GET.get('date_debut', ''),
            'filtre_date_fin': request.GET.get('date_fin', ''),
            'filtre_statut': request.GET.get('statut', ''),
        },
    )


@login_required
@administrateur_required
def admin_export_download(request):
    """Téléchargement du fichier d'export (délégation au service)."""
    try:
        result = exporter(
            administrateur=request.user,
            type_export=request.GET.get('type') or 'utilisateurs',
            format_export=request.GET.get('format') or 'json',
            date_debut=request.GET.get('date_debut') or None,
            date_fin=request.GET.get('date_fin') or None,
            statut=request.GET.get('statut') or None,
        )
    except ValidationError as exc:
        messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
        return redirect('administration:exports')

    response = HttpResponse(
        result['content'],
        content_type=result['content_type'],
    )
    response['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
    return response


@login_required
@administrateur_required
@require_http_methods(['GET', 'POST'])
def admin_parametres(request):
    parametres = get_parametres(administrateur=request.user)
    form = ParametresForm(request.POST or None, instance=parametres)
    if request.method == 'POST' and form.is_valid():
        try:
            update_parametres(
                administrateur=request.user,
                adresse_ip=client_ip(request),
                **form.cleaned_data,
            )
        except ValidationError as exc:
            messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
        else:
            messages.success(request, 'Paramètres mis à jour.')
            return redirect('administration:parametres')
    return render(
        request,
        'administration/parametres.html',
        {'form': form, 'parametres': parametres},
    )


@login_required
@administrateur_required
def admin_utilisateurs(request):
    q = request.GET.get('q') or None
    actif = request.GET.get('est_actif')
    est_actif = None
    if actif == '1':
        est_actif = True
    elif actif == '0':
        est_actif = False
    utilisateurs = list_utilisateurs_admin(
        administrateur=request.user,
        q=q,
        est_actif=est_actif,
    )
    return render(
        request,
        'administration/utilisateurs.html',
        {
            'utilisateurs': utilisateurs,
            'filtre_q': q or '',
            'filtre_est_actif': actif or '',
        },
    )


@login_required
@administrateur_required
@require_POST
def admin_utilisateur_activer(request, pk):
    activer_utilisateur(
        administrateur=request.user,
        utilisateur_id=pk,
        adresse_ip=client_ip(request),
    )
    messages.success(request, 'Utilisateur activé.')
    return redirect('administration:utilisateurs')


@login_required
@administrateur_required
@require_POST
def admin_utilisateur_desactiver(request, pk):
    try:
        desactiver_utilisateur(
            administrateur=request.user,
            utilisateur_id=pk,
            adresse_ip=client_ip(request),
        )
    except ValidationError as exc:
        messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
    else:
        messages.success(request, 'Utilisateur désactivé.')
    return redirect('administration:utilisateurs')


@login_required
@administrateur_required
def admin_wallets(request):
    wallets = list_wallets_admin(
        administrateur=request.user,
        q=request.GET.get('q') or None,
        statut=request.GET.get('statut') or None,
        devise=request.GET.get('devise') or None,
    )
    return render(
        request,
        'administration/wallets.html',
        {
            'wallets': wallets,
            'filtre_q': request.GET.get('q', ''),
            'filtre_statut': request.GET.get('statut', ''),
            'filtre_devise': request.GET.get('devise', ''),
            'statut_choices': Wallet.Statut.choices,
        },
    )


@login_required
@administrateur_required
def admin_operations(request):
    type_op = request.GET.get('type') or 'historique'
    q = request.GET.get('q') or None
    statut = request.GET.get('statut') or None

    context = {
        'type_op': type_op,
        'filtre_q': q or '',
        'filtre_statut': statut or '',
        'items': [],
        'statut_choices': [],
    }

    if type_op == 'virements':
        context['items'] = list_virements_admin(
            administrateur=request.user, q=q, statut=statut
        )
        context['statut_choices'] = Virement.Statut.choices
    elif type_op == 'paiements':
        context['items'] = list_paiements_admin(
            administrateur=request.user, q=q, statut=statut
        )
        context['statut_choices'] = Paiement.Statut.choices
    elif type_op == 'remboursements':
        context['items'] = list_remboursements_admin(
            administrateur=request.user, q=q, statut=statut
        )
        context['statut_choices'] = Remboursement.Statut.choices
    else:
        type_op = 'historique'
        context['type_op'] = type_op
        context['items'] = list_historique_admin(
            administrateur=request.user,
            q=q,
            type_operation=request.GET.get('type_operation') or None,
            statut=statut,
        )
        context['statut_choices'] = HistoriqueOperation.Statut.choices
        context['type_operation_choices'] = HistoriqueOperation.TypeOperation.choices
        context['filtre_type_operation'] = request.GET.get('type_operation', '')

    return render(request, 'administration/operations.html', context)


@login_required
@administrateur_required
def admin_journal(request):
    """Consultation du journal d'administration."""
    action = request.GET.get('action') or None
    entrees = list_journal_admin(administrateur=request.user, action=action)
    return render(
        request,
        'administration/journal.html',
        {
            'entrees': entrees,
            'filtre_action': action or '',
            'action_choices': JournalAdministration.Action.choices,
        },
    )

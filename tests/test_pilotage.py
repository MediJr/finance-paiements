"""
Tests Sprint 8 — Tableau de bord, statistiques et rapports.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse

from administration.services import (
    generer_rapport,
    get_dashboard,
    get_statistiques,
)
from beneficiaires.services import create_beneficiaire
from virements.services import executer_virement


def _crediter(wallet, montant='1000.00'):
    wallet.solde = Decimal(montant)
    wallet.save(update_fields=['solde', 'date_mise_a_jour'])


@pytest.fixture
def lien(utilisateur, autre_utilisateur):
    return create_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=autre_utilisateur.pk,
        alias='Bob',
    )


@pytest.fixture
def virement_ok(utilisateur, autre_utilisateur, lien):
    _crediter(utilisateur.wallet, '500.00')
    return executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien.pk,
        montant='120.00',
        motif='test sprint 8',
    )


@pytest.mark.django_db
def test_dashboard_refuse_non_admin(utilisateur):
    with pytest.raises(PermissionDenied):
        get_dashboard(administrateur=utilisateur.user)


@pytest.mark.django_db
def test_dashboard_compteurs(staff_user, utilisateur, autre_utilisateur, virement_ok):
    data = get_dashboard(administrateur=staff_user)
    assert data['utilisateurs'] == 2
    assert data['wallets_actifs'] >= 2
    assert data['beneficiaires'] >= 1
    assert data['virements'] == 1
    assert data['operations'] >= 2


@pytest.mark.django_db
def test_statistiques_montants(staff_user, virement_ok):
    stats = get_statistiques(administrateur=staff_user)
    assert stats['virements']['nombre'] == 1
    assert stats['virements']['montant_cumule'] == '120.00'
    assert 'reussi' in stats['virements']['par_statut']


@pytest.mark.django_db
def test_statistiques_filtre_utilisateur(staff_user, utilisateur, virement_ok):
    stats = get_statistiques(
        administrateur=staff_user,
        utilisateur_id=utilisateur.pk,
    )
    assert stats['virements']['nombre'] == 1
    stats_autre = get_statistiques(
        administrateur=staff_user,
        utilisateur_id=999999,
    )
    assert stats_autre['virements']['nombre'] == 0


@pytest.mark.django_db
def test_rapport_virements(staff_user, virement_ok):
    rapport = generer_rapport(
        administrateur=staff_user,
        type_rapport='virements',
    )
    assert rapport['type'] == 'virements'
    assert rapport['totaux']['nombre'] == 1
    assert rapport['lignes'][0]['reference'] == virement_ok.reference


@pytest.mark.django_db
def test_rapport_utilisateurs_et_wallets(staff_user, utilisateur):
    r_users = generer_rapport(
        administrateur=staff_user,
        type_rapport='utilisateurs',
    )
    assert r_users['totaux']['nombre'] >= 1
    r_wallets = generer_rapport(
        administrateur=staff_user,
        type_rapport='wallets',
    )
    assert r_wallets['totaux']['nombre'] >= 1


@pytest.mark.django_db
def test_rapport_type_invalide(staff_user):
    with pytest.raises(ValidationError):
        generer_rapport(administrateur=staff_user, type_rapport='analytics')


@pytest.mark.django_db
def test_web_pilotage_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    for name in ('dashboard', 'statistiques', 'rapports'):
        response = client.get(reverse(f'administration:{name}'))
        assert response.status_code == 302
        assert response.url == reverse('accounts:utilisateur-list')


@pytest.mark.django_db
def test_web_pilotage_ok(staff_user, virement_ok):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    dash = client.get(reverse('administration:dashboard'))
    assert dash.status_code == 200
    assert b'Tableau de bord' in dash.content

    stats = client.get(reverse('administration:statistiques'))
    assert stats.status_code == 200
    assert b'Statistiques' in stats.content

    rapports = client.get(reverse('administration:rapports') + '?type=virements')
    assert rapports.status_code == 200
    assert virement_ok.reference.encode() in rapports.content


@pytest.mark.django_db
def test_api_pilotage_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    for url in (
        '/api/administration/dashboard/',
        '/api/administration/statistiques/',
        '/api/administration/rapports/?type=virements',
    ):
        assert client.get(url).status_code == 403


@pytest.mark.django_db
def test_api_pilotage_ok(staff_user, virement_ok):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')

    dash = client.get('/api/administration/dashboard/')
    assert dash.status_code == 200
    assert dash.json()['virements'] == 1

    stats = client.get('/api/administration/statistiques/')
    assert stats.status_code == 200
    assert stats.json()['virements']['montant_cumule'] == '120.00'

    rapport = client.get('/api/administration/rapports/?type=virements')
    assert rapport.status_code == 200
    payload = rapport.json()
    assert payload['totaux']['nombre'] == 1
    assert payload['lignes'][0]['reference'] == virement_ok.reference

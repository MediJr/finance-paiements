"""
Tests métier Sprint 6 — Administration et paramètres.
"""

import json

import pytest
from django.test import Client
from django.urls import reverse

from administration.services import get_parametres, update_parametres


@pytest.fixture
def admin_user(db, staff_user):
    """Staff déjà fourni par conftest."""
    return staff_user


@pytest.mark.django_db
def test_acces_admin_web_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.get(reverse('administration:index'))
    assert response.status_code == 302
    assert response.url == reverse('accounts:utilisateur-list')


@pytest.mark.django_db
def test_acces_admin_web_ok(admin_user):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    response = client.get(reverse('administration:index'))
    assert response.status_code == 200
    assert b'Administration' in response.content


@pytest.mark.django_db
def test_parametres_consultation_et_maj(admin_user):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    get_page = client.get(reverse('administration:parametres'))
    assert get_page.status_code == 200

    updated = client.post(
        reverse('administration:parametres'),
        data={
            'nom_application': 'Finance Lab',
            'devise_par_defaut': 'EUR',
            'mode_maintenance': True,
            'montant_virement_max': '5000.00',
            'montant_paiement_max': '2500.00',
            'plafond_journalier': '8000.00',
            'montant_alimentation_max': '3000.00',
            'delai_session_minutes': 30,
        },
    )
    assert updated.status_code == 302
    params = get_parametres(administrateur=admin_user)
    assert params.nom_application == 'Finance Lab'
    assert params.mode_maintenance is True
    assert params.delai_session_minutes == 30


@pytest.mark.django_db
def test_consultation_wallets_et_operations(admin_user, utilisateur):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    wallets = client.get(reverse('administration:wallets'))
    assert wallets.status_code == 200
    assert b'Alice' in wallets.content or b'Wallet' in wallets.content

    ops = client.get(reverse('administration:operations') + '?type=historique')
    assert ops.status_code == 200


@pytest.mark.django_db
def test_activation_desactivation_utilisateur(admin_user, utilisateur):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    des = client.post(
        reverse('administration:utilisateur-desactiver', args=[utilisateur.pk])
    )
    assert des.status_code == 302
    utilisateur.refresh_from_db()
    assert utilisateur.est_actif is False
    assert utilisateur.user.is_active is False

    act = client.post(
        reverse('administration:utilisateur-activer', args=[utilisateur.pk])
    )
    assert act.status_code == 302
    utilisateur.refresh_from_db()
    assert utilisateur.est_actif is True


@pytest.mark.django_db
def test_api_admin_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.get('/api/administration/parametres/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_api_admin_parametres_et_listes(admin_user, utilisateur):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')

    params = client.get('/api/administration/parametres/')
    assert params.status_code == 200
    assert 'devise_par_defaut' in params.json()

    patch = client.patch(
        '/api/administration/parametres/',
        data=json.dumps({'mode_maintenance': True}),
        content_type='application/json',
    )
    assert patch.status_code == 200
    assert patch.json()['mode_maintenance'] is True

    users = client.get('/api/administration/utilisateurs/')
    assert users.status_code == 200
    assert any(u['email'] == 'alice@example.com' for u in users.json())

    wallets = client.get('/api/administration/wallets/')
    assert wallets.status_code == 200

    ops = client.get('/api/administration/operations/?type=historique')
    assert ops.status_code == 200
    assert ops.json()['type'] == 'historique'


@pytest.mark.django_db
def test_service_update_parametres_validation(admin_user):
    with pytest.raises(Exception):
        update_parametres(
            administrateur=admin_user,
            devise_par_defaut='EURO',
        )

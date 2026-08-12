"""
Tests métier Sprint 1 — Utilisateurs et Wallets.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse

from accounts.models import Utilisateur
from accounts.services import create_utilisateur, get_utilisateur, list_utilisateurs
from wallets.models import Wallet
from wallets.services import create_wallet_for_utilisateur, get_wallet


@pytest.mark.django_db
def test_create_utilisateur_via_service():
    """La création d'un utilisateur métier fonctionne."""
    utilisateur = create_utilisateur(
        username='bob',
        password='MotDePasseFort123!',
        prenom='Bob',
        nom='Dupont',
        email='bob@example.com',
    )
    assert utilisateur.pk is not None
    assert utilisateur.prenom == 'Bob'
    assert utilisateur.email == 'bob@example.com'
    assert utilisateur.est_actif is True
    assert utilisateur.user.username == 'bob'


@pytest.mark.django_db
def test_wallet_cree_automatiquement(utilisateur):
    """Un Wallet est créé automatiquement avec l'utilisateur."""
    assert hasattr(utilisateur, 'wallet')
    assert utilisateur.wallet.pk is not None
    assert utilisateur.wallet.utilisateur_id == utilisateur.pk


@pytest.mark.django_db
def test_solde_initial_est_zero(utilisateur):
    """Le solde initial du Wallet est toujours 0."""
    assert utilisateur.wallet.solde == Decimal('0.00')
    assert utilisateur.wallet.devise == 'EUR'


@pytest.mark.django_db
def test_unicite_wallet_par_utilisateur(utilisateur):
    """Un utilisateur ne peut posséder qu'un seul Wallet."""
    with pytest.raises(IntegrityError):
        Wallet.objects.create(
            utilisateur=utilisateur,
            solde=Decimal('0.00'),
            devise='EUR',
        )


@pytest.mark.django_db
def test_create_wallet_idempotent(utilisateur):
    """La création de Wallet est idempotente (pas de doublon)."""
    wallet = create_wallet_for_utilisateur(utilisateur)
    assert wallet.pk == utilisateur.wallet.pk
    assert Wallet.objects.filter(utilisateur=utilisateur).count() == 1


@pytest.mark.django_db
def test_wallet_sans_utilisateur_refuse():
    """Un Wallet ne peut pas être créé sans utilisateur."""
    with pytest.raises(ValidationError):
        create_wallet_for_utilisateur(None)


@pytest.mark.django_db
def test_list_et_get_utilisateur(utilisateur):
    """Les services de lecture utilisateurs fonctionnent."""
    assert list_utilisateurs().count() == 1
    assert get_utilisateur(utilisateur.pk).email == 'alice@example.com'


@pytest.mark.django_db
def test_api_utilisateurs_requiert_auth():
    """L'API utilisateurs exige une authentification."""
    client = Client()
    response = client.get('/api/utilisateurs/')
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_api_utilisateurs_liste_et_detail(utilisateur):
    """GET utilisateurs et GET utilisateur."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    list_response = client.get('/api/utilisateurs/')
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) == 1
    assert data[0]['email'] == 'alice@example.com'

    detail_response = client.get(f'/api/utilisateurs/{utilisateur.pk}/')
    assert detail_response.status_code == 200
    assert detail_response.json()['nom'] == 'Martin'


@pytest.mark.django_db
def test_api_wallet_lecture(utilisateur):
    """GET Wallet (par id et via utilisateur)."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    by_id = client.get(f'/api/wallets/{utilisateur.wallet.pk}/')
    assert by_id.status_code == 200
    payload = by_id.json()
    assert payload['solde'] == '0.00'
    assert payload['utilisateur_id'] == utilisateur.pk

    by_user = client.get(f'/api/utilisateurs/{utilisateur.pk}/wallet/')
    assert by_user.status_code == 200
    assert by_user.json()['id'] == utilisateur.wallet.pk


@pytest.mark.django_db
def test_vues_web_utilisateurs_et_wallet(utilisateur):
    """Pages web liste / détail / wallet."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    list_page = client.get(reverse('accounts:utilisateur-list'))
    assert list_page.status_code == 200
    assert b'Alice' in list_page.content

    detail_page = client.get(
        reverse('accounts:utilisateur-detail', args=[utilisateur.pk])
    )
    assert detail_page.status_code == 200
    assert b'Wallet' in detail_page.content

    wallet_page = client.get(
        reverse('wallets:wallet-detail', args=[utilisateur.wallet.pk])
    )
    assert wallet_page.status_code == 200
    # Locale fr-fr : Decimal rendu sous la forme 0,00
    assert b'0,00' in wallet_page.content or b'0.00' in wallet_page.content
    assert b'EUR' in wallet_page.content


@pytest.mark.django_db
def test_admin_consultation_utilisateur_et_wallet(staff_user, utilisateur):
    """L'administration permet de consulter utilisateurs et Wallets."""
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')

    users_admin = client.get('/admin/accounts/utilisateur/')
    assert users_admin.status_code == 200
    assert b'Alice' in users_admin.content

    wallets_admin = client.get('/admin/wallets/wallet/')
    assert wallets_admin.status_code == 200

    # Consultation autorisée (vue lecture) ; ajout Wallet interdit.
    wallet_view = client.get(f'/admin/wallets/wallet/{utilisateur.wallet.pk}/change/')
    assert wallet_view.status_code == 200

    wallet_add = client.get('/admin/wallets/wallet/add/')
    assert wallet_add.status_code == 403


@pytest.mark.django_db
def test_get_wallet_service(utilisateur):
    """Le service get_wallet retourne le bon portefeuille."""
    wallet = get_wallet(utilisateur.wallet.pk)
    assert wallet.utilisateur_id == utilisateur.pk


@pytest.mark.django_db
def test_signal_cree_wallet_sans_appel_explicite(db):
    """Le signal crée un Wallet lors d'une création ORM d'Utilisateur."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(
        username='signal_user',
        password='MotDePasseFort123!',
        email='signal@example.com',
    )
    utilisateur = Utilisateur.objects.create(
        user=user,
        prenom='Sig',
        nom='Nal',
        email='signal@example.com',
    )
    assert Wallet.objects.filter(utilisateur=utilisateur).count() == 1
    assert utilisateur.wallet.solde == Decimal('0.00')

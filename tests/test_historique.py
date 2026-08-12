"""
Tests métier Sprint 2 — Historique des opérations.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse

from historique.models import HistoriqueOperation
from historique.services import (
    create_historique_operation,
    get_historique_operation,
    list_historique_operations,
)


@pytest.fixture
def operation(utilisateur):
    """Opération d'historique de test."""
    return create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.AUTRE,
        description='Événement technique de test',
        montant=None,
        reference='OP-TEST-001',
    )


@pytest.mark.django_db
def test_create_historique_operation(utilisateur):
    """Création d'un enregistrement d'historique sans modifier le solde."""
    solde_avant = utilisateur.wallet.solde
    operation = create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.CREDIT,
        description='Préparation future',
        montant=Decimal('10.00'),
        reference='OP-CREATE-001',
    )
    utilisateur.wallet.refresh_from_db()
    assert operation.pk is not None
    assert operation.wallet_id == utilisateur.wallet.pk
    assert operation.montant == Decimal('10.00')
    assert utilisateur.wallet.solde == solde_avant == Decimal('0.00')


@pytest.mark.django_db
def test_reference_unique(utilisateur, operation):
    """La référence d'une opération est unique."""
    with pytest.raises(IntegrityError):
        HistoriqueOperation.objects.create(
            wallet=utilisateur.wallet,
            type_operation=HistoriqueOperation.TypeOperation.AUTRE,
            reference=operation.reference,
        )


@pytest.mark.django_db
def test_consultation_par_wallet(utilisateur, operation):
    """Consultation de l'historique d'un Wallet."""
    create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.DEBIT,
        reference='OP-TEST-002',
    )
    ops = list_historique_operations(wallet_id=utilisateur.wallet.pk)
    assert ops.count() == 2
    assert all(op.wallet_id == utilisateur.wallet.pk for op in ops)


@pytest.mark.django_db
def test_filtres_type_et_statut(utilisateur):
    """Les filtres type et statut fonctionnent."""
    create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.PAIEMENT,
        statut=HistoriqueOperation.Statut.ENREGISTREE,
        reference='OP-FILTRE-1',
    )
    create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.VIREMENT,
        statut=HistoriqueOperation.Statut.ECHOUEE,
        reference='OP-FILTRE-2',
    )
    paiements = list_historique_operations(
        type_operation=HistoriqueOperation.TypeOperation.PAIEMENT
    )
    assert paiements.count() == 1
    assert paiements.first().reference == 'OP-FILTRE-1'

    echouees = list_historique_operations(
        statut=HistoriqueOperation.Statut.ECHOUEE
    )
    assert echouees.count() == 1
    assert echouees.first().reference == 'OP-FILTRE-2'


@pytest.mark.django_db
def test_filtre_periode(utilisateur, operation):
    """Le filtre par période fonctionne."""
    from django.utils.timezone import localtime

    jour = localtime(operation.date_creation).date().isoformat()
    ops = list_historique_operations(date_debut=jour, date_fin=jour)
    assert ops.filter(pk=operation.pk).exists()


@pytest.mark.django_db
def test_get_historique_operation(operation):
    """Lecture d'une opération par identifiant."""
    found = get_historique_operation(operation.pk)
    assert found.reference == 'OP-TEST-001'


@pytest.mark.django_db
def test_api_historique_liste_et_detail(utilisateur, operation):
    """GET historique et GET historique/<id>."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get('/api/historique/')
    assert liste.status_code == 200
    assert len(liste.json()) == 1

    detail = client.get(f'/api/historique/{operation.pk}/')
    assert detail.status_code == 200
    assert detail.json()['reference'] == 'OP-TEST-001'


@pytest.mark.django_db
def test_api_historique_filtres_et_wallet(utilisateur, operation):
    """Filtres API et historique d'un Wallet."""
    create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.DEBIT,
        reference='OP-API-DEBIT',
    )
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    filtres = client.get('/api/historique/', {'type': 'debit'})
    assert filtres.status_code == 200
    assert len(filtres.json()) == 1
    assert filtres.json()[0]['reference'] == 'OP-API-DEBIT'

    wallet_hist = client.get(f'/api/wallets/{utilisateur.wallet.pk}/historique/')
    assert wallet_hist.status_code == 200
    assert len(wallet_hist.json()) == 2


@pytest.mark.django_db
def test_api_historique_pas_de_creation(utilisateur):
    """Aucune création via l'API."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.post(
        '/api/historique/',
        data={'type_operation': 'autre', 'wallet_id': utilisateur.wallet.pk},
        content_type='application/json',
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_vues_web_historique(operation):
    """Pages web liste et détail."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get(reverse('historique:historique-list'))
    assert liste.status_code == 200
    assert b'OP-TEST-001' in liste.content

    detail = client.get(reverse('historique:historique-detail', args=[operation.pk]))
    assert detail.status_code == 200
    assert b'OP-TEST-001' in detail.content


@pytest.mark.django_db
def test_admin_consultation_historique(staff_user, operation):
    """L'administration permet de consulter l'historique."""
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')

    liste = client.get('/admin/historique/historiqueoperation/')
    assert liste.status_code == 200
    assert b'OP-TEST-001' in liste.content

    add_page = client.get('/admin/historique/historiqueoperation/add/')
    assert add_page.status_code == 403

    delete_page = client.get(
        f'/admin/historique/historiqueoperation/{operation.pk}/delete/'
    )
    assert delete_page.status_code == 403

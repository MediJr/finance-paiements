"""
Tests métier Sprint 5 — Paiements et remboursements.
"""

import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from beneficiaires.services import create_beneficiaire, desactiver_beneficiaire
from historique.models import HistoriqueOperation
from paiements.models import Paiement, Remboursement
from paiements.services import (
    executer_paiement,
    executer_remboursement,
    list_paiements,
)
from wallets.models import Wallet


def _crediter(wallet, montant: Decimal):
    wallet.solde = Decimal(montant)
    wallet.save(update_fields=['solde', 'date_mise_a_jour'])
    wallet.refresh_from_db()
    return wallet


@pytest.fixture
def lien(utilisateur, autre_utilisateur):
    return create_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=autre_utilisateur.pk,
        alias='Bob',
    )


@pytest.fixture
def payeur_alimente(utilisateur):
    return _crediter(utilisateur.wallet, Decimal('100.00'))


@pytest.mark.django_db
def test_paiement_valide(utilisateur, autre_utilisateur, lien, payeur_alimente):
    paiement = executer_paiement(
        payeur=utilisateur,
        beneficiaire_id=lien.pk,
        montant=Decimal('30.00'),
        motif='Achat',
    )
    utilisateur.wallet.refresh_from_db()
    autre_utilisateur.wallet.refresh_from_db()
    assert paiement.statut == Paiement.Statut.REUSSI
    assert utilisateur.wallet.solde == Decimal('70.00')
    assert autre_utilisateur.wallet.solde == Decimal('30.00')


@pytest.mark.django_db
def test_paiement_solde_insuffisant(utilisateur, lien, payeur_alimente):
    with pytest.raises(ValidationError, match='Solde insuffisant'):
        executer_paiement(
            payeur=utilisateur,
            beneficiaire_id=lien.pk,
            montant=Decimal('200.00'),
        )


@pytest.mark.django_db
def test_paiement_wallet_inactif(utilisateur, lien, payeur_alimente):
    payeur_alimente.statut = Wallet.Statut.INACTIF
    payeur_alimente.save(update_fields=['statut'])
    with pytest.raises(ValidationError, match='payeur est inactif'):
        executer_paiement(
            payeur=utilisateur,
            beneficiaire_id=lien.pk,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_paiement_beneficiaire_inactif(utilisateur, lien, payeur_alimente):
    desactiver_beneficiaire(proprietaire=utilisateur, beneficiaire_id=lien.pk)
    with pytest.raises(ValidationError, match='inactif'):
        executer_paiement(
            payeur=utilisateur,
            beneficiaire_id=lien.pk,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_paiement_atomique_et_historique(
    utilisateur, autre_utilisateur, lien, payeur_alimente
):
    with patch(
        'wallets.services.mouvement_service.create_historique_operation',
        side_effect=RuntimeError('boom'),
    ):
        with pytest.raises(RuntimeError):
            executer_paiement(
                payeur=utilisateur,
                beneficiaire_id=lien.pk,
                montant=Decimal('10.00'),
            )
    utilisateur.wallet.refresh_from_db()
    assert utilisateur.wallet.solde == Decimal('100.00')
    assert Paiement.objects.count() == 0

    paiement = executer_paiement(
        payeur=utilisateur,
        beneficiaire_id=lien.pk,
        montant=Decimal('10.00'),
    )
    ops = HistoriqueOperation.objects.filter(
        type_operation=HistoriqueOperation.TypeOperation.PAIEMENT
    )
    assert ops.count() == 2
    assert ops.filter(reference=f'{paiement.reference}-OUT').exists()


@pytest.mark.django_db
def test_remboursement_valide(utilisateur, autre_utilisateur, lien, payeur_alimente):
    paiement = executer_paiement(
        payeur=utilisateur,
        beneficiaire_id=lien.pk,
        montant=Decimal('40.00'),
    )
    remboursement = executer_remboursement(
        acteur=autre_utilisateur,
        paiement_id=paiement.pk,
        montant=Decimal('15.00'),
    )
    paiement.refresh_from_db()
    utilisateur.wallet.refresh_from_db()
    autre_utilisateur.wallet.refresh_from_db()

    assert remboursement.montant == Decimal('15.00')
    assert paiement.statut == Paiement.Statut.REMBOURSE_PARTIELLEMENT
    assert paiement.montant_rembourse == Decimal('15.00')
    assert utilisateur.wallet.solde == Decimal('75.00')
    assert autre_utilisateur.wallet.solde == Decimal('25.00')


@pytest.mark.django_db
def test_remboursement_total_puis_refus(
    utilisateur, autre_utilisateur, lien, payeur_alimente
):
    paiement = executer_paiement(
        payeur=utilisateur,
        beneficiaire_id=lien.pk,
        montant=Decimal('20.00'),
    )
    executer_remboursement(acteur=autre_utilisateur, paiement_id=paiement.pk)
    paiement.refresh_from_db()
    assert paiement.statut == Paiement.Statut.REMBOURSE
    with pytest.raises(ValidationError, match='totalement remboursé'):
        executer_remboursement(acteur=autre_utilisateur, paiement_id=paiement.pk)


@pytest.mark.django_db
def test_remboursement_paiement_inexistant(autre_utilisateur):
    with pytest.raises(ValidationError, match='inexistant'):
        executer_remboursement(acteur=autre_utilisateur, paiement_id=99999)


@pytest.mark.django_db
def test_remboursement_montant_excessif(
    utilisateur, autre_utilisateur, lien, payeur_alimente
):
    paiement = executer_paiement(
        payeur=utilisateur,
        beneficiaire_id=lien.pk,
        montant=Decimal('10.00'),
    )
    with pytest.raises(ValidationError, match='reste remboursable'):
        executer_remboursement(
            acteur=autre_utilisateur,
            paiement_id=paiement.pk,
            montant=Decimal('50.00'),
        )


@pytest.mark.django_db
def test_remboursement_historique_et_atomicite(
    utilisateur, autre_utilisateur, lien, payeur_alimente
):
    paiement = executer_paiement(
        payeur=utilisateur,
        beneficiaire_id=lien.pk,
        montant=Decimal('25.00'),
    )
    with patch(
        'wallets.services.mouvement_service.create_historique_operation',
        side_effect=RuntimeError('boom'),
    ):
        with pytest.raises(RuntimeError):
            executer_remboursement(
                acteur=autre_utilisateur,
                paiement_id=paiement.pk,
                montant=Decimal('5.00'),
            )
    paiement.refresh_from_db()
    assert paiement.montant_rembourse == Decimal('0.00')
    assert Remboursement.objects.count() == 0

    remboursement = executer_remboursement(
        acteur=autre_utilisateur,
        paiement_id=paiement.pk,
        montant=Decimal('5.00'),
    )
    assert HistoriqueOperation.objects.filter(
        type_operation=HistoriqueOperation.TypeOperation.REMBOURSEMENT,
        reference=f'{remboursement.reference}-OUT',
    ).exists()


@pytest.mark.django_db
def test_api_paiements_et_remboursements(
    utilisateur, autre_utilisateur, lien, payeur_alimente
):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    pay = client.post(
        '/api/paiements/',
        data=json.dumps({
            'beneficiaire_id': lien.pk,
            'montant': '18.00',
            'motif': 'API',
        }),
        content_type='application/json',
    )
    assert pay.status_code == 201
    paiement_id = pay.json()['id']

    liste = client.get('/api/paiements/')
    assert liste.status_code == 200
    assert len(liste.json()) == 1

    detail = client.get(f'/api/paiements/{paiement_id}/')
    assert detail.status_code == 200

    # Bob rembourse
    client.logout()
    assert client.login(username='bob', password='MotDePasseFort123!')
    refund = client.post(
        '/api/remboursements/',
        data=json.dumps({'paiement_id': paiement_id, 'montant': '8.00'}),
        content_type='application/json',
    )
    assert refund.status_code == 201
    assert client.get('/api/remboursements/').json()

    # Carol n'a pas accès
    from accounts.services import create_utilisateur

    create_utilisateur(
        username='carol',
        password='MotDePasseFort123!',
        prenom='Carol',
        nom='Leroy',
        email='carol@example.com',
    )
    client.logout()
    assert client.login(username='carol', password='MotDePasseFort123!')
    assert client.get(f'/api/paiements/{paiement_id}/').status_code == 404


@pytest.mark.django_db
def test_vues_web_paiements_remboursements(
    utilisateur, autre_utilisateur, lien, payeur_alimente
):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    assert client.get(reverse('paiements:paiement-list')).status_code == 200
    created = client.post(
        reverse('paiements:paiement-create'),
        data={'beneficiaire': lien.pk, 'montant': '12.00', 'motif': 'Web'},
    )
    assert created.status_code == 302
    paiement = Paiement.objects.get()

    client.logout()
    assert client.login(username='bob', password='MotDePasseFort123!')
    assert client.get(reverse('paiements:remboursement-list')).status_code == 200
    refund = client.post(
        reverse('paiements:remboursement-create'),
        data={'paiement': paiement.pk, 'montant': '4.00'},
    )
    assert refund.status_code == 302
    assert Remboursement.objects.count() == 1


@pytest.mark.django_db
def test_admin_paiements(staff_user, utilisateur, lien, payeur_alimente):
    executer_paiement(payeur=utilisateur, beneficiaire_id=lien.pk, montant='5.00')
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    assert client.get('/admin/paiements/paiement/').status_code == 200
    assert client.get('/admin/paiements/paiement/add/').status_code == 403

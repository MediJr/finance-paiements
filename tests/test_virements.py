"""
Tests métier Sprint 4 — Virements sécurisés.
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
from virements.models import Virement
from virements.services import executer_virement, get_virement_pour_utilisateur, list_virements
from wallets.models import Wallet


def _crediter_pour_tests(wallet, montant: Decimal):
    """Alimente un Wallet pour les tests (hors parcours métier production)."""
    wallet.solde = Decimal(montant)
    wallet.save(update_fields=['solde', 'date_mise_a_jour'])
    wallet.refresh_from_db()
    return wallet


@pytest.fixture
def lien_beneficiaire(utilisateur, autre_utilisateur):
    return create_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=autre_utilisateur.pk,
        alias='Bob',
    )


@pytest.fixture
def wallet_alimente(utilisateur):
    return _crediter_pour_tests(utilisateur.wallet, Decimal('100.00'))


@pytest.mark.django_db
def test_virement_valide(utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente):
    """Un virement valide débite et crédite les deux Wallets."""
    virement = executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien_beneficiaire.pk,
        montant=Decimal('25.50'),
        motif='Loyer',
    )
    utilisateur.wallet.refresh_from_db()
    autre_utilisateur.wallet.refresh_from_db()

    assert virement.statut == Virement.Statut.REUSSI
    assert utilisateur.wallet.solde == Decimal('74.50')
    assert autre_utilisateur.wallet.solde == Decimal('25.50')
    assert virement.montant == Decimal('25.50')


@pytest.mark.django_db
def test_solde_insuffisant(utilisateur, lien_beneficiaire, wallet_alimente):
    """Solde insuffisant → refus, soldes inchangés."""
    with pytest.raises(ValidationError, match='Solde insuffisant'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien_beneficiaire.pk,
            montant=Decimal('150.00'),
        )
    utilisateur.wallet.refresh_from_db()
    assert utilisateur.wallet.solde == Decimal('100.00')


@pytest.mark.django_db
def test_beneficiaire_inexistant(utilisateur, wallet_alimente):
    """Bénéficiaire inexistant / non autorisé."""
    with pytest.raises(ValidationError, match='Bénéficiaire inexistant'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=99999,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_beneficiaire_inactif(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """Bénéficiaire inactif refusé."""
    desactiver_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=lien_beneficiaire.pk,
    )
    with pytest.raises(ValidationError, match='inactif'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien_beneficiaire.pk,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_auto_virement_interdit(utilisateur, wallet_alimente):
    """Impossible de se virer à soi-même même via un lien artificiel."""
    # Création ORM directe pour simuler une donnée incohérente.
    from beneficiaires.models import Beneficiaire

    lien = Beneficiaire.objects.create(
        proprietaire=utilisateur,
        utilisateur_beneficiaire=utilisateur,
        statut=Beneficiaire.Statut.ACTIF,
    )
    with pytest.raises(ValidationError, match='soi-même'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien.pk,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_wallet_emetteur_inactif(
    utilisateur, lien_beneficiaire, wallet_alimente
):
    """Wallet émetteur inactif refusé."""
    wallet_alimente.statut = Wallet.Statut.INACTIF
    wallet_alimente.save(update_fields=['statut'])
    with pytest.raises(ValidationError, match='émetteur est inactif'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien_beneficiaire.pk,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_wallet_beneficiaire_inactif(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """Wallet bénéficiaire inactif refusé."""
    autre_utilisateur.wallet.statut = Wallet.Statut.INACTIF
    autre_utilisateur.wallet.save(update_fields=['statut'])
    with pytest.raises(ValidationError, match='bénéficiaire est inactif'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien_beneficiaire.pk,
            montant=Decimal('10.00'),
        )


@pytest.mark.django_db
def test_transaction_atomique_en_cas_echec_historique(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """Si l'historique échoue, aucun solde ni virement n'est persisté."""
    with patch(
        'wallets.services.mouvement_service.create_historique_operation',
        side_effect=RuntimeError('échec historique'),
    ):
        with pytest.raises(RuntimeError):
            executer_virement(
                emetteur=utilisateur,
                beneficiaire_id=lien_beneficiaire.pk,
                montant=Decimal('20.00'),
            )

    utilisateur.wallet.refresh_from_db()
    autre_utilisateur.wallet.refresh_from_db()
    assert utilisateur.wallet.solde == Decimal('100.00')
    assert autre_utilisateur.wallet.solde == Decimal('0.00')
    assert Virement.objects.count() == 0
    assert HistoriqueOperation.objects.count() == 0


@pytest.mark.django_db
def test_historique_automatique(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """Deux entrées d'historique (débit + crédit) sont créées."""
    virement = executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien_beneficiaire.pk,
        montant=Decimal('15.00'),
    )
    ops = HistoriqueOperation.objects.order_by('id')
    assert ops.count() == 2
    assert ops[0].type_operation == HistoriqueOperation.TypeOperation.VIREMENT
    assert ops[0].wallet_id == utilisateur.wallet.pk
    assert ops[1].type_operation == HistoriqueOperation.TypeOperation.VIREMENT
    assert ops[1].wallet_id == autre_utilisateur.wallet.pk
    assert ops[0].reference.startswith(virement.reference)


@pytest.mark.django_db
def test_montant_non_positif(utilisateur, lien_beneficiaire, wallet_alimente):
    """Montant <= 0 refusé."""
    with pytest.raises(ValidationError, match='strictement positif'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien_beneficiaire.pk,
            montant=Decimal('0.00'),
        )


@pytest.mark.django_db
def test_api_virement_et_acces(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """API POST/GET + contrôle d'accès."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    created = client.post(
        '/api/virements/',
        data=json.dumps({
            'beneficiaire_id': lien_beneficiaire.pk,
            'montant': '12.00',
            'motif': 'API',
        }),
        content_type='application/json',
    )
    assert created.status_code == 201
    virement_id = created.json()['id']

    liste = client.get('/api/virements/')
    assert liste.status_code == 200
    assert len(liste.json()) == 1

    detail = client.get(f'/api/virements/{virement_id}/')
    assert detail.status_code == 200

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
    forbidden = client.get(f'/api/virements/{virement_id}/')
    assert forbidden.status_code == 404


@pytest.mark.django_db
def test_api_solde_insuffisant(utilisateur, lien_beneficiaire, wallet_alimente):
    """API renvoie 400 si solde insuffisant."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.post(
        '/api/virements/',
        data=json.dumps({
            'beneficiaire_id': lien_beneficiaire.pk,
            'montant': '999.00',
        }),
        content_type='application/json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_vues_web_virements(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """Pages web liste / détail / création."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get(reverse('virements:virement-list'))
    assert liste.status_code == 200

    form_page = client.get(reverse('virements:virement-create'))
    assert form_page.status_code == 200

    created = client.post(
        reverse('virements:virement-create'),
        data={
            'beneficiaire': lien_beneficiaire.pk,
            'montant': '8.00',
            'motif': 'Web',
        },
    )
    assert created.status_code == 302
    virement = Virement.objects.get()
    detail = client.get(reverse('virements:virement-detail', args=[virement.pk]))
    assert detail.status_code == 200
    assert virement.reference.encode() in detail.content


@pytest.mark.django_db
def test_admin_consultation_virement(
    staff_user, utilisateur, lien_beneficiaire, wallet_alimente
):
    """Admin : consultation seule, pas d'ajout."""
    executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien_beneficiaire.pk,
        montant=Decimal('5.00'),
    )
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    liste = client.get('/admin/virements/virement/')
    assert liste.status_code == 200
    add_page = client.get('/admin/virements/virement/add/')
    assert add_page.status_code == 403


@pytest.mark.django_db
def test_list_virements_parties(
    utilisateur, autre_utilisateur, lien_beneficiaire, wallet_alimente
):
    """Émetteur et destinataire voient le virement."""
    virement = executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien_beneficiaire.pk,
        montant=Decimal('7.00'),
    )
    assert list_virements(utilisateur=utilisateur).filter(pk=virement.pk).exists()
    assert list_virements(utilisateur=autre_utilisateur).filter(pk=virement.pk).exists()
    found = get_virement_pour_utilisateur(
        utilisateur=autre_utilisateur,
        virement_id=virement.pk,
    )
    assert found.reference == virement.reference

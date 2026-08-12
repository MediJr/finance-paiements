"""
Tests Sprint 7 — Security by Design.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from administration.models import JournalAdministration
from administration.services import get_parametres, update_parametres
from beneficiaires.services import create_beneficiaire
from historique.services import create_historique_operation
from historique.models import HistoriqueOperation
from paiements.services import executer_paiement, executer_remboursement
from virements.services import executer_virement


def _crediter(wallet, montant: str = '5000.00'):
    wallet.solde = Decimal(montant)
    wallet.save(update_fields=['solde', 'date_mise_a_jour'])


@pytest.fixture
def lien(utilisateur, autre_utilisateur):
    return create_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=autre_utilisateur.pk,
        alias='Bob',
    )


@pytest.mark.django_db
def test_idor_api_utilisateurs_wallets(utilisateur, autre_utilisateur):
    """Alice ne peut pas lire le profil / wallet de Bob."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get('/api/utilisateurs/')
    assert liste.status_code == 200
    assert len(liste.json()) == 1
    assert liste.json()[0]['email'] == 'alice@example.com'

    detail_bob = client.get(f'/api/utilisateurs/{autre_utilisateur.pk}/')
    assert detail_bob.status_code == 403

    wallet_bob = client.get(f'/api/wallets/{autre_utilisateur.wallet.pk}/')
    assert wallet_bob.status_code == 404

    wallet_via_user = client.get(f'/api/utilisateurs/{autre_utilisateur.pk}/wallet/')
    assert wallet_via_user.status_code == 403


@pytest.mark.django_db
def test_idor_api_historique(utilisateur, autre_utilisateur):
    """Alice ne voit pas l'historique de Bob."""
    create_historique_operation(
        wallet=autre_utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.AUTRE,
        reference='OP-BOB-SECRET',
    )
    create_historique_operation(
        wallet=utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.AUTRE,
        reference='OP-ALICE-OK',
    )
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get('/api/historique/')
    assert liste.status_code == 200
    refs = {item['reference'] for item in liste.json()}
    assert 'OP-ALICE-OK' in refs
    assert 'OP-BOB-SECRET' not in refs

    bob_ops = create_historique_operation(
        wallet=autre_utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.AUTRE,
        reference='OP-BOB-DET',
    )
    detail = client.get(f'/api/historique/{bob_ops.pk}/')
    assert detail.status_code == 404

    hist_wallet = client.get(
        f'/api/wallets/{autre_utilisateur.wallet.pk}/historique/'
    )
    assert hist_wallet.status_code == 404


@pytest.mark.django_db
def test_idor_web_utilisateurs_wallets_historique(
    utilisateur, autre_utilisateur
):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get(reverse('accounts:utilisateur-list'))
    assert liste.status_code == 200
    assert b'Alice' in liste.content
    assert b'Bob' not in liste.content

    detail_bob = client.get(
        reverse('accounts:utilisateur-detail', args=[autre_utilisateur.pk])
    )
    assert detail_bob.status_code == 403

    wallet_bob = client.get(
        reverse('wallets:wallet-detail', args=[autre_utilisateur.wallet.pk])
    )
    assert wallet_bob.status_code == 404

    op_bob = create_historique_operation(
        wallet=autre_utilisateur.wallet,
        type_operation=HistoriqueOperation.TypeOperation.AUTRE,
        reference='OP-WEB-BOB',
    )
    hist = client.get(reverse('historique:historique-list'))
    assert hist.status_code == 200
    assert b'OP-WEB-BOB' not in hist.content

    detail_op = client.get(
        reverse('historique:historique-detail', args=[op_bob.pk])
    )
    assert detail_op.status_code == 404


@pytest.mark.django_db
def test_admin_voit_globalement(staff_user, utilisateur, autre_utilisateur):
    """Un staff conserve la vision globale via l'API métier."""
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    liste = client.get('/api/utilisateurs/')
    assert liste.status_code == 200
    emails = {u['email'] for u in liste.json()}
    assert 'alice@example.com' in emails
    assert 'bob@example.com' in emails

    wallet_bob = client.get(f'/api/wallets/{autre_utilisateur.wallet.pk}/')
    assert wallet_bob.status_code == 200


@pytest.mark.django_db
def test_plafond_virement(utilisateur, autre_utilisateur, lien, staff_user):
    update_parametres(
        administrateur=staff_user,
        montant_virement_max='100.00',
    )
    _crediter(utilisateur.wallet, '1000.00')
    with pytest.raises(ValidationError, match='plafond de virement'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien.pk,
            montant='150.00',
        )


@pytest.mark.django_db
def test_plafond_paiement(utilisateur, autre_utilisateur, lien, staff_user):
    update_parametres(
        administrateur=staff_user,
        montant_paiement_max='50.00',
    )
    _crediter(utilisateur.wallet, '1000.00')
    with pytest.raises(ValidationError, match='plafond de paiement'):
        executer_paiement(
            payeur=utilisateur,
            beneficiaire_id=lien.pk,
            montant='75.00',
        )


@pytest.mark.django_db
def test_mode_maintenance_bloque_operations(
    utilisateur, autre_utilisateur, lien, staff_user
):
    update_parametres(administrateur=staff_user, mode_maintenance=True)
    _crediter(utilisateur.wallet, '1000.00')
    with pytest.raises(ValidationError, match='maintenance'):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien.pk,
            montant='10.00',
        )
    with pytest.raises(ValidationError, match='maintenance'):
        executer_paiement(
            payeur=utilisateur,
            beneficiaire_id=lien.pk,
            montant='10.00',
        )


@pytest.mark.django_db
def test_mode_maintenance_middleware_api(
    utilisateur, autre_utilisateur, lien, staff_user
):
    update_parametres(administrateur=staff_user, mode_maintenance=True)
    _crediter(utilisateur.wallet, '1000.00')
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.post(
        '/api/virements/',
        data={'beneficiaire_id': lien.pk, 'montant': '10.00'},
        content_type='application/json',
    )
    assert response.status_code == 503


@pytest.mark.django_db
def test_journal_modification_parametres_et_activation(
    staff_user, utilisateur
):
    update_parametres(
        administrateur=staff_user,
        nom_application='Finance Sécurisée',
        adresse_ip='127.0.0.1',
    )
    assert JournalAdministration.objects.filter(
        action=JournalAdministration.Action.MODIFICATION_PARAMETRES
    ).exists()

    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    client.post(
        reverse('administration:utilisateur-desactiver', args=[utilisateur.pk])
    )
    assert JournalAdministration.objects.filter(
        action=JournalAdministration.Action.DESACTIVATION_UTILISATEUR,
        cible_id=utilisateur.pk,
    ).exists()

    journal_page = client.get(reverse('administration:journal'))
    assert journal_page.status_code == 200


@pytest.mark.django_db
def test_journal_acces_admin(staff_user):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    client.get(reverse('administration:index'))
    assert JournalAdministration.objects.filter(
        action=JournalAdministration.Action.ACCES_ADMIN
    ).exists()


@pytest.mark.django_db
def test_parametres_effectifs_lecture(staff_user):
    params = get_parametres(administrateur=staff_user)
    assert params.montant_virement_max == Decimal('10000.00')
    update_parametres(
        administrateur=staff_user,
        montant_virement_max='999.99',
    )
    params = get_parametres(administrateur=staff_user)
    assert params.montant_virement_max == Decimal('999.99')


@pytest.mark.django_db
def test_virement_sous_plafond_ok(utilisateur, autre_utilisateur, lien, staff_user):
    update_parametres(
        administrateur=staff_user,
        montant_virement_max='200.00',
        mode_maintenance=False,
    )
    _crediter(utilisateur.wallet, '500.00')
    virement = executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien.pk,
        montant='150.00',
    )
    assert virement.montant == Decimal('150.00')

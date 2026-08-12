"""
Tests Prototype 4 Sprint 9 — Observabilité.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, RequestFactory
from django.urls import reverse

from beneficiaires.services import create_beneficiaire
from observabilite.middleware import ObservabiliteExceptionMiddleware
from observabilite.models import Evenement
from observabilite.services.journal_service import (
    TYPE_HTTP_500,
    TYPE_UTILISATEUR_CREATION,
    TYPE_VIREMENT_ECHEC,
    TYPE_VIREMENT_REUSSITE,
    TYPE_WALLET_CREATION,
    enregistrer_evenement,
    get_evenement,
    list_evenements,
)
from virements.services import executer_virement


def _crediter(wallet, montant='500.00'):
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
def test_enregistrer_evenement_unique_point(utilisateur):
    evt = enregistrer_evenement(
        type_evenement='test_manuel',
        module='tests',
        description='Événement de test',
        utilisateur=utilisateur.user,
        contexte={'ok': True},
    )
    assert evt is not None
    assert evt.pk is not None
    assert Evenement.objects.filter(pk=evt.pk).exists()


@pytest.mark.django_db
def test_evenement_immutable(utilisateur):
    evt = enregistrer_evenement(
        type_evenement='test_immuable',
        module='tests',
        description='x',
        utilisateur=utilisateur.user,
    )
    with pytest.raises(ValueError):
        evt.description = 'modifié'
        evt.save()
    with pytest.raises(ValueError):
        evt.delete()


@pytest.mark.django_db
def test_instrumentation_utilisateur_wallet(db):
    from accounts.services import create_utilisateur

    u = create_utilisateur(
        username='obs_user',
        password='MotDePasseFort123!',
        prenom='Obs',
        nom='User',
        email='obs@example.com',
    )
    assert Evenement.objects.filter(type_evenement=TYPE_UTILISATEUR_CREATION).exists()
    assert Evenement.objects.filter(type_evenement=TYPE_WALLET_CREATION).exists()
    assert u.wallet.pk is not None


@pytest.mark.django_db
def test_instrumentation_virement_reussite_et_echec(
    utilisateur, autre_utilisateur, lien
):
    _crediter(utilisateur.wallet, '200.00')
    virement = executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien.pk,
        montant='50.00',
    )
    assert Evenement.objects.filter(type_evenement=TYPE_VIREMENT_REUSSITE).exists()
    assert virement.reference

    with pytest.raises(ValidationError):
        executer_virement(
            emetteur=utilisateur,
            beneficiaire_id=lien.pk,
            montant='99999.00',
        )
    assert Evenement.objects.filter(type_evenement=TYPE_VIREMENT_ECHEC).exists()


@pytest.mark.django_db
def test_list_evenements_admin_only(staff_user, utilisateur):
    enregistrer_evenement(
        type_evenement='filtre_test',
        module='tests',
        description='filtre',
        niveau=Evenement.Niveau.INFO,
    )
    with pytest.raises(PermissionDenied):
        list_evenements(administrateur=utilisateur.user)

    rows = list_evenements(
        administrateur=staff_user,
        module='tests',
        type_evenement='filtre_test',
    )
    assert len(rows) >= 1
    detail = get_evenement(administrateur=staff_user, evenement_id=rows[0].pk)
    assert detail.type_evenement == 'filtre_test'


@pytest.mark.django_db
def test_web_evenements_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.get(reverse('observabilite:evenement-list'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_web_et_api_evenements(staff_user, utilisateur):
    enregistrer_evenement(
        type_evenement='api_test',
        module='tests',
        description='via api',
        utilisateur=utilisateur.user,
    )
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')

    page = client.get(reverse('observabilite:evenement-list'))
    assert page.status_code == 200
    assert b'api_test' in page.content

    api = client.get('/api/administration/evenements/?module=tests')
    assert api.status_code == 200
    assert any(e['type_evenement'] == 'api_test' for e in api.json())

    evt_id = Evenement.objects.filter(type_evenement='api_test').first().pk
    detail_api = client.get(f'/api/administration/evenements/{evt_id}/')
    assert detail_api.status_code == 200
    assert detail_api.json()['id'] == evt_id

    detail_web = client.get(reverse('observabilite:evenement-detail', args=[evt_id]))
    assert detail_web.status_code == 200


@pytest.mark.django_db
def test_middleware_journalise_exception(staff_user):
    factory = RequestFactory()
    request = factory.get('/boom/')
    request.user = staff_user
    middleware = ObservabiliteExceptionMiddleware(get_response=lambda r: None)
    middleware.process_exception(request, RuntimeError('boom-test'))
    assert Evenement.objects.filter(type_evenement=TYPE_HTTP_500).exists()


@pytest.mark.django_db
def test_api_evenements_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    assert client.get('/api/administration/evenements/').status_code == 403

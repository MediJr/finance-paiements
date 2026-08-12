"""
Tests Prototype 4 Sprint 10 — Export CSV / JSON.
"""

import csv
import io
import json
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse

from administration.services.export_service import TYPES_EXPORT, exporter
from beneficiaires.services import create_beneficiaire
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
def test_export_refuse_non_admin(utilisateur):
    with pytest.raises(PermissionDenied):
        exporter(
            administrateur=utilisateur.user,
            type_export='utilisateurs',
            format_export='json',
        )


@pytest.mark.django_db
def test_export_json_utilisateurs(staff_user, utilisateur):
    result = exporter(
        administrateur=staff_user,
        type_export='utilisateurs',
        format_export='json',
    )
    assert result['filename'].endswith('.json')
    payload = json.loads(result['content'])
    assert payload['export']['version'] == 'finance-export-v1'
    assert payload['export']['type'] == 'utilisateurs'
    assert payload['export']['count'] >= 1
    assert any(row['email'] == 'alice@example.com' for row in payload['data'])


@pytest.mark.django_db
def test_export_csv_virements(staff_user, utilisateur, autre_utilisateur, lien):
    _crediter(utilisateur.wallet, '300.00')
    virement = executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien.pk,
        montant='25.00',
    )
    result = exporter(
        administrateur=staff_user,
        type_export='virements',
        format_export='csv',
    )
    assert result['filename'].endswith('.csv')
    assert 'text/csv' in result['content_type']
    reader = csv.DictReader(io.StringIO(result['content'].lstrip('\ufeff')))
    rows = list(reader)
    assert any(row['reference'] == virement.reference for row in rows)


@pytest.mark.django_db
def test_export_filtre_statut(staff_user, utilisateur, autre_utilisateur, lien):
    _crediter(utilisateur.wallet, '300.00')
    executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien.pk,
        montant='10.00',
    )
    result = exporter(
        administrateur=staff_user,
        type_export='virements',
        format_export='json',
        statut='reussi',
    )
    payload = json.loads(result['content'])
    assert payload['export']['count'] >= 1
    assert all(row['statut'] == 'reussi' for row in payload['data'])

    vide = exporter(
        administrateur=staff_user,
        type_export='virements',
        format_export='json',
        statut='echoue',
    )
    assert json.loads(vide['content'])['export']['count'] == 0


@pytest.mark.django_db
def test_export_type_invalide(staff_user):
    with pytest.raises(ValidationError):
        exporter(
            administrateur=staff_user,
            type_export='analytics',
            format_export='json',
        )


@pytest.mark.django_db
def test_export_tous_types_json(staff_user, utilisateur):
    for type_export in TYPES_EXPORT:
        result = exporter(
            administrateur=staff_user,
            type_export=type_export,
            format_export='json',
        )
        payload = json.loads(result['content'])
        assert payload['export']['type'] == type_export
        assert isinstance(payload['data'], list)


@pytest.mark.django_db
def test_web_export_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    assert client.get(reverse('administration:exports')).status_code == 302


@pytest.mark.django_db
def test_web_et_api_export(staff_user, utilisateur):
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')

    page = client.get(reverse('administration:exports'))
    assert page.status_code == 200
    assert b'Exports' in page.content

    download = client.get(
        reverse('administration:export-download'),
        {'type': 'utilisateurs', 'format': 'json'},
    )
    assert download.status_code == 200
    assert download['Content-Disposition'].startswith('attachment;')
    payload = json.loads(download.content.decode('utf-8'))
    assert payload['export']['type'] == 'utilisateurs'

    api = client.get(
        '/api/administration/exports/',
        {'type': 'wallets', 'export_format': 'csv'},
    )
    assert api.status_code == 200
    assert b'solde' in api.content or b'id' in api.content


@pytest.mark.django_db
def test_api_export_refuse_non_staff(utilisateur):
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    assert client.get('/api/administration/exports/?type=utilisateurs').status_code == 403

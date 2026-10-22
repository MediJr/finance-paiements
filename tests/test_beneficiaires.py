"""
Tests métier Sprint 3 — Gestion des bénéficiaires.
"""

import json

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from beneficiaires.models import Beneficiaire
from beneficiaires.services import (
    create_beneficiaire,
    desactiver_beneficiaire,
    get_beneficiaire_pour_proprietaire,
    list_beneficiaires,
    list_beneficiaires_selectionnables,
    reactiver_beneficiaire,
    update_beneficiaire,
)


@pytest.fixture
def beneficiaire(utilisateur, autre_utilisateur):
    return create_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=autre_utilisateur.pk,
        alias='Bob ami',
    )


@pytest.mark.django_db
def test_create_beneficiaire(utilisateur, autre_utilisateur):
    """Création d'un bénéficiaire."""
    beneficiaire = create_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=autre_utilisateur.pk,
        alias='Contact Bob',
    )
    assert beneficiaire.pk is not None
    assert beneficiaire.proprietaire_id == utilisateur.pk
    assert beneficiaire.utilisateur_beneficiaire_id == autre_utilisateur.pk
    assert beneficiaire.statut == Beneficiaire.Statut.ACTIF


@pytest.mark.django_db
def test_impossible_s_ajouter_soi_meme(utilisateur):
    """Un utilisateur ne peut pas s'ajouter lui-même."""
    with pytest.raises(ValidationError):
        create_beneficiaire(
            proprietaire=utilisateur,
            beneficiaire_id=utilisateur.pk,
        )


@pytest.mark.django_db
def test_unicite_beneficiaire_par_utilisateur(utilisateur, autre_utilisateur, beneficiaire):
    """Un même destinataire ne peut être ajouté qu'une fois."""
    with pytest.raises(ValidationError):
        create_beneficiaire(
            proprietaire=utilisateur,
            beneficiaire_id=autre_utilisateur.pk,
        )


@pytest.mark.django_db
def test_consultation_et_modification(utilisateur, beneficiaire):
    """Consultation et modification d'alias / statut."""
    found = get_beneficiaire_pour_proprietaire(
        proprietaire=utilisateur,
        beneficiaire_id=beneficiaire.pk,
    )
    assert found.alias == 'Bob ami'

    updated = update_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=beneficiaire.pk,
        alias='Bob mis à jour',
    )
    assert updated.alias == 'Bob mis à jour'


@pytest.mark.django_db
def test_desactivation_et_reactivation(utilisateur, beneficiaire):
    """Désactivation logique puis réactivation."""
    desactive = desactiver_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=beneficiaire.pk,
    )
    assert desactive.statut == Beneficiaire.Statut.INACTIF
    assert list_beneficiaires_selectionnables(proprietaire=utilisateur).count() == 0

    reactive = reactiver_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=beneficiaire.pk,
    )
    assert reactive.statut == Beneficiaire.Statut.ACTIF
    assert list_beneficiaires_selectionnables(proprietaire=utilisateur).count() == 1


@pytest.mark.django_db
def test_acces_interdit_autre_proprietaire(utilisateur, autre_utilisateur, beneficiaire):
    """Un utilisateur ne peut pas consulter le bénéficiaire d'un autre."""
    from django.http import Http404

    with pytest.raises(Http404):
        get_beneficiaire_pour_proprietaire(
            proprietaire=autre_utilisateur,
            beneficiaire_id=beneficiaire.pk,
        )


@pytest.mark.django_db
def test_api_beneficiaires_crud(utilisateur, autre_utilisateur):
    """API création, lecture, modification, désactivation."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    create_resp = client.post(
        '/api/beneficiaires/',
        data=json.dumps({
            'email': autre_utilisateur.email,
            'alias': 'API Bob',
        }),
        content_type='application/json',
    )
    assert create_resp.status_code == 201
    beneficiaire_id = create_resp.json()['id']

    liste = client.get('/api/beneficiaires/')
    assert liste.status_code == 200
    assert len(liste.json()) == 1

    detail = client.get(f'/api/beneficiaires/{beneficiaire_id}/')
    assert detail.status_code == 200
    assert detail.json()['alias'] == 'API Bob'

    patch = client.patch(
        f'/api/beneficiaires/{beneficiaire_id}/',
        data=json.dumps({'alias': 'API Bob 2'}),
        content_type='application/json',
    )
    assert patch.status_code == 200
    assert patch.json()['alias'] == 'API Bob 2'

    delete = client.delete(f'/api/beneficiaires/{beneficiaire_id}/')
    assert delete.status_code == 200
    assert delete.json()['statut'] == 'inactif'


@pytest.mark.django_db
def test_api_controle_acces(utilisateur, autre_utilisateur, beneficiaire):
    """Bob ne peut pas accéder au bénéficiaire d'Alice."""
    client = Client()
    assert client.login(username='bob', password='MotDePasseFort123!')

    liste = client.get('/api/beneficiaires/')
    assert liste.status_code == 200
    assert liste.json() == []

    detail = client.get(f'/api/beneficiaires/{beneficiaire.pk}/')
    assert detail.status_code == 404

    self_add = client.post(
        '/api/beneficiaires/',
        data=json.dumps({'email': autre_utilisateur.email}),
        content_type='application/json',
    )
    assert self_add.status_code == 400
    assert 'lui-même' in self_add.content.decode()


@pytest.mark.django_db
def test_api_refus_auto_ajout(utilisateur):
    """API refuse l'auto-ajout."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')
    response = client.post(
        '/api/beneficiaires/',
        data=json.dumps({'email': utilisateur.email}),
        content_type='application/json',
    )
    assert response.status_code == 400
    assert 'lui-même' in response.content.decode()


@pytest.mark.django_db
def test_vues_web_beneficiaires(utilisateur, autre_utilisateur, beneficiaire):
    """Pages web liste / détail / création / modification."""
    client = Client()
    assert client.login(username='alice', password='MotDePasseFort123!')

    liste = client.get(reverse('beneficiaires:beneficiaire-list'))
    assert liste.status_code == 200
    assert b'Bob' in liste.content

    detail = client.get(
        reverse('beneficiaires:beneficiaire-detail', args=[beneficiaire.pk])
    )
    assert detail.status_code == 200

    create_page = client.get(reverse('beneficiaires:beneficiaire-create'))
    assert create_page.status_code == 200

    # Créer un 3e utilisateur pour le formulaire (Bob déjà lié)
    from accounts.services import create_utilisateur

    carol = create_utilisateur(
        username='carol',
        password='MotDePasseFort123!',
        prenom='Carol',
        nom='Leroy',
        email='carol@example.com',
    )
    created = client.post(
        reverse('beneficiaires:beneficiaire-create'),
        data={
            'email': carol.email,
            'alias': 'Carol',
        },
    )
    assert created.status_code == 302

    update = client.post(
        reverse('beneficiaires:beneficiaire-update', args=[beneficiaire.pk]),
        data={'alias': 'Nouveau alias', 'statut': 'inactif'},
    )
    assert update.status_code == 302
    beneficiaire.refresh_from_db()
    assert beneficiaire.alias == 'Nouveau alias'
    assert beneficiaire.statut == Beneficiaire.Statut.INACTIF


@pytest.mark.django_db
def test_admin_beneficiaires(staff_user, beneficiaire):
    """Administration : consultation et filtrage."""
    client = Client()
    assert client.login(username='admin_finance', password='MotDePasseFort123!')
    response = client.get('/admin/beneficiaires/beneficiaire/')
    assert response.status_code == 200
    assert b'Bob' in response.content


@pytest.mark.django_db
def test_list_beneficiaires_filtre_statut(utilisateur, beneficiaire):
    """Filtrage des bénéficiaires par statut."""
    desactiver_beneficiaire(
        proprietaire=utilisateur,
        beneficiaire_id=beneficiaire.pk,
    )
    assert list_beneficiaires(proprietaire=utilisateur, statut='actif').count() == 0
    assert list_beneficiaires(proprietaire=utilisateur, statut='inactif').count() == 1

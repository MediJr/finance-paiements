"""
Tests Sprint 11 — audit de sécurité et durcissement.

Chaque section correspond à un défaut de l'audit (voir docs/securite.md,
tableau « Défauts corrigés ») et vérifie qu'il ne peut plus se reproduire.
"""

import json
from decimal import Decimal

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import Client, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Utilisateur
from administration.models import ParametresApplication
from administration.services.export_service import exporter, neutraliser_formule
from beneficiaires.services import ajouter_beneficiaire_par_email
from commun.http import adresse_ip_client
from historique.models import HistoriqueOperation
from paiements.services import executer_paiement
from virements.models import Virement
from virements.services import executer_virement
from wallets.models import Alimentation
from wallets.services import alimenter_wallet, parse_montant
from wallets.services.passerelle_carte import CARTE_TEST_ACCEPTEE, CARTE_TEST_REFUSEE

MOT_DE_PASSE = 'MotDePasseFort123!'


@pytest.fixture
def lien_bob(utilisateur, autre_utilisateur):
    """Alice a Bob pour bénéficiaire et dispose de 1 000 EUR."""
    alimenter_wallet(utilisateur=utilisateur, montant='1000.00', numero_carte=CARTE_TEST_ACCEPTEE)
    return ajouter_beneficiaire_par_email(
        proprietaire=utilisateur,
        email=autre_utilisateur.email,
        alias='Bob',
    )


def _client_web(username='alice'):
    web = Client()
    assert web.login(username=username, password=MOT_DE_PASSE)
    return web


def _client_api(username='alice'):
    api = APIClient()
    assert api.login(username=username, password=MOT_DE_PASSE)
    return api


# ---------------------------------------------------------------------------
# F1 — Annuaire des clients non énumérable
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_formulaire_beneficiaire_ne_liste_pas_les_clients(utilisateur, autre_utilisateur):
    page = _client_web().get(reverse('beneficiaires:beneficiaire-create'))
    contenu = page.content.decode()
    assert page.status_code == 200
    assert autre_utilisateur.email not in contenu
    assert 'Dupont' not in contenu


@pytest.mark.django_db
def test_api_refuse_l_ajout_par_identifiant(utilisateur, autre_utilisateur):
    """Avant correction : itérer sur les identifiants révélait nom et e-mail de chaque client."""
    response = _client_api().post(
        '/api/beneficiaires/',
        {'utilisateur_beneficiaire_id': autre_utilisateur.pk},
        format='json',
    )
    assert response.status_code == 400
    assert autre_utilisateur.email not in response.content.decode()


@pytest.mark.django_db
def test_api_ajout_par_email(utilisateur, autre_utilisateur):
    response = _client_api().post(
        '/api/beneficiaires/',
        {'email': 'BOB@example.com', 'alias': 'Bob'},
        format='json',
    )
    assert response.status_code == 201
    assert response.json()['alias'] == 'Bob'


@pytest.mark.django_db
def test_email_inconnu_message_generique(utilisateur):
    with pytest.raises(ValidationError, match='Aucun client actif'):
        ajouter_beneficiaire_par_email(proprietaire=utilisateur, email='personne@example.com')


# ---------------------------------------------------------------------------
# F2 — Espace client : inscription, connexion, déconnexion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_inscription_web_cree_compte_wallet_et_session():
    web = Client()
    response = web.post(
        reverse('accounts:inscription'),
        {
            'prenom': 'Chloé',
            'nom': 'Bernard',
            'email': 'chloe@example.com',
            'username': 'chloe',
            'password': MOT_DE_PASSE,
            'password_confirm': MOT_DE_PASSE,
        },
    )
    assert response.status_code == 302
    assert response['Location'] == reverse('accounts:espace')
    utilisateur = Utilisateur.objects.get(email='chloe@example.com')
    assert utilisateur.wallet.solde == Decimal('0.00')
    assert web.get(reverse('accounts:espace')).status_code == 200


@pytest.mark.django_db
def test_inscription_refuse_email_deja_utilise(utilisateur):
    response = Client().post(
        reverse('accounts:inscription'),
        {
            'prenom': 'Alice',
            'nom': 'Bis',
            'email': 'ALICE@example.com',
            'username': 'alice2',
            'password': MOT_DE_PASSE,
            'password_confirm': MOT_DE_PASSE,
        },
    )
    assert response.status_code == 200
    assert 'existe déjà' in response.content.decode()


@pytest.mark.django_db
def test_client_se_connecte_hors_du_site_admin(utilisateur):
    """Avant correction : seule la connexion /admin/ existait, réservée au personnel."""
    response = Client().post(
        reverse('accounts:connexion'),
        {'username': 'alice', 'password': MOT_DE_PASSE},
    )
    assert response.status_code == 302
    assert response['Location'] == '/'


@pytest.mark.django_db
def test_accueil_oriente_client_et_personnel(utilisateur, staff_user):
    assert _client_web().get('/')['Location'] == reverse('accounts:espace')
    staff = _client_web('admin_finance')
    assert staff.get('/')['Location'] == reverse('administration:index')


@pytest.mark.django_db
def test_deconnexion_post_uniquement(utilisateur):
    web = _client_web()
    assert web.get(reverse('accounts:deconnexion')).status_code == 405
    assert web.post(reverse('accounts:deconnexion')).status_code == 302
    assert '_auth_user_id' not in web.session


@pytest.mark.django_db
def test_connexion_ignore_une_redirection_externe(utilisateur):
    response = Client().post(
        reverse('accounts:connexion') + '?next=https://site-malveillant.example/',
        {'username': 'alice', 'password': MOT_DE_PASSE},
    )
    assert response['Location'] == '/'


# ---------------------------------------------------------------------------
# F3 — Alimentation du Wallet par carte (décision serveur)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_alimentation_acceptee_credite_et_trace(utilisateur):
    alimentation = alimenter_wallet(
        utilisateur=utilisateur, montant='250.00', numero_carte='4242 4242 4242 4242'
    )
    utilisateur.wallet.refresh_from_db()
    assert alimentation.statut == Alimentation.Statut.ACCEPTEE
    assert alimentation.carte_masquee == '•••• 4242'
    assert utilisateur.wallet.solde == Decimal('250.00')
    assert HistoriqueOperation.objects.filter(
        reference=alimentation.reference,
        type_operation=HistoriqueOperation.TypeOperation.CREDIT,
        statut=HistoriqueOperation.Statut.REUSSIE,
    ).exists()


@pytest.mark.django_db
def test_alimentation_refusee_ne_credite_pas(utilisateur):
    alimentation = alimenter_wallet(
        utilisateur=utilisateur, montant='250.00', numero_carte=CARTE_TEST_REFUSEE
    )
    utilisateur.wallet.refresh_from_db()
    assert alimentation.statut == Alimentation.Statut.REFUSEE
    assert alimentation.motif_refus
    assert utilisateur.wallet.solde == Decimal('0.00')


@pytest.mark.django_db
@pytest.mark.parametrize('carte', ['4242424242424241', '1234', 'abcd'])
def test_carte_invalide_rejetee_sans_trace(utilisateur, carte):
    with pytest.raises(ValidationError, match='carte invalide'):
        alimenter_wallet(utilisateur=utilisateur, montant='10.00', numero_carte=carte)
    assert not Alimentation.objects.exists()


@pytest.mark.django_db
def test_alimentation_plafonnee(utilisateur):
    with pytest.raises(ValidationError, match='plafond'):
        alimenter_wallet(
            utilisateur=utilisateur, montant='5000.01', numero_carte=CARTE_TEST_ACCEPTEE
        )


@pytest.mark.django_db
def test_numero_de_carte_jamais_conserve(utilisateur):
    alimentation = alimenter_wallet(
        utilisateur=utilisateur, montant='10.00', numero_carte=CARTE_TEST_ACCEPTEE
    )
    for champ in ('carte_masquee', 'motif_refus', 'reference'):
        assert CARTE_TEST_ACCEPTEE not in getattr(alimentation, champ)


@pytest.mark.django_db
def test_api_alimentation_codes_retour(utilisateur):
    api = _client_api()
    acceptee = api.post(
        '/api/alimentations/',
        {'montant': '20.00', 'numero_carte': CARTE_TEST_ACCEPTEE},
        format='json',
    )
    refusee = api.post(
        '/api/alimentations/',
        {'montant': '20.00', 'numero_carte': CARTE_TEST_REFUSEE},
        format='json',
    )
    assert acceptee.status_code == 201
    assert refusee.status_code == 402
    assert 'numero_carte' not in acceptee.json()
    assert len(api.get('/api/alimentations/').json()) == 2


@pytest.mark.django_db
def test_page_alimentation_web(utilisateur):
    web = _client_web()
    page = web.get(reverse('wallets:alimentation'))
    assert page.status_code == 200
    assert CARTE_TEST_ACCEPTEE in page.content.decode()
    response = web.post(
        reverse('wallets:alimentation'),
        {'montant': '75.00', 'numero_carte': CARTE_TEST_ACCEPTEE, 'cle_idempotence': 'k1'},
        follow=True,
    )
    assert 'crédités' in response.content.decode()
    utilisateur.wallet.refresh_from_db()
    assert utilisateur.wallet.solde == Decimal('75.00')


# ---------------------------------------------------------------------------
# F4 — Idempotence : pas de double débit
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_double_soumission_virement_un_seul_debit(utilisateur, lien_bob):
    premier = executer_virement(
        emetteur=utilisateur, beneficiaire_id=lien_bob.pk, montant='100.00', cle_idempotence='cle-1'
    )
    second = executer_virement(
        emetteur=utilisateur, beneficiaire_id=lien_bob.pk, montant='100.00', cle_idempotence='cle-1'
    )
    utilisateur.wallet.refresh_from_db()
    assert second.pk == premier.pk
    assert second.est_rejeu is True
    assert Virement.objects.count() == 1
    assert utilisateur.wallet.solde == Decimal('900.00')


@pytest.mark.django_db
def test_api_virement_idempotency_key(utilisateur, lien_bob):
    api = _client_api()
    corps = {'beneficiaire_id': lien_bob.pk, 'montant': '50.00'}
    r1 = api.post('/api/virements/', corps, format='json', HTTP_IDEMPOTENCY_KEY='abc')
    r2 = api.post('/api/virements/', corps, format='json', HTTP_IDEMPOTENCY_KEY='abc')
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json()['reference'] == r2.json()['reference']


@pytest.mark.django_db
def test_double_soumission_paiement_web(utilisateur, lien_bob):
    web = _client_web()
    donnees = {'beneficiaire': lien_bob.pk, 'montant': '30.00', 'cle_idempotence': 'form-42'}
    web.post(reverse('paiements:paiement-create'), donnees)
    web.post(reverse('paiements:paiement-create'), donnees)
    utilisateur.wallet.refresh_from_db()
    assert utilisateur.wallet.solde == Decimal('970.00')


@pytest.mark.django_db
def test_formulaire_virement_contient_une_cle(utilisateur, lien_bob):
    page = _client_web().get(reverse('virements:virement-create'))
    assert 'name="cle_idempotence"' in page.content.decode()


# ---------------------------------------------------------------------------
# F5 — Plafond journalier cumulé
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plafond_journalier_cumule(utilisateur, lien_bob):
    ParametresApplication.objects.update_or_create(
        pk=1, defaults={'plafond_journalier': Decimal('150.00')}
    )
    executer_virement(emetteur=utilisateur, beneficiaire_id=lien_bob.pk, montant='100.00')
    executer_paiement(payeur=utilisateur, beneficiaire_id=lien_bob.pk, montant='40.00')
    with pytest.raises(ValidationError, match='Plafond journalier'):
        executer_virement(emetteur=utilisateur, beneficiaire_id=lien_bob.pk, montant='20.00')
    utilisateur.wallet.refresh_from_db()
    assert utilisateur.wallet.solde == Decimal('860.00')


# ---------------------------------------------------------------------------
# F6 — Montants : pas d'arrondi silencieux
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('valeur', ['0.001', '10.005', 'NaN', 'Infinity', '1e30', '-5', '0'])
def test_montants_invalides_rejetes(valeur):
    with pytest.raises(ValidationError):
        parse_montant(valeur)


def test_montant_valide_normalise():
    assert parse_montant('12.5') == Decimal('12.50')


# ---------------------------------------------------------------------------
# F7 — Injection de formules dans les exports CSV
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'valeur,attendu',
    [
        ('=HYPERLINK("http://x")', '\'=HYPERLINK("http://x")'),
        ('@SUM(A1)', "'@SUM(A1)"),
        ('-12.50', '-12.50'),
        ('Loyer', 'Loyer'),
        (42, 42),
    ],
)
def test_neutraliser_formule(valeur, attendu):
    assert neutraliser_formule(valeur) == attendu


@pytest.mark.django_db
def test_export_csv_neutralise_motif(utilisateur, lien_bob, staff_user):
    executer_virement(
        emetteur=utilisateur,
        beneficiaire_id=lien_bob.pk,
        montant='10.00',
        motif='=HYPERLINK("http://site-malveillant.example","Cliquez")',
    )
    export = exporter(administrateur=staff_user, type_export='virements', format_export='csv')
    assert "'=HYPERLINK" in export['content']


# ---------------------------------------------------------------------------
# F8 — Force brute et CSRF sur la connexion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(CONNEXION_MAX_ECHECS=3)
def test_blocage_apres_echecs(utilisateur):
    web = Client()
    for _ in range(3):
        web.post(reverse('accounts:connexion'), {'username': 'alice', 'password': 'faux'})
    response = web.post(
        reverse('accounts:connexion'), {'username': 'alice', 'password': MOT_DE_PASSE}
    )
    assert 'Trop de tentatives' in response.content.decode()
    assert '_auth_user_id' not in web.session


@pytest.mark.django_db
@override_settings(CONNEXION_MAX_ECHECS=1)
def test_blocage_par_adresse_ip(utilisateur):
    web = Client(REMOTE_ADDR='203.0.113.9')
    for i in range(4):
        web.post(reverse('accounts:connexion'), {'username': f'x{i}', 'password': 'faux'})
    response = web.post(
        reverse('accounts:connexion'), {'username': 'alice', 'password': MOT_DE_PASSE}
    )
    assert 'Trop de tentatives' in response.content.decode()


@pytest.mark.django_db
def test_connexion_api_exige_csrf(utilisateur):
    api = APIClient(enforce_csrf_checks=True)
    corps = {'username': 'alice', 'password': MOT_DE_PASSE}
    assert api.post('/api/auth/connexion/', corps, format='json').status_code == 403
    jeton = api.get('/api/auth/csrf/').json()['csrfToken']
    response = api.post('/api/auth/connexion/', corps, format='json', HTTP_X_CSRFTOKEN=jeton)
    assert response.status_code == 200


@pytest.mark.django_db
def test_inscription_api(db):
    api = APIClient()
    response = api.post(
        '/api/auth/inscription/',
        {
            'username': 'dan',
            'password': MOT_DE_PASSE,
            'password_confirm': MOT_DE_PASSE,
            'prenom': 'Dan',
            'nom': 'Roux',
            'email': 'dan@example.com',
        },
        format='json',
    )
    assert response.status_code == 201
    assert 'password' not in json.dumps(response.json())


# ---------------------------------------------------------------------------
# F9 — Adresse IP fiable
# ---------------------------------------------------------------------------


class _Requete:
    def __init__(self, meta):
        self.META = meta


def test_x_forwarded_for_ignore_par_defaut():
    req = _Requete({'REMOTE_ADDR': '10.0.0.5', 'HTTP_X_FORWARDED_FOR': '1.2.3.4'})
    assert adresse_ip_client(req) == '10.0.0.5'


@override_settings(TRUST_X_FORWARDED_FOR=True)
def test_x_forwarded_for_derriere_un_proxy_de_confiance():
    req = _Requete({'REMOTE_ADDR': '10.0.0.5', 'HTTP_X_FORWARDED_FOR': '1.2.3.4'})
    assert adresse_ip_client(req) == '1.2.3.4'


# ---------------------------------------------------------------------------
# F10 — Configuration de production
# ---------------------------------------------------------------------------

CLE_DE_TEST = 'une-vraie-cle-secrete-longue-et-aleatoire-0123456789'


def _charger_production(monkeypatch, **env):
    import importlib

    monkeypatch.setenv('DJANGO_SECRET_KEY', CLE_DE_TEST)
    monkeypatch.setenv('DJANGO_ALLOWED_HOSTS', 'finance.example')
    import config.settings.production as production

    for nom, valeur in env.items():
        if valeur is None:
            monkeypatch.delenv(nom, raising=False)
        else:
            monkeypatch.setenv(nom, valeur)
    return importlib.reload(production)


def test_production_refuse_de_demarrer_sans_cle_secrete(monkeypatch):
    with pytest.raises(ImproperlyConfigured):
        _charger_production(monkeypatch, DJANGO_SECRET_KEY=None)


def test_production_active_les_protections_https(monkeypatch):
    module = _charger_production(monkeypatch)
    assert module.DEBUG is False
    assert module.SESSION_COOKIE_SECURE is True
    assert module.SECURE_HSTS_SECONDS > 0


# ---------------------------------------------------------------------------
# Comptes de démonstration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_creer_comptes_demo():
    from django.core.management import call_command

    call_command('creer_comptes_demo')
    call_command('creer_comptes_demo')  # idempotent
    alice = Utilisateur.objects.get(user__username='alice')
    assert alice.wallet.solde > 0
    assert alice.beneficiaires.exists()


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_creer_comptes_demo_interdit_hors_debug():
    from django.core.management import call_command
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command('creer_comptes_demo')

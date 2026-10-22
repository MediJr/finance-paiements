"""
Tests de configuration et de démarrage du projet.

Ces tests vérifient que l'environnement technique est correctement initialisé.
Aucune logique métier n'est couverte au Sprint 0.
"""

from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import Client


def test_database_configuration():
    """Vérifie que la base de données est configurée."""
    db = settings.DATABASES['default']
    assert db['ENGINE'] in (
        'django.db.backends.postgresql',
        'django.db.backends.sqlite3',
    )


def test_installed_apps():
    """Vérifie que les applications techniques de base sont installées."""
    assert 'django.contrib.auth' in settings.INSTALLED_APPS
    assert 'rest_framework' in settings.INSTALLED_APPS
    assert 'accounts' in settings.INSTALLED_APPS
    assert 'wallets' in settings.INSTALLED_APPS
    assert 'historique' in settings.INSTALLED_APPS
    assert 'beneficiaires' in settings.INSTALLED_APPS
    assert 'virements' in settings.INSTALLED_APPS
    assert 'paiements' in settings.INSTALLED_APPS
    assert 'administration' in settings.INSTALLED_APPS
    assert 'api' in settings.INSTALLED_APPS


def test_django_configuration_is_valid():
    """Vérifie que la configuration Django ne présente aucune erreur."""
    out = StringIO()
    call_command('check', stdout=out)
    assert 'System check identified no issues' in out.getvalue()


def test_api_url_prefix_is_accessible():
    """Vérifie que le préfixe /api/ est routé sans erreur."""
    client = Client()
    response = client.get('/api/')
    assert response.status_code == 200
    data = response.json()
    assert data['application'] == 'finance-paiements'
    assert data['status'] == 'ready'


def test_drf_is_configured():
    """Vérifie la configuration de base de Django REST Framework."""
    assert 'DEFAULT_AUTHENTICATION_CLASSES' in settings.REST_FRAMEWORK
    assert 'DEFAULT_PERMISSION_CLASSES' in settings.REST_FRAMEWORK


def test_root_redirects_to_login_when_anonymous():
    """La racine redirige vers la connexion si l'utilisateur n'est pas authentifié."""
    client = Client()
    response = client.get('/')
    assert response.status_code in (301, 302)
    assert '/comptes/connexion/' in response.url


def test_auth_password_validators_configured():
    """Vérifie que les validateurs de mot de passe Django sont actifs."""
    assert len(settings.AUTH_PASSWORD_VALIDATORS) >= 1

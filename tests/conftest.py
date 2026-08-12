"""
Configuration pytest pour l'application Finance (11-finance).
"""

import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

from accounts.services import create_utilisateur

APP_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = APP_ROOT / 'backend'

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

User = get_user_model()


@pytest.fixture
def app_root():
    """Retourne le répertoire racine de l'application."""
    return APP_ROOT


@pytest.fixture
def utilisateur(db):
    """Utilisateur métier de test avec Wallet automatique."""
    return create_utilisateur(
        username='alice',
        password='MotDePasseFort123!',
        prenom='Alice',
        nom='Martin',
        email='alice@example.com',
        telephone='0601020304',
    )


@pytest.fixture
def autre_utilisateur(db):
    """Second utilisateur métier (destinataire / autre propriétaire)."""
    return create_utilisateur(
        username='bob',
        password='MotDePasseFort123!',
        prenom='Bob',
        nom='Dupont',
        email='bob@example.com',
    )


@pytest.fixture
def staff_user(db):
    """Utilisateur staff pour l'administration Django."""
    return User.objects.create_user(
        username='admin_finance',
        password='MotDePasseFort123!',
        email='admin@example.com',
        is_staff=True,
        is_superuser=True,
    )

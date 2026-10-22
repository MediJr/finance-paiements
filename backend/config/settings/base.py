"""
Configuration Django de base — Finance Paiements.

Ce module centralise les paramètres communs à tous les environnements.
Aucune logique métier n'est définie ici (Sprint 0).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Répertoire backend/ (contient manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Répertoire racine du projet
APP_ROOT = BASE_DIR.parent

# Permet l'import des modules situés à la racine de l'application (api/, etc.)
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

load_dotenv(APP_ROOT / '.env')

SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-only-change-in-production',
)

# Sûr par défaut : le mode debug doit être activé explicitement (development.py).
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'accounts',
    'wallets',
    'historique',
    'beneficiaires',
    'virements',
    'paiements',
    'administration',
    'observabilite',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'administration.middleware.SecurityParametresMiddleware',
    'observabilite.middleware.ObservabiliteExceptionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [APP_ROOT / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'finance'),
        'USER': os.getenv('POSTGRES_USER', 'finance'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'finance'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5433'),
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [APP_ROOT / 'frontend' / 'static']
STATIC_ROOT = APP_ROOT / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = APP_ROOT / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentification : espace client dédié (le site /admin/ reste réservé au personnel)
LOGIN_URL = '/comptes/connexion/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/comptes/connexion/'


def _env_int(nom: str, defaut: int) -> int:
    return int(os.getenv(nom, str(defaut)))


# Sécurité — protection contre la force brute sur la connexion
CONNEXION_MAX_ECHECS = _env_int('CONNEXION_MAX_ECHECS', 5)
CONNEXION_DUREE_BLOCAGE_MINUTES = _env_int('CONNEXION_DUREE_BLOCAGE_MINUTES', 15)

# N'activer que derrière un reverse proxy de confiance (sinon l'IP est falsifiable).
TRUST_X_FORWARDED_FOR = os.getenv('TRUST_X_FORWARDED_FOR', 'False').lower() in (
    'true',
    '1',
    'yes',
)

# Cache (compteurs de tentatives de connexion). Utiliser Redis/Memcached
# en production multi-processus.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'finance',
    },
}

# En-têtes de sécurité valables dans tous les environnements
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

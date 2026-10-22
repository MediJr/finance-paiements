"""
Configuration Django pour la production.

Usage : DJANGO_SETTINGS_MODULE=config.settings.production

Refuse de démarrer sans clé secrète ni hôtes autorisés, et active
les protections HTTPS (cookies sécurisés, HSTS, redirection SSL).
Vérification : python backend/manage.py check --deploy
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY or SECRET_KEY.startswith(('django-insecure', 'change-me')):
    raise ImproperlyConfigured('DJANGO_SECRET_KEY doit être définie pour la production.')

if not os.getenv('DJANGO_ALLOWED_HOSTS'):
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS doit être définie pour la production.')

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'True').lower() in (
    'true',
    '1',
    'yes',
)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Fichiers statiques servis par WhiteNoise (pas de serveur dédié nécessaire).
MIDDLEWARE = [  # noqa: F405
    MIDDLEWARE[0],  # noqa: F405  (SecurityMiddleware en premier)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    *MIDDLEWARE[1:],  # noqa: F405
]
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

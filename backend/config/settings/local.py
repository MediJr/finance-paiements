"""
Démarrage rapide sans Docker ni PostgreSQL (SQLite fichier).

Usage :
  set DJANGO_SETTINGS_MODULE=config.settings.local      (Windows)
  export DJANGO_SETTINGS_MODULE=config.settings.local   (Linux / macOS)

Les tests de concurrence (verrous de ligne) nécessitent PostgreSQL :
voir docs/tests.md.
"""

from .development import *  # noqa: F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    },
}

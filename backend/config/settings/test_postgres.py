"""
Tests contre PostgreSQL réel (verrous select_for_update effectifs).

Usage :
  pytest --ds=config.settings.test_postgres
"""

from .base import *  # noqa: F403

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'finance'),  # noqa: F405
        'USER': os.getenv('POSTGRES_USER', 'finance'),  # noqa: F405
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'finance'),  # noqa: F405
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),  # noqa: F405
        'PORT': os.getenv('POSTGRES_PORT', '5433'),  # noqa: F405
        'TEST': {'NAME': os.getenv('POSTGRES_TEST_DB', 'test_finance')},  # noqa: F405
    },
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

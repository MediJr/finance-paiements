from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Utilisateurs'

    def ready(self):
        # Enregistrement des signaux (délégation aux services).
        from . import signals  # noqa: F401

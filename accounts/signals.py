"""
Signaux du module comptes.

Toute règle métier reste dans les services ; les signaux ne font que déléguer.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Utilisateur
from wallets.services.wallet_service import create_wallet_for_utilisateur


@receiver(post_save, sender=Utilisateur)
def ensure_wallet_on_utilisateur_created(sender, instance, created, **kwargs):
    """Crée automatiquement un Wallet à la création d'un utilisateur métier."""
    if created:
        create_wallet_for_utilisateur(instance)

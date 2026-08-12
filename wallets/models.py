"""
Modèles du module Wallet (portefeuille).
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from accounts.models import Utilisateur


class Wallet(models.Model):
    """
    Portefeuille numérique associé à un unique utilisateur métier.

    Aucune opération financière n'est implémentée au Sprint 1.
    """

    class Statut(models.TextChoices):
        ACTIF = 'actif', 'Actif'
        INACTIF = 'inactif', 'Inactif'

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='propriétaire',
    )
    solde = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='solde',
    )
    devise = models.CharField(max_length=3, default='EUR', verbose_name='devise')
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIF,
        verbose_name='statut',
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name='date de création',
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name='date de mise à jour',
    )

    class Meta:
        verbose_name = 'wallet'
        verbose_name_plural = 'wallets'
        ordering = ['-date_creation']

    def __str__(self):
        return f'Wallet #{self.pk} — {self.utilisateur}'

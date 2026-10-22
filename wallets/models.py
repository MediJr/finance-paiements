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


class Alimentation(models.Model):
    """
    Alimentation d'un Wallet par carte bancaire (passerelle simulée).

    Seul un libellé masqué de la carte est conservé. Chaque tentative est
    enregistrée, qu'elle soit acceptée ou refusée par la passerelle.
    """

    class Statut(models.TextChoices):
        ACCEPTEE = 'acceptee', 'Acceptée'
        REFUSEE = 'refusee', 'Refusée'

    reference = models.CharField(max_length=64, unique=True, verbose_name='référence')
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='alimentations',
        verbose_name='wallet',
    )
    montant = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='montant',
    )
    devise = models.CharField(max_length=3, default='EUR', verbose_name='devise')
    statut = models.CharField(max_length=20, choices=Statut.choices, verbose_name='statut')
    carte_masquee = models.CharField(max_length=20, verbose_name='carte (masquée)')
    motif_refus = models.CharField(max_length=255, blank=True, default='', verbose_name='motif de refus')
    cle_idempotence = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="clé d'idempotence",
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='date de création')

    class Meta:
        verbose_name = 'alimentation'
        verbose_name_plural = 'alimentations'
        ordering = ['-date_creation']
        constraints = [
            models.UniqueConstraint(
                fields=['wallet', 'cle_idempotence'],
                condition=models.Q(cle_idempotence__isnull=False),
                name='alimentation_cle_idempotence_unique',
            ),
        ]

    def __str__(self):
        return f'{self.reference} — {self.montant} {self.devise} ({self.statut})'

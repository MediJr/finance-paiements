"""
Modèles — paiements et remboursements.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from wallets.models import Wallet


class Paiement(models.Model):
    """Paiement d'un Wallet payeur vers un Wallet bénéficiaire."""

    class Statut(models.TextChoices):
        REUSSI = 'reussi', 'Réussi'
        REMBOURSE_PARTIELLEMENT = 'rembourse_partiellement', 'Remboursé partiellement'
        REMBOURSE = 'rembourse', 'Remboursé'

    reference = models.CharField(max_length=64, unique=True, verbose_name='référence')
    wallet_payeur = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='paiements_emis',
        verbose_name='wallet payeur',
    )
    wallet_beneficiaire = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='paiements_recus',
        verbose_name='wallet bénéficiaire',
    )
    montant = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='montant',
    )
    montant_rembourse = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='montant remboursé',
    )
    devise = models.CharField(max_length=3, default='EUR', verbose_name='devise')
    statut = models.CharField(
        max_length=30,
        choices=Statut.choices,
        default=Statut.REUSSI,
        verbose_name='statut',
    )
    motif = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='motif',
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='date de création')
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name='date de mise à jour')

    class Meta:
        verbose_name = 'paiement'
        verbose_name_plural = 'paiements'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.reference} — {self.montant} {self.devise}'

    @property
    def montant_restant(self) -> Decimal:
        """Montant encore remboursable."""
        return (self.montant - self.montant_rembourse).quantize(Decimal('0.01'))


class Remboursement(models.Model):
    """Remboursement rattaché à un paiement existant."""

    class Statut(models.TextChoices):
        REUSSI = 'reussi', 'Réussi'

    reference = models.CharField(max_length=64, unique=True, verbose_name='référence')
    paiement = models.ForeignKey(
        Paiement,
        on_delete=models.PROTECT,
        related_name='remboursements',
        verbose_name='paiement',
    )
    wallet_remboursant = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='remboursements_emis',
        verbose_name='wallet remboursant',
    )
    wallet_rembourse = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='remboursements_recus',
        verbose_name='wallet remboursé',
    )
    montant = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='montant',
    )
    devise = models.CharField(max_length=3, default='EUR', verbose_name='devise')
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.REUSSI,
        verbose_name='statut',
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='date de création')
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name='date de mise à jour')

    class Meta:
        verbose_name = 'remboursement'
        verbose_name_plural = 'remboursements'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.reference} — {self.montant} {self.devise}'

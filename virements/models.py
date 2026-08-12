"""
Modèles — virements entre Wallets.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from wallets.models import Wallet


class Virement(models.Model):
    """
    Virement financier entre un Wallet émetteur et un Wallet bénéficiaire.

    L'exécution métier est exclusivement gérée par le service des virements.
    """

    class Statut(models.TextChoices):
        REUSSI = 'reussi', 'Réussi'
        ECHOUE = 'echoue', 'Échoué'

    reference = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='référence',
    )
    wallet_emetteur = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='virements_emis',
        verbose_name='wallet émetteur',
    )
    wallet_beneficiaire = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='virements_recus',
        verbose_name='wallet bénéficiaire',
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
    motif = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='motif',
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
        verbose_name = 'virement'
        verbose_name_plural = 'virements'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.reference} — {self.montant} {self.devise}'

"""
Modèles — historique des opérations financières.

Sprint 2 : structure d'enregistrement uniquement.
Aucune logique de débit/crédit ni modification de solde.
"""

from django.db import models

from wallets.models import Wallet


class HistoriqueOperation(models.Model):
    """
    Événement financier générique associé à un Wallet.

    Conçu pour accueillir les opérations des sprints suivants
    (paiements, virements, remboursements, etc.).
    """

    class TypeOperation(models.TextChoices):
        CREDIT = 'credit', 'Crédit'
        DEBIT = 'debit', 'Débit'
        VIREMENT = 'virement', 'Virement'
        PAIEMENT = 'paiement', 'Paiement'
        REMBOURSEMENT = 'remboursement', 'Remboursement'
        AUTRE = 'autre', 'Autre'

    class Statut(models.TextChoices):
        ENREGISTREE = 'enregistree', 'Enregistrée'
        EN_COURS = 'en_cours', 'En cours'
        REUSSIE = 'reussie', 'Réussie'
        ECHOUEE = 'echouee', 'Échouée'
        ANNULEE = 'annulee', 'Annulée'

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='operations',
        verbose_name='wallet',
    )
    type_operation = models.CharField(
        max_length=30,
        choices=TypeOperation.choices,
        verbose_name='type d\'opération',
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ENREGISTREE,
        verbose_name='statut',
    )
    description = models.TextField(blank=True, default='', verbose_name='description')
    montant = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='montant',
    )
    devise = models.CharField(max_length=3, default='EUR', verbose_name='devise')
    reference = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='référence',
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
        verbose_name = 'opération historique'
        verbose_name_plural = 'historique des opérations'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.reference} — {self.get_type_operation_display()}'

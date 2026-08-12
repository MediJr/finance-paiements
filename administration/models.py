"""
Modèles — paramètres globaux et journal d'administration.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ParametresApplication(models.Model):
    """
    Paramètres globaux (singleton logique, pk=1).
    """

    nom_application = models.CharField(
        max_length=200,
        default='11-finance',
        verbose_name='nom de l\'application',
    )
    devise_par_defaut = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name='devise par défaut',
    )
    mode_maintenance = models.BooleanField(
        default=False,
        verbose_name='mode maintenance',
    )
    montant_virement_max = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='montant maximum d\'un virement',
    )
    montant_paiement_max = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='montant maximum d\'un paiement',
    )
    delai_session_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name='durée de session (minutes)',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'paramètres application'
        verbose_name_plural = 'paramètres application'

    def __str__(self):
        return f'Paramètres — {self.nom_application}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Singleton : suppression interdite.
        return


class JournalAdministration(models.Model):
    """
    Journal simple des actions d'administration (Security by Design).

    Ne remplace pas un SIEM : traçabilité locale des actions sensibles uniquement.
    """

    class Action(models.TextChoices):
        MODIFICATION_PARAMETRES = 'modification_parametres', 'Modification des paramètres'
        ACTIVATION_UTILISATEUR = 'activation_utilisateur', 'Activation utilisateur'
        DESACTIVATION_UTILISATEUR = (
            'desactivation_utilisateur',
            'Désactivation utilisateur',
        )
        ACCES_ADMIN = 'acces_admin', 'Accès administration'
        AUTRE = 'autre', 'Autre'

    administrateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='journaux_administration',
        verbose_name='administrateur',
    )
    action = models.CharField(
        max_length=64,
        choices=Action.choices,
        verbose_name='action',
    )
    details = models.TextField(blank=True, default='', verbose_name='détails')
    cible_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='type de cible',
    )
    cible_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='identifiant cible',
    )
    adresse_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='adresse IP',
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='date')

    class Meta:
        verbose_name = 'journal administration'
        verbose_name_plural = 'journaux administration'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.action} — {self.administrateur_id} @ {self.date_creation}'

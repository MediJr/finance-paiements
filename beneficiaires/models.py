"""
Modèles — bénéficiaires (destinataires autorisés).

Sprint 3 : gestion de la liste uniquement.
Aucune opération financière.
"""

from django.db import models

from accounts.models import Utilisateur


class Beneficiaire(models.Model):
    """
    Lien entre un utilisateur propriétaire et un utilisateur destinataire.

    Un bénéficiaire inactif ne pourra pas être sélectionné
    pour les futurs virements (règle centralisée dans le service).
    """

    class Statut(models.TextChoices):
        ACTIF = 'actif', 'Actif'
        INACTIF = 'inactif', 'Inactif'

    proprietaire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='beneficiaires',
        verbose_name='propriétaire',
    )
    utilisateur_beneficiaire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='apparitions_beneficiaire',
        verbose_name='bénéficiaire',
    )
    alias = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name='alias',
    )
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
        verbose_name = 'bénéficiaire'
        verbose_name_plural = 'bénéficiaires'
        ordering = ['alias', 'utilisateur_beneficiaire__nom']
        constraints = [
            models.UniqueConstraint(
                fields=['proprietaire', 'utilisateur_beneficiaire'],
                name='uniq_beneficiaire_par_proprietaire',
            ),
        ]

    def __str__(self):
        label = self.alias or str(self.utilisateur_beneficiaire)
        return f'{label} (propriétaire #{self.proprietaire_id})'

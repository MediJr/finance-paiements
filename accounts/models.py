"""
Modèles du module utilisateurs métier.

L'authentification reste gérée par django.contrib.auth.User.
"""

from django.conf import settings
from django.db import models


class Utilisateur(models.Model):
    """
    Utilisateur métier de la plateforme de paiements.

    Lié en OneToOne au User Django (Sprint 0) sans le remplacer.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='utilisateur',
        verbose_name='compte d\'authentification',
    )
    prenom = models.CharField(max_length=150, verbose_name='prénom')
    nom = models.CharField(max_length=150, verbose_name='nom')
    email = models.EmailField(verbose_name='e-mail')
    telephone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name='téléphone',
    )
    est_actif = models.BooleanField(default=True, verbose_name='actif')
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name='date de création',
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name='date de mise à jour',
    )

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f'{self.prenom} {self.nom} ({self.email})'

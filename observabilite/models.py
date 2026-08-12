"""
Modèle générique de journalisation — Prototype 4 Sprint 9.

Trace d'audit en lecture seule. Pas de SIEM / Analytics.
"""

from django.conf import settings
from django.db import models


class Evenement(models.Model):
    """Événement d'observabilité (métier ou technique)."""

    class Niveau(models.TextChoices):
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        SECURITY = 'SECURITY', 'Security'

    date_creation = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='date',
    )
    type_evenement = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="type d'événement",
    )
    niveau = models.CharField(
        max_length=20,
        choices=Niveau.choices,
        default=Niveau.INFO,
        db_index=True,
        verbose_name='niveau',
    )
    module = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name='module',
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evenements_observabilite',
        verbose_name='utilisateur',
    )
    description = models.TextField(verbose_name='description')
    contexte = models.JSONField(default=dict, blank=True, verbose_name='contexte')
    adresse_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='adresse IP',
    )
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name='User-Agent',
    )

    class Meta:
        verbose_name = 'événement'
        verbose_name_plural = 'événements'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['-date_creation', 'niveau']),
            models.Index(fields=['module', 'type_evenement']),
        ]

    def __str__(self):
        return f'[{self.niveau}] {self.type_evenement} — {self.date_creation}'

    def save(self, *args, **kwargs):
        # Trace d'audit : pas de mise à jour après création.
        if self.pk is not None:
            raise ValueError('Un événement d\'observabilité ne peut pas être modifié.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Un événement d\'observabilité ne peut pas être supprimé.')

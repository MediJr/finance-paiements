# Generated manually for Sprint 7 — JournalAdministration

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalAdministration',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'action',
                    models.CharField(
                        choices=[
                            ('modification_parametres', 'Modification des paramètres'),
                            ('activation_utilisateur', 'Activation utilisateur'),
                            ('desactivation_utilisateur', 'Désactivation utilisateur'),
                            ('acces_admin', 'Accès administration'),
                            ('autre', 'Autre'),
                        ],
                        max_length=64,
                        verbose_name='action',
                    ),
                ),
                (
                    'details',
                    models.TextField(blank=True, default='', verbose_name='détails'),
                ),
                (
                    'cible_type',
                    models.CharField(
                        blank=True,
                        default='',
                        max_length=100,
                        verbose_name='type de cible',
                    ),
                ),
                (
                    'cible_id',
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name='identifiant cible',
                    ),
                ),
                (
                    'adresse_ip',
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        verbose_name='adresse IP',
                    ),
                ),
                (
                    'date_creation',
                    models.DateTimeField(auto_now_add=True, verbose_name='date'),
                ),
                (
                    'administrateur',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='journaux_administration',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='administrateur',
                    ),
                ),
            ],
            options={
                'verbose_name': 'journal administration',
                'verbose_name_plural': 'journaux administration',
                'ordering': ['-date_creation'],
            },
        ),
    ]

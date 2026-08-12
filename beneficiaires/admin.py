"""Administration Django — bénéficiaires."""

from django.contrib import admin

from beneficiaires.models import Beneficiaire


@admin.register(Beneficiaire)
class BeneficiaireAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'proprietaire',
        'utilisateur_beneficiaire',
        'alias',
        'statut',
        'date_creation',
        'date_mise_a_jour',
    )
    list_filter = ('statut',)
    search_fields = (
        'alias',
        'proprietaire__email',
        'proprietaire__nom',
        'proprietaire__prenom',
        'utilisateur_beneficiaire__email',
        'utilisateur_beneficiaire__nom',
        'utilisateur_beneficiaire__prenom',
    )
    list_editable = ('statut',)
    raw_id_fields = ('proprietaire', 'utilisateur_beneficiaire')
    readonly_fields = ('date_creation', 'date_mise_a_jour')
    ordering = ('-date_creation',)

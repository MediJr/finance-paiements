"""Administration Django — virements (consultation uniquement)."""

from django.contrib import admin

from virements.models import Virement


@admin.register(Virement)
class VirementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reference',
        'wallet_emetteur',
        'wallet_beneficiaire',
        'montant',
        'devise',
        'statut',
        'date_creation',
    )
    list_filter = ('statut', 'devise')
    search_fields = (
        'reference',
        'motif',
        'wallet_emetteur__utilisateur__email',
        'wallet_beneficiaire__utilisateur__email',
    )
    readonly_fields = (
        'reference',
        'wallet_emetteur',
        'wallet_beneficiaire',
        'montant',
        'devise',
        'statut',
        'motif',
        'date_creation',
        'date_mise_a_jour',
    )
    ordering = ('-date_creation',)
    date_hierarchy = 'date_creation'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

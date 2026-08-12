"""Administration Django — paiements et remboursements (consultation)."""

from django.contrib import admin

from paiements.models import Paiement, Remboursement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reference',
        'wallet_payeur',
        'wallet_beneficiaire',
        'montant',
        'montant_rembourse',
        'devise',
        'statut',
        'date_creation',
    )
    list_filter = ('statut', 'devise')
    search_fields = (
        'reference',
        'motif',
        'wallet_payeur__utilisateur__email',
        'wallet_beneficiaire__utilisateur__email',
    )
    readonly_fields = [f.name for f in Paiement._meta.fields]
    ordering = ('-date_creation',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Remboursement)
class RemboursementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reference',
        'paiement',
        'wallet_remboursant',
        'wallet_rembourse',
        'montant',
        'devise',
        'statut',
        'date_creation',
    )
    list_filter = ('statut', 'devise')
    search_fields = (
        'reference',
        'paiement__reference',
        'wallet_remboursant__utilisateur__email',
        'wallet_rembourse__utilisateur__email',
    )
    readonly_fields = [f.name for f in Remboursement._meta.fields]
    ordering = ('-date_creation',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

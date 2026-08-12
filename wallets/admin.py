"""Administration Django — Wallets."""

from django.contrib import admin

from wallets.models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'utilisateur',
        'solde',
        'devise',
        'statut',
        'date_creation',
        'date_mise_a_jour',
    )
    list_filter = ('statut', 'devise')
    search_fields = (
        'utilisateur__prenom',
        'utilisateur__nom',
        'utilisateur__email',
    )
    readonly_fields = (
        'utilisateur',
        'solde',
        'devise',
        'statut',
        'date_creation',
        'date_mise_a_jour',
    )
    ordering = ('-date_creation',)

    def has_add_permission(self, request):
        # Les Wallets sont créés exclusivement via le service métier.
        return False

    def has_change_permission(self, request, obj=None):
        # Consultation uniquement — aucune modification de solde.
        return False

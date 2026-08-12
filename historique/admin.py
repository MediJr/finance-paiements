"""Administration Django — historique des opérations (consultation)."""

from django.contrib import admin

from historique.models import HistoriqueOperation


@admin.register(HistoriqueOperation)
class HistoriqueOperationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reference',
        'wallet',
        'type_operation',
        'statut',
        'montant',
        'devise',
        'date_creation',
    )
    list_filter = ('type_operation', 'statut', 'devise')
    search_fields = (
        'reference',
        'description',
        'wallet__utilisateur__email',
        'wallet__utilisateur__nom',
    )
    readonly_fields = (
        'wallet',
        'type_operation',
        'statut',
        'description',
        'montant',
        'devise',
        'reference',
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
        # Aucune suppression via l'interface métier / admin.
        return False

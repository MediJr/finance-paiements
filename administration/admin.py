"""Administration Django — paramètres et journal."""

from django.contrib import admin

from administration.models import JournalAdministration, ParametresApplication


@admin.register(ParametresApplication)
class ParametresApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'nom_application',
        'devise_par_defaut',
        'mode_maintenance',
        'montant_virement_max',
        'montant_paiement_max',
        'plafond_journalier',
        'montant_alimentation_max',
        'delai_session_minutes',
        'date_mise_a_jour',
    )
    readonly_fields = ('date_creation', 'date_mise_a_jour')

    def has_add_permission(self, request):
        # Singleton : un seul enregistrement.
        return not ParametresApplication.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JournalAdministration)
class JournalAdministrationAdmin(admin.ModelAdmin):
    list_display = (
        'date_creation',
        'administrateur',
        'action',
        'cible_type',
        'cible_id',
        'adresse_ip',
    )
    list_filter = ('action',)
    search_fields = ('details', 'administrateur__username')
    readonly_fields = (
        'administrateur',
        'action',
        'details',
        'cible_type',
        'cible_id',
        'adresse_ip',
        'date_creation',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

"""Administration Django — événements (lecture seule)."""

from django.contrib import admin

from observabilite.models import Evenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date_creation',
        'niveau',
        'module',
        'type_evenement',
        'utilisateur',
        'adresse_ip',
    )
    list_filter = ('niveau', 'module', 'type_evenement')
    search_fields = ('description', 'type_evenement', 'module')
    readonly_fields = (
        'date_creation',
        'type_evenement',
        'niveau',
        'module',
        'utilisateur',
        'description',
        'contexte',
        'adresse_ip',
        'user_agent',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

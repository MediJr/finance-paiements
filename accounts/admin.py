"""Administration Django — utilisateurs métier."""

from django.contrib import admin

from accounts.models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'prenom',
        'nom',
        'email',
        'telephone',
        'est_actif',
        'date_creation',
        'date_mise_a_jour',
    )
    list_filter = ('est_actif',)
    search_fields = ('prenom', 'nom', 'email', 'telephone', 'user__username')
    readonly_fields = ('prenom', 'nom', 'email', 'telephone', 'date_creation', 'date_mise_a_jour')
    list_editable = ('est_actif',)
    raw_id_fields = ('user',)
    ordering = ('nom', 'prenom')

    def has_add_permission(self, request):
        # Création via service métier / parcours applicatif.
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Aligne le compte d'authentification sur l'état métier.
        if obj.user.is_active != obj.est_actif:
            obj.user.is_active = obj.est_actif
            obj.user.save(update_fields=['is_active'])


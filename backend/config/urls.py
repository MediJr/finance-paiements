"""
Configuration des URLs principales du projet Django.
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    """Redirige la racine vers la liste des utilisateurs."""
    if request.user.is_authenticated:
        return redirect('accounts:utilisateur-list')
    return redirect('admin:login')


urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('wallets.urls')),
    path('', include('historique.urls')),
    path('', include('beneficiaires.urls')),
    path('', include('virements.urls')),
    path('', include('paiements.urls')),
    path('', include('administration.urls')),
    path('', include('observabilite.urls')),
    path('api/', include('api.urls')),
]

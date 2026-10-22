"""
Configuration des URLs principales du projet Django.
"""

from django.contrib import admin
from django.urls import include, path

from accounts.views_auth import accueil

urlpatterns = [
    path('', accueil, name='accueil'),
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

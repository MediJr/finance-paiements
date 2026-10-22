"""Routes web — comptes clients et utilisateurs métier."""

from django.urls import path

from accounts import views, views_auth

app_name = 'accounts'

urlpatterns = [
    path('comptes/inscription/', views_auth.inscription, name='inscription'),
    path('comptes/connexion/', views_auth.connexion, name='connexion'),
    path('comptes/deconnexion/', views_auth.deconnexion, name='deconnexion'),
    path('mon-espace/', views_auth.espace_client, name='espace'),
    path('utilisateurs/', views.utilisateur_list, name='utilisateur-list'),
    path('utilisateurs/<int:pk>/', views.utilisateur_detail, name='utilisateur-detail'),
]

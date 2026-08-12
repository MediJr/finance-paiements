"""Routes web — administration."""

from django.urls import path

from administration import views

app_name = 'administration'

urlpatterns = [
    path('administration/', views.admin_index, name='index'),
    path('administration/dashboard/', views.admin_dashboard, name='dashboard'),
    path('administration/statistiques/', views.admin_statistiques, name='statistiques'),
    path('administration/rapports/', views.admin_rapports, name='rapports'),
    path('administration/exports/', views.admin_exports, name='exports'),
    path(
        'administration/exports/telecharger/',
        views.admin_export_download,
        name='export-download',
    ),
    path('administration/parametres/', views.admin_parametres, name='parametres'),
    path(
        'administration/utilisateurs/',
        views.admin_utilisateurs,
        name='utilisateurs',
    ),
    path(
        'administration/utilisateurs/<int:pk>/activer/',
        views.admin_utilisateur_activer,
        name='utilisateur-activer',
    ),
    path(
        'administration/utilisateurs/<int:pk>/desactiver/',
        views.admin_utilisateur_desactiver,
        name='utilisateur-desactiver',
    ),
    path('administration/wallets/', views.admin_wallets, name='wallets'),
    path('administration/operations/', views.admin_operations, name='operations'),
    path('administration/journal/', views.admin_journal, name='journal'),
]

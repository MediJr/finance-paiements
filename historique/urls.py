"""Routes web — historique des opérations."""

from django.urls import path

from historique import views

app_name = 'historique'

urlpatterns = [
    path('historique/', views.historique_list, name='historique-list'),
    path('historique/<int:pk>/', views.historique_detail, name='historique-detail'),
]

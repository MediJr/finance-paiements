"""Routes web — utilisateurs métier."""

from django.urls import path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('utilisateurs/', views.utilisateur_list, name='utilisateur-list'),
    path('utilisateurs/<int:pk>/', views.utilisateur_detail, name='utilisateur-detail'),
]

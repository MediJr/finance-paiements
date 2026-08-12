"""Routes web — observabilité."""

from django.urls import path

from observabilite import views

app_name = 'observabilite'

urlpatterns = [
    path(
        'administration/evenements/',
        views.evenement_list,
        name='evenement-list',
    ),
    path(
        'administration/evenements/<int:pk>/',
        views.evenement_detail,
        name='evenement-detail',
    ),
]

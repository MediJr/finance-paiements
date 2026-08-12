"""Routes web — bénéficiaires."""

from django.urls import path

from beneficiaires import views

app_name = 'beneficiaires'

urlpatterns = [
    path('beneficiaires/', views.beneficiaire_list, name='beneficiaire-list'),
    path(
        'beneficiaires/nouveau/',
        views.beneficiaire_create,
        name='beneficiaire-create',
    ),
    path(
        'beneficiaires/<int:pk>/',
        views.beneficiaire_detail,
        name='beneficiaire-detail',
    ),
    path(
        'beneficiaires/<int:pk>/modifier/',
        views.beneficiaire_update,
        name='beneficiaire-update',
    ),
]

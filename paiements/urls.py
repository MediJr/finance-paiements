"""Routes web — paiements et remboursements."""

from django.urls import path

from paiements import views

app_name = 'paiements'

urlpatterns = [
    path('paiements/', views.paiement_list, name='paiement-list'),
    path('paiements/nouveau/', views.paiement_create, name='paiement-create'),
    path('paiements/<int:pk>/', views.paiement_detail, name='paiement-detail'),
    path('remboursements/', views.remboursement_list, name='remboursement-list'),
    path(
        'remboursements/nouveau/',
        views.remboursement_create,
        name='remboursement-create',
    ),
    path(
        'remboursements/<int:pk>/',
        views.remboursement_detail,
        name='remboursement-detail',
    ),
]

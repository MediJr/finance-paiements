"""Routes web — Wallets."""

from django.urls import path

from wallets import views

app_name = 'wallets'

urlpatterns = [
    path('wallets/<int:pk>/', views.wallet_detail, name='wallet-detail'),
]

"""Routes web — Wallets."""

from django.urls import path

from wallets import views, views_alimentation

app_name = 'wallets'

urlpatterns = [
    path('wallets/alimenter/', views_alimentation.alimentation, name='alimentation'),
    path('wallets/<int:pk>/', views.wallet_detail, name='wallet-detail'),
]

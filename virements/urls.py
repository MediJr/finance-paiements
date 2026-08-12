"""Routes web — virements."""

from django.urls import path

from virements import views

app_name = 'virements'

urlpatterns = [
    path('virements/', views.virement_list, name='virement-list'),
    path('virements/nouveau/', views.virement_create, name='virement-create'),
    path('virements/<int:pk>/', views.virement_detail, name='virement-detail'),
]

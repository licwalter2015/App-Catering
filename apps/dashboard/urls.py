from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/calendario/', views.calendario, name='calendario'),
    path('panel/cotizaciones/', views.lista_cotizaciones, name='lista_cotizaciones'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('cotizar/', views.cotizador_wizard, name='cotizador_wizard'),
    path('cotizacion/<uuid:token>/', views.cotizacion_detail, name='cotizacion_detail'),
    path('cotizacion/<uuid:token>/pdf/', views.cotizacion_pdf, name='cotizacion_pdf'),
    path('calcular/', views.calcular_total, name='calcular_total'),
]

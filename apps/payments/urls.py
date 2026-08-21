from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<uuid:token>/', views.checkout, name='checkout'),
    path('pagos/webhook/', views.webhook, name='webhook'),
    path('pago/exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago/fallido/', views.pago_fallido, name='pago_fallido'),
    path('pago/pendiente/', views.pago_pendiente, name='pago_pendiente'),
]

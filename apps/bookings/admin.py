from django.contrib import admin

from apps.tenants.admin import TenantAdminMixin

from .models import Evento, FechaReservada


@admin.register(Evento)
class EventoAdmin(TenantAdminMixin):
    list_display = ('cotizacion', 'fecha', 'estado', 'created_at')
    list_filter = ('estado', 'fecha')
    search_fields = ('cotizacion__cliente__nombre', 'cotizacion__cliente__email')
    date_hierarchy = 'fecha'
    list_per_page = 50


@admin.register(FechaReservada)
class FechaReservadaAdmin(TenantAdminMixin):
    list_display = ('tenant', 'fecha', 'evento', 'created_at')
    list_filter = ('fecha',)
    search_fields = ('evento__cotizacion__cliente__nombre',)
    date_hierarchy = 'fecha'
    list_per_page = 50

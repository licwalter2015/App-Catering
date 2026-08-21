from django.contrib import admin

from apps.tenants.admin import TenantAdminMixin

from .models import Adicional, ServicioBase, ZonaEntrega


@admin.register(ServicioBase)
class ServicioBaseAdmin(TenantAdminMixin):
    list_display = ('nombre', 'precio_por_persona', 'capacidad_min', 'capacidad_max', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio_por_persona', 'is_active')
    list_per_page = 50


@admin.register(Adicional)
class AdicionalAdmin(TenantAdminMixin):
    list_display = ('nombre', 'tipo_precio', 'precio', 'is_active')
    list_filter = ('tipo_precio', 'is_active')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'is_active')
    list_per_page = 50


@admin.register(ZonaEntrega)
class ZonaEntregaAdmin(TenantAdminMixin):
    list_display = ('nombre', 'costo_traslado', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nombre',)
    list_editable = ('costo_traslado', 'is_active')
    list_per_page = 50

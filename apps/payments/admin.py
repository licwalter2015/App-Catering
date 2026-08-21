from django.contrib import admin

from apps.tenants.admin import TenantAdminMixin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(TenantAdminMixin):
    list_display = ('mp_payment_id', 'cotizacion', 'monto', 'estado', 'created_at')
    list_filter = ('estado', 'created_at')
    search_fields = ('mp_payment_id', 'cotizacion__cliente__nombre', 'cotizacion__cliente__email')
    readonly_fields = ('mp_payment_id', 'mp_preference_id', 'webhook_payload')
    list_per_page = 50

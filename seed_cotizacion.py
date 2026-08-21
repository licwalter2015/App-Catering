from apps.tenants.models import Tenant
from apps.catalog.models import ServicioBase, Adicional, ZonaEntrega
from apps.quotes.models import Cliente
from apps.quotes.services import crear_cotizacion_desde_calculo
from datetime import date

tenant = Tenant.objects.get(slug='demo')
servicio = ServicioBase.objects.filter(tenant=tenant).first()
adicionales_list = list(Adicional.objects.filter(tenant=tenant)[:2])
zona = ZonaEntrega.objects.filter(tenant=tenant).first()

cliente = Cliente.objects.create(
    tenant=tenant,
    nombre='Juan Pérez',
    email='juan@example.com',
    telefono='11-1234-5678',
)

adicionales = [{'adicional': a, 'cantidad': 1} for a in adicionales_list]

cotizacion = crear_cotizacion_desde_calculo(
    tenant=tenant,
    cliente=cliente,
    fecha_evento=date(2026, 12, 15),
    cantidad_invitados=50,
    servicio_base=servicio,
    adicionales=adicionales,
    zona_entrega=zona,
)

print(f'Cotizacion creada: #{cotizacion.id}')
print(f'Token: {cotizacion.token}')
print(f'Total: {cotizacion.total}')
print(f'Sena: {cotizacion.sena}')
print(f'Items: {cotizacion.items.count()}')

"""
Script de prueba para simular el flujo de pago y reserva.
"""
from apps.tenants.models import Tenant
from apps.catalog.models import ServicioBase, Adicional, ZonaEntrega
from apps.quotes.models import Cliente, Cotizacion
from apps.quotes.services import crear_cotizacion_desde_calculo
from apps.bookings.models import Evento, FechaReservada
from apps.payments.models import Pago
from datetime import date

tenant = Tenant.objects.get(slug='demo')
servicio = ServicioBase.objects.filter(tenant=tenant).first()
adicionales_list = list(Adicional.objects.filter(tenant=tenant)[:2])
zona = ZonaEntrega.objects.filter(tenant=tenant).first()

# Crear cliente y cotizacion
cliente = Cliente.objects.create(
    tenant=tenant,
    nombre='Maria Garcia',
    email='maria@example.com',
    telefono='11-9876-5432',
)

adicionales = [{'adicional': a, 'cantidad': 1} for a in adicionales_list]

cotizacion = crear_cotizacion_desde_calculo(
    tenant=tenant,
    cliente=cliente,
    fecha_evento=date(2026, 11, 20),
    cantidad_invitados=80,
    servicio_base=servicio,
    adicionales=adicionales,
    zona_entrega=zona,
)

print(f'Cotizacion creada: #{cotizacion.id}')
print(f'Token: {cotizacion.token}')
print(f'Estado: {cotizacion.estado}')
print(f'Total: {cotizacion.total}')
print(f'Sena: {cotizacion.sena}')

# Simular pago aprobado (sin webhook real)
print('\n--- Simulando pago aprobado ---')
from django.db import transaction, IntegrityError

try:
    with transaction.atomic():
        evento = Evento.objects.create(
            tenant=tenant,
            cotizacion=cotizacion,
            fecha=cotizacion.fecha_evento,
            estado=Evento.Estado.CONFIRMADO,
        )
        
        FechaReservada.objects.create(
            tenant=tenant,
            fecha=cotizacion.fecha_evento,
            evento=evento,
        )
        
        cotizacion.estado = Cotizacion.Estado.SENADA
        cotizacion.save()
        
        pago = Pago.objects.create(
            tenant=tenant,
            cotizacion=cotizacion,
            monto=cotizacion.sena,
            mp_payment_id='TEST_PAYMENT_123',
            mp_preference_id='TEST_PREF_456',
            estado=Pago.Estado.APROBADO,
        )
        
        print(f'Evento creado: {evento}')
        print(f'Fecha reservada: {cotizacion.fecha_evento}')
        print(f'Cotizacion estado: {cotizacion.estado}')
        print(f'Pago registrado: {pago}')
        
except IntegrityError as e:
    print(f'Error (fecha ya reservada): {e}')

# Verificar constraint anti-sobreventa
print('\n--- Probando anti-sobreventa ---')
cliente2 = Cliente.objects.create(
    tenant=tenant,
    nombre='Pedro Lopez',
    email='pedro@example.com',
)

cotizacion2 = crear_cotizacion_desde_calculo(
    tenant=tenant,
    cliente=cliente2,
    fecha_evento=date(2026, 11, 20),  # Misma fecha
    cantidad_invitados=50,
    servicio_base=servicio,
)

print(f'Cotizacion 2 creada: #{cotizacion2.id} para {cotizacion2.fecha_evento}')

try:
    with transaction.atomic():
        evento2 = Evento.objects.create(
            tenant=tenant,
            cotizacion=cotizacion2,
            fecha=cotizacion2.fecha_evento,
        )
        FechaReservada.objects.create(
            tenant=tenant,
            fecha=cotizacion2.fecha_evento,
            evento=evento2,
        )
    print('ERROR: No deberia permitir reservar la misma fecha!')
except IntegrityError:
    print('OK: Anti-sobreventa funciono - fecha ya estaba reservada')

print('\n--- Resumen ---')
print(f'Total cotizaciones: {Cotizacion.objects.filter(tenant=tenant).count()}')
print(f'Total eventos: {Evento.objects.filter(tenant=tenant).count()}')
print(f'Total fechas reservadas: {FechaReservada.objects.filter(tenant=tenant).count()}')
print(f'Total pagos: {Pago.objects.filter(tenant=tenant).count()}')

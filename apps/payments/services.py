"""
Servicio de integración con MercadoPago.
Maneja creación de preferencias y procesamiento de webhooks.
"""
import mercadopago
from django.db import transaction, IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from apps.bookings.models import Evento, FechaReservada
from apps.quotes.models import Cotizacion
from .models import Pago


def crear_preferencia_checkout(cotizacion, request):
    """
    Crea una preferencia de checkout en MercadoPago para la seña.

    Returns:
        dict con 'init_point' (URL de checkout) y 'preference_id'
    """
    tenant = cotizacion.tenant
    sdk = mercadopago.SDK(tenant.mp_access_token)

    base_url = f'{request.scheme}://{request.get_host()}'

    preference_data = {
        'items': [
            {
                'title': f'Seña - Evento {cotizacion.fecha_evento}',
                'quantity': 1,
                'unit_price': float(cotizacion.sena),
                'currency_id': 'ARS',
            }
        ],
        'payer': {
            'name': cotizacion.cliente.nombre,
            'email': cotizacion.cliente.email,
        },
        'back_urls': {
            'success': f'{base_url}/pago/exitoso/',
            'failure': f'{base_url}/pago/fallido/',
            'pending': f'{base_url}/pago/pendiente/',
        },
        'auto_return': 'approved',
        'notification_url': f'{base_url}/pagos/webhook/',
        'external_reference': str(cotizacion.token),
        'metadata': {
            'cotizacion_id': cotizacion.id,
            'tenant_id': tenant.id,
        }
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response['response']

    return {
        'init_point': preference['init_point'],
        'preference_id': preference['id'],
    }


def procesar_webhook_pago(payment_id, topic, tenant_id=None):
    """
    Procesa una notificación de webhook de MercadoPago.

    Args:
        payment_id: ID del pago en MercadoPago
        topic: tipo de notificación ('payment' o 'merchant_order')
        tenant_id: ID del tenant (opcional, se obtiene del pago)

    Returns:
        Pago instance o None si no se procesó
    """
    if topic != 'payment':
        return None

    # Obtener el tenant desde el pago si no se proporcionó
    if not tenant_id:
        # Buscar en pagos existentes o usar el primer tenant activo
        # En producción, el tenant_id debería venir en metadata
        from apps.tenants.models import Tenant
        tenant = Tenant.objects.filter(is_active=True).first()
        if not tenant:
            return None
    else:
        from apps.tenants.models import Tenant
        tenant = Tenant.objects.get(id=tenant_id)

    # Consultar el pago a la API de MercadoPago (no confiar solo en webhook)
    sdk = mercadopago.SDK(tenant.mp_access_token)
    payment_response = sdk.payment().get(payment_id)

    if payment_response['status'] != 200:
        return None

    payment_data = payment_response['response']
    status = payment_data['status']

    # Solo procesar pagos aprobados
    if status != 'approved':
        return None

    # Obtener la cotización desde external_reference
    cotizacion_token = payment_data.get('external_reference')
    if not cotizacion_token:
        return None

    try:
        cotizacion = Cotizacion.objects.get(token=cotizacion_token)
    except Cotizacion.DoesNotExist:
        return None

    # Verificar que el monto coincida con la seña
    monto_recibido = payment_data['transaction_amount']
    if abs(float(monto_recibido) - float(cotizacion.sena)) > 0.01:
        # Monto no coincide, no procesar
        return None

    # Transacción atómica: crear FechaReservada + Evento + actualizar Cotizacion + crear Pago
    try:
        with transaction.atomic():
            # Intentar reservar la fecha (falla si ya está tomada)
            evento = Evento.objects.create(
                tenant=cotizacion.tenant,
                cotizacion=cotizacion,
                fecha=cotizacion.fecha_evento,
                estado=Evento.Estado.CONFIRMADO,
            )

            FechaReservada.objects.create(
                tenant=cotizacion.tenant,
                fecha=cotizacion.fecha_evento,
                evento=evento,
            )

            # Actualizar estado de cotización
            cotizacion.estado = Cotizacion.Estado.SENADA
            cotizacion.save()

            # Registrar el pago
            pago = Pago.objects.create(
                tenant=cotizacion.tenant,
                cotizacion=cotizacion,
                monto=monto_recibido,
                mp_payment_id=str(payment_id),
                mp_preference_id=payment_data.get('preference_id', ''),
                estado=Pago.Estado.APROBADO,
                webhook_payload=payment_data,
            )

            # Enviar emails de confirmación
            _enviar_emails_confirmacion(cotizacion, evento)

            return pago

    except IntegrityError:
        # La fecha ya estaba reservada (sobreventa)
        # Marcar para reembolso
        Pago.objects.create(
            tenant=cotizacion.tenant,
            cotizacion=cotizacion,
            monto=monto_recibido,
            mp_payment_id=str(payment_id),
            mp_preference_id=payment_data.get('preference_id', ''),
            estado=Pago.Estado.REEMBOLSADO,
            webhook_payload=payment_data,
        )
        return None


def _enviar_emails_confirmacion(cotizacion, evento):
    """Envía emails de confirmación al cliente y al dueño del catering."""
    tenant = cotizacion.tenant

    # Email al cliente
    send_mail(
        subject=f'¡Fecha reservada! - {tenant.name}',
        message=f'Hola {cotizacion.cliente.nombre},\n\n'
                f'Tu evento del {cotizacion.fecha_evento} ha sido confirmado.\n'
                f'Nos vemos pronto!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[cotizacion.cliente.email],
        fail_silently=True,
    )

    # Email al dueño del catering (si tiene email configurado)
    if tenant.users.exists():
        owner = tenant.users.first()
        send_mail(
            subject=f'Nueva reserva - {cotizacion.cliente.nombre}',
            message=f'Nuevo evento confirmado:\n'
                    f'Cliente: {cotizacion.cliente.nombre}\n'
                    f'Fecha: {cotizacion.fecha_evento}\n'
                    f'Invitados: {cotizacion.cantidad_invitados}\n'
                    f'Total: ${cotizacion.total}\n'
                    f'Seña recibida: ${cotizacion.sena}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner.email],
            fail_silently=True,
        )

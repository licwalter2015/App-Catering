"""
Motor de cálculo de cotizaciones.
Lógica pura, sin dependencias de vistas ni requests.
"""
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from .models import Cotizacion, CotizacionItem


def calcular_cotizacion(servicio_base, cantidad_invitados, adicionales=None, zona_entrega=None):
    """
    Calcula el total de una cotización.

    Args:
        servicio_base: instancia de ServicioBase
        cantidad_invitados: int
        adicionales: list de dicts con {'adicional': Adicional, 'cantidad': int}
        zona_entrega: instancia de ZonaEntrega (opcional)

    Returns:
        dict con subtotal, total, seña, items (list de dicts)
    """
    items = []
    subtotal = Decimal('0.00')

    # Servicio base: precio por persona × invitados
    precio_servicio = servicio_base.precio_por_persona * cantidad_invitados
    items.append({
        'descripcion': f'{servicio_base.nombre} ({cantidad_invitados} personas)',
        'cantidad': cantidad_invitados,
        'precio_unitario': servicio_base.precio_por_persona,
        'subtotal': precio_servicio,
    })
    subtotal += precio_servicio

    # Adicionales
    if adicionales:
        for item in adicionales:
            adicional = item['adicional']
            cantidad = item.get('cantidad', 1)

            if adicional.tipo_precio == 'POR_PERSONA':
                precio_total = adicional.precio * cantidad_invitados
            elif adicional.tipo_precio == 'POR_UNIDAD':
                precio_total = adicional.precio * cantidad
            else:  # FIJO
                precio_total = adicional.precio

            items.append({
                'descripcion': adicional.nombre,
                'cantidad': cantidad,
                'precio_unitario': adicional.precio,
                'subtotal': precio_total,
            })
            subtotal += precio_total

    # Costo de traslado
    if zona_entrega:
        items.append({
            'descripcion': f'Traslado a {zona_entrega.nombre}',
            'cantidad': 1,
            'precio_unitario': zona_entrega.costo_traslado,
            'subtotal': zona_entrega.costo_traslado,
        })
        subtotal += zona_entrega.costo_traslado

    total = subtotal
    seña = total * Decimal(servicio_base.tenant.deposit_percentage) / Decimal('100')

    return {
        'subtotal': subtotal,
        'total': total,
        'sena': seña,
        'items': items,
    }


def crear_cotizacion_desde_calculo(
    tenant,
    cliente,
    fecha_evento,
    cantidad_invitados,
    servicio_base,
    adicionales=None,
    zona_entrega=None,
    dias_validez=7,
):
    """
    Crea una cotización completa con sus ítems a partir del cálculo.

    Returns:
        Cotizacion instance
    """
    calculo = calcular_cotizacion(
        servicio_base=servicio_base,
        cantidad_invitados=cantidad_invitados,
        adicionales=adicionales,
        zona_entrega=zona_entrega,
    )

    cotizacion = Cotizacion.objects.create(
        tenant=tenant,
        cliente=cliente,
        fecha_evento=fecha_evento,
        cantidad_invitados=cantidad_invitados,
        servicio_base=servicio_base,
        zona_entrega=zona_entrega,
        estado=Cotizacion.Estado.ENVIADA,
        subtotal=calculo['subtotal'],
        total=calculo['total'],
        sena=calculo['sena'],
        expira_en=timezone.now() + timedelta(days=dias_validez),
    )

    for item in calculo['items']:
        CotizacionItem.objects.create(
            cotizacion=cotizacion,
            descripcion=item['descripcion'],
            cantidad=item['cantidad'],
            precio_unitario_snapshot=item['precio_unitario'],
            subtotal=item['subtotal'],
        )

    return cotizacion

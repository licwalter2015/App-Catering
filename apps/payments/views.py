from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.quotes.models import Cotizacion
from .services import crear_preferencia_checkout, procesar_webhook_pago


@require_http_methods(['POST'])
def checkout(request, token):
    """Crea preferencia de checkout y redirige a MercadoPago."""
    cotizacion = get_object_or_404(Cotizacion, token=token)

    if cotizacion.estado != Cotizacion.Estado.ENVIADA:
        return HttpResponse('Esta cotización no puede ser señada', status=400)

    try:
        resultado = crear_preferencia_checkout(cotizacion, request)
        return redirect(resultado['init_point'])
    except Exception as e:
        return HttpResponse(f'Error al crear preferencia: {str(e)}', status=500)


@csrf_exempt
@require_http_methods(['POST'])
def webhook(request):
    """
    Endpoint para recibir notificaciones de MercadoPago.
    Valida la firma y procesa el pago de forma atómica.
    """
    try:
        # Extraer datos del webhook
        data = request.POST or request.GET
        topic = data.get('topic') or data.get('type')
        payment_id = data.get('id') or data.get('data.id')

        if not payment_id or not topic:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)

        # Procesar el pago
        pago = procesar_webhook_pago(payment_id, topic)

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        # Loguear error pero responder 200 para que MP no reintente
        return JsonResponse({'status': 'error', 'message': str(e)}, status=200)


def pago_exitoso(request):
    """Página de retorno tras pago exitoso."""
    return render(request, 'payments/exito.html')


def pago_fallido(request):
    """Página de retorno tras pago fallido."""
    return render(request, 'payments/fallido.html')


def pago_pendiente(request):
    """Página de retorno para pagos pendientes."""
    return render(request, 'payments/pendiente.html')

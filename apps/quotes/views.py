from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
import io
from xhtml2pdf import pisa

from apps.catalog.models import ServicioBase, Adicional, ZonaEntrega
from .models import Cliente, Cotizacion
from .forms import WizardForm
from .services import crear_cotizacion_desde_calculo, calcular_cotizacion


@require_http_methods(['GET', 'POST'])
def cotizador_wizard(request):
    """Wizard de cotización en 5 pasos."""
    tenant = request.tenant
    if not tenant:
        return HttpResponse('Tenant no encontrado', status=404)

    servicios = ServicioBase.objects.filter(tenant=tenant, is_active=True)
    adicionales = Adicional.objects.filter(tenant=tenant, is_active=True)
    zonas = ZonaEntrega.objects.filter(tenant=tenant, is_active=True)

    if request.method == 'POST':
        form = WizardForm(request.POST)
        if form.is_valid():
            # Obtener o crear cliente
            cliente, _ = Cliente.objects.get_or_create(
                tenant=tenant,
                email=form.cleaned_data['email'],
                defaults={
                    'nombre': form.cleaned_data['nombre'],
                    'telefono': form.cleaned_data.get('telefono', ''),
                    'notas': form.cleaned_data.get('notas', ''),
                }
            )

            # Obtener servicio base
            servicio_base = get_object_or_404(
                ServicioBase,
                id=form.cleaned_data['servicio_base'],
                tenant=tenant,
            )

            # Procesar adicionales (IDs enviados como lista)
            adicionales_seleccionados = []
            adicionales_ids = request.POST.getlist('adicionales')
            for adicional_id in adicionales_ids:
                try:
                    adicional = Adicional.objects.get(id=int(adicional_id), tenant=tenant)
                    cantidad = int(request.POST.get(f'cantidad_{adicional_id}', 1))
                    adicionales_seleccionados.append({
                        'adicional': adicional,
                        'cantidad': cantidad,
                    })
                except (Adicional.DoesNotExist, ValueError):
                    continue

            # Zona de entrega (opcional)
            zona_entrega = None
            if form.cleaned_data.get('zona_entrega'):
                zona_entrega = get_object_or_404(
                    ZonaEntrega,
                    id=form.cleaned_data['zona_entrega'],
                    tenant=tenant,
                )

            # Crear cotización
            cotizacion = crear_cotizacion_desde_calculo(
                tenant=tenant,
                cliente=cliente,
                fecha_evento=form.cleaned_data['fecha_evento'],
                cantidad_invitados=form.cleaned_data['cantidad_invitados'],
                servicio_base=servicio_base,
                adicionales=adicionales_seleccionados if adicionales_seleccionados else None,
                zona_entrega=zona_entrega,
            )

            return redirect('cotizacion_detail', token=cotizacion.token)
    else:
        form = WizardForm()

    return render(request, 'quotes/wizard.html', {
        'form': form,
        'servicios': servicios,
        'adicionales': adicionales,
        'zonas': zonas,
    })


def cotizacion_detail(request, token):
    """Vista pública de una cotización por token UUID."""
    cotizacion = get_object_or_404(Cotizacion, token=token)
    return render(request, 'quotes/detail.html', {
        'cotizacion': cotizacion,
    })


def cotizacion_pdf(request, token):
    """Genera y descarga el PDF de la cotización."""
    cotizacion = get_object_or_404(Cotizacion, token=token)

    # Renderizar HTML para PDF
    html_string = render(request, 'quotes/pdf.html', {
        'cotizacion': cotizacion,
    }).content.decode('utf-8')

    # Generar PDF
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html_string), dest=result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.id}.pdf"'
        return response

    return HttpResponse('Error generando PDF', status=500)


@require_http_methods(['POST'])
def calcular_total(request):
    """Endpoint HTMX para calcular el total en vivo."""
    tenant = request.tenant
    if not tenant:
        return HttpResponse('', status=400)

    try:
        servicio_id = int(request.POST.get('servicio_base', 0))
        cantidad_invitados = int(request.POST.get('cantidad_invitados', 0))
        adicionales_ids = request.POST.getlist('adicionales')

        servicio_base = ServicioBase.objects.get(id=servicio_id, tenant=tenant)

        adicionales_seleccionados = []
        for adicional_id in adicionales_ids:
            try:
                adicional = Adicional.objects.get(id=int(adicional_id), tenant=tenant)
                cantidad = int(request.POST.get(f'cantidad_{adicional_id}', 1))
                adicionales_seleccionados.append({
                    'adicional': adicional,
                    'cantidad': cantidad,
                })
            except (Adicional.DoesNotExist, ValueError):
                continue

        calculo = calcular_cotizacion(
            servicio_base=servicio_base,
            cantidad_invitados=cantidad_invitados,
            adicionales=adicionales_seleccionados if adicionales_seleccionados else None,
        )

        return render(request, 'quotes/_total_htmx.html', {
            'calculo': calculo,
            'tenant': tenant,
        })

    except (ServicioBase.DoesNotExist, ValueError):
        return HttpResponse('Datos inválidos', status=400)

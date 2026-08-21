from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from apps.quotes.models import Cotizacion
from apps.bookings.models import Evento
from apps.payments.models import Pago


@login_required
def dashboard(request):
    """Panel principal con métricas y resumen."""
    tenant = request.user.tenant
    if not tenant:
        return render(request, 'dashboard/no_tenant.html')

    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Métricas del mes
    cotizaciones_mes = Cotizacion.objects.filter(
        tenant=tenant,
        created_at__date__range=(inicio_mes, fin_mes)
    )

    total_cotizaciones = cotizaciones_mes.count()
    cotizaciones_senadas = cotizaciones_mes.filter(estado=Cotizacion.Estado.SENADA).count()
    tasa_conversion = (cotizaciones_senadas / total_cotizaciones * 100) if total_cotizaciones > 0 else 0

    ingresos_senas = Pago.objects.filter(
        tenant=tenant,
        estado=Pago.Estado.APROBADO,
        created_at__date__range=(inicio_mes, fin_mes)
    ).aggregate(total=Sum('monto'))['total'] or 0

    # Próximos eventos (próximos 30 días)
    proximos_eventos = Evento.objects.filter(
        tenant=tenant,
        fecha__gte=hoy,
        fecha__lte=hoy + timedelta(days=30),
        estado=Evento.Estado.CONFIRMADO
    ).select_related('cotizacion__cliente', 'cotizacion__servicio_base').order_by('fecha')[:5]

    # Cotizaciones recientes (últimas 10)
    cotizaciones_recientes = Cotizacion.objects.filter(
        tenant=tenant
    ).select_related('cliente', 'servicio_base').order_by('-created_at')[:10]

    context = {
        'total_cotizaciones': total_cotizaciones,
        'cotizaciones_senadas': cotizaciones_senadas,
        'tasa_conversion': round(tasa_conversion, 1),
        'ingresos_senas': ingresos_senas,
        'proximos_eventos': proximos_eventos,
        'cotizaciones_recientes': cotizaciones_recientes,
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def calendario(request):
    """Vista de calendario mensual de eventos."""
    tenant = request.user.tenant
    if not tenant:
        return render(request, 'dashboard/no_tenant.html')

    # Obtener mes y año de query params o usar mes actual
    hoy = timezone.now().date()
    try:
        year = int(request.GET.get('year', hoy.year))
        month = int(request.GET.get('month', hoy.month))
    except (ValueError, TypeError):
        year = hoy.year
        month = hoy.month

    # Validar rango
    if month < 1 or month > 12:
        month = hoy.month
    if year < 2020 or year > 2030:
        year = hoy.year

    inicio_mes = timezone.datetime(year, month, 1).date()
    if month == 12:
        fin_mes = timezone.datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        fin_mes = timezone.datetime(year, month + 1, 1).date() - timedelta(days=1)

    # Obtener eventos del mes
    eventos = Evento.objects.filter(
        tenant=tenant,
        fecha__range=(inicio_mes, fin_mes)
    ).select_related('cotizacion__cliente', 'cotizacion__servicio_base').order_by('fecha')

    # Construir estructura de calendario
    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    # Primer día del mes (0=Lunes, 6=Domingo)
    primer_dia_semana = inicio_mes.weekday()
    
    # Construir semanas del calendario
    semanas = []
    semana_actual = []
    
    # Días vacíos al inicio
    for _ in range(primer_dia_semana):
        semana_actual.append(None)
    
    # Días del mes
    dia_actual = inicio_mes
    while dia_actual.month == month:
        eventos_dia = [e for e in eventos if e.fecha == dia_actual]
        semana_actual.append({
            'fecha': dia_actual,
            'eventos': eventos_dia,
            'es_hoy': dia_actual == hoy,
        })
        
        if len(semana_actual) == 7:
            semanas.append(semana_actual)
            semana_actual = []
        
        dia_actual += timedelta(days=1)
    
    # Completar última semana
    while semana_actual and len(semana_actual) < 7:
        semana_actual.append(None)
    if semana_actual:
        semanas.append(semana_actual)

    # Navegación de meses
    mes_anterior = inicio_mes - timedelta(days=1)
    mes_siguiente = fin_mes + timedelta(days=1)

    nombres_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    context = {
        'year': year,
        'month': month,
        'nombre_mes': nombres_meses[month],
        'dias_semana': dias_semana,
        'semanas': semanas,
        'mes_anterior': mes_anterior,
        'mes_siguiente': mes_siguiente,
    }

    return render(request, 'dashboard/calendario.html', context)


@login_required
def lista_cotizaciones(request):
    """Lista de cotizaciones con filtros."""
    tenant = request.user.tenant
    if not tenant:
        return render(request, 'dashboard/no_tenant.html')

    cotizaciones = Cotizacion.objects.filter(
        tenant=tenant
    ).select_related('cliente', 'servicio_base').order_by('-created_at')

    # Filtros
    estado = request.GET.get('estado')
    if estado and estado in [e[0] for e in Cotizacion.Estado.choices]:
        cotizaciones = cotizaciones.filter(estado=estado)

    busqueda = request.GET.get('q')
    if busqueda:
        cotizaciones = cotizaciones.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__email__icontains=busqueda)
        )

    context = {
        'cotizaciones': cotizaciones,
        'estados': Cotizacion.Estado.choices,
        'estado_actual': estado,
        'busqueda': busqueda,
    }

    return render(request, 'dashboard/cotizaciones.html', context)

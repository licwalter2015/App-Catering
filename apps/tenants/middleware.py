from .models import Domain, Tenant


class TenantMiddleware:
    """
    Resuelve el tenant actual a partir del host de la request
    y lo expone como request.tenant (None si no hay coincidencia,
    por ejemplo en la landing pública de la plataforma).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # health check no toca DB (evita 500 si aún no migró)
        if request.path in ('/health/', '/health'):
            request.tenant = None
            return self.get_response(request)
        host = request.get_host().split(':')[0].lower()
        try:
            domain = (
                Domain.objects
                .select_related('tenant')
                .filter(domain=host)
                .first()
            )
        except Exception:
            # DB aún sin migrar (tablas no existen) -> no bloquea health/startup
            request.tenant = None
            return self.get_response(request)
        if domain and domain.tenant.is_active:
            request.tenant = domain.tenant
            return self.get_response(request)
        # Fallback demo: en Render (*.onrender.com) sin Domain configurado, usar/crear tenant demo
        if host.endswith('.onrender.com'):
            try:
                demo = Tenant.objects.filter(slug='demo', is_active=True).first()
                if not demo:
                    demo, _ = Tenant.objects.get_or_create(slug='demo', defaults={'name': 'Catering Demo', 'is_active': True})
                    # asegurar domain para host actual
                    Domain.objects.get_or_create(domain=host, defaults={'tenant': demo})
                if demo and demo.is_active:
                    request.tenant = demo
                    return self.get_response(request)
            except Exception:
                pass
        request.tenant = None
        return self.get_response(request)

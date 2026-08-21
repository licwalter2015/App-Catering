from .models import Domain


class TenantMiddleware:
    """
    Resuelve el tenant actual a partir del host de la request
    y lo expone como request.tenant (None si no hay coincidencia,
    por ejemplo en la landing pública de la plataforma).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        domain = (
            Domain.objects
            .select_related('tenant')
            .filter(domain=host)
            .first()
        )
        if domain and domain.tenant.is_active:
            request.tenant = domain.tenant
        else:
            request.tenant = None
        return self.get_response(request)

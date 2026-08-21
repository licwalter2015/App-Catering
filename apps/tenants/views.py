from django.shortcuts import render


def home(request):
    """
    Raíz del sitio: si el host corresponde a un tenant, muestra su
    portada (futuro cotizador público); si no, la landing de la plataforma.
    """
    if request.tenant:
        return render(request, 'tenants/home.html')
    return render(request, 'landing.html')

def tenant(request):
    """Expone el tenant actual a todos los templates."""
    return {'tenant': getattr(request, 'tenant', None)}

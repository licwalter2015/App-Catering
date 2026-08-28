"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# Auto-migrate en Render Free (sin Shell ni Start Command editable)
# Si las tablas no existen, las crea al arrancar el worker
if os.environ.get('RENDER'):
    try:
        import django
        django.setup()
        from django.core.management import call_command
        from django.db import connection
        # solo si faltan tablas
        with connection.cursor() as cur:
            cur.execute("SELECT 1 FROM tenants_tenant LIMIT 1")
    except Exception:
        try:
            from django.core.management import call_command
            call_command('migrate', '--no-input', verbosity=0)
        except Exception:
            pass

application = get_wsgi_application()

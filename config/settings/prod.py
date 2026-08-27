"""
Configuración de producción (VPS + Gunicorn + Nginx).
Uso: DJANGO_SETTINGS_MODULE=config.settings.prod
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = False

# Render termina SSL en su proxy; también sirve para VPS con Nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# En Render no forzar redirect a mano (el proxy ya lo hace y evita loops)
if not os.environ.get('RENDER'):
    SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Render inyecta RENDER_EXTERNAL_HOSTNAME; lo agregamos a ALLOWED_HOSTS
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
# Permitir *.onrender.com para previews
if 'RENDER' in os.environ:
    ALLOWED_HOSTS.append('.onrender.com')

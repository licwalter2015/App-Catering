"""
Configuración de desarrollo local.
Uso: python manage.py runserver (es el default de manage.py)
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# Permite probar subdominios de tenants: demo.localhost:8000
ALLOWED_HOSTS = ['*']

# Los emails se imprimen en consola en desarrollo
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

"""
Script de prueba para Sprint 5 - Dashboard
"""
from apps.accounts.models import User
from apps.tenants.models import Tenant

# Obtener el tenant demo
tenant = Tenant.objects.get(slug='demo')

# Crear usuario de prueba si no existe
user, created = User.objects.get_or_create(
    email='test@demo.com',
    defaults={
        'tenant': tenant,
        'is_active': True,
    }
)

if created:
    user.set_password('test123')
    user.save()
    print(f'Usuario creado: test@demo.com / test123')
else:
    print(f'Usuario ya existe: test@demo.com')

print(f'Tenant asignado: {tenant.name}')
print(f'\nPodés iniciar sesión en:')
print(f'  Email: test@demo.com')
print(f'  Password: test123')
print(f'\nLuego visitá: http://demo.localhost:8000/panel/')

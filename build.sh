#!/usr/bin/env bash
# Build para Render Free (también sirve local con Postgres)
set -o errexit

pip install -r requirements/prod.txt

# Tailwind: compilar CSS (si falla, no bloquea el deploy — WhiteNoise sirve el fallback)
python manage.py tailwind build --no-input || echo "tailwind build skip"

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Seed demo para que el cliente vea datos al abrir el link
python manage.py shell << 'PYEOF'
from apps.tenants.models import Tenant, Domain
from django.contrib.auth import get_user_model
User = get_user_model()
# Tenant demo + usuario demo (idempotente)
tenant, _ = Tenant.objects.get_or_create(slug="demo", defaults={"nombre": "Catering Demo", "activo": True})
Domain.objects.get_or_create(domain="demo.localhost", defaults={"tenant": tenant})
# Crear superuser demo si no existe
if not User.objects.filter(email="admin@catering.local").exists():
    u = User.objects.create_superuser(email="admin@catering.local", password="admin123", tenant=tenant)
    print(f"Superuser creado: {u.email}")
# Seed catálogo/cotizaciones si está vacío
from apps.catalog.models import ServicioBase
if ServicioBase.objects.count() == 0:
    print("Ejecutando seed del catálogo...")
    import subprocess, sys
    subprocess.run([sys.executable, "seed_cotizacion.py"], check=False)
PYEOF

echo "Build OK"

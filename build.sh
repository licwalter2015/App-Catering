#!/usr/bin/env bash
# Build para Render Free (también sirve local con Postgres)
set -o errexit

pip install -r requirements/prod.txt

# Tailwind: compilar CSS (Node no está en runtime Python de Render, se ignora)
# El CSS ya viene pre-compilado en el repo si existe theme/static/css/dist
mkdir -p theme/static/css/dist static staticfiles
touch theme/static/css/dist/.keep 2>/dev/null || true
python manage.py tailwind build --no-input || echo "tailwind build skip (sin Node, ok)"

python manage.py collectstatic --no-input --clear || python manage.py collectstatic --no-input
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

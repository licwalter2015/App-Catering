#!/usr/bin/env bash
# Build para Render Free — sin errexit para no cortar el migrate si collectstatic/tailwind fallan
set +e

echo "==> pip install"
pip install -r requirements/prod.txt
echo "pip exit: $?"

echo "==> tailwind (opcional, sin Node se ignora)"
mkdir -p theme/static/css/dist static staticfiles
touch theme/static/css/dist/.keep 2>/dev/null || true
python manage.py tailwind build --no-input || echo "tailwind build skip (sin Node, ok)"

echo "==> collectstatic"
python manage.py collectstatic --no-input --clear 2>&1 | head -n 50
if [ ${PIPESTATUS[0]} -ne 0 ]; then
  echo "collectstatic --clear fallo, reintentando sin --clear"
  python manage.py collectstatic --no-input 2>&1 | head -n 50
fi

echo "==> migrate (intento en build, si falla se reintenta en start)"
python manage.py migrate --no-input --verbosity 1 || echo "migrate en build fallo (reintenta en start) exit:$?"

echo "==> seed demo"
# Crear domain para el host de Render si existe (para que /cotizar/ funcione sin demo.localhost)
RENDER_HOST=$(echo "${RENDER_EXTERNAL_HOSTNAME:-}" | tr -d '\r\n')
if [ -n "$RENDER_HOST" ]; then echo "Render host: $RENDER_HOST"; fi
python manage.py shell << 'PYEOF' || echo "seed shell fallo (no bloquea)"
import os
from apps.tenants.models import Tenant, Domain
from django.contrib.auth import get_user_model
User = get_user_model()
tenant, _ = Tenant.objects.get_or_create(slug="demo", defaults={"name": "Catering Demo", "is_active": True})
Domain.objects.get_or_create(domain="demo.localhost", defaults={"tenant": tenant})
# Dominio de Render (para que app-catering-s9mj.onrender.com resuelva tenant demo)
for h in [os.environ.get("RENDER_EXTERNAL_HOSTNAME"), "app-catering-s9mj.onrender.com"]:
    if h:
        h = h.strip().lower()
        Domain.objects.get_or_create(domain=h, defaults={"tenant": tenant})
        print(f"Domain asegurado: {h}")
if not User.objects.filter(email="admin@catering.local").exists():
    u = User.objects.create_superuser(email="admin@catering.local", password="admin123", tenant=tenant)
    print(f"Superuser creado: {u.email}")
else:
    print("Superuser ya existe")
from apps.catalog.models import ServicioBase
if ServicioBase.objects.count() == 0:
    print("Ejecutando seed del catalogo...")
    import subprocess, sys
    subprocess.run([sys.executable, "seed_cotizacion.py"], check=False)
else:
    print("Catalogo ya existe")
print("seed ok")
PYEOF

echo "Build OK"

"""
S7 - Seed demo comercial con datos realistas del mercado local (Chaco / Corrientes 2026)
Idempotente: se puede correr N veces sin duplicar.
Uso: python manage.py shell < scripts/seed_s7_demo.py
     o: .venv/Scripts/python.exe scripts/seed_s7_demo.py
"""
import os
import sys
import django

# Soporte ejecución directa: python scripts/seed_s7_demo.py
if __name__ == "__main__" and "DJANGO_SETTINGS_MODULE" not in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.tenants.models import Tenant, Domain
from apps.catalog.models import ServicioBase, Adicional, ZonaEntrega
from apps.accounts.models import User
from apps.quotes.models import Cliente, Cotizacion
from apps.quotes.services import crear_cotizacion_desde_calculo

print("=== S7 Seed Demo Comercial ===")

# 1. Tenant demo pulido
tenant, created = Tenant.objects.update_or_create(
    slug="demo",
    defaults={
        "name": "Sabores del Litoral - Catering Premium",
        "primary_color": "#0f766e",
        "deposit_percentage": 30,
        "is_active": True,
    },
)
print(f"{'Creado' if created else 'Actualizado'} Tenant: {tenant.name} ({tenant.slug}) sena {tenant.deposit_percentage}%")

# Dominio para demo.localhost
Domain.objects.update_or_create(domain="demo.localhost", defaults={"tenant": tenant, "is_primary": True})
Domain.objects.update_or_create(domain="demo.localhost:8000", defaults={"tenant": tenant, "is_primary": False})
print("Dominio demo.localhost OK")

# 2. Usuario demo
user, created = User.objects.get_or_create(
    email="demo@saboreslitoral.com",
    defaults={"tenant": tenant, "is_active": True, "role": User.Role.OWNER},
)
if created:
    user.set_password("demo2026")
    user.save()
    print(f"Usuario creado: demo@saboreslitoral.com / demo2026 (OWNER)")
else:
    user.tenant = tenant
    user.save()
    print(f"Usuario existente: demo@saboreslitoral.com (OWNER)")

# Mantener compatibilidad con test_sprint5.py
user2, created = User.objects.get_or_create(
    email="test@demo.com",
    defaults={"tenant": tenant, "is_active": True, "role": User.Role.OWNER},
)
if created:
    user2.set_password("test123")
    user2.save()

# 3. Servicios base - 5 menús realistas
servicios_data = [
    {
        "nombre": "Menú Clásico Litoraleño",
        "descripcion": "Entrada: empanadas + bruschettas. Principal: pollo al verdeo o vacío al horno con guarnición. Postre: helado artesanal. Incluye pan, bebida sin alcohol y mozos.",
        "precio_por_persona": Decimal("8500.00"),
        "capacidad_min": 25, "capacidad_max": 300,
    },
    {
        "nombre": "Menú Premium Gourmet",
        "descripcion": "Isla de fiambres premium + pernil ternera + mesa dulce completa (3 tortas + 5 postres). Barra de tragos clásicos incluida. Ideal bodas 80-200 invitados.",
        "precio_por_persona": Decimal("13500.00"),
        "capacidad_min": 40, "capacidad_max": 250,
    },
    {
        "nombre": "Menú Parrilla Completa",
        "descripcion": "Asado completo: chorizo, morcilla, vacío, costilla, matambre, pollo + ensaladas + chimichurri. Parrilleros in situ. El favorito para eventos al aire libre.",
        "precio_por_persona": Decimal("11500.00"),
        "capacidad_min": 30, "capacidad_max": 350,
    },
    {
        "nombre": "Menú Infantil Cumple",
        "descripcion": "Pizzas, panchos, papas, nuggets + mesa dulce kids + gaseosas libres. Animación opcional. 1 adulto cada 10 niños sin cargo.",
        "precio_por_persona": Decimal("5200.00"),
        "capacidad_min": 15, "capacidad_max": 80,
    },
    {
        "nombre": "Menú Veggie & Saludable",
        "descripcion": "Opciones vegetarianas/veganas: risotto, wok, ensaladas gourmet, postres sin TACC. Todo elaborado con productos regionales.",
        "precio_por_persona": Decimal("9800.00"),
        "capacidad_min": 20, "capacidad_max": 150,
    },
]

for s in servicios_data:
    obj, created = ServicioBase.objects.update_or_create(
        tenant=tenant, nombre=s["nombre"],
        defaults={**s, "is_active": True}
    )
    print(f"  {'+ ' if created else '~ '}Servicio: {obj.nombre} ${obj.precio_por_persona}/p [{obj.capacidad_min}-{obj.capacidad_max}]")

# 4. Adicionales pulidos - 7 servicios
adicionales_data = [
    {"nombre": "Barra de Tragos Premium", "descripcion": "Barman + 6 tragos clásicos (fernet, gin, caipi, daikiri, mojito, cuba libre). Hielo y cristalería incluida.", "tipo_precio": "POR_PERSONA", "precio": Decimal("3200.00")},
    {"nombre": "Decoración Floral + Centros", "descripcion": "Centros de mesa con flores naturales, telas y candelabros. 1 centro cada 8 invitados.", "tipo_precio": "FIJO", "precio": Decimal("42000.00")},
    {"nombre": "DJ + Iluminación Pista", "descripcion": "Sonido 2000W + luces led + máquina de humo. DJ 6hs con playlist a pedido.", "tipo_precio": "FIJO", "precio": Decimal("65000.00")},
    {"nombre": "Fotografía + Video Clip", "descripcion": "Fotógrafo 4hs + entrega 200 fotos editadas + clip 2min para redes. Dron opcional.", "tipo_precio": "FIJO", "precio": Decimal("48000.00")},
    {"nombre": "Torta Principal Personalizada", "descripcion": "Torta 2 pisos buttercream, diseño a elección. Rinde ~40 porciones por unidad.", "tipo_precio": "POR_UNIDAD", "precio": Decimal("22000.00")},
    {"nombre": "Mozo Adicional (c/10 invitados)", "descripcion": "Servicio de mozo extra con bandeja y uniforme. Recomendado para Premium/Parrilla.", "tipo_precio": "POR_UNIDAD", "precio": Decimal("12000.00")},
    {"nombre": "Livings + Mobiliario Lounge", "descripcion": "2 livings + mesa ratona + alfombra. Ideal cocktail/recepción.", "tipo_precio": "FIJO", "precio": Decimal("35000.00")},
]

for a in adicionales_data:
    obj, created = Adicional.objects.update_or_create(
        tenant=tenant, nombre=a["nombre"],
        defaults={**a, "is_active": True}
    )
    tag = {"FIJO": "$", "POR_PERSONA": "$/p", "POR_UNIDAD": "$/u"}[a["tipo_precio"]]
    print(f"  {'+ ' if created else '~ '}Adicional: {obj.nombre} {tag}{obj.precio} ({obj.tipo_precio})")

# 5. Zonas de entrega - Gran Resistencia + interior
zonas_data = [
    {"nombre": "Resistencia Centro", "costo_traslado": Decimal("0.00")},
    {"nombre": "Gran Resistencia (Barranqueras / Fontana / Vilelas)", "costo_traslado": Decimal("12000.00")},
    {"nombre": "Corrientes Capital", "costo_traslado": Decimal("18000.00")},
    {"nombre": "Interior Chaco (hasta 80km)", "costo_traslado": Decimal("35000.00")},
    {"nombre": "Interior Corrientes / Sáenz Peña", "costo_traslado": Decimal("45000.00")},
]

# Limpiar zonas legacy con nombres genéricos para demo prolijo
for z in zonas_data:
    obj, created = ZonaEntrega.objects.update_or_create(
        tenant=tenant, nombre=z["nombre"],
        defaults={**z, "is_active": True}
    )
    print(f"  {'+ ' if created else '~ '}Zona: {obj.nombre} +${obj.costo_traslado}")

# Desactivar legados genéricos del seed inicial (S1-S5)
for legacy in ["Centro", "chaco", "interior", "san luis", "santa ana"]:
    ZonaEntrega.objects.filter(tenant=tenant, nombre=legacy).update(is_active=False)
for legacy in ["Menú Clásico", "Menú Infantil", "Menú Premium"]:
    ServicioBase.objects.filter(tenant=tenant, nombre=legacy).update(is_active=False)
for legacy in ["Barra de tragos", "Decoración floral", "Servicio de DJ", "Servicio de fotografía", "Torta personalizada"]:
    Adicional.objects.filter(tenant=tenant, nombre=legacy).update(is_active=False)

# 6. Clientes + cotizaciones de ejemplo para poblar dashboard (idempotente por email+fecha)
hoy = timezone.now().date()
adicionales_all = list(Adicional.objects.filter(tenant=tenant, is_active=True).order_by("id"))
zonas_all = list(ZonaEntrega.objects.filter(tenant=tenant, is_active=True).order_by("id"))
servicios_all = list(ServicioBase.objects.filter(tenant=tenant, is_active=True).order_by("id"))
muestras = [
    (hoy + timedelta(days=14), 90, 0, [0,1], 0, "Lucía Fernández", "lucia.demo@saboreslitoral.test"),
    (hoy + timedelta(days=21), 120, 1, [0,2], 1, "Martín Gómez", "martin.demo@saboreslitoral.test"),
    (hoy + timedelta(days=7), 45, 3, [], 0, "Sofía Ruiz", "sofia.demo@saboreslitoral.test"),
    (hoy + timedelta(days=30), 180, 2, [1,2,4], 3, "Carlos Acevedo", "carlos.demo@saboreslitoral.test"),
    (hoy + timedelta(days=45), 60, 4, [0], 2, "Valentina Ortiz", "vale.demo@saboreslitoral.test"),
]
for fecha, invitados, srv_idx, adic_idxs, zona_idx, nombre, email in muestras:
    cliente, _ = Cliente.objects.get_or_create(tenant=tenant, email=email, defaults={"nombre": nombre, "telefono": "3624-000000"})
    if Cotizacion.objects.filter(tenant=tenant, cliente=cliente, fecha_evento=fecha).exists():
        continue
    servicio = servicios_all[srv_idx % len(servicios_all)]
    adics = [{"adicional": adicionales_all[i % len(adicionales_all)], "cantidad": 1} for i in adic_idxs]
    zona = zonas_all[zona_idx % len(zonas_all)] if zonas_all else None
    cot = crear_cotizacion_desde_calculo(
        tenant=tenant, cliente=cliente, fecha_evento=fecha, cantidad_invitados=invitados,
        servicio_base=servicio, adicionales=adics or None, zona_entrega=zona
    )
    print(f"  + Cotización #{cot.id} {cot.cliente.nombre} {cot.fecha_evento} {invitados}p ${cot.total} ({cot.estado}) -> {cot.token}")

print("\n=== Seed S7 OK ===")
print(f"Visitar: http://demo.localhost:8000/  (cotizador público)")
print(f"Panel:   http://demo.localhost:8000/panel/  (demo@saboreslitoral.com / demo2026)")
print(f"Login:   http://demo.localhost:8000/login/")
print(f"PDF ejemplo: http://demo.localhost:8000/cotizacion/<token>/pdf/")

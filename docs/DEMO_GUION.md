# Guion Demo Comercial 3 min — Tablet / Celular

Objetivo: mostrar ciclo completo cotizacion -> sena automatica fuera de horario, cero sobreventa.

## Pre-requisitos (1 min antes)
- `docker compose up -d` y `python manage.py runserver` corriendo
- `python scripts/seed_s7_demo.py` ya ejecutado
- Abrir en tablet: `http://demo.localhost:8000/` (cotizador) y `http://demo.localhost:8000/panel/` en otra pestaña
- Login panel: `demo@saboreslitoral.com / demo2026`

## 0:00-0:30 — Hook (dolor)
> "¿Cuántas veces te pidieron presupuesto a las 11 de la noche y perdiste la fecha porque no respondiste a tiempo? Con Sabores del Litoral la fecha se reserva sola cuando el cliente sena, incluso domingo 3AM. Y nunca sobrevendes un día: la base lo bloquea."

Mostrar `PLAN.md:188` mitigaciones y `apps/bookings/models.py:28` UNIQUE(tenant,fecha).

## 0:30-1:30 — Cotizador 5 pasos (mobile-first)
En `http://demo.localhost:8000/`:
1. **Fecha** — calendario, fechas ocupadas deshabilitadas (ej 2026-11-20 ya señada). Elegir `hoy+14`.
2. **Invitados** — 90 (valida min/max del servicio).
3. **Menu** — elegir `Menú Parrilla Completa $11.500/p` (foto + precio). Tarjetas `templates/quotes/wizard.html:38`.
4. **Adicionales** — tildar `Barra Premium` + `DJ`, zona `Gran Resistencia +$12k`. Mostrar total en vivo HTMX `templates/quotes/_total_htmx.html:1` y barra progreso 20->80%.
5. **Datos** — `Lucía Demo / lucia@test.com` -> **Enviar**.

## 1:30-2:00 — Presupuesto + PDF
Redirige a `templates/quotes/detail.html:1` con token UUID `apps/quotes/models.py:89`. Mostrar:
- Detalle con snapshot de precios `apps/quotes/models.py:114`
- Total, seña 30% `apps/quotes/services.py:70`
- Botones **Descargar PDF** `apps/quotes/views.py:99` y **Reservar fecha (seña)** `apps/payments/services.py:16`

Abrir PDF: membrete con logo, colores tenant `templates/base.html:16` CSS variables.

## 2:00-2:30 — Sena + anti-sobreventa
Click **Reservar fecha** -> Checkout MP (modo test). Volver como `APROBADO`.

Explicar transaccion atomica `apps/payments/services.py:122`:
```
with transaction.atomic():
  FechaReservada.create()  # UNIQUE falla si tomada
  cotizacion.estado = SEÑADA
  pago.estado = APROBADO
```
Si fecha tomada en el interin -> `IntegrityError` -> pago `REEMBOLSADO` `apps/payments/services.py:158`. Cero sobreventa.

Mostrar email automatico consola `apps/payments/services.py:173`.

## 2:30-3:00 — Panel del dueño
En `http://demo.localhost:8000/panel/` `apps/dashboard/views.py:12`:
- Metricas mes: cotizaciones 13, conversion, ingresos $624.900 `apps/dashboard/views.py:29`
- Proximos eventos 30 dias `apps/dashboard/views.py:39`
- Calendario mensual `templates/dashboard/calendario.html:1` — fecha nueva en verde
- Lista cotizaciones con filtros estado `templates/dashboard/cotizaciones.html:1`

## Cierre
> "Setup inicial: tu logo, colores, menú y MP. Abono mensual incluye hosting, SSL wildcard `*.tudominio.com` `nginx/conf.d/default.conf:53`, backups y soporte. ¿Agendamos carga de tu carta real?"

## Checklist tablet
- [ ] Brillo 100%, no notificaciones
- [ ] 4G/wifi probado
- [ ] Demo datos pulidos `scripts/seed_s7_demo.py`
- [ ] Verificacion `scripts/verify_demo.py` OK (anti-sobreventa, aislamiento, snapshot)

## Troubleshooting demo
- `demo.localhost` no resuelve -> agregar `127.0.0.1 demo.localhost` a hosts o usar `localhost:8000` con `request.tenant=None` fallback
- Total no actualiza -> `python manage.py check` y revisar `apps/quotes/views.py:120` HTMX endpoint

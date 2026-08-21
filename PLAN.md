# Plan del Sistema — SaaS de Catering (Cotizador Dinámico)

## 1. Decisiones de Arquitectura

### Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Lenguaje | Python 3.12 | Requerimiento del proyecto |
| Framework | Django 5.x | Admin nativo, ORM robusto, ecosistema maduro |
| Base de datos | MySQL 8 | Requerimiento del proyecto |
| UI | Tailwind CSS + HTMX | UI profesional con interactividad sin SPA |
| Estilos base | django-tailwind | Integración limpia de Tailwind con Django |
| Pagos | SDK `mercadopago` (Python) | Seña + webhooks |
| Servidor WSGI | Gunicorn | Estándar para Django en producción |
| Proxy / SSL | Nginx + Certbot (Let's Encrypt) | Proxy inverso y HTTPS gratuito |
| Tareas async | django-db-task ó Celery+Redis (Fase 2+) | Expiración de cotizaciones, recordatorios |
| CI/CD | GitHub Actions | Deploy automático al VPS |

### Estrategia Multi-tenant

**Esquema compartido con discriminador de tenant** (shared schema):

- Una sola base MySQL, una sola instancia de la app.
- Cada empresa de catering es un registro en la tabla `tenants`.
- **Todas** las tablas de negocio llevan FK a `Tenant`.
- Un middleware resuelve el tenant actual a partir del **subdominio** (`empresa1.tudominio.com`) o dominio personalizado, y un manager personalizado del ORM filtra automáticamente por tenant (imposible mezclar datos entre clientes).
- Cada tenant puede configurar: logo, colores, catálogo, porcentaje de seña, zonas de entrega.

> Nota: `django-tenants` no es opción porque depende de schemas de PostgreSQL. Con MySQL, el discriminador por columna es el enfoque correcto y más simple de operar.

### Regla de oro del motor de precios

- Las cotizaciones en estado **BORRADOR/ENVIADA** se recalculan si cambian los precios del catálogo.
- Al **señarse**, se congela un *snapshot* de precios en los ítems de la cotización: cambios posteriores del catálogo **no** afectan eventos ya señados.

---

## 2. Estructura del Proyecto

```
App-Catering/
├── config/                    # settings (base.py, dev.py, prod.py), urls, wsgi
├── apps/
│   ├── tenants/               # Tenant, dominio, configuración visual, middleware
│   ├── accounts/              # Usuarios (dueño de catering, staff), roles
│   ├── catalog/               # ServiciosBase, Adicionales, zonas de entrega
│   ├── quotes/                # Cotizacion, CotizacionItem, motor de cálculo
│   ├── bookings/              # Evento, FechaReservada (anti-sobreventa)
│   ├── payments/              # Pago, integración MercadoPago, webhooks
│   └── dashboard/             # Panel del dueño (métricas, calendario)
├── templates/                 # Base, cotizador público, panel
├── theme/                     # App django-tailwind (config Tailwind)
├── static/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── Dockerfile                     # Imagen de producción (Gunicorn)
├── docker-compose.yml             # MySQL 8.4 local (dev)
├── docker-compose.prod.yml        # MySQL + Django + Nginx + Certbot (prod)
├── nginx/                         # Configuración de Nginx (reverse proxy + SSL)
├── scripts/
│   ├── setup-vps.sh               # Configuración inicial del VPS
│   └── deploy.sh                  # Despliegue manual
├── docs/DEPLOY.md                 # Guía completa de despliegue
├── .github/workflows/deploy.yml
└── PLAN.md
```

---

## 3. Modelo de Datos (entidades clave)

### tenants
- **Tenant**: nombre, slug (subdominio), logo, color primario, porcentaje_seña (default 30%), credenciales MP propias (cada catering cobra con su cuenta), activo.
- **Usuario** (accounts): email como login, FK a Tenant, rol (OWNER / STAFF).

### catalog
- **ServicioBase**: tenant, nombre (ej. "Menú Clásico"), descripción, precio_por_persona, capacidad_min/max, activo.
- **Adicional**: tenant, nombre, tipo_precio (FIJO | POR_UNIDAD | POR_PERSONA), precio, activo.
- **ZonaEntrega**: tenant, nombre, costo_traslado.

### quotes
- **Cotizacion**: tenant, cliente (FK), fecha_evento, cantidad_invitados, servicio_base (FK), estado (`BORRADOR | ENVIADA | SEÑADA | CONFIRMADA | VENCIDA | CANCELADA`), subtotal, total, token público (UUID para que el cliente vea su presupuesto sin login), expira_en.
- **CotizacionItem**: cotizacion (FK), descripcion, cantidad, **precio_unitario_snapshot**, subtotal. *(Es la foto de precios congelada.)*
- **Cliente**: tenant, nombre, email, teléfono.

### bookings
- **Evento**: tenant, cotizacion (FK), fecha, estado, datos del cliente.
- **FechaReservada**: tenant, fecha, evento (FK). Constraint `UNIQUE(tenant, fecha)` → **garantía a nivel base de datos contra sobreventa de un mismo día**.

### payments
- **Pago**: tenant, cotizacion (FK), monto, mp_payment_id, estado (`PENDIENTE | ACREDITADO | RECHAZADO | REEMBOLSADO`), webhook_payload (JSON, para auditoría).

---

## 4. Flujos de Negocio

### 4.1 Cotizador público (wizard de 5 pasos, sin registro)
1. **Fecha**: selector de calendario; HTMX consulta disponibilidad del tenant en tiempo real (fechas ocupadas deshabilitadas).
2. **Invitados**: cantidad (valida min/max del servicio).
3. **Menú**: elige ServicioBase (tarjetas con foto y precio/persona).
4. **Adicionales**: checkboxes/cantidades; el total se recalcula en vivo vía HTMX.
5. **Datos de contacto** → se emite la cotización con link único (`/cotizacion/<uuid>/`) y PDF descargable.

### 4.2 Motor de cálculo
```
total = (precio_servicio × invitados) + Σ adicionales + costo_traslado
seña  = total × tenant.porcentaje_seña
```
Servicio Python puro (`services.py` en `quotes`), testeable, sin lógica en vistas.

### 4.3 Seña con MercadoPago
1. Desde el link de su cotización, el cliente presiona **"Reservar fecha"**.
2. Backend crea preferencia con el SDK de MP (Checkout Pro) y redirige.
3. MP notifica al **webhook** (`/pagos/webhook/`): se valida la firma, se consulta el pago a la API (nunca confiar solo en el webhook) y, si está acreditado, se ejecuta **transacción atómica**:
   ```python
   with transaction.atomic():
       FechaReservada.objects.create(tenant=..., fecha=...)  # UNIQUE → falla si ya está tomada
       cotizacion.estado = 'SEÑADA'
       pago.estado = 'ACREDITADO'
   ```
4. Si la fecha fue tomada en el ínterin → `IntegrityError` → se marca el pago para reembolso y se notifica. **Cero sobreventa.**
5. Emails automáticos: confirmación al cliente + aviso al dueño del catering.

### 4.4 Panel del dueño (Django Admin personalizado + dashboard)
- Calendario mensual de eventos.
- Lista de cotizaciones con filtros por estado y acciones (reenviar, marcar vencida).
- CRUD de catálogo y precios con fricción cero (admin nativo con `list_editable`).
- Métricas simples: cotizaciones del mes, tasa de conversión a seña, ingresos por señas.

---

## 5. UI Profesional

**Sistema de diseño (Tailwind):**
- Paleta por tenant (color primario configurable vía CSS variables).
- Tipografía: Inter o similar (Google Fonts).
- Componentes: tarjetas de menú, wizard con barra de progreso, calendario, badges de estado, tablas responsive, toasts de confirmación.

**Dos superficies:**
- **Pública** (cotizador + vista de presupuesto): diseño orientado a conversión, mobile-first (la demo se muestra desde tablet/celular).
- **Panel**: limpio y denso en información, pensado para uso diario.

---

## 6. Infraestructura y Despliegue (Fase 3)

- **Desarrollo local**: MySQL 8.4 vía Docker (`docker compose up -d`, puerto 3308, ver `docker-compose.yml`).
- **VPS Ubuntu Server** (hardening básico: UFW, fail2ban, SSH por clave, usuario no-root).
- **Gunicorn** (servicio systemd, auto-restart) detrás de **Nginx** (proxy inverso + estáticos + SSL con Certbot). Certificado wildcard `*.tudominio.com` para subdominios de tenants.
- **MySQL 8** en el mismo VPS al inicio; backups diarios automáticos (mysqldump + retención).
- **GitHub Actions**: push a `main` → corre tests → SSH al VPS → `git pull`, `pip install`, `migrate`, `collectstatic`, reload de Gunicorn (sin downtime perceptible).

---

## 7. Roadmap de Ejecución (sprints de 1-2 semanas)

| Sprint | Entregable | Estado |
|---|---|---|
| **S1 — Fundaciones** | Proyecto Django, settings por entorno, conexión MySQL, Tailwind andando, modelo Tenant + middleware de subdominios, login. | ✅ |
| **S2 — Catálogo** | CRUD de ServiciosBase/Adicionales/Zonas en admin personalizado. | ✅ |
| **S3 — Cotizador** | Wizard público completo + motor de cálculo + emisión de presupuesto con link UUID y PDF. | ✅ |
| **S4 — Reservas y pagos** | Checkout MP, webhooks, transacción atómica anti-sobreventa, emails de confirmación. | ✅ |
| **S5 — Panel y calendario** | Dashboard con calendario de eventos, gestión de cotizaciones, métricas básicas. | ✅ |
| **S6 — Infraestructura** | Dockerfile, docker-compose.prod, Nginx+SSL, CI/CD, scripts de VPS y guía (código listo). | 🔧 listo, falta VPS |
| **S7 — Demo comercial** | Instancia demo con datos realistas del mercado local (menús, precios, zonas). Pulido de UI para venta en vivo. | ⏳ |

---

## 8. Modelo Comercial (Fase 4)

- **Setup inicial**: parametrización del catálogo, branding (logo/colores), credenciales MP, capacitación.
- **Abono mensual**: hosting, mantenimiento, soporte y mejoras.
- **Venta consultiva**: demo en vivo desde tablet mostrando el ciclo completo (cotización → seña automática fuera de horario comercial).

---

## 9. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Sobreventa de fecha | UNIQUE(tenant, fecha) + transacción atómica en confirmación de pago |
| Webhook falso de MP | Validar firma + consultar el pago a la API antes de acreditar |
| Fuga de datos entre tenants | Manager del ORM con filtro automático + tests que lo verifican |
| Precios cambian tras la seña | Snapshot de precios en CotizacionItem al confirmar |

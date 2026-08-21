# Guía de Despliegue en Producción

Esta guía te lleva paso a paso desde cero hasta tener el sistema corriendo en un VPS con dominio propio.

## Requisitos previos

- Un VPS con Ubuntu 22.04 o superior (recomendado: 2GB RAM, 2 vCPU, 40GB disco)
- Un dominio propio (ej: `tudominio.com`)
- Acceso root al VPS vía SSH
- Cuenta en Docker Hub (para el pipeline CI/CD)
- Cuenta en GitHub con el repositorio del proyecto

## Paso 1: Comprar y configurar el VPS

### Opciones recomendadas (Argentina/Latam)
- **DigitalOcean**: desde USD 12/mes (2GB RAM)
- **Vultr**: desde USD 12/mes
- **Hetzner**: desde EUR 4.5/mes (muy buena relación precio/calidad, servidores en Europa)
- **Hostinger VPS**: desde USD 6/mes

### Configuración inicial del VPS

1. **Conectarte por SSH como root:**
```bash
ssh root@TU_IP_DEL_VPS
```

2. **Ejecutar el script de setup:**
```bash
# Copiar el script al VPS
scp scripts/setup-vps.sh root@TU_IP_DEL_VPS:/root/

# Ejecutar
ssh root@TU_IP_DEL_VPS
chmod +x /root/setup-vps.sh
./setup-vps.sh
```

3. **Configurar acceso SSH sin contraseña:**
```bash
# Desde tu máquina local
ssh-copy-id deploy@TU_IP_DEL_VPS

# Probar conexión
ssh deploy@TU_IP_DEL_VPS
```

## Paso 2: Configurar el dominio

1. **Apuntar tu dominio al VPS:**
   - En tu registrador de dominios (Namecheap, GoDaddy, etc.), crear registros DNS:
   ```
   Tipo    Nombre    Valor
   A       @         TU_IP_DEL_VPS
   A       www       TU_IP_DEL_VPS
   A       *         TU_IP_DEL_VPS   (wildcard para subdominios de tenants)
   ```
   - Esperar propagación DNS (5-30 minutos)

2. **Verificar propagación:**
```bash
# Desde tu máquina local
ping tudominio.com
ping demo.tudominio.com
```

## Paso 3: Clonar el repositorio en el VPS

```bash
ssh deploy@TU_IP_DEL_VPS
cd /opt/catering
git clone https://github.com/TU_USUARIO/App-Catering.git .
```

## Paso 4: Configurar variables de entorno

```bash
cd /opt/catering
cp .env.example .env
nano .env
```

**Variables obligatorias:**
```bash
# Django
SECRET_KEY=genera-una-clave-segura-aqui
ALLOWED_HOSTS=tudominio.com,www.tudominio.com,.tudominio.com

# Base de datos
DB_ROOT_PASSWORD=contraseña_segura_para_root
DB_NAME=catering_saas
DB_USER=catering_user
DB_PASSWORD=contraseña_segura_para_usuario

# MercadoPago (access token de producción)
MP_ACCESS_TOKEN=APP_USR-xxxx...
```

**Generar SECRET_KEY segura:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Paso 5: Configurar Nginx con tu dominio

Editar `nginx/conf.d/default.conf` y reemplazar `tudominio.com` por tu dominio real:

```bash
nano nginx/conf.d/default.conf
# Reemplazar todas las ocurrencias de "tudominio.com" por tu dominio
```

## Paso 6: Primer despliegue

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Esto va a:
- Descargar las imágenes de Docker
- Levantar MySQL, Django y Nginx
- Ejecutar migraciones
- Recopilar archivos estáticos

## Paso 7: Obtener certificado SSL (Let's Encrypt)

**Opción A: Certificado simple (sin wildcard)**
```bash
# Detener Nginx temporalmente
docker compose -f docker-compose.prod.yml stop nginx

# Obtener certificado
docker run -it --rm \
  -v ./certbot/conf:/etc/letsencrypt \
  -v ./certbot/www:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d tudominio.com -d www.tudominio.com

# Reiniciar Nginx
docker compose -f docker-compose.prod.yml start nginx
```

**Opción B: Certificado wildcard (recomendado para subdominios)**
```bash
# Usar DNS challenge (requiere acceso a tu panel de DNS)
docker run -it --rm \
  -v ./certbot/conf:/etc/letsencrypt \
  certbot/certbot certonly --manual \
  --preferred-challenges dns \
  -d tudominio.com -d *.tudominio.com

# Seguir las instrucciones (crear registro TXT en tu DNS)
```

## Paso 8: Crear superusuario

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Paso 9: Configurar CI/CD (despliegue automático)

### En GitHub:

1. Ir a tu repositorio → Settings → Secrets and variables → Actions

2. Agregar los siguientes secrets:

| Secret | Valor |
|--------|-------|
| `DOCKER_USERNAME` | Tu usuario de Docker Hub |
| `DOCKER_PASSWORD` | Tu password/token de Docker Hub |
| `VPS_HOST` | IP de tu VPS |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Contenido de tu clave privada SSH (`cat ~/.ssh/id_rsa`) |

### Cómo funciona:

Cada vez que hagas push a `main`:
1. GitHub Actions construye la imagen Docker
2. La sube a Docker Hub
3. Se conecta por SSH al VPS
4. Descarga la nueva imagen
5. Reinicia los servicios
6. Ejecuta migraciones

## Paso 10: Verificar que todo funciona

```bash
# Ver estado de contenedores
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Probar en el navegador
# https://tudominio.com (landing de plataforma)
# https://demo.tudominio.com (tenant de prueba)
# https://tudominio.com/admin/ (panel admin)
```

## Comandos útiles

```bash
# Reiniciar todos los servicios
docker compose -f docker-compose.prod.yml restart

# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f web

# Entrar al contenedor web
docker compose -f docker-compose.prod.yml exec web bash

# Backup de base de datos
docker compose -f docker-compose.prod.yml exec db mysqldump -u root -p catering_saas > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker compose -f docker-compose.prod.yml exec -T db mysql -u root -p catering_saas < backup_20260120.sql

# Renovar certificado SSL (automático con certbot container)
# O manualmente:
docker compose -f docker-compose.prod.yml run --rm certbot renew
```

## Troubleshooting

### El sitio no carga
```bash
# Verificar que los contenedores están corriendo
docker compose -f docker-compose.prod.yml ps

# Ver logs de Nginx
docker compose -f docker-compose.prod.yml logs nginx

# Ver logs de Django
docker compose -f docker-compose.prod.yml logs web
```

### Error de base de datos
```bash
# Verificar que MySQL está healthy
docker compose -f docker-compose.prod.yml ps db

# Ver logs de MySQL
docker compose -f docker-compose.prod.yml logs db

# Reiniciar MySQL
docker compose -f docker-compose.prod.yml restart db
```

### Error 502 Bad Gateway
```bash
# Verificar que Django está corriendo
docker compose -f docker-compose.prod.yml ps web

# Ver logs de Django
docker compose -f docker-compose.prod.yml logs web

# Reiniciar Django
docker compose -f docker-compose.prod.yml restart web
```

### Certificado SSL vencido
```bash
# Renovar certificado
docker compose -f docker-compose.prod.yml run --rm certbot renew

# Reiniciar Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

## Mantenimiento

### Backups automáticos (recomendado)

Crear cron job para backups diarios:
```bash
# Editar crontab
crontab -e

# Agregar línea (backup diario a las 3 AM)
0 3 * * * cd /opt/catering && docker compose -f docker-compose.prod.yml exec -T db mysqldump -u root -pTU_PASSWORD catering_saas | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Actualizaciones de seguridad

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Actualizar imágenes Docker
cd /opt/catering
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Monitoreo básico

```bash
# Uso de recursos
docker stats

# Espacio en disco
df -h

# Logs del sistema
journalctl -u docker -f
```

## Próximos pasos

Una vez que todo esté funcionando:

1. **Crear tenants de prueba** desde el admin
2. **Configurar MercadoPago** con credenciales de producción
3. **Probar el flujo completo** de cotización y pago
4. **Monitorear logs** los primeros días
5. **Configurar alertas** (opcional: UptimeRobot, Sentry)

## Soporte

Si tenés problemas:
- Revisar logs: `docker compose -f docker-compose.prod.yml logs -f`
- Verificar que todos los contenedores están "Up": `docker compose -f docker-compose.prod.yml ps`
- Consultar la documentación de Docker: https://docs.docker.com/
- Consultar la documentación de Django: https://docs.djangoproject.com/

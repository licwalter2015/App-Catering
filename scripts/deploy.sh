#!/bin/bash
# Script de despliegue manual
# Ejecutar desde /opt/catering como usuario deploy

set -e

echo "=== Desplegando aplicación ==="

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: No se encontró docker-compose.prod.yml"
    echo "Asegurate de estar en /opt/catering"
    exit 1
fi

# Pull de última imagen
echo "Descargando última imagen..."
docker compose -f docker-compose.prod.yml pull

# Levantar servicios
echo "Iniciando servicios..."
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
sleep 10

# Ejecutar migraciones
echo "Ejecutando migraciones..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Limpiar imágenes antiguas
echo "Limpiando imágenes antiguas..."
docker image prune -f

echo ""
echo "=== Despliegue completado ==="
echo ""
echo "Verificar estado:"
echo "  docker compose -f docker-compose.prod.yml ps"
echo ""
echo "Ver logs:"
echo "  docker compose -f docker-compose.prod.yml logs -f"

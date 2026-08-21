#!/bin/bash
# Script de configuración inicial del VPS
# Ejecutar como root o con sudo

set -e

echo "=== Configuración inicial del VPS ==="

# Actualizar sistema
echo "Actualizando sistema..."
apt update && apt upgrade -y

# Instalar dependencias
echo "Instalando dependencias..."
apt install -y \
    curl \
    git \
    ufw \
    fail2ban \
    docker.io \
    docker-compose-plugin

# Configurar firewall
echo "Configurando firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configurar fail2ban
echo "Configurando fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Crear usuario de deploy (opcional, recomendado)
echo "Creando usuario de deploy..."
if ! id -u deploy &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
    usermod -aG docker deploy
    mkdir -p /home/deploy/.ssh
    cp ~/.ssh/authorized_keys /home/deploy/.ssh/
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    chmod 600 /home/deploy/.ssh/authorized_keys
fi

# Crear directorio de la aplicación
echo "Creando directorio de la aplicación..."
mkdir -p /opt/catering
chown deploy:deploy /opt/catering

# Iniciar Docker
echo "Iniciando Docker..."
systemctl enable docker
systemctl start docker

echo ""
echo "=== Configuración completada ==="
echo ""
echo "Próximos pasos:"
echo "1. Copiar tu clave SSH pública al usuario deploy:"
echo "   ssh-copy-id deploy@TU_IP_DEL_VPS"
echo ""
echo "2. Clonar el repositorio:"
echo "   su - deploy"
echo "   cd /opt/catering"
echo "   git clone https://github.com/TU_USUARIO/App-Catering.git ."
echo ""
echo "3. Configurar variables de entorno:"
echo "   cp .env.example .env"
echo "   nano .env  # Editar con tus valores"
echo ""
echo "4. Ejecutar deploy inicial:"
echo "   ./scripts/deploy.sh"

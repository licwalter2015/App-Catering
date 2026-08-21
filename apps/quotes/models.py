import uuid
from django.db import models
from django.core.validators import MinValueValidator


class Cliente(models.Model):
    """Datos de contacto del cliente que solicita la cotización."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='clientes',
    )
    nombre = models.CharField('nombre completo', max_length=180)
    email = models.EmailField('email')
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    notas = models.TextField('notas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nombre} <{self.email}>'


class Cotizacion(models.Model):
    """Presupuesto generado por el cotizador público."""

    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        ENVIADA = 'ENVIADA', 'Enviada'
        SENADA = 'SENADA', 'Señada'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        VENCIDA = 'VENCIDA', 'Vencida'
        CANCELADA = 'CANCELADA', 'Cancelada'

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='cotizaciones',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='cotizaciones',
    )
    fecha_evento = models.DateField('fecha del evento')
    cantidad_invitados = models.PositiveSmallIntegerField('cantidad de invitados')
    servicio_base = models.ForeignKey(
        'catalog.ServicioBase',
        on_delete=models.PROTECT,
        related_name='cotizaciones',
    )
    zona_entrega = models.ForeignKey(
        'catalog.ZonaEntrega',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cotizaciones',
    )
    estado = models.CharField(
        'estado',
        max_length=15,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    subtotal = models.DecimalField(
        'subtotal',
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total = models.DecimalField(
        'total',
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    sena = models.DecimalField(
        'seña',
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Monto de seña calculado según porcentaje del tenant.',
    )
    token = models.UUIDField(
        'token público',
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text='Identificador público para compartir el presupuesto.',
    )
    expira_en = models.DateTimeField(
        'expira el',
        null=True,
        blank=True,
        help_text='Fecha y hora de expiración de la cotización.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'cotización'
        verbose_name_plural = 'cotizaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'Cotización #{self.id} - {self.cliente.nombre} ({self.get_estado_display()})'


class CotizacionItem(models.Model):
    """Línea de detalle de una cotización (snapshot de precios)."""

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='items',
    )
    descripcion = models.CharField('descripción', max_length=255)
    cantidad = models.PositiveSmallIntegerField('cantidad', default=1)
    precio_unitario_snapshot = models.DecimalField(
        'precio unitario (snapshot)',
        max_digits=10,
        decimal_places=2,
        help_text='Precio al momento de crear la cotización.',
    )
    subtotal = models.DecimalField(
        'subtotal',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = 'ítem de cotización'
        verbose_name_plural = 'ítems de cotización'

    def __str__(self):
        return f'{self.descripcion} x{self.cantidad}'

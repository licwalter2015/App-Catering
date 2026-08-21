from django.core.validators import MinValueValidator
from django.db import models


class ServicioBase(models.Model):
    """Menú o servicio base que se cobra por persona."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='servicios_base',
    )
    nombre = models.CharField('nombre', max_length=120)
    descripcion = models.TextField('descripción', blank=True)
    precio_por_persona = models.DecimalField(
        'precio por persona',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    capacidad_min = models.PositiveSmallIntegerField(
        'capacidad mínima',
        default=10,
        help_text='Cantidad mínima de invitados para este servicio.',
    )
    capacidad_max = models.PositiveSmallIntegerField(
        'capacidad máxima',
        default=500,
        help_text='Cantidad máxima de invitados para este servicio.',
    )
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'servicio base'
        verbose_name_plural = 'servicios base'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} (${self.precio_por_persona}/persona)'


class Adicional(models.Model):
    """Servicio adicional con precio fijo, por unidad o por persona."""

    class TipoPrecio(models.TextChoices):
        FIJO = 'FIJO', 'Precio fijo'
        POR_UNIDAD = 'POR_UNIDAD', 'Por unidad'
        POR_PERSONA = 'POR_PERSONA', 'Por persona'

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='adicionales',
    )
    nombre = models.CharField('nombre', max_length=120)
    descripcion = models.TextField('descripción', blank=True)
    tipo_precio = models.CharField(
        'tipo de precio',
        max_length=15,
        choices=TipoPrecio.choices,
        default=TipoPrecio.FIJO,
    )
    precio = models.DecimalField(
        'precio',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'adicional'
        verbose_name_plural = 'adicionales'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} (${self.precio} - {self.get_tipo_precio_display()})'


class ZonaEntrega(models.Model):
    """Zona geográfica con costo de traslado."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='zonas_entrega',
    )
    nombre = models.CharField('nombre de la zona', max_length=120)
    costo_traslado = models.DecimalField(
        'costo de traslado',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'zona de entrega'
        verbose_name_plural = 'zonas de entrega'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} (+${self.costo_traslado})'

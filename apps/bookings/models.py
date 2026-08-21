from django.db import models
from django.core.exceptions import ValidationError


class FechaReservada(models.Model):
    """
    Garantía anti-sobreventa: una fecha por tenant.
    La constraint UNIQUE(tenant, fecha) asegura a nivel de base de datos
    que nunca haya dos eventos el mismo día para el mismo tenant.
    """

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='fechas_reservadas',
    )
    fecha = models.DateField('fecha reservada')
    evento = models.OneToOneField(
        'Evento',
        on_delete=models.CASCADE,
        related_name='fecha_reservada',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'fecha reservada'
        verbose_name_plural = 'fechas reservadas'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'fecha'],
                name='unique_fecha_por_tenant',
            )
        ]

    def __str__(self):
        return f'{self.tenant.name} - {self.fecha}'


class Evento(models.Model):
    """Evento confirmado tras la seña."""

    class Estado(models.TextChoices):
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        COMPLETADO = 'COMPLETADO', 'Completado'

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='eventos',
    )
    cotizacion = models.OneToOneField(
        'quotes.Cotizacion',
        on_delete=models.PROTECT,
        related_name='evento',
    )
    fecha = models.DateField('fecha del evento')
    estado = models.CharField(
        'estado',
        max_length=15,
        choices=Estado.choices,
        default=Estado.CONFIRMADO,
    )
    notas = models.TextField('notas internas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cotizacion.cliente.nombre} - {self.fecha}'

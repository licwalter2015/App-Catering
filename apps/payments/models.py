from django.db import models


class Pago(models.Model):
    """Registro de pagos procesados vía MercadoPago."""

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        REEMBOLSADO = 'REEMBOLSADO', 'Reembolsado'

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='pagos',
    )
    cotizacion = models.ForeignKey(
        'quotes.Cotizacion',
        on_delete=models.PROTECT,
        related_name='pagos',
    )
    monto = models.DecimalField('monto', max_digits=12, decimal_places=2)
    mp_payment_id = models.CharField(
        'ID de pago MercadoPago',
        max_length=100,
        unique=True,
        help_text='Identificador único del pago en MercadoPago.',
    )
    mp_preference_id = models.CharField(
        'ID de preferencia MercadoPago',
        max_length=100,
        blank=True,
        help_text='ID de la preferencia de checkout creada.',
    )
    estado = models.CharField(
        'estado',
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    webhook_payload = models.JSONField(
        'payload del webhook',
        blank=True,
        null=True,
        help_text='Payload completo recibido del webhook para auditoría.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'pago'
        verbose_name_plural = 'pagos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pago #{self.mp_payment_id} - ${self.monto} ({self.get_estado_display()})'

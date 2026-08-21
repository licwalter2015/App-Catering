from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Tenant(models.Model):
    """Una empresa de catering cliente de la plataforma."""

    name = models.CharField('nombre comercial', max_length=120)
    slug = models.SlugField(
        'subdominio',
        unique=True,
        help_text='Identificador del subdominio: <slug>.tudominio.com',
    )
    logo = models.ImageField(upload_to='tenants/logos/', blank=True)
    primary_color = models.CharField(
        'color primario',
        max_length=7,
        default='#0f766e',
        help_text='Hexadecimal, ej: #0f766e',
    )
    deposit_percentage = models.PositiveSmallIntegerField(
        'porcentaje de seña',
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Porcentaje del total que se cobra como seña (1-100).',
    )
    mp_access_token = models.CharField(
        'access token de MercadoPago',
        max_length=255,
        blank=True,
        help_text='Credencial productiva de la cuenta MP del catering.',
    )
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'empresa (tenant)'
        verbose_name_plural = 'empresas (tenants)'

    def __str__(self):
        return self.name


class Domain(models.Model):
    """Dominio o subdominio asociado a un tenant."""

    domain = models.CharField('dominio', max_length=253, unique=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='domains',
    )
    is_primary = models.BooleanField('es primario', default=False)

    class Meta:
        verbose_name = 'dominio'
        verbose_name_plural = 'dominios'

    def __str__(self):
        return self.domain
